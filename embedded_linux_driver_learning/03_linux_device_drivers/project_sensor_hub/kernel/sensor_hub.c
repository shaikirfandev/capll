// SPDX-License-Identifier: GPL-2.0-only
/*
 * sensor_hub.c — Industrial Sensor Hub platform driver
 *
 * Demonstrates:
 *  - platform_driver probe/remove with DT matching
 *  - MMIO register access (devm_platform_ioremap_resource)
 *  - Threaded IRQ (devm_request_threaded_irq)
 *  - Char device (cdev) with read/ioctl/poll
 *  - Wait queue for blocking read
 *  - kfifo for sample ring buffer (kernel→user)
 *  - sysfs attributes (DEVICE_ATTR_RW) per channel
 *  - DMA coherent buffer for burst FIFO drain
 *  - devm_ for all resource management
 */

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_irq.h>
#include <linux/io.h>
#include <linux/interrupt.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/uaccess.h>
#include <linux/slab.h>
#include <linux/kfifo.h>
#include <linux/poll.h>
#include <linux/dma-mapping.h>
#include <linux/ktime.h>
#include <linux/mutex.h>
#include <linux/spinlock.h>

#include "sensor_hub.h"

/* ------------------------------------------------------------------ */
/*  Driver-private data                                                 */
/* ------------------------------------------------------------------ */

#define DRIVER_NAME     "sensor-hub"
#define SH_KFIFO_SIZE   512     /* samples in the kernel ring buffer */

DEFINE_KFIFO(sh_sample_fifo, struct sh_sample, SH_KFIFO_SIZE);

struct sensor_hub_dev {
    /* hardware */
    void __iomem            *base;
    int                      irq;
    u32                      active_channel;

    /* DMA for burst reads */
    u16                     *dma_buf;       /* kernel virtual */
    dma_addr_t               dma_addr;      /* bus/physical address */

    /* sample ring buffer (IRQ → read path) */
    DECLARE_KFIFO_PTR(fifo, struct sh_sample);
    spinlock_t               fifo_lock;
    wait_queue_head_t        read_wq;

    /* char device */
    struct cdev              cdev;
    struct device           *chardev;
    dev_t                    devt;

    /* calibration offsets (per channel) */
    s32                      cal_offset[SH_NUM_CHANNELS];

    /* sysfs control */
    struct mutex             sysfs_lock;

    /* parent device (for dev_* logging and devm) */
    struct device           *dev;
};

/* ------------------------------------------------------------------ */
/*  Register accessors                                                  */
/* ------------------------------------------------------------------ */

static inline u32 sh_read(struct sensor_hub_dev *sh, u32 reg)
{
    return ioread32(sh->base + reg);
}

static inline void sh_write(struct sensor_hub_dev *sh, u32 reg, u32 val)
{
    iowrite32(val, sh->base + reg);
}

static inline void sh_set_bits(struct sensor_hub_dev *sh, u32 reg, u32 mask)
{
    sh_write(sh, reg, sh_read(sh, reg) | mask);
}

static inline void sh_clear_bits(struct sensor_hub_dev *sh, u32 reg, u32 mask)
{
    sh_write(sh, reg, sh_read(sh, reg) & ~mask);
}

/* ------------------------------------------------------------------ */
/*  IRQ handler (hard + threaded)                                       */
/* ------------------------------------------------------------------ */

/*
 * Hard IRQ: just acknowledge and disable further IRQs until thread runs.
 * Returns IRQ_WAKE_THREAD to schedule the threaded handler.
 */
static irqreturn_t sh_irq_hard(int irq, void *dev_id)
{
    struct sensor_hub_dev *sh = dev_id;
    u32 status = sh_read(sh, SH_STATUS);

    if (!(status & SH_STATUS_IRQ_PENDING))
        return IRQ_NONE;

    /* Mask IRQs at hardware; threaded handler will re-enable */
    sh_clear_bits(sh, SH_CTRL, SH_CTRL_IRQ_DATA_RDY |
                               SH_CTRL_IRQ_OVERFLOW  |
                               SH_CTRL_IRQ_THR);
    return IRQ_WAKE_THREAD;
}

/*
 * Threaded IRQ: runs in process context, safe to sleep.
 * Drains the hardware FIFO into the kfifo ring buffer.
 */
