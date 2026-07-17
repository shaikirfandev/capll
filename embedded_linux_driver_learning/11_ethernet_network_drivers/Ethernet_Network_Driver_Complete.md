# Ethernet & Network Driver Development

## Level 1: Linux Network Stack Overview

```
Application: socket(AF_INET, SOCK_STREAM, ...)
        │ BSD socket API
        ▼
Socket Layer (net/socket.c)
        │
        ▼
Transport Layer: TCP/UDP (net/ipv4/tcp.c, udp.c)
        │
        ▼
Network Layer: IP (net/ipv4/ip_output.c)
        │
        ▼
Netfilter (iptables hooks)
        │
        ▼
Traffic Control (qdisc, tc)
        │
        ▼
Network Device Layer (net/core/dev.c)
        │ netdev API
        ▼
NIC Driver (drivers/net/ethernet/...)
        │ MMIO, DMA, IRQ
        ▼
NIC Hardware
```

---

## Level 2: Network Driver Architecture

### 2.1 net_device Structure

```c
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/if_ether.h>
#include <linux/dma-mapping.h>

struct my_nic {
    struct net_device    *netdev;    /* kernel netdev object */
    void __iomem         *base;      /* MMIO registers */
    struct pci_dev       *pdev;

    /* TX/RX descriptor rings */
    struct my_tx_ring    tx_ring;
    struct my_rx_ring    rx_ring;

    /* Statistics */
    struct net_device_stats stats;

    /* NAPI (New API for polling) */
    struct napi_struct   napi;

    /* MDIO/PHY */
    struct mii_bus       *mii_bus;
    struct phy_device    *phydev;

    spinlock_t           lock;
};
```

### 2.2 TX Path — Sending Packets

```c
/*
 * TX flow:
 * 1. Kernel calls ndo_start_xmit() with sk_buff
 * 2. Driver maps sk_buff data to DMA
 * 3. Driver fills TX descriptor ring
 * 4. Driver kicks hardware (write to TX doorbell)
 * 5. Hardware reads descriptor, fetches data via DMA, transmits
 * 6. TX complete interrupt fires
 * 7. Driver frees DMA mapping and sk_buff
 */

static netdev_tx_t my_start_xmit(struct sk_buff *skb,
                                   struct net_device *netdev)
{
    struct my_nic *nic = netdev_priv(netdev);
    struct my_tx_ring *ring = &nic->tx_ring;
    struct my_tx_desc *desc;
    dma_addr_t dma_addr;
    u32 len = skb->len;

    /* Check if TX ring is full */
    if (unlikely(my_tx_ring_full(ring))) {
        netif_stop_queue(netdev);
        return NETDEV_TX_BUSY;
    }

    /* Map sk_buff data for DMA */
    dma_addr = dma_map_single(&nic->pdev->dev,
                               skb->data, len, DMA_TO_DEVICE);
    if (dma_mapping_error(&nic->pdev->dev, dma_addr)) {
        dev_kfree_skb_any(skb);
        netdev->stats.tx_dropped++;
        return NETDEV_TX_OK;
    }

    /* Fill TX descriptor */
    desc = &ring->desc[ring->tail];
    desc->addr   = cpu_to_le64(dma_addr);
    desc->length = cpu_to_le16(len);
    desc->flags  = TX_DESC_EOP | TX_DESC_CHECKSUM;

    ring->skb[ring->tail] = skb;
    ring->tail = (ring->tail + 1) % ring->count;

    /* Memory barrier before doorbell */
    wmb();

    /* Kick hardware */
    writel(ring->tail, nic->base + TX_DOORBELL);

    netdev->stats.tx_packets++;
    netdev->stats.tx_bytes += len;

    return NETDEV_TX_OK;
}

/* TX completion IRQ handler cleanup */
static void my_clean_tx_irq(struct my_nic *nic)
{
    struct my_tx_ring *ring = &nic->tx_ring;
    u32 hw_head = readl(nic->base + TX_HEAD);

    while (ring->head != hw_head) {
        struct sk_buff *skb = ring->skb[ring->head];
        struct my_tx_desc *desc = &ring->desc[ring->head];

        dma_unmap_single(&nic->pdev->dev,
                          le64_to_cpu(desc->addr),
                          le16_to_cpu(desc->length),
                          DMA_TO_DEVICE);
        dev_kfree_skb_any(skb);

        ring->head = (ring->head + 1) % ring->count;
    }

    if (netif_queue_stopped(nic->netdev) && !my_tx_ring_full(ring))
        netif_wake_queue(nic->netdev);
}
```

### 2.3 RX Path — Receiving Packets (NAPI)

