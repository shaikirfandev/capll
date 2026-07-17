# C Programming Mastery for Kernel/Driver Development

## Level 1: Basics — Foundation C for Embedded/Kernel Work

### 1.1 Data Types & Sizes (Platform-aware)

```c
#include <stdint.h>  /* Always use fixed-width types in drivers */

/* Kernel uses its own types — memorize these */
typedef uint8_t   u8;
typedef uint16_t  u16;
typedef uint32_t  u32;
typedef uint64_t  u64;
typedef int8_t    s8;
typedef int16_t   s16;
typedef int32_t   s32;
typedef int64_t   s64;

/* Example: Register access always uses u32 */
u32 reg_val = readl(base_addr + REG_OFFSET);
```

**Why it matters:** On 32-bit ARM, `int` is 32 bits. On 64-bit x86, `long` is 64 bits.  
Kernel drivers use `u32`, `u64`, etc. to be architecture-agnostic.

---

### 1.2 Pointers — The Core of Driver Programming

```c
/* Basic pointer */
int x = 10;
int *ptr = &x;
*ptr = 20;  /* x is now 20 */

/* Pointer arithmetic — critical for MMIO register access */
void __iomem *base = ioremap(PHYS_ADDR, SIZE);
u32 *reg0 = (u32 *)base;        /* register 0 */
u32 *reg1 = (u32 *)base + 1;    /* register 1 (offset +4 bytes) */
u32 *reg2 = (u32 *)((char *)base + 8); /* offset +8 bytes */

/* Double pointer — used in linked lists, kobject trees */
void **data_ptr;
```

**MMIO Register Access (NEVER dereference directly — use helpers):**
```c
/* CORRECT — uses memory barriers */
u32 val = readl(base + 0x100);
writel(0xDEAD, base + 0x104);

/* WRONG — no memory barrier, compiler may reorder */
u32 val = *(volatile u32 *)(base + 0x100);
```

---

### 1.3 Bitwise Operations — Driver Register Manipulation

```c
#define BIT(n)          (1UL << (n))
#define GENMASK(h, l)   (((~0UL) >> (BITS_PER_LONG - 1 - (h))) & (~0UL << (l)))

u32 reg = readl(base + CTRL_REG);

/* Set bit 3 */
reg |= BIT(3);

/* Clear bit 5 */
reg &= ~BIT(5);

/* Toggle bit 7 */
reg ^= BIT(7);

/* Check if bit 2 is set */
if (reg & BIT(2))
    pr_info("Bit 2 is set\n");

/* Set bits [7:4] = 0b1010 */
reg &= ~GENMASK(7, 4);          /* clear bits 7–4 */
reg |= (0xA << 4);              /* set new value */

/* Extract field [11:8] */
u32 field = (reg & GENMASK(11, 8)) >> 8;

/* Using FIELD_GET/FIELD_PREP (Linux kernel macros) */
#include <linux/bitfield.h>
#define CTRL_SPEED    GENMASK(3, 0)
#define CTRL_ENABLE   BIT(4)

u32 speed = FIELD_GET(CTRL_SPEED, reg);
reg = FIELD_PREP(CTRL_SPEED, 5) | CTRL_ENABLE;
```

---

### 1.4 Structures & Memory Layout

```c
/* Packed structure — for hardware register maps */
struct __attribute__((packed)) usb_descriptor {
    u8  bLength;
    u8  bDescriptorType;
    u16 bcdUSB;
    u8  bDeviceClass;
};

/* Alignment — important for DMA buffers */
struct dma_buffer {
    u32 data[256];
} __attribute__((aligned(4096)));  /* page-aligned */

/* Designated initializers (C99) */
struct file_operations my_fops = {
    .owner   = THIS_MODULE,
    .open    = my_open,
    .read    = my_read,
    .write   = my_write,
    .release = my_release,
};
```

---

### 1.5 Function Pointers — The Heart of Driver Callbacks

```c
/* Function pointer type */
typedef int (*irq_handler_fn)(int irq, void *data);

/* Callback table (like file_operations, dma_ops) */
struct my_driver_ops {
    int  (*init)(struct device *dev);
    void (*cleanup)(struct device *dev);
    int  (*transfer)(void *buf, size_t len);
    irq_handler_fn irq_handler;
};

/* Registering operations */
static struct my_driver_ops ops = {
    .init      = my_init,
    .cleanup   = my_cleanup,
    .transfer  = my_transfer,
    .irq_handler = my_irq_handler,
};

/* Calling through function pointer */
if (ops.transfer)
    ret = ops.transfer(buf, len);
```

---

## Level 2: Intermediate — Kernel-Specific C Patterns

### 2.1 Linked Lists (kernel style)

