# 05 — Embedded Linux

## Overview

This module documents the **Embedded Linux configuration** for real-time automotive ADAS: PREEMPT_RT kernel, system tuning, memory management, CPU isolation, cross-compilation, and deployment.

---

## 1. Linux Kernel Variants for RT

| Kernel Config | Max Latency | Used For |
|--------------|-------------|---------|
| `CONFIG_PREEMPT=n` (Desktop) | ~10 ms | Desktop, servers |
| `CONFIG_PREEMPT=y` (Voluntary) | ~1 ms | General embedded |
| `CONFIG_PREEMPT_VOLUNTARY=y` | ~1 ms | Light RT workloads |
| `CONFIG_PREEMPT_RT=y` (PREEMPT_RT) | ~50 µs | Automotive RT control |
| Xenomai / RTAI (dual-kernel) | ~5 µs | Hard industrial RT (rarely used now) |

For ADAS control loops at 50–100 Hz (10–20 ms period), **PREEMPT_RT** is sufficient and is now being mainlined into Linux 6.x.

### 1.1 Verifying PREEMPT_RT

```bash
uname -v
# Expected: #1 SMP PREEMPT_RT Thu Mar 14 14:00:00 UTC 2024

cat /boot/config-$(uname -r) | grep PREEMPT_RT
# CONFIG_PREEMPT_RT=y
```

### 1.2 Obtaining PREEMPT_RT

```bash
# Ubuntu / Debian (pre-built)
sudo apt install linux-image-rt-amd64     # x86_64
sudo apt install linux-image-rt-arm64     # ARM64

# Or patch manually:
# Download kernel + rt-patch from kernel.org/pub/linux/kernel/projects/rt/
patch -p1 < patch-6.6.x-rt-y.patch
make menuconfig  # Enable CONFIG_PREEMPT_RT
make -j$(nproc)
```

---

## 2. System Tuning — Full Checklist

### 2.1 GRUB Boot Parameters

Edit `/etc/default/grub`:

```bash
GRUB_CMDLINE_LINUX_DEFAULT="isolcpus=2,3 nohz_full=2,3 rcu_nocbs=2,3 \
  nosoftlockup intel_idle.max_cstate=0 processor.max_cstate=0 \
  idle=poll mce=ignore_ce"
```

```bash
sudo update-grub && sudo reboot
```

| Parameter | Effect |
|-----------|--------|
| `isolcpus=2,3` | Remove CPUs 2,3 from Linux scheduler — OS never schedules on them |
| `nohz_full=2,3` | Disable scheduler ticks on CPUs 2,3 (reduces interrupt wakeups) |
| `rcu_nocbs=2,3` | Move RCU callbacks off isolated CPUs |
| `intel_idle.max_cstate=0` | Disable CPU deep sleep states (C-state exit latency) |
| `idle=poll` | CPU spins instead of sleeping — zero wakeup latency |

### 2.2 CPU Frequency Scaling

```bash
# Set all CPUs to performance governor
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance > "$cpu"
done

# Verify
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# performance
```

### 2.3 IRQ Affinity

```bash
# Move all IRQs to CPU 0-1 (housekeeping CPUs)
for irq in /proc/irq/*/smp_affinity; do
    echo "3" > "$irq" 2>/dev/null  # bitmask: CPU0 + CPU1
done

# Check specific IRQ
cat /proc/irq/24/smp_affinity
# 00000003  (CPUs 0 and 1)
```

### 2.4 RT Throttling

By default, Linux reserves 5% of CPU time for non-RT tasks (prevents RT tasks from starving the kernel). Disable for ADAS:

```bash
echo -1 > /proc/sys/kernel/sched_rt_runtime_us
# -1 = unlimited (RT tasks can use 100% of CPU)

# Make permanent:
echo "kernel.sched_rt_runtime_us = -1" >> /etc/sysctl.conf
```

### 2.5 Memory — Huge Pages & Swap

```bash
# Disable swap
sudo swapoff -a
echo "vm.swappiness = 0" >> /etc/sysctl.conf

# Transparent huge pages — disable for determinism
echo never > /sys/kernel/mm/transparent_hugepage/enabled

# Lock limits — allow RT process to mlockall
echo "@adas_rt - memlock unlimited" >> /etc/security/limits.conf
```

### 2.6 Complete Setup Script

All the above is automated in `scripts/setup_rt_linux.sh`. Run once after provisioning:

```bash
sudo bash scripts/setup_rt_linux.sh
```

---

## 3. Process-Level RT Setup

### 3.1 Memory Locking (mlockall)

**File**: `src/realtime/rt_scheduler.cpp`

```cpp
void RtScheduler::lockMemory() {
    if (mlockall(MCL_CURRENT | MCL_FUTURE) != 0) {
        perror("mlockall");
        throw std::runtime_error("Cannot lock memory — check ulimits");
    }
    ADAS_LOG_INFO("Memory locked (mlockall)");
}
```

| Flag | Effect |
|------|--------|
| `MCL_CURRENT` | Lock all pages currently mapped |
| `MCL_FUTURE` | Lock all pages mapped in future (new allocations) |

After `mlockall`, any attempt to access unmapped memory immediately throws SIGSEGV — no page faults during RT execution.

### 3.2 Stack Pre-Faulting

```cpp
void prefaultStack() {
    // Touch 256KB of stack to force kernel to map all pages
    volatile char stack_mem[256 * 1024];
    memset(const_cast<char*>(stack_mem), 0, sizeof(stack_mem));
}
```

