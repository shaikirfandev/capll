# Virtualization — Xen, KVM, QNX Hypervisor

## Level 1: Hypervisor Fundamentals

### 1.1 Hypervisor Types

```
Type 1 (Bare-metal):                Type 2 (Hosted):
┌──────────────────────┐            ┌──────────────────────┐
│  Guest OS 1 Guest 2  │            │    Host OS           │
├──────────────────────┤            │  ┌─────────────────┐ │
│      Hypervisor      │            │  │  Hypervisor     │ │
├──────────────────────┤            │  │  (KVM/QEMU)     │ │
│      Hardware        │            │  └─────────────────┘ │
└──────────────────────┘            ├──────────────────────┤
                                    │      Hardware        │
Xen, KVM (with hardware)            └──────────────────────┘
QNX Hypervisor                      VirtualBox, VMware WS
```

### 1.2 Virtualization Concepts

| Term | Meaning |
|------|---------|
| VMM / Hypervisor | Manages multiple VMs |
| VM / Guest | Virtualized machine instance |
| Host | Physical machine running hypervisor |
| Dom0 / Control VM | Privileged VM that manages others |
| DomU / Guest VM | Unprivileged guest domain |
| vCPU | Virtual CPU assigned to a VM |
| VMCS | VM Control Structure (Intel VT-x) |
| EPT | Extended Page Tables (hardware MMU assist) |
| SR-IOV | Single Root I/O Virtualization (PCIe passthrough) |
| Paravirtualization | Guest knows it's virtualized, uses hypercalls |
| Full virtualization | Guest doesn't know it's virtualized |

---

## Level 2: KVM (Kernel-based Virtual Machine)

### 2.1 KVM Architecture

```
User Space                  Kernel Space
┌──────────────────────┐    ┌─────────────────────────────┐
│  QEMU process        │    │  Linux Kernel               │
│  ┌────────────────┐  │    │  ┌─────────────────────┐    │
│  │ Guest RAM      │  │    │  │  KVM module          │    │
│  │ Virtual Devices│  │    │  │  (kvm.ko + kvm_intel/│    │
│  │ BIOS/UEFI      │  │    │  │   kvm_amd.ko)        │    │
│  └────────────────┘  │    │  └──────────┬──────────┘    │
│          │ /dev/kvm  │    │             │                │
│          │ ioctls    │    │  Intel VT-x │ or AMD-V       │
└──────────┼───────────┘    └─────────────┼───────────────┘
           │                              │
           └──────────────────────────────┘
                      Hardware
```

### 2.2 KVM API Usage (C)

```c
#include <linux/kvm.h>
#include <sys/ioctl.h>
#include <sys/mman.h>

/* Create VM */
int kvm_fd = open("/dev/kvm", O_RDWR);
int vm_fd  = ioctl(kvm_fd, KVM_CREATE_VM, 0);

/* Allocate guest memory */
size_t mem_size = 256 * 1024 * 1024;   /* 256 MB */
void *mem = mmap(NULL, mem_size, PROT_READ | PROT_WRITE,
                 MAP_SHARED | MAP_ANONYMOUS, -1, 0);

/* Map guest physical address space */
struct kvm_userspace_memory_region region = {
    .slot            = 0,
    .flags           = 0,
    .guest_phys_addr = 0x0,
    .memory_size     = mem_size,
    .userspace_addr  = (uint64_t)mem,
};
ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION, &region);

/* Create vCPU */
int vcpu_fd = ioctl(vm_fd, KVM_CREATE_VCPU, 0);

/* Map vCPU run struct */
int vcpu_mmap_size = ioctl(kvm_fd, KVM_GET_VCPU_MMAP_SIZE, 0);
struct kvm_run *run = mmap(NULL, vcpu_mmap_size, PROT_READ | PROT_WRITE,
                            MAP_SHARED, vcpu_fd, 0);

/* Setup initial registers */
struct kvm_regs regs;
ioctl(vcpu_fd, KVM_GET_REGS, &regs);
regs.rip = 0x1000;   /* entry point */
regs.rsp = 0xFFFF;
ioctl(vcpu_fd, KVM_SET_REGS, &regs);

/* Run vCPU */
while (1) {
    ioctl(vcpu_fd, KVM_RUN, 0);

    switch (run->exit_reason) {
    case KVM_EXIT_HLT:
        printf("HLT reached\n");
        goto done;

    case KVM_EXIT_IO:
        /* Handle I/O port access */
        if (run->io.direction == KVM_EXIT_IO_OUT) {
            printf("Guest IO write: port=0x%x data=%.*s\n",
                   run->io.port, run->io.size,
                   (char *)run + run->io.data_offset);
        }
        break;

    case KVM_EXIT_MMIO:
        /* Handle MMIO access */
        handle_mmio(run);
        break;

    case KVM_EXIT_SHUTDOWN:
        goto done;
    }
}
```

### 2.3 virtio — Para-virtual Device Driver

