# IPC & DMA Driver Development

## Level 1: IPC Mechanisms in Linux

### 1.1 IPC Overview

```
IPC Mechanism    | Kernel/User | Speed    | Use Case
─────────────────┼─────────────┼──────────┼──────────────────────────
Signals          | Both        | Fast     | Process control/events
Pipes            | User        | Medium   | Parent-child data flow
FIFOs (named)    | User        | Medium   | Unrelated processes
POSIX msg queues | User        | Medium   | Structured messages
UNIX sockets     | User        | Fast     | IPC with datagram/stream
Shared memory    | User        | Fastest  | High-bandwidth data share
Netlink          | K↔U         | Fast     | Kernel↔userspace protocol
IIO events       | K→U         | Fast     | Sensor/GPIO events
DBus             | User        | Slow     | Desktop/app messaging
```

### 1.2 Netlink — Kernel ↔ User IPC

```c
/* Netlink: kernel driver sends events to user space */
#include <linux/netlink.h>
#include <net/netlink.h>
#include <net/net_namespace.h>

/* ===== KERNEL SIDE ===== */

static struct sock *my_nl_sock;

/* Receive message from user space */
static void my_nl_recv(struct sk_buff *skb)
{
    struct nlmsghdr *nlh = nlmsg_hdr(skb);
    char *msg = (char *)NLMSG_DATA(nlh);
    int pid = nlh->nlmsg_pid;

    pr_info("Received from userspace (pid %d): %s\n", pid, msg);

    /* Send reply */
    struct sk_buff *skb_out = nlmsg_new(100, GFP_KERNEL);
    struct nlmsghdr *nlh_out = nlmsg_put(skb_out, 0, 0,
                                          NLMSG_DONE, 100, 0);
    strncpy(NLMSG_DATA(nlh_out), "Hello from kernel!", 18);
    NETLINK_CB(skb_out).dst_group = 0;

    nlmsg_unicast(my_nl_sock, skb_out, pid);
}

/* Send event from kernel interrupt handler */
static void my_send_event(u32 event_type, void *data, size_t len)
{
    struct sk_buff *skb = nlmsg_new(len, GFP_ATOMIC);
    struct nlmsghdr *nlh = nlmsg_put(skb, 0, 0, event_type, len, 0);
    memcpy(NLMSG_DATA(nlh), data, len);

    /* Multicast to all listeners in group 1 */
    nlmsg_multicast(my_nl_sock, skb, 0, 1, GFP_ATOMIC);
}

static int __init my_nl_init(void)
{
    struct netlink_kernel_cfg cfg = {
        .input  = my_nl_recv,
        .groups = 1,
    };
    my_nl_sock = netlink_kernel_create(&init_net, NETLINK_USERSOCK, &cfg);
    return my_nl_sock ? 0 : -ENOMEM;
}

/* ===== USER SPACE SIDE ===== */
#include <sys/socket.h>
#include <linux/netlink.h>

int sock = socket(AF_NETLINK, SOCK_RAW, NETLINK_USERSOCK);

struct sockaddr_nl src_addr = {
    .nl_family = AF_NETLINK,
    .nl_pid    = getpid(),
    .nl_groups = 1,    /* subscribe to group 1 */
};
bind(sock, (struct sockaddr*)&src_addr, sizeof(src_addr));

/* Receive kernel events */
char buf[4096];
struct nlmsghdr *nlh = (struct nlmsghdr *)buf;
recv(sock, buf, sizeof(buf), 0);
printf("Event: %s\n", (char *)NLMSG_DATA(nlh));
```

### 1.3 Shared Memory (POSIX)

```c
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>

/* Process A — create and write */
int fd = shm_open("/my_shm", O_CREAT | O_RDWR, 0666);
ftruncate(fd, 4096);
void *ptr = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
strcpy(ptr, "Hello from Process A");

/* Process B — open and read */
int fd = shm_open("/my_shm", O_RDONLY, 0666);
void *ptr = mmap(NULL, 4096, PROT_READ, MAP_SHARED, fd, 0);
printf("Received: %s\n", (char *)ptr);

/* Cleanup */
munmap(ptr, 4096);
shm_unlink("/my_shm");
```