Call this before entering the RT loop:
```cpp
RtTask task;
task.callback = []() {
    prefaultStack();  // ← call once, before RT loop
    while (!stop) {
        // RT work
    }
};
```

### 3.3 SCHED_FIFO with CPU Affinity

```cpp
void setRealtimePriority(pthread_t tid, int priority, int cpu) {
    // Set SCHED_FIFO
    struct sched_param param{};
    param.sched_priority = priority;
    pthread_setschedparam(tid, SCHED_FIFO, &param);

    // Pin to specific CPU
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu, &cpuset);
    pthread_setaffinity_np(tid, sizeof(cpuset), &cpuset);
}
```

---

## 4. Memory Layout in Embedded Linux

```
Virtual address space (64-bit process)
─────────────────────────────────────────────────────────────────
0xFFFFFFFFFFFFFFFF  ┌────────────────────────────────────────────┐
                    │  Kernel virtual address space              │
0xFFFF800000000000  ├────────────────────────────────────────────┤
                    │  User stack (grows down)                   │
                    │  ← Stack pre-faulted 256KB → always in RAM │
                    ├────────────────────────────────────────────┤
                    │  Shared libraries (.so) mmapped region     │
                    ├────────────────────────────────────────────┤
                    │  Heap                                      │
                    │  ← NO malloc() in RT hot path              │
                    │  ← Pre-allocated before RT tasks start     │
                    ├────────────────────────────────────────────┤
                    │  BSS segment (zero-init globals)           │
                    │  g_detector, g_fusion, g_planner objects   │
                    ├────────────────────────────────────────────┤
                    │  Data segment (initialised globals)        │
                    ├────────────────────────────────────────────┤
0x0000000000400000  │  Text segment (code)                      │
                    └────────────────────────────────────────────┘
```

After `mlockall(MCL_CURRENT | MCL_FUTURE)`, the entire process virtual address space is locked in physical RAM by the kernel. No page will ever be swapped out.

---

## 5. Embedded Hardware Targets

### 5.1 Common Automotive SOCs

| SOC | CPU | Architecture | OS | ADAS Use |
|-----|-----|-------------|-----|---------|
| NXP S32G274A | 4× Cortex-A53 @ 1GHz | AArch64 | Linux + PREEMPT_RT | Gateway ECU |
| Renesas R-Car H3 | 4× Cortex-A57 @ 1.5GHz | AArch64 | Linux | ADAS compute |
| Qualcomm SA8155P (Snapdragon Ride) | 8× Kryo @ 2.84GHz | AArch64 | Linux / QNX | High-perf ADAS |
| NXP LS1028A | 2× Cortex-A72 | AArch64 | Linux | Ethernet switch |
| Infineon TC397 | 6× TriCore | TriCore | AUTOSAR / FreeRTOS | Safety controller |

### 5.2 Cross-Compilation with Bazel

```bash
# Build for AArch64 target
bazel build //src:adas_rt --config=embedded

# Strip debug info for deployment
bazel build //src:adas_rt --config=embedded --config=release --strip=always

# Copy to target over SSH
scp bazel-bin/src/adas_rt root@192.168.1.100:/opt/adas/
```

**Toolchain definition** (stub, in `toolchains/BUILD`):

```python
cc_toolchain(
    name = "aarch64_linux_toolchain",
    toolchain_identifier = "aarch64-linux-gnu",
    toolchain_config = ":aarch64_toolchain_config",
    all_files = ":aarch64_all_files",
    ...
)
```

---

## 6. Deployment Checklist

```
Before deploying to embedded target:
─────────────────────────────────────────────────────────────────
[ ] RT kernel confirmed: uname -v | grep PREEMPT_RT
[ ] isolcpus set: cat /sys/devices/system/cpu/isolated
[ ] CPU governor = performance: cat /sys/...cpu0.../scaling_governor
[ ] IRQ moved to housekeeping CPUs: cat /proc/irq/*/smp_affinity
[ ] sched_rt_runtime_us = -1: sysctl kernel.sched_rt_runtime_us
[ ] Swap disabled: swapon --show (should be empty)
[ ] memlock = unlimited: ulimit -l
[ ] vcan0 up (SIL): ip link show vcan0
[ ] can0 up (HIL): ip link show can0 (bitrate 500000)
[ ] rt_config.json matches hardware: priorities, CPUs, periods
```

---

## 7. Real-Time Latency Testing

```bash
# Install rt-tests package
sudo apt install rt-tests

# Run cyclictest — measures scheduler wakeup latency
sudo cyclictest \
  --mlockall \
  --smp \
  --priority=80 \
  --interval=10000 \    # 10ms interval
  --histogram=500 \     # bucket size 500ns
  --duration=60s

# Expected output on PREEMPT_RT:
# T: 0 ( 1234) P:80 I:10000 C:6000 Min:   5 Act:   8 Avg:   9 Max:  47
#                                            ^Min µs          ^Max µs
```

**Acceptable Max Latency**: < 100 µs for a well-tuned PREEMPT_RT system.

---

*See also*: [09_Multithreading_Realtime.md](07_Multithreading_Realtime.md) for SCHED_FIFO priority assignment and jitter budget.  
*See also*: [04_Bazel_Build_System.md](04_Bazel_Build_System.md) for `--config=embedded` cross-compilation.