static irqreturn_t sh_irq_thread(int irq, void *dev_id)
{
    struct sensor_hub_dev *sh = dev_id;
    u32 status = sh_read(sh, SH_STATUS);
    u32 fifo_lvl;
    struct sh_sample sample;
    u64 ts = ktime_get_ns();

    if (status & SH_STATUS_OVERFLOW)
        dev_warn(sh->dev, "FIFO overflow — samples lost\n");

    /* Drain up to FIFO_DEPTH samples */
    fifo_lvl = sh_read(sh, SH_FIFO_LVL);
    while (fifo_lvl--) {
        u32 raw = sh_read(sh, SH_FIFO_DATA);   /* 16-bit sample, read-clears */
        s32 calibrated = (s16)raw + sh->cal_offset[sh->active_channel];

        /* Clamp to u16 range */
        if (calibrated < 0)        calibrated = 0;
        if (calibrated > 0xFFFF)   calibrated = 0xFFFF;

        sample.value        = (u16)calibrated;
        sample.channel      = (u8)sh->active_channel;
        sample.flags        = (u8)(status & 0x0F);
        sample.reserved     = 0;
        sample.timestamp_ns = ts;

        spin_lock(&sh->fifo_lock);
        if (kfifo_put(&sh->fifo, sample) == 0)
            dev_dbg(sh->dev, "kfifo full, dropping sample\n");
        spin_unlock(&sh->fifo_lock);
    }

    /* Clear IRQ pending bit (W1C) */
    sh_write(sh, SH_STATUS, SH_STATUS_IRQ_PENDING);

    /* Re-enable IRQs at hardware */
    sh_set_bits(sh, SH_CTRL, SH_CTRL_IRQ_DATA_RDY |
                              SH_CTRL_IRQ_OVERFLOW  |
                              SH_CTRL_IRQ_THR);

    /* Wake any blocking read() calls */
    wake_up_interruptible(&sh->read_wq);

    return IRQ_HANDLED;
}

/* ------------------------------------------------------------------ */
/*  Char device file operations                                         */
/* ------------------------------------------------------------------ */

static int sh_open(struct inode *inode, struct file *filp)
{
    struct sensor_hub_dev *sh =
        container_of(inode->i_cdev, struct sensor_hub_dev, cdev);

    filp->private_data = sh;
    return nonseekable_open(inode, filp);
}

static int sh_release(struct inode *inode, struct file *filp)
{
    return 0;
}

/*
 * read() — blocks until at least one sample is available,
 * then copies as many sh_sample structs as fit in the user buffer.
 */
static ssize_t sh_read(struct file *filp, char __user *ubuf,
                        size_t count, loff_t *ppos)
{
    struct sensor_hub_dev *sh = filp->private_data;
    struct sh_sample sample;
    size_t copied = 0;
    int ret;

    /* count must be a multiple of sample size */
    if (count < sizeof(sample))
        return -EINVAL;

    /* Blocking wait: sleep until a sample is in the fifo */
    if (filp->f_flags & O_NONBLOCK) {
        if (kfifo_is_empty(&sh->fifo))
            return -EAGAIN;
    } else {
        ret = wait_event_interruptible(sh->read_wq,
                                       !kfifo_is_empty(&sh->fifo));
        if (ret)
            return ret;
    }

    /* Copy samples to user, up to 'count' bytes */
    while (copied + sizeof(sample) <= count) {
        unsigned int got;

        spin_lock_irq(&sh->fifo_lock);
        got = kfifo_get(&sh->fifo, &sample);
        spin_unlock_irq(&sh->fifo_lock);

        if (!got)
            break;

        if (copy_to_user(ubuf + copied, &sample, sizeof(sample)))
            return -EFAULT;

        copied += sizeof(sample);
    }

    return copied ? (ssize_t)copied : -EAGAIN;
}

/*
 * poll() — signals EPOLLIN when samples are available.
 */
static __poll_t sh_poll(struct file *filp, poll_table *wait)
{
    struct sensor_hub_dev *sh = filp->private_data;

    poll_wait(filp, &sh->read_wq, wait);
    if (!kfifo_is_empty(&sh->fifo))
        return EPOLLIN | EPOLLRDNORM;
    return 0;
}

/*
 * ioctl() — channel select, rate, calibration, flush, burst DMA read.
 */
