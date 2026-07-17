# Power Management — System Sleep States, S0ix, S3, Runtime PM

## Level 1: Power Management Basics

### 1.1 Linux PM Framework Overview

```
User Space
    │ echo mem > /sys/power/state
    ▼
kernel/power/main.c
    │
    ├── suspend_ops (platform-specific: ACPI, DT)
    │
    ├── Device PM Core (drivers/base/power/)
    │     → calls each driver's .suspend / .resume
    │
    └── CPU Idle (cpuidle framework)
          → C-states (C0-active, C1-halt, C2-stop, C6-off)
```

### 1.2 System Sleep States (ACPI)

| State | Name | Description | Wake latency |
|-------|------|-------------|-------------|
| S0 | Working | Normal operation | 0 |
| S0ix | Modern Standby | CPU in deep C-states, DRAM self-refresh | <100ms |
| S1 | Power-on Suspend | CPU stopped, RAM powered | <1s |
| S2 | (rare) | Similar to S1 but CPU context lost | |
| S3 | Suspend to RAM (STR) | CPU+devices off, RAM powered | 1–3s |
| S4 | Hibernate (STD) | Everything off, RAM saved to disk | 15–30s |
| S5 | Soft Off | Full shutdown | Full boot |

```bash
# Check supported sleep states
cat /sys/power/state
# typical: freeze mem disk

# Trigger suspend to RAM
echo mem > /sys/power/state

# Check mem_sleep mode (S3 vs s2idle/S0ix)
cat /sys/power/mem_sleep
# output: s2idle [shallow] deep
# s2idle = S0ix (modern standby)
# deep = S3 (suspend to RAM)

echo deep > /sys/power/mem_sleep   # force S3
echo s2idle > /sys/power/mem_sleep # force S0ix
```

---

## Level 2: S3 — Suspend to RAM (Classic)

### 2.1 S3 Suspend Flow

```
echo mem > /sys/power/state
    │
    ▼ pm_suspend(PM_SUSPEND_MEM)
    │
    ├── 1. notify_pm_event(PM_SUSPEND_PREPARE)
    │        — freezes user space
    │
    ├── 2. dpm_suspend_start()
    │        — calls .prepare() for all devices
    │
    ├── 3. dpm_suspend()
    │        — calls .suspend() for all devices (deepest first)
    │        — reverse probe order
    │
    ├── 4. dpm_suspend_late()  
    │        — .suspend_late() — just before power off
    │
    ├── 5. dpm_suspend_noirq()
    │        — .suspend_noirq() — IRQs disabled
    │
    ├── 6. CPU goes to sleep (ACPI S3 or arm_pm_restart)
    │        — DRAM in self-refresh
    │
    ├── 7. WAKE EVENT (power button, RTC alarm, etc.)
    │
    ├── 8. dpm_resume_noirq()    → .resume_noirq()
    ├── 9. dpm_resume_early()    → .resume_early()
    ├── 10. dpm_resume()         → .resume()
    ├── 11. dpm_resume_end()     → .complete()
    └── 12. notify_pm_event(PM_POST_SUSPEND)
```

### 2.2 Implementing Suspend/Resume in a Driver

