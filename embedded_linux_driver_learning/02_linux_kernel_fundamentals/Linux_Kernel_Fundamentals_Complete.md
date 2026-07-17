# Linux Kernel Fundamentals — Basic to Advanced

## Level 1: Kernel Architecture

### 1.1 What is the Linux Kernel?

```
User Space
┌─────────────────────────────────────────────────┐
│  Applications: bash, python, your-app           │
│  Libraries: glibc, libpthread, libdrm           │
├─────────────────────────────────────────────────┤
│           System Call Interface (syscalls)       │
├─────────────────────────────────────────────────┤
Kernel Space
├─────────┬──────────┬───────────┬────────────────┤
│ Process │  Memory  │   VFS     │  Network Stack │
│ Sched   │  Mgmt    │           │                │
├─────────┴──────────┴───────────┴────────────────┤
│             Device Drivers                       │
├──────────────────────────────────────────────────┤
│         Hardware Abstraction Layer               │
├──────────────────────────────────────────────────┤
Hardware: CPU, RAM, GPU, NIC, USB, I2C, SPI...
```

**Key Subsystems:**
- **Process Management:** `kernel/sched/` — CFS scheduler, task states
- **Memory Management:** `mm/` — virtual memory, page tables, slab allocator
- **VFS:** `fs/` — file system abstraction, inode/dentry/file
- **Network:** `net/` — socket API, protocol stacks (TCP/IP)
- **Drivers:** `drivers/` — hardware drivers
- **IPC:** signals, pipes, sockets, shared memory

---

### 1.2 Kernel Source Tree

```bash
linux/
├── arch/           ← architecture-specific (arm, arm64, x86, riscv)
│   └── arm64/
│       ├── boot/   ← kernel entry, compressed image
│       ├── mm/     ← arch-specific memory management
│       └── kernel/ ← CPU init, IRQ, SMP
├── drivers/        ← ALL device drivers
│   ├── base/       ← driver model core
│   ├── char/       ← character devices
│   ├── block/      ← block devices
│   ├── net/        ← network drivers
│   ├── gpu/        ← graphics drivers (DRM)
│   ├── media/      ← V4L2, DVB
│   ├── sound/      ← ALSA, ASoC
│   ├── usb/        ← USB host and gadget
│   └── platform/   ← platform devices
├── fs/             ← file systems (ext4, btrfs, nfs, etc.)
├── include/
│   ├── linux/      ← public kernel headers
│   └── uapi/       ← user-space facing headers
├── init/           ← kernel init (start_kernel)
├── ipc/            ← IPC mechanisms
├── kernel/         ← core kernel (sched, signals, timers)
├── lib/            ← utility functions
├── mm/             ← memory management
├── net/            ← networking
└── Documentation/  ← READ THIS — best docs available
```

---

### 1.3 Kernel Configuration & Compilation

```bash
# Get kernel source
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
cd linux

# Configure
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- defconfig
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- menuconfig

# Build
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc) Image.gz dtbs modules

# Build for host (x86_64)
make defconfig
make -j$(nproc)

# Install modules
sudo make modules_install

# Key menuconfig sections:
# General Setup → Kernel compression, timers
# Device Drivers → Enable specific drivers
# Kernel hacking → Debug options (KASAN, LOCKDEP, FTRACE)
```

**Important Kconfig options for driver development:**
```
CONFIG_DEBUG_KERNEL=y
CONFIG_KASAN=y              # Kernel Address Sanitizer
CONFIG_LOCKDEP=y            # Lock dependency checker
CONFIG_DYNAMIC_DEBUG=y      # pr_debug/dev_dbg activation
CONFIG_FTRACE=y             # Function tracing
CONFIG_KPROBES=y            # Dynamic kernel probes
CONFIG_PROVE_LOCKING=y      # Lockdep proving
CONFIG_DEBUG_PAGEALLOC=y    # Page allocation debug
```

---

## Level 2: Kernel Modules

### 2.1 Minimal Kernel Module

```c
// File: hello.c
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Hello World Driver");
MODULE_VERSION("1.0");

static int __init hello_init(void)
{
    pr_info("Hello, Kernel!\n");
    return 0;   /* 0 = success, negative = error */
}

static void __exit hello_exit(void)
{
    pr_info("Goodbye, Kernel!\n");
}

module_init(hello_init);
module_exit(hello_exit);
```

```makefile
# Kbuild Makefile
obj-m := hello.o

KDIR := /lib/modules/$(shell uname -r)/build

all:
	make -C $(KDIR) M=$(PWD) modules

clean:
	make -C $(KDIR) M=$(PWD) clean
```

```bash
make
sudo insmod hello.ko
dmesg | tail -5           # see "Hello, Kernel!"
sudo rmmod hello
dmesg | tail -5           # see "Goodbye, Kernel!"
modinfo hello.ko          # display module info
```