static long sh_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
    struct sensor_hub_dev *sh = filp->private_data;
    void __user *uarg = (void __user *)arg;
    u32 val;
    int ret = 0;

    if (_IOC_TYPE(cmd) != SH_IOC_MAGIC)
        return -ENOTTY;
    if (_IOC_NR(cmd) > SH_IOC_MAXNR)
        return -ENOTTY;

    switch (cmd) {

    case SH_IOC_SET_CHANNEL:
        if (copy_from_user(&val, uarg, sizeof(val)))
            return -EFAULT;
        if (val >= SH_NUM_CHANNELS)
            return -EINVAL;
        sh->active_channel = val;
        sh_write(sh, SH_CH_SEL, val);
        break;

    case SH_IOC_GET_CHANNEL:
        val = sh->active_channel;
        if (copy_to_user(uarg, &val, sizeof(val)))
            return -EFAULT;
        break;

    case SH_IOC_SET_RATE:
        if (copy_from_user(&val, uarg, sizeof(val)))
            return -EFAULT;
        if (val < 1 || val > 1000)
            return -EINVAL;
        sh_write(sh, SH_RATE, val);
        break;

    case SH_IOC_GET_RATE:
        val = sh_read(sh, SH_RATE);
        if (copy_to_user(uarg, &val, sizeof(val)))
            return -EFAULT;
        break;

    case SH_IOC_FLUSH_FIFO:
        /* Reset bit is self-clearing */
        sh_set_bits(sh, SH_CTRL, SH_CTRL_RESET);
        spin_lock_irq(&sh->fifo_lock);
        kfifo_reset(&sh->fifo);
        spin_unlock_irq(&sh->fifo_lock);
        break;

    case SH_IOC_SET_CAL: {
        struct sh_cal cal;
        if (copy_from_user(&cal, uarg, sizeof(cal)))
            return -EFAULT;
        if (cal.channel >= SH_NUM_CHANNELS)
            return -EINVAL;
        sh->cal_offset[cal.channel] = cal.offset;
        sh_write(sh, SH_CAL_BASE + cal.channel * 4, (u32)cal.offset);
        break;
    }

    case SH_IOC_GET_CAL: {
        struct sh_cal cal;
        if (copy_from_user(&cal, uarg, sizeof(cal)))
            return -EFAULT;
        if (cal.channel >= SH_NUM_CHANNELS)
            return -EINVAL;
        cal.offset = sh->cal_offset[cal.channel];
        if (copy_to_user(uarg, &cal, sizeof(cal)))
            return -EFAULT;
        break;
    }

    case SH_IOC_BURST_READ: {
        /*
         * Trigger a DMA FIFO drain: hardware fills dma_buf,
         * then we copy the requested number of samples to userspace.
         */
        struct sh_burst_req req;
        u32 available;

        if (copy_from_user(&req, uarg, sizeof(req)))
            return -EFAULT;

        if (req.count > SH_DMA_BUF_SAMPLES)
            req.count = SH_DMA_BUF_SAMPLES;

        available = sh_read(sh, SH_FIFO_LVL);
        req.actual = min(req.count, available);

        if (req.actual > 0) {
            /*
             * In real hardware: program DMA controller with dma_addr,
             * wait for DMA completion (here we simulate with PIO).
             */
            u32 i;
            for (i = 0; i < req.actual; i++)
                sh->dma_buf[i] = (u16)sh_read(sh, SH_FIFO_DATA);

            /* Apply calibration and copy to user */
            for (i = 0; i < req.actual; i++) {
                s32 v = (s16)sh->dma_buf[i] +
                        sh->cal_offset[sh->active_channel];
                sh->dma_buf[i] = (u16)clamp(v, 0, (s32)0xFFFF);
            }

            if (copy_to_user(req.buf, sh->dma_buf,
                             req.actual * sizeof(u16)))
                return -EFAULT;
        }

        if (copy_to_user(uarg, &req, sizeof(req)))
            return -EFAULT;
        break;
    }

    default:
        return -ENOTTY;
    }

    return ret;
}

static const struct file_operations sh_fops = {
    .owner          = THIS_MODULE,
    .open           = sh_open,
    .release        = sh_release,
    .read           = sh_read,
    .poll           = sh_poll,
    .unlocked_ioctl = sh_ioctl,
    .llseek         = no_llseek,
};

/* ------------------------------------------------------------------ */
/*  sysfs attributes                                                    */
/* ------------------------------------------------------------------ */