```c
/*
 * virtio = standard virtual I/O framework
 * Guest driver (virtio-net, virtio-blk, virtio-gpu) uses virtqueues
 * QEMU provides backend implementation
 */

/* virtqueue = ring buffer between guest and hypervisor */
/* Flow:
 * 1. Guest driver adds descriptor to virtqueue
 * 2. Guest kicks hypervisor (write to MMIO)
 * 3. Hypervisor processes descriptor, adds used ring entry
 * 4. Hypervisor interrupts guest
 * 5. Guest reads used ring
 */

#include <linux/virtio.h>
#include <linux/virtio_ids.h>
#include <linux/virtio_config.h>

struct my_virtio_dev {
    struct virtio_device *vdev;
    struct virtqueue     *vq;
};

static void my_virtio_callback(struct virtqueue *vq)
{
    /* Buffer was consumed by host */
    struct my_virtio_dev *dev = vq->vdev->priv;
    unsigned int len;
    void *buf;

    while ((buf = virtqueue_get_buf(vq, &len)) != NULL) {
        /* Process completed buffer */
        process_buffer(buf, len);
    }
}

static int my_virtio_probe(struct virtio_device *vdev)
{
    struct my_virtio_dev *dev;

    dev = kzalloc(sizeof(*dev), GFP_KERNEL);
    dev->vdev = vdev;

    /* Create virtqueue */
    dev->vq = virtio_find_single_vq(vdev, my_virtio_callback, "my-vq");
    if (IS_ERR(dev->vq))
        return PTR_ERR(dev->vq);

    vdev->priv = dev;

    /* Send a buffer to host */
    struct scatterlist sg;
    void *buf = kmalloc(PAGE_SIZE, GFP_KERNEL);
    sg_init_one(&sg, buf, PAGE_SIZE);
    virtqueue_add_outbuf(dev->vq, &sg, 1, buf, GFP_KERNEL);
    virtqueue_kick(dev->vq);

    return 0;
}

static struct virtio_device_id my_virtio_id_table[] = {
    { MY_VIRTIO_ID, VIRTIO_DEV_ANY_ID },
    { 0 },
};

static struct virtio_driver my_virtio_driver = {
    .driver.name = "my-virtio",
    .id_table    = my_virtio_id_table,
    .probe       = my_virtio_probe,
    .remove      = my_virtio_remove,
};
```

---

## Level 3: Xen Hypervisor

### 3.1 Xen Architecture

```
Hardware
├── Xen Hypervisor (runs in highest privilege)
│
├── Dom0 (Control Domain)
│   ├── Linux kernel with Xen drivers
│   ├── xenstore (configuration database)
│   ├── libxl / xl toolstack
│   └── Backend drivers (netback, blkback, fbback)
│
└── DomU (Guest Domains)
    ├── DomU-1: Linux guest
    │   └── Frontend drivers (netfront, blkfront)
    ├── DomU-2: Windows guest (HVM mode)
    └── DomU-3: RTOS (PV mode or passthrough)
```

### 3.2 Xen PV (Para-Virtualization) Driver Model

```c
/* SPLIT DRIVER MODEL:
 * Backend (dom0) ←→ xenstore ←→ Frontend (domU)
 *
 * Backend: provides real hardware access
 * Frontend: uses virtual device in guest
 * Communication: grant tables (shared memory) + event channels
 */

/* Frontend driver (runs in DomU) — netfront example */
#include <xen/xen.h>
#include <xen/xenbus.h>
#include <xen/grant_table.h>
#include <xen/events.h>

struct netfront_info {
    struct net_device    *netdev;
    struct xenbus_device *xbdev;
    grant_ref_t           tx_ring_ref;
    grant_ref_t           rx_ring_ref;
    unsigned int          tx_evtchn;
    unsigned int          rx_evtchn;
    int                   tx_irq;
    int                   rx_irq;
};

/* Setup shared ring with backend */
static int netfront_setup_rings(struct netfront_info *info)
{
    struct xenbus_device *dev = info->xbdev;
    struct xenbus_transaction xbt;
    int err;

    /* Allocate shared page for TX ring */
    struct netif_tx_front_ring *txring;
    txring = (void *)__get_free_page(GFP_KERNEL);

    /* Grant backend access to shared page */
    info->tx_ring_ref = gnttab_grant_foreign_access(
        dev->otherend_id,
        virt_to_gfn(txring),
        0);   /* 0 = read/write */

    /* Allocate event channel */
    xenbus_alloc_evtchn(dev, &info->tx_evtchn);
    info->tx_irq = bind_evtchn_to_irqhandler(info->tx_evtchn,
                       netfront_tx_interrupt, 0, "netfront", info);

    /* Publish ring ref and evtchn to xenstore */
again:
    err = xenbus_transaction_start(&xbt);
    xenbus_printf(xbt, dev->nodename, "tx-ring-ref", "%u", info->tx_ring_ref);
    xenbus_printf(xbt, dev->nodename, "event-channel-tx", "%u", info->tx_evtchn);
    err = xenbus_transaction_end(xbt, 0);
    if (err == -EAGAIN) goto again;

    return 0;
}

/* State machine: Frontend transitions to Connected */
static void netfront_backend_changed(struct xenbus_device *dev,
                                      enum xenbus_state backend_state)
{
    switch (backend_state) {
    case XenbusStateConnected:
        xenbus_switch_state(dev, XenbusStateConnected);
        netif_carrier_on(info->netdev);
        break;
    case XenbusStateClosing:
        xenbus_switch_state(dev, XenbusStateClosing);
        break;
    default:
        break;
    }
}
```