```c
/*
 * NAPI (New API):
 * 1. IRQ fires for first RX packet
 * 2. Driver disables RX interrupt, schedules NAPI poll
 * 3. Kernel calls napi->poll() in softirq context
 * 4. Driver polls descriptor ring, processes packets
 * 5. When ring empty or budget exhausted: re-enable interrupt, complete NAPI
 *
 * Benefits:
 * - High throughput: no per-packet interrupt overhead
 * - Lower latency at moderate load (still uses interrupts for first packet)
 */

static int my_napi_poll(struct napi_struct *napi, int budget)
{
    struct my_nic *nic = container_of(napi, struct my_nic, napi);
    struct my_rx_ring *ring = &nic->rx_ring;
    int work_done = 0;

    while (work_done < budget) {
        struct my_rx_desc *desc = &ring->desc[ring->head];

        /* Check if descriptor is complete */
        if (!(desc->status & RX_DESC_DONE))
            break;

        u32 len = le16_to_cpu(desc->length);
        struct sk_buff *skb = ring->skb[ring->head];

        /* Unmap DMA */
        dma_unmap_single(&nic->pdev->dev,
                          le64_to_cpu(desc->addr),
                          MY_RX_BUF_SIZE, DMA_FROM_DEVICE);

        /* Trim to actual packet length */
        skb_put(skb, len);
        skb->protocol = eth_type_trans(skb, nic->netdev);

        /* Checksum offload */
        if (desc->status & RX_DESC_CSUM_OK)
            skb->ip_summed = CHECKSUM_UNNECESSARY;

        /* Pass to network stack */
        napi_gro_receive(napi, skb);

        /* Allocate replacement buffer */
        ring->skb[ring->head] = my_alloc_rx_skb(nic, desc);

        ring->head = (ring->head + 1) % ring->count;
        work_done++;

        nic->netdev->stats.rx_packets++;
        nic->netdev->stats.rx_bytes += len;
    }

    /* Re-enable interrupts if done */
    if (work_done < budget) {
        napi_complete_done(napi, work_done);
        my_enable_rx_irq(nic);
    }

    return work_done;
}

/* IRQ handler — just schedules NAPI */
static irqreturn_t my_irq_handler(int irq, void *data)
{
    struct my_nic *nic = data;
    u32 status = readl(nic->base + IRQ_STATUS);

    if (!status)
        return IRQ_NONE;

    writel(status, nic->base + IRQ_CLEAR);

    if (status & IRQ_RX) {
        my_disable_rx_irq(nic);
        napi_schedule(&nic->napi);
    }

    if (status & IRQ_TX)
        my_clean_tx_irq(nic);

    return IRQ_HANDLED;
}
```

### 2.4 Driver Registration

```c
static const struct net_device_ops my_netdev_ops = {
    .ndo_open               = my_open,
    .ndo_stop               = my_stop,
    .ndo_start_xmit         = my_start_xmit,
    .ndo_get_stats64        = my_get_stats64,
    .ndo_set_rx_mode        = my_set_rx_mode,      /* promiscuous, multicast */
    .ndo_set_mac_address    = eth_mac_addr,
    .ndo_validate_addr      = eth_validate_addr,
    .ndo_change_mtu         = my_change_mtu,
    .ndo_tx_timeout         = my_tx_timeout,
    .ndo_set_features       = my_set_features,     /* ethtool features */
    .ndo_eth_ioctl          = my_ioctl,
};

static int my_probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
    struct net_device *netdev;
    struct my_nic *nic;
    int ret;

    /* Allocate netdev (includes private data) */
    netdev = alloc_etherdev(sizeof(struct my_nic));
    if (!netdev)
        return -ENOMEM;

    nic = netdev_priv(netdev);
    nic->netdev = netdev;
    nic->pdev   = pdev;

    SET_NETDEV_DEV(netdev, &pdev->dev);

    /* PCI setup */
    ret = pcim_enable_device(pdev);
    if (ret) goto err_pci;

    ret = pcim_iomap_regions(pdev, BIT(0), "my_nic");
    nic->base = pcim_iomap_table(pdev)[0];
    pci_set_master(pdev);

    /* DMA */
    ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64));
    if (ret) {
        ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
        if (ret) goto err_dma;
    }

    /* Setup rings */
    ret = my_setup_tx_ring(nic);
    if (ret) goto err_rings;

    ret = my_setup_rx_ring(nic);
    if (ret) goto err_rings;

    /* Initialize NAPI */
    netif_napi_add(netdev, &nic->napi, my_napi_poll, NAPI_POLL_WEIGHT);

    /* Setup IRQ */
    ret = pci_alloc_irq_vectors(pdev, 1, 4, PCI_IRQ_MSI | PCI_IRQ_MSIX);
    ret = devm_request_irq(&pdev->dev, pci_irq_vector(pdev, 0),
                            my_irq_handler, 0, netdev->name, nic);

    /* MAC address */
    my_read_mac_addr(nic, netdev->dev_addr);

    /* netdev capabilities */
    netdev->netdev_ops   = &my_netdev_ops;
    netdev->ethtool_ops  = &my_ethtool_ops;
    netdev->features     = NETIF_F_IP_CSUM | NETIF_F_IPV6_CSUM |
                           NETIF_F_SG | NETIF_F_TSO | NETIF_F_TSO6 |
                           NETIF_F_RXCSUM | NETIF_F_GRO;
    netdev->hw_features  = netdev->features;

    pci_set_drvdata(pdev, nic);

    ret = register_netdev(netdev);
    if (ret) goto err_register;

    netdev_info(netdev, "Registered, MAC: %pM\n", netdev->dev_addr);
    return 0;

err_register:
err_rings:
err_dma:
err_pci:
    free_netdev(netdev);
    return ret;
}
```