### 1.4 dma-buf — Zero-Copy Inter-driver IPC

```c
/*
 * dma-buf: file descriptor based buffer sharing between drivers
 * GPU allocates buffer → shares FD → camera DMA writes directly
 * No CPU copy!
 *
 * Use cases:
 *   Camera ISP → GPU (no CPU memcpy)
 *   GPU → Display controller (zero-copy scanout)
 *   Codec → GPU (video decode → texture)
 */

#include <linux/dma-buf.h>

/* ===== EXPORTER (allocates buffer, e.g., GPU driver) ===== */

static struct sg_table *my_map_dma_buf(struct dma_buf_attachment *att,
                                         enum dma_data_direction dir)
{
    struct my_buf *buf = att->dmabuf->priv;
    struct sg_table *sgt = kmalloc(sizeof(*sgt), GFP_KERNEL);

    sg_alloc_table(sgt, 1, GFP_KERNEL);
    sg_set_page(sgt->sgl, buf->page, buf->size, 0);
    dma_map_sgtable(att->dev, sgt, dir, 0);
    return sgt;
}

static void my_unmap_dma_buf(struct dma_buf_attachment *att,
                               struct sg_table *sgt,
                               enum dma_data_direction dir)
{
    dma_unmap_sgtable(att->dev, sgt, dir, 0);
    sg_free_table(sgt);
    kfree(sgt);
}

static const struct dma_buf_ops my_dmabuf_ops = {
    .attach         = my_attach,
    .detach         = my_detach,
    .map_dma_buf    = my_map_dma_buf,
    .unmap_dma_buf  = my_unmap_dma_buf,
    .release        = my_release,
    .mmap           = my_mmap,
    .vmap           = my_vmap,
};

/* Export a buffer as dma-buf fd */
int export_to_userspace(struct my_buf *buf)
{
    DEFINE_DMA_BUF_EXPORT_INFO(exp_info);
    exp_info.ops   = &my_dmabuf_ops;
    exp_info.size  = buf->size;
    exp_info.flags = O_CLOEXEC;
    exp_info.priv  = buf;

    struct dma_buf *dmabuf = dma_buf_export(&exp_info);
    return dma_buf_fd(dmabuf, O_CLOEXEC);
}

/* ===== IMPORTER (uses buffer, e.g., camera driver) ===== */

void import_from_fd(int fd, struct device *dev)
{
    struct dma_buf *dmabuf = dma_buf_get(fd);

    struct dma_buf_attachment *att = dma_buf_attach(dmabuf, dev);

    struct sg_table *sgt = dma_buf_map_attachment(att, DMA_FROM_DEVICE);

    /* Use sgt->sgl to program DMA controller */
    dma_addr_t addr = sg_dma_address(sgt->sgl);
    u32 len         = sg_dma_len(sgt->sgl);
    my_dma_setup(addr, len);

    /* After DMA complete */
    dma_buf_unmap_attachment(att, sgt, DMA_FROM_DEVICE);
    dma_buf_detach(dmabuf, att);
    dma_buf_put(dmabuf);
}
```

---

## Level 2: DMA Engine Framework

### 2.1 DMA Types

| Type | Description | Use Case |
|------|-------------|----------|
| Coherent DMA | Bypasses CPU cache | Control structures, ring buffers |
| Streaming DMA | CPU cache + explicit sync | Single-use data transfer |
| DMA Engine | Central DMA controller | Memory copies, peripheral DMA |

### 2.2 DMA Coherent Memory