---

### 2.2 Module Parameters

```c
#include <linux/moduleparam.h>

static int debug_level = 0;
static char *device_name = "my_device";
static int ports[4] = {0, 1, 2, 3};
static int num_ports;

module_param(debug_level, int, 0644);
MODULE_PARM_DESC(debug_level, "Debug verbosity 0-3");

module_param(device_name, charp, 0444);
MODULE_PARM_DESC(device_name, "Device name string");

module_param_array(ports, int, &num_ports, 0444);
MODULE_PARM_DESC(ports, "Comma-separated port numbers");

/* Usage: sudo insmod my.ko debug_level=2 device_name=eth0 */
/* Change at runtime: echo 3 > /sys/module/my/parameters/debug_level */
```

---

### 2.3 Kernel Data Structures

#### Linked List
```c
#include <linux/list.h>
LIST_HEAD(my_list);
list_add(&node->list, &my_list);
list_add_tail(&node->list, &my_list);
list_del(&node->list);
list_for_each_entry(pos, &my_list, list) { }
list_for_each_entry_safe(pos, tmp, &my_list, list) { } /* safe for deletion */
```

#### Hash Table
```c
#include <linux/hashtable.h>
DEFINE_HASHTABLE(my_htable, 8);  /* 2^8 = 256 buckets */

hash_add(my_htable, &obj->hnode, obj->key);
hash_for_each(my_htable, bkt, obj, hnode) { }
hash_del(&obj->hnode);
```

#### Red-Black Tree
```c
#include <linux/rbtree.h>
struct rb_root my_tree = RB_ROOT;
/* Manual insert/search needed — see Documentation/core-api/rbtree.rst */
```

#### Radix Tree / XArray (modern)
```c
#include <linux/xarray.h>
DEFINE_XARRAY(my_xa);
xa_store(&my_xa, index, ptr, GFP_KERNEL);
void *val = xa_load(&my_xa, index);
xa_erase(&my_xa, index);
```

---

## Level 3: Kernel Memory Management Internals

### 3.1 Physical Memory Layout

```
Physical Memory (example ARM64 4GB system):
0x00000000 ─────────────────────────────────────
           │  Reserved (firmware, DTB)           │ ~2 MB
0x00200000 ─────────────────────────────────────
           │  Kernel Image (code + data)         │ ~10–50 MB
           ─────────────────────────────────────
           │  initramfs                          │
           ─────────────────────────────────────
           │  Page Allocator managed             │
           │  (ZONE_NORMAL)                      │ remaining RAM
0xFFFFFFFF ─────────────────────────────────────
```

### 3.2 Slab Allocator Internals

```
kmalloc() flow:
kmalloc(size, flags)
  → __kmalloc()
    → if size ≤ 8KB: kmalloc_caches[size_index]  (SLAB/SLUB)
    → if size > 8KB: alloc_pages() directly

SLUB allocator:
  ┌─────────────────────────────────────────────┐
  │  kmem_cache "my_cache" (128 bytes per obj)  │
  │  ┌────────┬────────┬────────┬──────────     │
  │  │ obj 0  │ obj 1  │ obj 2  │ ...           │ ← slab page
  └──┴────────┴────────┴────────┴───────────────┘
  Per-CPU free list → partial slabs → full slabs
```

### 3.3 Virtual Memory Areas

```bash
# Inspect process virtual memory
cat /proc/self/maps
# or
cat /proc/self/smaps

# Example output:
# 7f8a3000-7f8b2000 r-xp 00000000 08:01 12345  /lib/libc.so
# addr_start-addr_end perms offset dev ino path
```

```c
/* In kernel: vm_area_struct describes a VMA */
struct vm_area_struct {
    unsigned long vm_start;
    unsigned long vm_end;
    unsigned long vm_flags;     /* VM_READ, VM_WRITE, VM_EXEC */
    struct file *vm_file;       /* mapped file, if any */
    const struct vm_operations_struct *vm_ops;
};
```

---

## Level 4: Kernel Synchronization (Deep Dive)

### 4.1 Spinlock vs Mutex vs RCU

| Mechanism | Context | Can Sleep | Overhead |
|-----------|---------|-----------|----------|
| `spinlock` | IRQ+Process | NO | Low (busy wait) |
| `mutex` | Process only | YES | Medium |
| `rwlock` | IRQ+Process | NO | Low |
| `rwsem` | Process only | YES | Medium |
| `seqlock` | IRQ+Process | NO | Low (readers retry) |
| `RCU` | All | Reader:No, Writer:Yes | Very Low for reads |

### 4.2 Spinlock Usage