/* /sys/.../rate — sample rate in Hz */
static ssize_t rate_show(struct device *dev, struct device_attribute *attr,
                          char *buf)
{
    struct sensor_hub_dev *sh = dev_get_drvdata(dev);
    return sysfs_emit(buf, "%u\n", sh_read(sh, SH_RATE));
}

static ssize_t rate_store(struct device *dev, struct device_attribute *attr,
                           const char *buf, size_t count)
{
    struct sensor_hub_dev *sh = dev_get_drvdata(dev);
    u32 val;
    int ret;

    ret = kstrtou32(buf, 10, &val);
    if (ret)
        return ret;
    if (val < 1 || val > 1000)
        return -EINVAL;

    mutex_lock(&sh->sysfs_lock);
    sh_write(sh, SH_RATE, val);
    mutex_unlock(&sh->sysfs_lock);

    return count;
}
static DEVICE_ATTR_RW(rate);

/* /sys/.../channel — active channel (0–3) */
static ssize_t channel_show(struct device *dev, struct device_attribute *attr,
                             char *buf)
{
    struct sensor_hub_dev *sh = dev_get_drvdata(dev);
    return sysfs_emit(buf, "%u\n", sh->active_channel);
}

static ssize_t channel_store(struct device *dev, struct device_attribute *attr,
                              const char *buf, size_t count)
{
    struct sensor_hub_dev *sh = dev_get_drvdata(dev);
    u32 val;
    int ret;

    ret = kstrtou32(buf, 10, &val);
    if (ret)
        return ret;
    if (val >= SH_NUM_CHANNELS)
        return -EINVAL;

    mutex_lock(&sh->sysfs_lock);
    sh->active_channel = val;
    sh_write(sh, SH_CH_SEL, val);
    mutex_unlock(&sh->sysfs_lock);

    return count;
}
static DEVICE_ATTR_RW(channel);

/* /sys/.../status — snapshot of SH_STATUS register */
static ssize_t status_show(struct device *dev, struct device_attribute *attr,
                            char *buf)
{
    struct sensor_hub_dev *sh = dev_get_drvdata(dev);
    u32 s = sh_read(sh, SH_STATUS);
    return sysfs_emit(buf,
        "data_rdy=%u overflow=%u thr_hi=%u thr_lo=%u fifo_lvl=%u\n",
        !!(s & SH_STATUS_DATA_RDY),
        !!(s & SH_STATUS_OVERFLOW),
        !!(s & SH_STATUS_THR_HI),
        !!(s & SH_STATUS_THR_LO),
        sh_read(sh, SH_FIFO_LVL));
}
static DEVICE_ATTR_RO(status);

/* /sys/.../threshold — "hi lo" space-separated */
static ssize_t threshold_show(struct device *dev, struct device_attribute *attr,
                               char *buf)
{
    struct sensor_hub_dev *sh = dev_get_drvdata(dev);
    return sysfs_emit(buf, "%u %u\n",
                      sh_read(sh, SH_THR_HI),
                      sh_read(sh, SH_THR_LO));
}

static ssize_t threshold_store(struct device *dev,
                                struct device_attribute *attr,
                                const char *buf, size_t count)
{
    struct sensor_hub_dev *sh = dev_get_drvdata(dev);
    u32 hi, lo;

    if (sscanf(buf, "%u %u", &hi, &lo) != 2)
        return -EINVAL;
    if (hi > 0xFFFF || lo > 0xFFFF || lo > hi)
        return -EINVAL;

    mutex_lock(&sh->sysfs_lock);
    sh_write(sh, SH_THR_HI, hi);
    sh_write(sh, SH_THR_LO, lo);
    mutex_unlock(&sh->sysfs_lock);

    return count;
}
static DEVICE_ATTR_RW(threshold);

/* /sys/.../enable — 1 = enable ADC, 0 = disable */
static ssize_t enable_show(struct device *dev, struct device_attribute *attr,
                            char *buf)
{
    struct sensor_hub_dev *sh = dev_get_drvdata(dev);
    return sysfs_emit(buf, "%u\n",
                      !!(sh_read(sh, SH_CTRL) & SH_CTRL_ENABLE));
}

static ssize_t enable_store(struct device *dev, struct device_attribute *attr,
                             const char *buf, size_t count)
{
    struct sensor_hub_dev *sh = dev_get_drvdata(dev);
    u32 val;
    int ret;

    ret = kstrtou32(buf, 10, &val);
    if (ret)
        return ret;

    mutex_lock(&sh->sysfs_lock);
    if (val)
        sh_set_bits(sh, SH_CTRL, SH_CTRL_ENABLE);
    else
        sh_clear_bits(sh, SH_CTRL, SH_CTRL_ENABLE);
    mutex_unlock(&sh->sysfs_lock);

    return count;
}
static DEVICE_ATTR_RW(enable);