### 3.3 Xen Grant Tables (Shared Memory)

```c
/*
 * Grant tables = Xen's mechanism for safe inter-domain memory sharing
 * Dom A grants access to its page to Dom B
 * Xen validates the grant — no direct physical address sharing
 */

/* Grant page access to another domain */
grant_ref_t ref = gnttab_grant_foreign_access(
    remote_domid,           /* domain that gets access */
    virt_to_gfn(page),      /* our page */
    0);                     /* 0=RW, 1=RO */

/* Map a remote domain's page (in the other domain) */
struct gnttab_map_grant_ref op = {
    .host_addr = (unsigned long)mapped_addr,
    .flags     = GNTMAP_host_map,
    .ref       = remote_ref,
    .dom       = remote_domid,
};
HYPERVISOR_grant_table_op(GNTTABOP_map_grant_ref, &op, 1);
```

### 3.4 Xen Event Channels (Inter-domain Notifications)

```c
/* Event channel = lightweight interrupt between domains */

/* Allocate and bind event channel */
int evtchn;
xenbus_alloc_evtchn(dev, &evtchn);

int irq = bind_evtchn_to_irqhandler(evtchn,
    my_event_handler,
    IRQF_SAMPLE_RANDOM,
    "my_driver",
    dev);

/* Notify remote domain */
notify_remote_via_evtchn(evtchn);
/* or */
notify_remote_via_irq(irq);
```

---

## Level 4: QNX Hypervisor

### 4.1 QNX Hypervisor Overview

```
QNX Hypervisor (automotive-grade, ASIL-D capable)
├── Host: QNX Neutrino RTOS (safety OS)
│   ├── Real-time tasks (ABS, airbag, instrument cluster)
│   └── vdev server (virtual device backend)
│
├── Guest 1: Android Auto / Linux (infotainment)
└── Guest 2: Another RTOS or safety partition

Use cases:
  - Automotive: safety RTOS + Android on same SoC
  - Avionics: DO-178C certified partition
  - Medical: IEC-62304 certified partition
```

### 4.2 QNX Hypervisor Key Concepts

```
vdev (virtual device):
  Backend in host provides virtual hardware to guest
  Guest driver talks to vdev via shared memory

vdev-serial:  virtual UART
vdev-virtio-net: virtual network
vdev-sata:    virtual disk
vdev-display: virtual display

Passthrough:
  Physical device assigned exclusively to a guest
  Guest driver accesses hardware directly (with IOMMU protection)

QVM (QNX Virtual Machine):
  A guest configuration + its virtual devices
  Defined in a .qvmconf file
```

---

## QEMU — Testing Without Hardware

```bash
# Run Linux in KVM
qemu-system-x86_64 \
    -enable-kvm \
    -cpu host \
    -m 2048 \
    -kernel /boot/vmlinuz \
    -initrd /boot/initrd.img \
    -append "console=ttyS0 root=/dev/vda" \
    -drive file=rootfs.img,format=raw,if=virtio \
    -net nic,model=virtio -net user \
    -nographic

# Run ARM64 Linux (emulated)
qemu-system-aarch64 \
    -machine virt \
    -cpu cortex-a53 \
    -m 1024 \
    -kernel Image \
    -dtb my-board.dtb \
    -append "console=ttyAMA0 root=/dev/vda" \
    -drive file=rootfs.ext4,format=raw,if=virtio \
    -nographic

# Add virtio-net device
-netdev user,id=net0,hostfwd=tcp::5555-:22 \
-device virtio-net-pci,netdev=net0

# Test driver with QEMU
modprobe kvm_intel      # or kvm_amd
ls /dev/kvm             # should exist
```

---

## Interview Questions

1. What is the difference between Type 1 and Type 2 hypervisors?
2. How does KVM work? What is the role of `/dev/kvm`?
3. Explain Xen's split driver model (frontend/backend).
4. What are grant tables in Xen?
5. What is virtio? Why is it used instead of emulating real hardware?
6. What is SR-IOV and how does it work for PCIe device passthrough?
7. What is an event channel in Xen?
8. How does the QNX Hypervisor differ from Xen/KVM for automotive use?
9. What is IOMMU and why is it important for virtualization?
10. What is a virtqueue in the virtio protocol?
