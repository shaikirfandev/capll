# System Debugging — From Basic to Expert

## Level 1: Debugging Tools Overview

```
Problem Type               → Tool
─────────────────────────────────────────────────────────────
Kernel crash / oops        → dmesg, crash, addr2line
Memory corruption          → KASAN, KFENCE, kmemcheck
Locking bugs               → LOCKDEP, lockstat
Race conditions            → KTSAN (ThreadSanitizer)
Function tracing           → ftrace, perf
Latency / performance      → perf, cyclictest, latencytop
Live kernel debugging      → KGDB, kdb
User space crash           → GDB, core dumps, valgrind
Memory leaks (user)        → valgrind --leak-check
Memory leaks (kernel)      → kmemleak
Boot issues                → earlycon, initcall_debug
I2C/SPI/UART issues        → logic analyzer, oscilloscope
```

---

## Level 2: dmesg / Kernel Log Analysis

### 2.1 Reading Kernel Messages

```bash
# Live monitoring
dmesg -w                         # follow mode (like tail -f)
dmesg -T                         # human-readable timestamps
dmesg -l err,warn                # show only errors and warnings
journalctl -k -f                 # systemd journal, kernel, follow

# Persistence
journalctl -k --since "1 hour ago"
journalctl -k -b -1              # previous boot

# Filter by subsystem
dmesg | grep -i "usb\|ehci\|xhci"
dmesg | grep "my_driver"
```

### 2.2 Kernel Oops Analysis

```
[12345.678901] BUG: unable to handle kernel NULL pointer dereference at 0000000000000010
[12345.678902] #PF: supervisor write access in kernel mode
[12345.678903] #PF: error_code(0x0002) - not-present page
[12345.678904] PGD 0 P4D 0
[12345.678905] Oops: 0002 [#1] PREEMPT SMP NOPTI
[12345.678906] CPU: 3 PID: 1234 Comm: modprobe Tainted: G   OE  5.15.30 #1
[12345.678907] Hardware name: My Board (DT)
[12345.678908] pc : my_driver_probe+0x5c/0x120 [my_driver]
[12345.678909] lr : my_driver_probe+0x48/0x120 [my_driver]
[12345.678910] Call trace:
[12345.678911]  my_driver_probe+0x5c/0x120 [my_driver]
[12345.678912]  platform_drv_probe+0x28/0x80
[12345.678913]  really_probe+0xf4/0x3a0
```

**Analysis Steps:**
```bash
# Step 1: Find exact source line from function+offset
scripts/faddr2line my_driver.ko my_driver_probe+0x5c
# Output: my_driver.c:87  ← exact line number

# Step 2: addr2line for module
aarch64-linux-gnu-addr2line -e my_driver.ko -i 0x5c

# Step 3: objdump to see assembly
objdump -d my_driver.ko | grep -A5 "my_driver_probe"

# Common oops error codes:
# 0000  = read, kernel, not-present
# 0002  = write, kernel, not-present  ← NULL pointer write
# 0004  = read, user, not-present
# 0010  = read, kernel, protection fault
```

---

## Level 3: KASAN — Kernel Address Sanitizer

```bash
# Enable in menuconfig:
# Kernel hacking → Memory Debugging → KASAN

# KASAN catches:
# - Use after free
# - Buffer overflow / underflow
# - Stack buffer overflow
# - Uninitialized memory read

# KASAN report example:
# ==================================================================
# BUG: KASAN: use-after-free in my_func+0x30/0x50 [my_drv]
# Write of size 4 at addr ffff888012345678 by task kworker/0:1/12
# 
# Allocated by task 1234:
#   kmalloc+0x50/0x80
#   my_alloc+0x24/0x40 [my_drv]
# 
# Freed by task 5678:
#   kfree+0x30/0x50
#   my_free+0x1c/0x30 [my_drv]
# ==================================================================
```

---

## Level 4: LOCKDEP — Lock Dependency Checker

