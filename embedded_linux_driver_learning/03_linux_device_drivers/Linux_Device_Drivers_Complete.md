# Linux Device Driver Programming — Complete Guide

## Level 1: Driver Model Basics

### 1.1 Linux Driver Model (bus/device/driver)

```
Bus (e.g., Platform, PCI, USB, I2C, SPI)
    │
    ├── Device (registered via DT or ACPI or board file)
    │     hardware_exists = true
    │
    └── Driver (registered via module_platform_driver())
          can_handle_device() checked by bus core
          → if match: .probe() called
          → if remove: .remove() called
```

```c
/* Driver registers itself */
module_platform_driver(my_platform_driver);

/* Expands to: */
static int __init my_platform_driver_init(void)
{
    return platform_driver_register(&my_platform_driver);
}
static void __exit my_platform_driver_exit(void)
{
    platform_driver_unregister(&my_platform_driver);
}
module_init(my_platform_driver_init);
module_exit(my_platform_driver_exit);
```

---

### 1.2 Complete Character Device Driver

```c
// File: chardev.c — Complete char driver with all file operations
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/uaccess.h>
#include <linux/slab.h>

#define DEVICE_NAME "chardev"
#define BUF_SIZE    4096

struct chardev_data {
    struct cdev cdev;
    char *buf;
    size_t buf_len;
    struct mutex lock;
    wait_queue_head_t read_wq;
    int has_data;
};

static dev_t dev_num;
static struct class *dev_class;
static struct chardev_data *cdata;

/* open */
static int chardev_open(struct inode *inode, struct file *filp)
{
    struct chardev_data *data = container_of(inode->i_cdev,
                                             struct chardev_data, cdev);
    filp->private_data = data;
    pr_info("chardev: opened\n");
    return 0;
}

/* release */
static int chardev_release(struct inode *inode, struct file *filp)
{
    pr_info("chardev: released\n");
    return 0;
}

/* read — blocking read */
static ssize_t chardev_read(struct file *filp, char __user *ubuf,
                             size_t count, loff_t *ppos)
{
    struct chardev_data *data = filp->private_data;
    ssize_t ret;

    if (wait_event_interruptible(data->read_wq, data->has_data))
        return -ERESTARTSYS;

    mutex_lock(&data->lock);

    if (count > data->buf_len)
        count = data->buf_len;

    if (copy_to_user(ubuf, data->buf, count)) {
        ret = -EFAULT;
        goto out;
    }

    data->has_data = 0;
    ret = count;

out:
    mutex_unlock(&data->lock);
    return ret;
}

/* write */
static ssize_t chardev_write(struct file *filp, const char __user *ubuf,
                              size_t count, loff_t *ppos)
{
    struct chardev_data *data = filp->private_data;

    if (count > BUF_SIZE)
        return -EINVAL;

    mutex_lock(&data->lock);

    if (copy_from_user(data->buf, ubuf, count)) {
        mutex_unlock(&data->lock);
        return -EFAULT;
    }

    data->buf_len = count;
    data->has_data = 1;
    wake_up_interruptible(&data->read_wq);

    mutex_unlock(&data->lock);
    return count;
}

/* ioctl */
#define CHARDEV_IOC_MAGIC    'k'
#define CHARDEV_IOCRESET     _IO(CHARDEV_IOC_MAGIC, 0)
#define CHARDEV_IOCGBUFSIZE  _IOR(CHARDEV_IOC_MAGIC, 1, int)
#define CHARDEV_IOCSBUFSIZE  _IOW(CHARDEV_IOC_MAGIC, 2, int)

static long chardev_ioctl(struct file *filp, unsigned int cmd,
                           unsigned long arg)
{
    struct chardev_data *data = filp->private_data;

    switch (cmd) {
    case CHARDEV_IOCRESET:
        mutex_lock(&data->lock);
        data->buf_len = 0;
        data->has_data = 0;
        mutex_unlock(&data->lock);
        break;

    case CHARDEV_IOCGBUFSIZE:
        if (put_user(BUF_SIZE, (int __user *)arg))
            return -EFAULT;
        break;

    default:
        return -ENOTTY;
    }

    return 0;
}

static const struct file_operations chardev_fops = {
    .owner          = THIS_MODULE,
    .open           = chardev_open,
    .release        = chardev_release,
    .read           = chardev_read,
    .write          = chardev_write,
    .unlocked_ioctl = chardev_ioctl,
};

static int __init chardev_init(void)
{
    int ret;

    cdata = kzalloc(sizeof(*cdata), GFP_KERNEL);
    if (!cdata)
        return -ENOMEM;

    cdata->buf = kmalloc(BUF_SIZE, GFP_KERNEL);
    if (!cdata->buf) {
        ret = -ENOMEM;
        goto err_buf;
    }

    mutex_init(&cdata->lock);
    init_waitqueue_head(&cdata->read_wq);

    /* Allocate device number */
    ret = alloc_chrdev_region(&dev_num, 0, 1, DEVICE_NAME);
    if (ret)
        goto err_chrdev;

    /* Initialize cdev */
    cdev_init(&cdata->cdev, &chardev_fops);
    cdata->cdev.owner = THIS_MODULE;

    ret = cdev_add(&cdata->cdev, dev_num, 1);
    if (ret)
        goto err_cdev;

    /* Create device class and node in /dev/ */
    dev_class = class_create(THIS_MODULE, DEVICE_NAME);
    if (IS_ERR(dev_class)) {
        ret = PTR_ERR(dev_class);
        goto err_class;
    }

    device_create(dev_class, NULL, dev_num, NULL, DEVICE_NAME);
    pr_info("chardev: registered at major=%d\n", MAJOR(dev_num));
    return 0;

err_class:
    cdev_del(&cdata->cdev);
err_cdev:
    unregister_chrdev_region(dev_num, 1);
err_chrdev:
    kfree(cdata->buf);
err_buf:
    kfree(cdata);
    return ret;
}

static void __exit chardev_exit(void)
{
    device_destroy(dev_class, dev_num);
    class_destroy(dev_class);
    cdev_del(&cdata->cdev);
    unregister_chrdev_region(dev_num, 1);
    kfree(cdata->buf);
    kfree(cdata);
    pr_info("chardev: unregistered\n");
}

module_init(chardev_init);
module_exit(chardev_exit);
MODULE_LICENSE("GPL");
```