```c
#include <linux/list.h>

struct my_device {
    int id;
    char name[32];
    struct list_head list;   /* embedded list node */
};

/* Global list head */
static LIST_HEAD(device_list);
static DEFINE_SPINLOCK(device_list_lock);

/* Add to list */
struct my_device *dev = kmalloc(sizeof(*dev), GFP_KERNEL);
dev->id = 1;
spin_lock(&device_list_lock);
list_add_tail(&dev->list, &device_list);
spin_unlock(&device_list_lock);

/* Iterate */
struct my_device *entry;
list_for_each_entry(entry, &device_list, list) {
    pr_info("Device: %d %s\n", entry->id, entry->name);
}

/* Delete */
spin_lock(&device_list_lock);
list_del(&dev->list);
spin_unlock(&device_list_lock);
kfree(dev);
```

---

### 2.2 Container_of — Reverse Struct Navigation

```c
/*
 * Given a pointer to a member, get pointer to the containing struct
 * This is HOW list_for_each_entry works internally
 */
#define container_of(ptr, type, member) ({              \
    const typeof(((type *)0)->member) *__mptr = (ptr);  \
    (type *)((char *)__mptr - offsetof(type, member));  \
})

/* Real usage: IRQ handler gets back to device struct */
struct my_device {
    struct platform_device *pdev;
    void __iomem *base;
    int irq;
    struct work_struct work;   /* workqueue item */
};

static void my_work_handler(struct work_struct *work)
{
    /* Navigate from work_struct pointer back to my_device */
    struct my_device *mydev = container_of(work, struct my_device, work);
    /* Now we have our full device context */
    dev_info(&mydev->pdev->dev, "Work handled\n");
}
```

---

### 2.3 Memory Allocation in the Kernel

```c
#include <linux/slab.h>
#include <linux/vmalloc.h>

/* kmalloc — physically contiguous, limited to ~4MB, fast */
void *buf = kmalloc(size, GFP_KERNEL);   /* can sleep */
void *buf = kmalloc(size, GFP_ATOMIC);   /* cannot sleep (IRQ context) */
if (!buf)
    return -ENOMEM;
kfree(buf);

/* kzalloc — kmalloc + zero-initialize */
struct my_data *d = kzalloc(sizeof(*d), GFP_KERNEL);

/* vmalloc — virtual contiguous, not physically contiguous, larger */
void *vbuf = vmalloc(10 * 1024 * 1024);  /* 10 MB OK */
vfree(vbuf);

/* DMA coherent — physically contiguous, no cache */
dma_addr_t dma_handle;
void *cpu_addr = dma_alloc_coherent(dev, size, &dma_handle, GFP_KERNEL);
dma_free_coherent(dev, size, cpu_addr, dma_handle);

/* Memory pool — for fixed-size frequent allocations */
struct kmem_cache *cache = kmem_cache_create("my_cache",
    sizeof(struct my_obj), 0, SLAB_HWCACHE_ALIGN, NULL);
struct my_obj *obj = kmem_cache_alloc(cache, GFP_KERNEL);
kmem_cache_free(cache, obj);
```

**GFP Flags Quick Reference:**
| Flag | Context | Behavior |
|------|---------|----------|
| `GFP_KERNEL` | Process context | Can sleep, reclaim memory |
| `GFP_ATOMIC` | IRQ/spinlock | Cannot sleep, may fail |
| `GFP_DMA` | DMA zones | 16 MB zone (legacy ISA) |
| `GFP_DMA32` | DMA32 zone | 4 GB zone for 32-bit devices |
| `GFP_HIGHUSER` | User space | High memory |

---

### 2.4 Volatile & Memory Barriers

```c
#include <linux/compiler.h>
#include <asm/barrier.h>

/* mb()  — full memory barrier (reads + writes) */
/* rmb() — read memory barrier */
/* wmb() — write memory barrier */

/* MMIO sequence — order matters for hardware */
writel(CMD_START, base + CMD_REG);
wmb();                              /* ensure CMD_START is visible before STATUS check */
u32 status = readl(base + STATUS_REG);

/* Compiler barrier — prevent compiler reordering only */
barrier();

/* ACCESS_ONCE / READ_ONCE / WRITE_ONCE — prevent compiler optimizations */
u32 val = READ_ONCE(shared_variable);
WRITE_ONCE(shared_variable, new_val);
```

---

### 2.5 Kernel Error Handling Patterns

```c
/* PTR_ERR, IS_ERR, ERR_PTR — encode errors in pointers */
struct clk *clk = clk_get(dev, "aclk");
if (IS_ERR(clk)) {
    ret = PTR_ERR(clk);  /* extract -ENOENT, -EINVAL, etc. */
    dev_err(dev, "Failed to get clock: %d\n", ret);
    return ret;
}

/* goto-based cleanup — standard kernel pattern */
static int my_probe(struct platform_device *pdev)
{
    struct my_dev *mydev;
    int ret;

    mydev = devm_kzalloc(&pdev->dev, sizeof(*mydev), GFP_KERNEL);
    if (!mydev)
        return -ENOMEM;

    mydev->base = devm_platform_ioremap_resource(pdev, 0);
    if (IS_ERR(mydev->base)) {
        ret = PTR_ERR(mydev->base);
        goto err_ioremap;
    }

    ret = devm_request_irq(&pdev->dev, mydev->irq, my_irq_handler,
                           0, "my_driver", mydev);
    if (ret)
        goto err_irq;

    return 0;

err_irq:
    /* cleanup IRQ allocation */
err_ioremap:
    /* cleanup ioremap */
    return ret;
}
```