```bash
# Enable: Kernel hacking → Lock Debugging → Detect Soft/Hard Lockups
# CONFIG_PROVE_LOCKING=y
# CONFIG_LOCKDEP=y

# LOCKDEP detects:
# - Deadlocks (AB-BA lock ordering)
# - Lock held from interrupt context with might_sleep
# - Recursive locking

# Example LOCKDEP warning:
# ======================================================
# WARNING: possible circular locking dependency detected
# kworker/0:1/12 is trying to acquire lock:
# ffff888012345678 (&dev->lock){+.+.}, at: my_work+0x30
# 
# but task is already holding lock:
# ffff888087654321 (&bus->lock){+.+.}, at: my_bus_op+0x20
# 
# which lock already depends on the new lock.
# 
# Possible unsafe locking scenario:
#        CPU0                    CPU1
#        ----                    ----
#   lock(&bus->lock);
#                           lock(&dev->lock);
#                           lock(&bus->lock);
#   lock(&dev->lock);
#  *** DEADLOCK ***
# ======================================================
```

---

## Level 5: ftrace — Function Tracing

### 5.1 ftrace Basics

```bash
# ftrace mount point
mount -t debugfs none /sys/kernel/debug

cd /sys/kernel/debug/tracing

# Available tracers
cat available_tracers
# nop blk mmiotrace wakeup_dl wakeup_rt wakeup function_graph function

# 1. Function tracer — trace all kernel functions
echo function > current_tracer
echo 1 > tracing_on
sleep 1
echo 0 > tracing_on
cat trace | head -50

# 2. function_graph — shows call depth + duration
echo function_graph > current_tracer
echo 1 > tracing_on
sleep 0.1
echo 0 > tracing_on
cat trace

# Output:
# CPU DURATION                  FUNCTION CALLS
#  |   |   |                     |   |   |   |
#  0) + 12.345 us  |  my_driver_probe() {
#  0)   1.234 us   |    devm_kzalloc();
#  0)   0.567 us   |    platform_get_resource();
#  0) + 12.345 us  |  }
```

### 5.2 Trace Specific Functions

```bash
# Trace only specific functions
echo "my_driver_*" > set_ftrace_filter
echo function > current_tracer
echo 1 > tracing_on

# Trace a function and its callees (graph filter)
echo my_driver_probe > set_graph_function
echo function_graph > current_tracer
echo 1 > tracing_on

# Trace specific module
echo ":mod:my_driver" > set_ftrace_filter

# Trace events (better than function tracing for drivers)
cat available_events | grep "irq\|sched\|power"
echo irq:irq_handler_entry > set_event
echo irq:irq_handler_exit  >> set_event
echo 1 > events/enable

# Power events (suspend/resume latency)
echo 1 > events/power/enable
echo 1 > tracing_on
echo mem > /sys/power/state   # suspend
echo 0 > tracing_on
cat trace | grep -E "device_pm|rpm"
```

### 5.3 Dynamic Tracing with kprobes

```bash
# Trace a function entry (kprobe)
echo 'p:my_probe my_driver_probe pdev=%di' > kprobe_events
echo 1 > events/kprobes/my_probe/enable

# Trace function return + retval (kretprobe)
echo 'r:my_probe_ret my_driver_probe retval=$retval' >> kprobe_events
echo 1 > events/kprobes/my_probe_ret/enable

echo 1 > tracing_on
# Load your driver
cat trace
```

---

## Level 6: perf — Performance Analysis

```bash
# CPU performance counter stats
sudo perf stat -a sleep 5
# Shows: cycles, instructions, cache-misses, branch-misses, etc.

# Profile a specific process
sudo perf record -g -p <PID> sleep 10
sudo perf report

# System-wide profile (find hotspots)
sudo perf record -ag sleep 5
sudo perf report --stdio | head -50

# Trace kernel function calls (like ftrace)
sudo perf trace -e 'irq:*,sched:*' sleep 1

# Memory access profiling
sudo perf mem record ./my_app
sudo perf mem report

# Specific hardware events
sudo perf stat -e cache-misses,cache-references,instructions,cycles ./my_app

# Flamegraph (visual performance analysis)
sudo perf record -F 99 -ag -- sleep 60
sudo perf script | FlameGraph/stackcollapse-perf.pl | FlameGraph/flamegraph.pl > out.svg
```

---

## Level 7: KGDB — Kernel GDB Debugger