```c
/* Physically contiguous, cache-coherent, permanent mapping */
void *cpu_addr;
dma_addr_t dma_handle;

cpu_addr = dma_alloc_coherent(dev, size, &dma_handle, GFP_KERNEL);
if (!cpu_addr)
    return -ENOMEM;

/* Write data */
memcpy(cpu_addr, data, size);

/* Give to hardware */
writel(dma_handle, hw_base + DMA_ADDR_REG);  /* hw uses dma_handle */
writel(size,       hw_base + DMA_SIZE_REG);
writel(DMA_START,  hw_base + DMA_CMD_REG);

/* Cleanup */
dma_free_coherent(dev, size, cpu_addr, dma_handle);
```

### 2.3 Streaming DMA

```c
/* Single-use DMA — explicit cache sync */

/* Map for DMA (CPU writes, device reads) */
dma_addr_t dma_addr = dma_map_single(dev, cpu_buf, size, DMA_TO_DEVICE);
if (dma_mapping_error(dev, dma_addr))
    return -ENOMEM;

/* Device does DMA transfer... */
start_dma_transfer(dma_addr, size);
wait_for_completion(&dma_done);

/* Unmap (invalidates CPU cache if DMA_FROM_DEVICE) */
dma_unmap_single(dev, dma_addr, size, DMA_TO_DEVICE);

/* For scatter-gather */
dma_map_sg(dev, sgl, nents, DMA_TO_DEVICE);
for_each_sg(sgl, sg, nents, i) {
    dma_addr_t addr = sg_dma_address(sg);
    u32 len         = sg_dma_len(sg);
    /* program HW with each segment */
}
dma_unmap_sg(dev, sgl, nents, DMA_TO_DEVICE);
```

### 2.4 DMA Engine API (Central DMA Controller)

```c
#include <linux/dmaengine.h>
#include <linux/dma-direction.h>

/* Request a DMA channel */
struct dma_chan *chan = dma_request_chan(dev, "rx");
if (IS_ERR(chan))
    return PTR_ERR(chan);

/* Prepare a memcpy transaction */
dma_addr_t src_dma = dma_map_single(dev, src, size, DMA_TO_DEVICE);
dma_addr_t dst_dma = dma_map_single(dev, dst, size, DMA_FROM_DEVICE);

struct dma_async_tx_descriptor *tx = dmaengine_prep_dma_memcpy(
    chan, dst_dma, src_dma, size,
    DMA_PREP_INTERRUPT | DMA_CTRL_ACK);

/* Set completion callback */
tx->callback = my_dma_callback;
tx->callback_param = my_data;

/* Submit and fire */
dma_cookie_t cookie = dmaengine_submit(tx);
dma_async_issue_pending(chan);

/* Wait for completion (alternative to callback) */
dma_sync_wait(chan, cookie);

/* Cyclic DMA (for audio, ADC) */
struct dma_async_tx_descriptor *tx = dmaengine_prep_dma_cyclic(
    chan, buf_dma, buf_size, period_size,
    DMA_DEV_TO_MEM, DMA_PREP_INTERRUPT);

/* Device → Memory DMA (peripheral to buffer) */
struct dma_slave_config cfg = {
    .direction       = DMA_DEV_TO_MEM,
    .src_addr        = periph_phys_addr,
    .src_addr_width  = DMA_SLAVE_BUSWIDTH_4_BYTES,
    .src_maxburst    = 16,
};
dmaengine_slave_config(chan, &cfg);
```

---

## Level 3: IOMMU — DMA Protection

```c
/*
 * IOMMU = I/O Memory Management Unit
 * Maps device-visible addresses to physical addresses
 * Protects system RAM from rogue DMA
 * Enables DMA for devices that need specific address ranges
 * Foundation for SR-IOV, KVM passthrough, dma-buf
 */

#include <linux/iommu.h>

/* IOMMU domain — address space for a device */
struct iommu_domain *domain = iommu_domain_alloc(&platform_bus_type);

/* Map physical page to IOVA (I/O virtual address) */
phys_addr_t phys = page_to_phys(page);
iommu_map(domain, iova, phys, PAGE_SIZE, IOMMU_READ | IOMMU_WRITE);

/* Device uses IOVA for DMA, IOMMU translates to phys */
writel(iova, hw_base + DMA_ADDR_REG);

/* Unmap */
iommu_unmap(domain, iova, PAGE_SIZE);

/* Driver framework auto-handles IOMMU via dma_alloc_coherent */
/* If CONFIG_IOMMU_DMA=y, all dma_map_* calls go through IOMMU */
```