---

## Level 2: Platform Driver (Device Tree)

### 2.1 Platform Driver Structure

```c
// File: my_platform_driver.c
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/io.h>
#include <linux/clk.h>
#include <linux/interrupt.h>
#include <linux/pm_runtime.h>

struct my_priv {
    struct device       *dev;
    void __iomem        *base;
    struct clk          *clk;
    int                  irq;
};

/* IRQ handler */
static irqreturn_t my_irq_handler(int irq, void *data)
{
    struct my_priv *priv = data;
    u32 status = readl(priv->base + 0x04);

    if (!status)
        return IRQ_NONE;

    writel(status, priv->base + 0x04);   /* clear IRQ */
    return IRQ_HANDLED;
}

static int my_probe(struct platform_device *pdev)
{
    struct my_priv *priv;
    struct resource *res;
    int ret;

    priv = devm_kzalloc(&pdev->dev, sizeof(*priv), GFP_KERNEL);
    if (!priv)
        return -ENOMEM;

    priv->dev = &pdev->dev;

    /* Get memory resource from DT */
    priv->base = devm_platform_ioremap_resource(pdev, 0);
    if (IS_ERR(priv->base))
        return PTR_ERR(priv->base);

    /* Get clock from DT */
    priv->clk = devm_clk_get(&pdev->dev, "core");
    if (IS_ERR(priv->clk))
        return dev_err_probe(&pdev->dev, PTR_ERR(priv->clk),
                             "Failed to get clock\n");

    ret = clk_prepare_enable(priv->clk);
    if (ret)
        return ret;

    /* Get IRQ from DT */
    priv->irq = platform_get_irq(pdev, 0);
    if (priv->irq < 0)
        return priv->irq;

    ret = devm_request_irq(&pdev->dev, priv->irq, my_irq_handler,
                           0, dev_name(&pdev->dev), priv);
    if (ret)
        return ret;

    platform_set_drvdata(pdev, priv);
    pm_runtime_enable(&pdev->dev);

    dev_info(&pdev->dev, "Probed successfully at %p\n", priv->base);
    return 0;
}

static int my_remove(struct platform_device *pdev)
{
    struct my_priv *priv = platform_get_drvdata(pdev);
    pm_runtime_disable(&pdev->dev);
    clk_disable_unprepare(priv->clk);
    return 0;
}

/* Device Tree match table */
static const struct of_device_id my_of_match[] = {
    { .compatible = "vendor,my-controller-v1" },
    { .compatible = "vendor,my-controller-v2" },
    { /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, my_of_match);

static struct platform_driver my_driver = {
    .probe  = my_probe,
    .remove = my_remove,
    .driver = {
        .name           = "my_controller",
        .of_match_table = my_of_match,
        .pm             = &my_pm_ops,   /* optional */
    },
};

module_platform_driver(my_driver);
MODULE_LICENSE("GPL");
```

### 2.2 Device Tree Binding (DTS)

```dts
/* arch/arm64/boot/dts/vendor/board.dts */
/ {
    my_controller: controller@40000000 {
        compatible = "vendor,my-controller-v1";
        reg = <0x0 0x40000000 0x0 0x1000>;  /* base_addr, size */
        interrupts = <GIC_SPI 55 IRQ_TYPE_LEVEL_HIGH>;
        clocks = <&ccu CLK_CORE>, <&ccu CLK_BUS>;
        clock-names = "core", "bus";
        resets = <&rst RST_CTRL>;
        reset-names = "ctrl";
        status = "okay";
    };
};
```

---

## Level 3: PCI Driver