---

## Level 3: Advanced — Kernel Internals & Performance C

### 3.1 RCU (Read-Copy-Update) — Lock-free Reads

```c
#include <linux/rcupdate.h>

/* RCU-protected global pointer */
static struct config_data __rcu *config;

/* READER — very fast, no lock taken */
rcu_read_lock();
struct config_data *cfg = rcu_dereference(config);
if (cfg)
    use_config(cfg);        /* must not block! */
rcu_read_unlock();

/* WRITER — allocates new, publishes, waits for readers */
struct config_data *new_cfg = kmalloc(sizeof(*new_cfg), GFP_KERNEL);
copy_and_modify(new_cfg);

struct config_data *old_cfg = rcu_dereference_protected(config,
                                lockdep_is_held(&config_lock));
rcu_assign_pointer(config, new_cfg);
synchronize_rcu();          /* wait for all readers to finish */
kfree(old_cfg);
```

### 3.2 Atomic Operations

```c
#include <linux/atomic.h>

atomic_t refcount = ATOMIC_INIT(0);

atomic_inc(&refcount);
atomic_dec(&refcount);
int val = atomic_read(&refcount);
atomic_set(&refcount, 5);

/* Atomic bit operations */
unsigned long flags = 0;
set_bit(0, &flags);
clear_bit(0, &flags);
test_and_set_bit(1, &flags);

/* 64-bit atomics */
atomic64_t counter = ATOMIC64_INIT(0);
atomic64_add(1000, &counter);
```

### 3.3 Per-CPU Variables

```c
#include <linux/percpu.h>

/* Static per-CPU variable */
DEFINE_PER_CPU(u32, packet_count);

/* Access (must disable preemption) */
u32 *cnt = this_cpu_ptr(&packet_count);
(*cnt)++;

/* Or use helpers */
this_cpu_inc(packet_count);
this_cpu_add(packet_count, 5);

/* Read another CPU's variable */
u32 remote = per_cpu(packet_count, cpu_id);
```

### 3.4 Completion and Wait Queues

```c
#include <linux/completion.h>
#include <linux/wait.h>

/* Completion — single event signaling */
struct completion dma_done;
init_completion(&dma_done);

/* In IRQ handler */
complete(&dma_done);

/* In process context — wait for DMA */
wait_for_completion(&dma_done);
wait_for_completion_timeout(&dma_done, msecs_to_jiffies(500));

/* Wait queue — conditional waiting */
DECLARE_WAIT_QUEUE_HEAD(wq);
int condition = 0;

/* Waiter */
wait_event_interruptible(wq, condition != 0);

/* Waker (from IRQ) */
condition = 1;
wake_up_interruptible(&wq);
```

---

## Level 4: Kernel Coding Style (checkpatch rules)

```c
/* Indentation: TABS, not spaces */
if (condition) {
	do_something();   /* TAB indented */
}

/* Line length: max 100 characters (historically 80) */

/* Function naming: lower_case_with_underscores */
static int my_driver_probe(struct platform_device *pdev) { }

/* No typedef for structs (except specific cases) */
struct my_device { };          /* CORRECT */
typedef struct my_device { };  /* WRONG in kernel */

/* Opening brace on same line for functions — WRONG */
static int foo()
{                              /* CORRECT — brace on new line for functions */
}

/* All other blocks — brace on same line */
if (x) {                       /* CORRECT */
}

/* Comments: C89 style or kernel doc */
/* Single line comment */

/**
 * my_function - brief description
 * @param1: description of param1
 * @param2: description of param2
 *
 * Long description here.
 *
 * Return: 0 on success, negative error code on failure.
 */

/* Error messages */
dev_err(dev, "Failed to %s: %d\n", "init", ret);   /* CORRECT */
printk(KERN_ERR "msg\n");                           /* OLD STYLE */
pr_err("msg\n");                                    /* OK for non-device code */
```

---

## Practice Projects

1. **Basic:** Write a char driver that reads/writes a circular buffer
2. **Intermediate:** Write a platform driver that controls a GPIO via sysfs
3. **Advanced:** Write a DMA-capable driver that transfers data between two memory regions
4. **Expert:** Implement a virtual network device using netdev API

## Interview Questions

1. What is the difference between `kmalloc` and `vmalloc`? When do you use each?
2. Why can't you use `mutex_lock` in an interrupt handler?
3. What does `container_of` do and how does it work?
4. Explain `volatile` usage in kernel drivers — when is it appropriate?
5. What is RCU? Explain the reader/writer model.
6. What happens if you call `schedule()` while holding a spinlock?
7. Explain `GFP_ATOMIC` vs `GFP_KERNEL`.
8. What is a memory barrier and why is it needed for MMIO?