---

## Level 4: Complete DMA Driver Example

```c
/* Memory-to-Memory DMA driver using DMA Engine framework */
#include <linux/platform_device.h>
#include <linux/dmaengine.h>
#include <linux/of_dma.h>

struct my_dma_dev {
    struct device           *dev;
    void __iomem            *base;
    struct dma_device        dma_dev;
    struct my_dma_chan       channels[4];
    int                      irq;
};

struct my_dma_chan {
    struct dma_chan           chan;
    struct my_dma_dev        *dev;
    struct tasklet_struct     tasklet;
    struct list_head          pending_list;
    struct list_head          active_list;
    spinlock_t                lock;
};

/* Channel operations */
static struct dma_async_tx_descriptor *
my_prep_dma_memcpy(struct dma_chan *chan, dma_addr_t dst,
                    dma_addr_t src, size_t len, unsigned long flags)
{
    struct my_dma_chan *mychan = to_my_dma_chan(chan);
    struct my_dma_desc *desc = my_alloc_desc(mychan);

    desc->src   = src;
    desc->dst   = dst;
    desc->len   = len;
    desc->flags = flags;

    return &desc->async_tx;
}

static dma_cookie_t my_tx_submit(struct dma_async_tx_descriptor *tx)
{
    struct my_dma_chan *mychan = to_my_dma_chan(tx->chan);
    struct my_dma_desc *desc = to_my_dma_desc(tx);
    dma_cookie_t cookie;
    unsigned long flags;

    spin_lock_irqsave(&mychan->lock, flags);
    cookie = dma_cookie_assign(tx);
    list_add_tail(&desc->node, &mychan->pending_list);
    spin_unlock_irqrestore(&mychan->lock, flags);

    return cookie;
}

/* IRQ handler — task complete */
static irqreturn_t my_dma_irq(int irq, void *data)
{
    struct my_dma_dev *mydev = data;
    u32 status = readl(mydev->base + DMA_STATUS);

    if (!status)
        return IRQ_NONE;

    writel(status, mydev->base + DMA_STATUS);

    for (int i = 0; i < 4; i++) {
        if (status & BIT(i))
            tasklet_schedule(&mydev->channels[i].tasklet);
    }

    return IRQ_HANDLED;
}

static struct dma_device my_dma_device = {
    .device_prep_dma_memcpy = my_prep_dma_memcpy,
    .device_tx_status       = my_tx_status,
    .device_issue_pending   = my_issue_pending,
    .device_free_chan_resources  = my_free_chan_resources,
    .device_alloc_chan_resources = my_alloc_chan_resources,
    .copy_align = DMAENGINE_ALIGN_4_BYTES,
    .directions = BIT(DMA_MEM_TO_MEM),
    .residue_granularity = DMA_RESIDUE_GRANULARITY_BURST,
};
```

---

## Interview Questions

1. What is Netlink and when is it preferred over `/proc` or `sysfs`?
2. Explain `dma-buf`. How does it enable zero-copy?
3. What is the difference between coherent and streaming DMA?
4. What does `dma_map_single` do? When must you call `dma_unmap_single`?
5. What is an IOMMU? How does it protect system memory?
6. What is a DMA descriptor ring?
7. Explain cyclic DMA and where it is used.
8. What is `DMA_FROM_DEVICE` vs `DMA_TO_DEVICE`?
9. How do you use the DMA Engine framework in a driver?
10. What is the difference between `dma_addr_t` and `phys_addr_t`?