```bash
# Enable in kernel config:
# CONFIG_KGDB=y
# CONFIG_KGDB_SERIAL_CONSOLE=y
# CONFIG_DEBUG_INFO=y
# CONFIG_FRAME_POINTER=y

# Boot with kernel params:
# kgdboc=ttyS0,115200 kgdbwait

# On host machine (attaches to target via serial/network)
gdb vmlinux

(gdb) set remotebaud 115200
(gdb) target remote /dev/ttyUSB0
# or
(gdb) target remote :1234   # QEMU kgdb over tcp

# Debug kernel in GDB
(gdb) bt                    # backtrace
(gdb) info threads          # show all CPUs/threads
(gdb) thread 2              # switch to CPU 2
(gdb) p my_global_var       # print kernel variable
(gdb) x/10i $pc             # examine 10 instructions at PC
(gdb) b my_driver_probe     # set breakpoint
(gdb) watch my_var          # watchpoint on variable
(gdb) c                     # continue
```

---

## Level 8: Crash — Post-mortem Analysis

```bash
# Analyze kernel crash dump
# Requires: kdump + crash tool
# CONFIG_CRASH_DUMP=y, CONFIG_PROC_VMCORE=y

# Configure kdump
sudo systemctl enable kdump
echo "crashkernel=256M" >> /etc/default/grub

# When crash occurs, vmcore saved in /var/crash/

# Analyze crash dump
crash /usr/lib/debug/boot/vmlinux-5.15.0 /var/crash/.../vmcore

crash> bt                    # current backtrace
crash> ps                    # all processes
crash> log                   # kernel message log
crash> mod                   # loaded modules
crash> vm [PID]              # virtual memory map
crash> struct my_device 0xffff888012345678  # dump structure
crash> kmem -s               # slab cache info
crash> rd -64 0xffff888012345678 10  # read 10 words at address
crash> dis my_driver_probe   # disassemble function
```

---

## Level 9: kmemleak — Kernel Memory Leak Detector

```bash
# Enable: CONFIG_DEBUG_KMEMLEAK=y

# Trigger scan
echo scan > /sys/kernel/debug/kmemleak
cat /sys/kernel/debug/kmemleak

# Output shows unreferenced objects:
# unreferenced object 0xffff888012345678 (size 512):
#   comm "my_driver", pid 1234, jiffies 123456
#   backtrace:
#     kmalloc+0x50
#     my_driver_probe+0x30
#     platform_drv_probe+0x28
```

---

## Level 10: System-Level Debugging

```bash
# Interrupt statistics
watch -n1 cat /proc/interrupts
cat /proc/irq/<N>/spurious     # spurious interrupt count

# Memory statistics
cat /proc/meminfo
cat /proc/slabinfo | sort -k3 -rn | head  # largest slab caches
cat /proc/buddyinfo             # page allocator free pages

# CPU frequency and idle
cat /proc/cpuinfo | grep "cpu MHz"
cpupower frequency-info
cpupower monitor               # C-state residency

# I/O statistics
iostat -xz 1
iotop                          # per-process I/O

# Network statistics
ss -s                          # socket summary
netstat -s                     # protocol statistics
ip -s link show eth0           # interface stats

# Device tree inspection
dtc -I fs /sys/firmware/devicetree/base | less
cat /sys/firmware/devicetree/base/compatible

# System call tracing
strace -c ./my_app             # count syscalls
strace -T ./my_app             # show syscall timing
ltrace ./my_app                # library call tracing
```

---

## Debugging Checklist

```
□ Module loads?                       → dmesg | grep my_driver
□ Probe called?                       → add dev_info in probe
□ Resources mapped?                   → /proc/iomem, /proc/interrupts
□ Device tree correct?                → dtc -I fs /sys/firmware/devicetree
□ Clock enabled?                      → cat /sys/kernel/debug/clk/*/clk_rate
□ IRQ registered?                     → cat /proc/interrupts
□ Sysfs created?                      → ls /sys/devices/...
□ DMA mapped correctly?               → check dma_mapping_error()
□ No lockdep warnings?                → dmesg | grep LOCKDEP
□ No KASAN reports?                   → dmesg | grep KASAN
□ No memory leaks?                    → kmemleak scan
□ Suspend/resume works?               → echo mem > /sys/power/state
```

---

## Interview Questions

1. How do you analyze a kernel oops? Walk through the process.
2. What is KASAN? What class of bugs does it detect?
3. What is LOCKDEP and how does it detect deadlocks?
4. Explain ftrace function_graph tracer — how do you use it?
5. What is kmemleak? How do you enable and use it?
6. How do you debug a kernel hang (no oops, just frozen)?
7. What is KGDB? How do you connect to it?
8. What is the `crash` tool and when do you use it?
9. How do you find which function is causing high CPU usage?
10. What kernel config options do you enable for debug builds?