---

## Level 3: ethtool Support

```c
#include <linux/ethtool.h>

static void my_get_drvinfo(struct net_device *netdev,
                            struct ethtool_drvinfo *drvinfo)
{
    strscpy(drvinfo->driver,  "my_nic",  sizeof(drvinfo->driver));
    strscpy(drvinfo->version, "1.0",     sizeof(drvinfo->version));
    strscpy(drvinfo->bus_info, pci_name(nic->pdev), sizeof(drvinfo->bus_info));
}

static int my_get_link_ksettings(struct net_device *netdev,
                                   struct ethtool_link_ksettings *cmd)
{
    struct my_nic *nic = netdev_priv(netdev);
    return phy_ethtool_get_link_ksettings(netdev, cmd);
}

static u32 my_get_msglevel(struct net_device *netdev)
{
    struct my_nic *nic = netdev_priv(netdev);
    return nic->msg_enable;
}

static const struct ethtool_ops my_ethtool_ops = {
    .get_drvinfo         = my_get_drvinfo,
    .get_link            = ethtool_op_get_link,
    .get_link_ksettings  = my_get_link_ksettings,
    .set_link_ksettings  = my_set_link_ksettings,
    .get_msglevel        = my_get_msglevel,
    .set_msglevel        = my_set_msglevel,
    .get_strings         = my_get_strings,
    .get_ethtool_stats   = my_get_ethtool_stats,
    .get_sset_count      = my_get_sset_count,
    .get_ringparam       = my_get_ringparam,
    .set_ringparam       = my_set_ringparam,
    .get_coalesce        = my_get_coalesce,
    .set_coalesce        = my_set_coalesce,
};
```

---

## Level 4: PHY / MDIO

```c
#include <linux/mii.h>
#include <linux/phy.h>
#include <linux/mdio.h>

/* Register MDIO bus */
static int my_mdio_read(struct mii_bus *bus, int phy_id, int reg)
{
    struct my_nic *nic = bus->priv;
    /* Write to MDIO control register */
    u32 cmd = MDIO_START | MDIO_RD | (phy_id << 21) | (reg << 16);
    writel(cmd, nic->base + MDIO_CMD);
    /* Wait for completion */
    while (readl(nic->base + MDIO_STATUS) & MDIO_BUSY)
        cpu_relax();
    return readl(nic->base + MDIO_DATA) & 0xFFFF;
}

/* Connect PHY */
static int my_phy_connect(struct my_nic *nic)
{
    struct net_device *netdev = nic->netdev;
    struct phy_device *phydev;

    phydev = phy_find_first(nic->mii_bus);
    if (!phydev)
        return -ENODEV;

    phy_connect_direct(netdev, phydev, my_adjust_link,
                        PHY_INTERFACE_MODE_RGMII_ID);

    phydev->supported &= PHY_GBIT_ALL;
    phydev->advertising = phydev->supported;
    phy_attached_info(phydev);

    return 0;
}

static void my_adjust_link(struct net_device *netdev)
{
    struct my_nic *nic = netdev_priv(netdev);
    struct phy_device *phydev = netdev->phydev;

    if (phydev->link) {
        my_configure_speed(nic, phydev->speed, phydev->duplex);
        netif_carrier_on(netdev);
    } else {
        netif_carrier_off(netdev);
    }
}
```

---

## Debugging Network Drivers

```bash
# Device info
ip link show eth0
ethtool eth0                    # link status, speed
ethtool -i eth0                 # driver info
ethtool -S eth0                 # statistics
ethtool -k eth0                 # features (checksum offload, etc.)

# Test TX/RX
ping -c 100 192.168.1.1         # basic connectivity
iperf3 -s; iperf3 -c <server>  # throughput test

# Packet capture
tcpdump -i eth0 -w capture.pcap
wireshark capture.pcap

# Interrupt tuning
cat /proc/interrupts | grep eth0
ethtool -C eth0 rx-usecs 50 tx-usecs 50  # coalescing

# Ring buffer size
ethtool -G eth0 rx 512 tx 512

# Driver debug log
ethtool -s eth0 msglvl 0xFFFF   # enable all debug messages
dmesg | grep my_nic

# NAPI stats
cat /proc/net/softnet_stat       # shows NAPI poll statistics
```

---

## Interview Questions

1. What is NAPI? Why is it preferred over pure interrupt-driven RX?
2. Explain the TX descriptor ring — how does it work?
3. What is DMA coherency and why does it matter for NICs?
4. What is `netif_stop_queue` and when do you call it?
5. What is `sk_buff`? What fields are most important for a NIC driver?
6. Explain checksum offloading (TSO, GSO, GRO).
7. What is an MDIO bus and how does it relate to PHY management?
8. What is SR-IOV and how does it enable multiple VMs to share a NIC?
9. What is `napi_gro_receive` vs `netif_receive_skb`?
10. How do you handle TX timeout in a network driver?