```c
#include <linux/spinlock.h>

DEFINE_SPINLOCK(my_lock);

/* Process context */
spin_lock(&my_lock);
/* critical section */
spin_unlock(&my_lock);

/* IRQ-safe (saves/restores IRQ state) */
unsigned long flags;
spin_lock_irqsave(&my_lock, flags);
/* critical section — safe even if IRQ fires */
spin_unlock_irqrestore(&my_lock, flags);

/* Bottom half safe */
spin_lock_bh(&my_lock);
spin_unlock_bh(&my_lock);
```

### 4.3 Mutex Usage

```c
#include <linux/mutex.h>

DEFINE_MUTEX(my_mutex);

mutex_lock(&my_mutex);          /* sleeps if locked — NEVER in IRQ! */
/* critical section */
mutex_unlock(&my_mutex);

/* Interruptible variant */
if (mutex_lock_interruptible(&my_mutex))
    return -ERESTARTSYS;
```

### 4.4 IRQ Handling

```c
#include <linux/interrupt.h>

/* Request IRQ */
ret = request_irq(irq_num, my_irq_handler,
                  IRQF_SHARED,           /* shared IRQ line */
                  "my_driver",
                  dev);                  /* dev_id for shared IRQs */

/* IRQ handler — runs in hardirq context (no sleep!) */
static irqreturn_t my_irq_handler(int irq, void *data)
{
    struct my_device *mydev = data;
    u32 status = readl(mydev->base + IRQ_STATUS);

    if (!(status & MY_IRQ_BIT))
        return IRQ_NONE;   /* not our interrupt */

    writel(status, mydev->base + IRQ_CLEAR);  /* ack hardware */

    /* Schedule bottom half for slow work */
    schedule_work(&mydev->work);

    return IRQ_HANDLED;
}

/* Threaded IRQ — handler runs in kernel thread (can sleep) */
ret = request_threaded_irq(irq, my_hardirq, my_threaded_irq,
                           IRQF_ONESHOT, "my_driver", dev);
```

---

## Level 5: Kernel Debugging Techniques

### 5.1 printk & Dynamic Debug

```c
/* Log levels */
pr_emerg("System is unusable\n");   /* KERN_EMERG   0 */
pr_alert("Action must be taken\n"); /* KERN_ALERT   1 */
pr_crit("Critical condition\n");    /* KERN_CRIT    2 */
pr_err("Error condition\n");        /* KERN_ERR     3 */
pr_warn("Warning\n");               /* KERN_WARNING 4 */
pr_notice("Normal but notable\n");  /* KERN_NOTICE  5 */
pr_info("Informational\n");         /* KERN_INFO    6 */
pr_debug("Debug (disabled)\n");     /* KERN_DEBUG   7 */

/* Device-specific logging (preferred) */
dev_err(dev, "Error: %d\n", ret);
dev_warn(dev, "Warning\n");
dev_info(dev, "Info\n");
dev_dbg(dev, "Debug\n");  /* activated via dynamic debug */

/* Enable dynamic debug at runtime */
echo "file my_driver.c +p" > /sys/kernel/debug/dynamic_debug/control
echo "module my_driver +p" > /sys/kernel/debug/dynamic_debug/control
```

### 5.2 Kernel Oops Analysis

```
[ 1234.567890] BUG: unable to handle kernel NULL pointer dereference at 0000000000000008
[ 1234.567891] PGD 0 P4D 0
[ 1234.567892] Oops: 0002 [#1] PREEMPT SMP NOPTI
[ 1234.567893] CPU: 2 PID: 1234 Comm: my_app Tainted: G   OE  5.15.0
[ 1234.567894] RIP: 0010:my_function+0x1c/0x40 [my_module]
[ 1234.567895] Call Trace:
[ 1234.567896]  <TASK>
[ 1234.567897]  another_function+0x30/0x50 [my_module]
[ 1234.567898]  sys_ioctl+0x100/0x200
```

```bash
# Decode oops — find exact source line
addr2line -e my_module.ko -i 0x1c
# or
scripts/faddr2line my_module.ko my_function+0x1c

# KASAN output shows exact buffer overflow
# LOCKDEP shows lock ordering violations
```

---

## Practice Projects

1. Write a kernel module with a character device + proc entry + sysfs attribute
2. Implement a blocking read() that waits for data using wait queues
3. Write a module that uses a workqueue to defer IRQ processing
4. Write a module with per-CPU statistics counters

## Interview Questions

1. What is the difference between process context and interrupt context?
2. Explain the Linux kernel memory zones (ZONE_DMA, ZONE_NORMAL, ZONE_HIGHMEM).
3. What happens during a kernel oops? How do you analyze one?
4. How does the Linux scheduler (CFS) work?
5. What is a softirq, tasklet, and workqueue? When do you use each?
6. Explain the difference between `request_irq` and `request_threaded_irq`.
7. What is KASAN and how does it help driver development?
8. Describe the lifecycle of a kernel module (init → in-use → exit).