```c
#include <linux/pm.h>
#include <linux/pm_runtime.h>

/* Method 1: struct dev_pm_ops */
static int my_suspend(struct device *dev)
{
    struct my_priv *priv = dev_get_drvdata(dev);

    dev_dbg(dev, "Suspending\n");

    /* 1. Stop hardware operations */
    my_hw_stop(priv);

    /* 2. Save hardware state (registers) */
    my_save_context(priv);

    /* 3. Disable clocks and power */
    clk_disable_unprepare(priv->clk);

    return 0;
}

static int my_resume(struct device *dev)
{
    struct my_priv *priv = dev_get_drvdata(dev);

    dev_dbg(dev, "Resuming\n");

    /* 1. Re-enable clocks */
    clk_prepare_enable(priv->clk);

    /* 2. Restore hardware state */
    my_restore_context(priv);

    /* 3. Re-start hardware */
    my_hw_start(priv);

    return 0;
}

/* Method 2: hibernation-aware */
static const struct dev_pm_ops my_pm_ops = {
    .suspend        = my_suspend,
    .resume         = my_resume,
    .freeze         = my_freeze,        /* S4 pre-save */
    .thaw           = my_thaw,          /* S4 restore */
    .poweroff       = my_poweroff,
    .restore        = my_restore,
    /* Or use SET_SYSTEM_SLEEP_PM_OPS macro: */
};

/* Convenient macro — maps suspend → freeze, resume → thaw/restore */
static const struct dev_pm_ops my_pm_ops = {
    SET_SYSTEM_SLEEP_PM_OPS(my_suspend, my_resume)
    SET_RUNTIME_PM_OPS(my_runtime_suspend, my_runtime_resume, NULL)
};

/* In driver */
static struct platform_driver my_driver = {
    .driver = {
        .name = "my_device",
        .pm   = &my_pm_ops,
    },
};
```

---

## Level 3: S0ix — Modern Standby (Intel/AMD)

### 3.1 S0ix vs S3

```
S3 (legacy suspend to RAM):
  All clocks off, all devices suspended
  Wake on: power button, RTC alarm only
  
S0ix (modern standby / connected standby):
  System appears "asleep" to user
  CPU in C10 (deepest C-state)
  Low-power islands active: Bluetooth, WiFi, LTE, audio
  Can receive email/chat notifications in background
  
Intel S0ix states:
  S0i1 — CPU in C6/C7, some IP blocks off
  S0i2 — CPU in C9, more IP off
  S0i3 — CPU in C10, DRAM in self-refresh, only PMC active
```

### 3.2 S0ix Requirements for Drivers

```c
/*
 * For S0ix to reach deep state:
 * 1. ALL devices must enter D3 (device power state)
 * 2. No active clocks or IRQ activity
 * 3. LPSS (Low Power Subsystem) devices must assert idle
 */

/* Runtime PM must be enabled and device in D3 */
static int my_runtime_suspend(struct device *dev)
{
    struct my_priv *priv = dev_get_drvdata(dev);

    /* Disable device — allow S0ix */
    my_hw_power_down(priv);
    clk_disable_unprepare(priv->clk);

    return 0;
}

static int my_runtime_resume(struct device *dev)
{
    struct my_priv *priv = dev_get_drvdata(dev);

    clk_prepare_enable(priv->clk);
    my_hw_power_up(priv);

    return 0;
}

/* Probe: enable runtime PM */
static int my_probe(struct platform_device *pdev)
{
    /* ... */
    pm_runtime_set_active(&pdev->dev);
    pm_runtime_enable(&pdev->dev);
    pm_runtime_set_autosuspend_delay(&pdev->dev, 2000); /* 2s idle timeout */
    pm_runtime_use_autosuspend(&pdev->dev);
    /* ... */
}

/* Remove: disable runtime PM */
static int my_remove(struct platform_device *pdev)
{
    pm_runtime_disable(&pdev->dev);
    pm_runtime_set_suspended(&pdev->dev);
    return 0;
}
```

### 3.3 Debugging S0ix

```bash
# Intel SLP_S0 counter (should increase when in S0ix)
cat /sys/kernel/debug/pmc_core/slp_s0_residency_usec

# Power management debug
cat /sys/kernel/debug/pm_genpd/pm_genpd_summary
cat /sys/kernel/debug/device_component/*/status

# Check why system can't enter S0ix
cat /sys/kernel/debug/pmc_core/lpm_reject_stats
# Common blockers: audio, USB, PCIe active

# turbostat shows C-state residency
sudo turbostat --show idle,Busy%,Bzy_MHz,IRQ

# powertop — interactive PM analysis
sudo powertop
```