static struct attribute *sh_attrs[] = {
    &dev_attr_rate.attr,
    &dev_attr_channel.attr,
    &dev_attr_status.attr,
    &dev_attr_threshold.attr,
    &dev_attr_enable.attr,
    NULL,
};

static const struct attribute_group sh_attr_group = {
    .name  = "sensor_hub",
    .attrs = sh_attrs,
};

/* ------------------------------------------------------------------ */
/*  Char device class (shared across all instances)                     */
/* ------------------------------------------------------------------ */

static struct class *sh_class;
static dev_t        sh_devt_base;
static DEFINE_IDA(sh_ida);

/* ------------------------------------------------------------------ */
/*  Platform driver probe / remove                                      */
/* ------------------------------------------------------------------ */

static int sh_probe(struct platform_device *pdev)
{
    struct device *dev = &pdev->dev;
    struct sensor_hub_dev *sh;
    struct resource *res;
    int ret;
    int id;

    /* Allocate driver state (devm: freed on remove) */
    sh = devm_kzalloc(dev, sizeof(*sh), GFP_KERNEL);
    if (!sh)
        return -ENOMEM;

    sh->dev = dev;
    platform_set_drvdata(pdev, sh);

    /* Map MMIO registers */
    sh->base = devm_platform_ioremap_resource(pdev, 0);
    if (IS_ERR(sh->base))
        return dev_err_probe(dev, PTR_ERR(sh->base),
                             "cannot map MMIO registers\n");

    /* Get IRQ from DT */
    sh->irq = platform_get_irq(pdev, 0);
    if (sh->irq < 0)
        return dev_err_probe(dev, sh->irq, "no IRQ in DT\n");

    /* Allocate DMA coherent buffer for burst reads */
    sh->dma_buf = dma_alloc_coherent(dev, SH_DMA_BUF_BYTES,
                                     &sh->dma_addr, GFP_KERNEL);
    if (!sh->dma_buf)
        return dev_err_probe(dev, -ENOMEM, "DMA alloc failed\n");

    /* Allocate kfifo ring buffer */
    ret = kfifo_alloc(&sh->fifo, SH_KFIFO_SIZE, GFP_KERNEL);
    if (ret)
        goto err_dma;

    /* Init synchronisation primitives */
    spin_lock_init(&sh->fifo_lock);
    init_waitqueue_head(&sh->read_wq);
    mutex_init(&sh->sysfs_lock);

    /* Hardware reset + configure */
    sh_write(sh, SH_CTRL, SH_CTRL_RESET);
    /* Reset is self-clearing; wait one MMIO cycle */
    sh_read(sh, SH_CTRL);
    sh_write(sh, SH_RATE, 100);   /* default 100 Hz */
    sh_write(sh, SH_CH_SEL, 0);
    sh->active_channel = 0;

    /* Request threaded IRQ */
    ret = devm_request_threaded_irq(dev, sh->irq,
                                    sh_irq_hard, sh_irq_thread,
                                    IRQF_SHARED, DRIVER_NAME, sh);
    if (ret)
        goto err_fifo;

    /* Assign device number */
    id = ida_alloc(&sh_ida, GFP_KERNEL);
    if (id < 0) {
        ret = id;
        goto err_fifo;
    }
    sh->devt = MKDEV(MAJOR(sh_devt_base), id);

    /* Register char device */
    cdev_init(&sh->cdev, &sh_fops);
    sh->cdev.owner = THIS_MODULE;
    ret = cdev_add(&sh->cdev, sh->devt, 1);
    if (ret)
        goto err_ida;

    /* Create /dev/sensor_hubN node */
    sh->chardev = device_create(sh_class, dev, sh->devt, sh,
                                "sensor_hub%d", id);
    if (IS_ERR(sh->chardev)) {
        ret = PTR_ERR(sh->chardev);
        goto err_cdev;
    }

    /* Create sysfs attribute group */
    ret = devm_device_add_group(dev, &sh_attr_group);
    if (ret)
        goto err_chardev;

    /* Enable hardware with IRQs */
    sh_write(sh, SH_CTRL, SH_CTRL_ENABLE    |
                           SH_CTRL_IRQ_DATA_RDY |
                           SH_CTRL_IRQ_OVERFLOW |
                           SH_CTRL_IRQ_THR);

    dev_info(dev, "sensor hub ready: /dev/sensor_hub%d IRQ=%d\n", id, sh->irq);
    return 0;

err_chardev:
    device_destroy(sh_class, sh->devt);
err_cdev:
    cdev_del(&sh->cdev);
err_ida:
    ida_free(&sh_ida, id);
err_fifo:
    kfifo_free(&sh->fifo);
err_dma:
    dma_free_coherent(dev, SH_DMA_BUF_BYTES, sh->dma_buf, sh->dma_addr);
    return ret;
}