```c
#include <linux/pci.h>

struct my_pci_dev {
    struct pci_dev *pdev;
    void __iomem   *bar0;
    int             irq;
};

static int my_pci_probe(struct pci_dev *pdev,
                         const struct pci_device_id *id)
{
    struct my_pci_dev *mydev;
    int ret;

    mydev = devm_kzalloc(&pdev->dev, sizeof(*mydev), GFP_KERNEL);
    if (!mydev)
        return -ENOMEM;

    mydev->pdev = pdev;

    ret = pcim_enable_device(pdev);   /* devm variant */
    if (ret)
        return ret;

    ret = pcim_iomap_regions(pdev, BIT(0), "my_pci_driver");
    if (ret)
        return ret;

    mydev->bar0 = pcim_iomap_table(pdev)[0];
    pci_set_master(pdev);

    ret = pci_alloc_irq_vectors(pdev, 1, 4, PCI_IRQ_MSI | PCI_IRQ_MSIX);
    if (ret < 0)
        return ret;

    mydev->irq = pci_irq_vector(pdev, 0);
    ret = devm_request_irq(&pdev->dev, mydev->irq, my_irq_handler,
                           0, "my_pci", mydev);
    if (ret)
        return ret;

    pci_set_drvdata(pdev, mydev);
    return 0;
}

static void my_pci_remove(struct pci_dev *pdev)
{
    pci_free_irq_vectors(pdev);
}

static const struct pci_device_id my_pci_ids[] = {
    { PCI_DEVICE(0x1234, 0x5678) },
    { 0, }
};
MODULE_DEVICE_TABLE(pci, my_pci_ids);

static struct pci_driver my_pci_driver = {
    .name       = "my_pci_driver",
    .id_table   = my_pci_ids,
    .probe      = my_pci_probe,
    .remove     = my_pci_remove,
};

module_pci_driver(my_pci_driver);
MODULE_LICENSE("GPL");
```

---

## Level 4: devm_ (Device Managed Resources)

```c
/*
 * devm_ functions automatically release resources when device is removed
 * Eliminates error-path cleanup boilerplate
 */

/* Memory */
void *buf = devm_kzalloc(dev, size, GFP_KERNEL);

/* MMIO mapping */
void __iomem *base = devm_ioremap(dev, phys_addr, size);
void __iomem *base = devm_ioremap_resource(dev, res);
void __iomem *base = devm_platform_ioremap_resource(pdev, 0);

/* IRQ */
devm_request_irq(dev, irq, handler, flags, name, data);

/* GPIO */
struct gpio_desc *gpiod = devm_gpiod_get(dev, "reset", GPIOD_OUT_LOW);

/* Clock */
struct clk *clk = devm_clk_get(dev, "core");

/* Regulator */
struct regulator *reg = devm_regulator_get(dev, "vcc");

/* Custom devm action */
static void my_cleanup(void *data)
{
    struct my_hw *hw = data;
    my_hw_disable(hw);
}
devm_add_action_or_reset(dev, my_cleanup, hw);
```

---

## Level 5: Sysfs Interface

```c
#include <linux/sysfs.h>

/* Show callback (read from user space: cat /sys/...) */
static ssize_t speed_show(struct device *dev,
                           struct device_attribute *attr, char *buf)
{
    struct my_priv *priv = dev_get_drvdata(dev);
    return sysfs_emit(buf, "%u\n", priv->speed);
}

/* Store callback (write from user space: echo 100 > /sys/...) */
static ssize_t speed_store(struct device *dev,
                            struct device_attribute *attr,
                            const char *buf, size_t count)
{
    struct my_priv *priv = dev_get_drvdata(dev);
    unsigned int val;
    int ret;

    ret = kstrtouint(buf, 10, &val);
    if (ret)
        return ret;

    priv->speed = val;
    return count;
}

static DEVICE_ATTR_RW(speed);          /* creates speed_show + speed_store */
static DEVICE_ATTR_RO(status);         /* creates status_show only */
static DEVICE_ATTR_WO(command);        /* creates command_store only */

/* Attribute group */
static struct attribute *my_attrs[] = {
    &dev_attr_speed.attr,
    &dev_attr_status.attr,
    &dev_attr_command.attr,
    NULL,
};

static const struct attribute_group my_attr_group = {
    .attrs = my_attrs,
};

/* In probe */
ret = sysfs_create_group(&pdev->dev.kobj, &my_attr_group);
/* Or devm variant */
ret = devm_device_add_group(&pdev->dev, &my_attr_group);
```

---

## Interview Questions

1. What is the Linux driver model? Explain bus, device, driver relationship.
2. What is `container_of` and give a real usage example?
3. How do you map physical MMIO registers to kernel virtual address?
4. What is the difference between `ioremap()` and `devm_ioremap()`?
5. How does `probe()` get called? Explain the DT matching process.
6. What is `platform_get_drvdata` / `platform_set_drvdata`?
7. How do you create a `/dev/` node for your driver?
8. Explain `copy_to_user` and `copy_from_user` — why are they needed?
9. What is `IRQF_SHARED` and when do you use it?
10. How do you implement a non-blocking `ioctl`?