---

## Level 4: Runtime PM

### 4.1 Runtime PM Lifecycle

```
Device state:       D0 (active)  ←──→  D3cold (runtime suspended)

pm_runtime_get_sync(dev)   → wakes device (D3→D0), increments usage count
pm_runtime_put(dev)        → decrements usage count
pm_runtime_put_autosuspend → decrements, schedules autosuspend

Usage count: 0 → autosuspend timer fires → .runtime_suspend() called → D3
Usage count: 1+ → device stays active (D0)
```

```c
/* In any driver callback that needs the device: */
static int my_read_register(struct my_priv *priv, u32 offset)
{
    int ret;

    ret = pm_runtime_get_sync(priv->dev);
    if (ret < 0) {
        pm_runtime_put_noidle(priv->dev);
        return ret;
    }

    u32 val = readl(priv->base + offset);

    pm_runtime_mark_last_busy(priv->dev);
    pm_runtime_put_autosuspend(priv->dev);

    return val;
}

/* Runtime suspend — called when usage_count hits 0 */
static int my_runtime_suspend(struct device *dev)
{
    struct my_priv *priv = dev_get_drvdata(dev);
    clk_disable_unprepare(priv->clk);
    return 0;
}

/* Runtime resume — called when usage_count goes to 1 */
static int my_runtime_resume(struct device *dev)
{
    struct my_priv *priv = dev_get_drvdata(dev);
    return clk_prepare_enable(priv->clk);
}
```

---

## Level 5: Power Domains (genpd)

```c
#include <linux/pm_domain.h>

/*
 * Power domains group devices that share a power rail.
 * Entire domain powers down when all devices are idle.
 */

static int my_power_on(struct generic_pm_domain *genpd)
{
    struct my_domain *domain = container_of(genpd, struct my_domain, genpd);
    regulator_enable(domain->regulator);
    clk_prepare_enable(domain->clk);
    reset_control_deassert(domain->rst);
    return 0;
}

static int my_power_off(struct generic_pm_domain *genpd)
{
    struct my_domain *domain = container_of(genpd, struct my_domain, genpd);
    reset_control_assert(domain->rst);
    clk_disable_unprepare(domain->clk);
    regulator_disable(domain->regulator);
    return 0;
}

/* DT: power-domains = <&pd MY_PD_GPU>; */
```

---

## Power Management Debugging Tools

```bash
# System-level PM tools
pm-suspend                         # suspend to RAM
pm-hibernate                       # hibernate

# Check PM callbacks being called
echo 1 > /sys/power/pm_debug_messages
dmesg | grep "PM:"

# Device PM stats
cat /sys/devices/.../power/runtime_status      # active/suspended/suspended
cat /sys/devices/.../power/runtime_active_time
cat /sys/devices/.../power/runtime_suspended_time
cat /sys/devices/.../power/wakeup               # wakeup source info

# Energy consumption
powertop --auto-tune                # auto-enable power saving
powertop --html=report.html         # HTML power report

# ftrace PM events
echo 1 > /sys/kernel/debug/tracing/events/power/enable
cat /sys/kernel/debug/tracing/trace | grep "cpu_idle\|device_pm"

# ACPI PM
acpidbg                             # ACPI debugger
cat /proc/acpi/wakeup               # ACPI wakeup sources
```

---

## Interview Questions

1. What is the difference between S3 and S0ix?
2. Explain Runtime PM. When does `runtime_suspend` get called?
3. What is a power domain (`genpd`) and how does it work?
4. What blocks S0ix entry? How do you debug it?
5. Why must a driver be Runtime PM aware for modern standby to work?
6. Explain the suspend/resume call order for devices.
7. What is `IRQF_NO_SUSPEND` and when is it used?
8. What is a wakeup source? How do you register one?
9. What is `pm_runtime_set_autosuspend_delay`?
10. How do you handle suspend in a driver that controls DMA?