static void sh_remove(struct platform_device *pdev)
{
    struct sensor_hub_dev *sh = platform_get_drvdata(pdev);
    int id = MINOR(sh->devt);

    /* Disable hardware first */
    sh_write(sh, SH_CTRL, 0);

    device_destroy(sh_class, sh->devt);
    cdev_del(&sh->cdev);
    ida_free(&sh_ida, id);
    kfifo_free(&sh->fifo);
    dma_free_coherent(sh->dev, SH_DMA_BUF_BYTES, sh->dma_buf, sh->dma_addr);
    /* devm_ resources (ioremap, irq, sysfs group) freed automatically */
}

/* ------------------------------------------------------------------ */
/*  Power management (suspend / resume)                                 */
/* ------------------------------------------------------------------ */

static int sh_suspend(struct device *dev)
{
    struct sensor_hub_dev *sh = dev_get_drvdata(dev);

    sh_clear_bits(sh, SH_CTRL, SH_CTRL_ENABLE);
    dev_dbg(dev, "suspended\n");
    return 0;
}

static int sh_resume(struct device *dev)
{
    struct sensor_hub_dev *sh = dev_get_drvdata(dev);

    sh_set_bits(sh, SH_CTRL, SH_CTRL_ENABLE |
                              SH_CTRL_IRQ_DATA_RDY |
                              SH_CTRL_IRQ_OVERFLOW |
                              SH_CTRL_IRQ_THR);
    dev_dbg(dev, "resumed\n");
    return 0;
}

static DEFINE_SIMPLE_DEV_PM_OPS(sh_pm_ops, sh_suspend, sh_resume);

/* ------------------------------------------------------------------ */
/*  Device Tree match table                                             */
/* ------------------------------------------------------------------ */

static const struct of_device_id sh_of_ids[] = {
    { .compatible = "example,sensor-hub-v1" },
    { .compatible = "example,sensor-hub-v2" },
    { /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, sh_of_ids);

static struct platform_driver sh_driver = {
    .driver = {
        .name           = DRIVER_NAME,
        .of_match_table = sh_of_ids,
        .pm             = pm_sleep_ptr(&sh_pm_ops),
    },
    .probe  = sh_probe,
    .remove = sh_remove,
};

/* ------------------------------------------------------------------ */
/*  Module init / exit                                                  */
/* ------------------------------------------------------------------ */

static int __init sh_init(void)
{
    int ret;

    /* Allocate a range of char device numbers (up to 8 instances) */
    ret = alloc_chrdev_region(&sh_devt_base, 0, 8, DRIVER_NAME);
    if (ret)
        return ret;

    sh_class = class_create(DRIVER_NAME);
    if (IS_ERR(sh_class)) {
        ret = PTR_ERR(sh_class);
        goto err_chrdev;
    }

    ret = platform_driver_register(&sh_driver);
    if (ret)
        goto err_class;

    pr_info("sensor_hub: driver loaded (major %d)\n", MAJOR(sh_devt_base));
    return 0;

err_class:
    class_destroy(sh_class);
err_chrdev:
    unregister_chrdev_region(sh_devt_base, 8);
    return ret;
}

static void __exit sh_exit(void)
{
    platform_driver_unregister(&sh_driver);
    class_destroy(sh_class);
    unregister_chrdev_region(sh_devt_base, 8);
    ida_destroy(&sh_ida);
    pr_info("sensor_hub: driver unloaded\n");
}

module_init(sh_init);
module_exit(sh_exit);

MODULE_AUTHOR("Embedded Linux Team");
MODULE_DESCRIPTION("Industrial Sensor Hub platform driver");
MODULE_LICENSE("GPL v2");
