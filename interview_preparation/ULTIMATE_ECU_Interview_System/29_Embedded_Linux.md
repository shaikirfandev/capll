# Embedded Linux Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Embedded Linux is used in **infotainment, ADAS domain controllers, telematics units (TCUs), and Adaptive AUTOSAR platforms**. At Harman, Continental, Qualcomm Automotive, and NXP, Linux expertise is a key differentiator. This includes the kernel, device drivers, real-time extensions, and SocketCAN.

**Key areas probed:**
- Linux kernel architecture and process model
- Device drivers (character, block, network)
- SocketCAN — CAN networking in Linux
- IPC mechanisms (pipes, shared memory, sockets, D-Bus)
- Real-time Linux (PREEMPT_RT patch, SCHED_FIFO)
- Memory management (virtual memory, DMA, mmap)
- Yocto Project / BuildRoot for automotive Linux images
- Systemd for service management
- Linux namespaces and containers (Docker in automotive)
- Debugging: strace, perf, GDB, ftrace

---

## BEGINNER QUESTIONS

---

### Q1. Explain the Linux process model and how it differs in embedded automotive use.

**Short Answer:** Linux processes have isolated virtual address spaces, file descriptor tables, and PIDs. Threads within a process share the address space. In embedded automotive (TCU/ADAS), processes often manage specific ECU functions and communicate via D-Bus, Unix sockets, or shared memory.

**Detailed Expert Answer:**

```
Linux Process Memory Layout:

High address (0xFFFFFFFF on 32-bit, 0x7FFFFFFFFFFF on 64-bit):
┌──────────────────────────────────────┐
│          Kernel Space                │  (inaccessible from user space)
├──────────────────────────────────────┤ 0xC0000000 (32-bit) / 0x800000000000
│          Stack (grows down)          │  ← Thread stacks, local variables
│              ↓                       │
│          (unmapped gap)              │
│              ↑                       │
│          Memory Maps (mmap)          │  ← Shared libs, DMA buffers, file maps
│          Heap (grows up)             │  ← malloc/new
├──────────────────────────────────────┤
│          BSS (uninitialised data)    │  ← Global/static vars initialised to 0
│          Data (initialised data)     │  ← Global/static vars with initial value
│          Text (code)                 │  ← Executable code (read-only)
└──────────────────────────────────────┘ 0x00000000
```

**Automotive process architecture (TCU example):**
```
Process layout on a Harman TCU (Linux 5.15, NXP i.MX8):

  PID 1:   systemd (init)
  PID 100: tcu-manager      (main TCU service: CAN read, telemetry publish)
  PID 101: mqtt-client       (dedicated MQTT broker connection)
  PID 102: ota-service       (OTA download and verification daemon)
  PID 103: gps-daemon        (NMEA parser, GNSS interface)
  PID 104: can-gateway        (CAN-to-Ethernet gateway)
  PID 200: vehicle-analytics  (periodic data aggregation)

Inter-process communication:
  tcu-manager → mqtt-client:   Unix domain socket (high throughput)
  tcu-manager → ota-service:   D-Bus (method calls for control)
  gps-daemon → tcu-manager:    POSIX shared memory (GPS position struct)
  can-gateway → tcu-manager:   Netlink socket (kernel CAN events)
```

**Why processes (not threads) for automotive services:**
```
1. Fault isolation: if ota-service crashes, tcu-manager continues
2. Security: each process has separate capabilities (seccomp, SELinux)
3. Watchdog: systemd monitors each process, restarts on crash
4. Update: individual processes can be updated independently (containers)
5. ASIL partitioning: QM and ASIL services separated by process boundary + MPU
```

---

### Q2. Explain SocketCAN — how to set up a CAN interface and send/receive frames in Linux.

**Short Answer:** SocketCAN integrates CAN into the Linux network subsystem, allowing CAN communication using the standard POSIX socket API. CAN interfaces appear as network devices (can0, vcan0).

**Detailed Expert Answer:**

**Interface setup:**
```bash
# Physical CAN interface (e.g., PEAK PCAN-USB)
sudo modprobe can
sudo modprobe can_raw
sudo modprobe peak_usb         # Or: mcp251x for SPI-based controllers

sudo ip link set can0 type can bitrate 500000 sample-point 0.875
sudo ip link set can0 up
# Verify:
ip -details link show can0

# Virtual CAN (for testing without hardware)
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set vcan0 up

# CAN-FD setup
sudo ip link set can0 type can bitrate 500000 dbitrate 2000000 fd on
sudo ip link set can0 up
```

**Complete send/receive program:**
```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <linux/can.h>
#include <linux/can/raw.h>

/* Open CAN socket */
int can_socket_open(const char *ifname) {
    int s = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (s < 0) { perror("socket"); return -1; }
    
    struct ifreq ifr;
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);
    if (ioctl(s, SIOCGIFINDEX, &ifr) < 0) {
        perror("ioctl SIOCGIFINDEX");
        close(s);
        return -1;
    }
    
    struct sockaddr_can addr = {
        .can_family  = AF_CAN,
        .can_ifindex = ifr.ifr_ifindex,
    };
    if (bind(s, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(s);
        return -1;
    }
    return s;
}

/* Send frame */
int can_send_frame(int s, uint32_t id, const uint8_t *data, uint8_t dlc) {
    struct can_frame frame;
    memset(&frame, 0, sizeof(frame));
    frame.can_id  = id;
    frame.can_dlc = dlc;
    if (data && dlc > 0) memcpy(frame.data, data, dlc);
    
    ssize_t nbytes = write(s, &frame, sizeof(struct can_frame));
    return (nbytes == sizeof(struct can_frame)) ? 0 : -1;
}

/* Receive with timeout */
int can_recv_frame(int s, struct can_frame *frame, int timeout_ms) {
    fd_set readfds;
    FD_ZERO(&readfds);
    FD_SET(s, &readfds);
    
    struct timeval tv = {
        .tv_sec  = timeout_ms / 1000,
        .tv_usec = (timeout_ms % 1000) * 1000,
    };
    
    int ret = select(s + 1, &readfds, NULL, NULL, &tv);
    if (ret < 0)  { perror("select"); return -1; }
    if (ret == 0) { return 0; }  /* Timeout */
    
    ssize_t nbytes = read(s, frame, sizeof(struct can_frame));
    return (nbytes == sizeof(struct can_frame)) ? 1 : -1;
}

/* Set hardware receive filter */
void can_set_filter(int s, uint32_t id, uint32_t mask) {
    struct can_filter filter = { .can_id = id, .can_mask = mask };
    setsockopt(s, SOL_CAN_RAW, CAN_RAW_FILTER, &filter, sizeof(filter));
}

/* Main */
int main(void) {
    int s = can_socket_open("vcan0");
    if (s < 0) return 1;
    
    /* Only receive messages with ID 0x120-0x12F */
    can_set_filter(s, 0x120, 0xFF0);
    
    /* Send vehicle speed message */
    uint8_t speed_data[8] = {0x00, 0x17, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    /* speed = 0x1700 × 0.01 = 58.88 km/h */
    can_send_frame(s, 0x120, speed_data, 8);
    
    /* Receive loop */
    struct can_frame rx;
    while (1) {
        int ret = can_recv_frame(s, &rx, 1000);  /* 1 second timeout */
        if (ret > 0) {
            printf("ID: 0x%03X DLC: %d Data:", rx.can_id, rx.can_dlc);
            for (int i = 0; i < rx.can_dlc; i++) printf(" %02X", rx.data[i]);
            printf("\n");
        } else if (ret == 0) {
            printf("Timeout — no frames received\n");
        }
    }
    close(s);
    return 0;
}
```

---

### Q3. What is PREEMPT_RT and why is it used in automotive Linux?

**Short Answer:** PREEMPT_RT is a Linux kernel patch that converts most non-preemptible kernel sections into preemptible code, reducing worst-case interrupt latency from milliseconds to tens of microseconds — enabling soft real-time performance.

**Detailed Expert Answer:**

```
Standard Linux vs PREEMPT_RT:

Standard Linux:
  Interrupt handlers: non-preemptible spinlocks, latency 1-50ms worst case
  Use case: infotainment, general computing
  
PREEMPT_RT Linux:
  Most spinlocks converted to RT-mutexes (preemptible)
  Interrupt handlers run as kernel threads (preemptible)
  Worst-case latency: 50-200μs (verified by cyclictest)
  Use case: ADAS sensor fusion, real-time CAN processing, TCU timing

Full RTOS (FreeRTOS/OSEK):
  Deterministic, verified WCET
  Use case: safety-critical ASIL-D (brake ECU, airbag, steering)
```

**Configuring PREEMPT_RT:**
```bash
# Check current kernel preemption model
cat /sys/kernel/debug/sched_features
# Or check kernel config:
grep CONFIG_PREEMPT /boot/config-$(uname -r)

# Build with PREEMPT_RT:
# CONFIG_PREEMPT_RT=y (full preemption)
# Or: CONFIG_PREEMPT=y (voluntary preemption — not full RT)
```

**Using SCHED_FIFO for real-time CAN processing:**
```c
#include <sched.h>
#include <pthread.h>

/* Set real-time scheduling for CAN Rx thread */
void set_rt_priority(int priority) {
    struct sched_param params = { .sched_priority = priority };
    
    if (sched_setscheduler(0, SCHED_FIFO, &params) != 0) {
        perror("sched_setscheduler");
        /* May need CAP_SYS_NICE or /etc/security/limits.conf */
    }
    
    /* Lock memory (prevent page faults in RT thread) */
    mlockall(MCL_CURRENT | MCL_FUTURE);
}

/* Real-time CAN receive thread */
void *can_rt_thread(void *arg) {
    /* Priority 80 = high RT priority (below kernel RT threads at 99) */
    set_rt_priority(80);
    
    /* Pre-fault stack memory to avoid page faults during operation */
    char stack_dummy[65536];
    memset(stack_dummy, 0, sizeof(stack_dummy));
    
    int s = can_socket_open("can0");
    struct can_frame frame;
    
    while (running) {
        ssize_t n = read(s, &frame, sizeof(frame));
        if (n == sizeof(frame)) {
            process_can_frame_rt(&frame);  /* Must be fast, no blocking! */
        }
    }
    return NULL;
}
```

**Measuring RT performance:**
```bash
# cyclictest — measures scheduling latency
sudo cyclictest --mlockall --smp --priority=80 --interval=1000 --distance=0

# Results example (PREEMPT_RT Yocto on NXP i.MX8):
# T: 0 (  1234) P:80 I:1000 C:1000000 Min:    8 Act:   12 Avg:   11 Max:     67
# Min/Avg/Max latency in microseconds — Max=67μs means worst case is 67μs
```

---

## INTERMEDIATE QUESTIONS

---

### Q4. Explain character device drivers in Linux. How would you write a simple ECU sensor driver?

**Short Answer:** Character device drivers expose a device as a file with `read()`/`write()`/`ioctl()` operations. The driver registers with the kernel, handles interrupt-driven data from hardware, and provides a user-space interface.

**Detailed Expert Answer:**
```c
/* Minimal SPI sensor driver — automotive temperature sensor on SPI3 */

#include <linux/module.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/spi/spi.h>
#include <linux/uaccess.h>
#include <linux/interrupt.h>

#define DRIVER_NAME  "automotive_temp"
#define CLASS_NAME   "autotemp"

static struct class  *s_class;
static struct cdev    s_cdev;
static dev_t          s_devnum;
static struct spi_device *s_spi;
static int16_t        s_last_temp;
static wait_queue_head_t s_read_queue;
static int            s_data_ready;

/* Called when user calls read() on /dev/autotemp */
static ssize_t autotemp_read(struct file *f, char __user *buf,
                              size_t count, loff_t *pos) {
    int16_t temp;
    
    /* Block until data is ready (interrupt sets flag) */
    if (wait_event_interruptible(s_read_queue, s_data_ready)) {
        return -ERESTARTSYS;
    }
    s_data_ready = 0;
    temp = s_last_temp;
    
    /* Copy to user space (safe — handles faults) */
    if (copy_to_user(buf, &temp, sizeof(temp))) return -EFAULT;
    return sizeof(temp);
}

/* ioctl for sensor configuration */
static long autotemp_ioctl(struct file *f, unsigned int cmd, unsigned long arg) {
    switch (cmd) {
    case AUTOTEMP_IOCTL_SET_RATE: {
        uint32_t rate_hz;
        if (copy_from_user(&rate_hz, (void __user*)arg, sizeof(rate_hz)))
            return -EFAULT;
        /* Configure SPI to trigger at rate_hz */
        return spi_write_then_read(s_spi, &rate_hz, 1, NULL, 0);
    }
    default:
        return -ENOTTY;  /* Unknown ioctl */
    }
}

/* SPI interrupt handler — called when sensor data is ready */
static irqreturn_t autotemp_irq(int irq, void *dev) {
    uint8_t rx[2];
    spi_write_then_read(s_spi, NULL, 0, rx, 2);  /* Read temperature */
    s_last_temp = (int16_t)((rx[0] << 8) | rx[1]);
    s_data_ready = 1;
    wake_up_interruptible(&s_read_queue);
    return IRQ_HANDLED;
}

static const struct file_operations autotemp_fops = {
    .owner          = THIS_MODULE,
    .read           = autotemp_read,
    .unlocked_ioctl = autotemp_ioctl,
};

static int autotemp_spi_probe(struct spi_device *spi) {
    s_spi = spi;
    alloc_chrdev_region(&s_devnum, 0, 1, DRIVER_NAME);
    s_class = class_create(THIS_MODULE, CLASS_NAME);
    cdev_init(&s_cdev, &autotemp_fops);
    cdev_add(&s_cdev, s_devnum, 1);
    device_create(s_class, NULL, s_devnum, NULL, DRIVER_NAME);
    init_waitqueue_head(&s_read_queue);
    request_irq(spi->irq, autotemp_irq, IRQF_TRIGGER_FALLING, DRIVER_NAME, spi);
    return 0;
}
```

---

### Q5. Explain Yocto Project for automotive — how is it used to build a TCU Linux image?

**Short Answer:** Yocto Project is a build framework for creating custom embedded Linux distributions. In automotive, it's used to build OEM-specific Linux images for TCUs, infotainment, and ADAS platforms — with specific drivers, security policies, and package sets.

**Detailed Expert Answer:**

```
Yocto layer structure for automotive TCU:

poky/                          ← Yocto base (OE-core, bitbake)
├── meta/                      ← OpenEmbedded core
├── meta-poky/                 ← Yocto reference distro
├── meta-openembedded/         ← Additional packages
│   ├── meta-oe/
│   ├── meta-networking/
│   └── meta-python/
├── meta-automotive/           ← GENIVI/COVESA automotive layer
│   └── meta-ivi/
├── meta-yocto-bsp/
├── meta-freescale/            ← NXP BSP (for i.MX8/S32G)
│   └── meta-freescale-3rdparty/
└── meta-tcu/                  ← Custom TCU layer (your OEM layer)
    ├── conf/
    │   ├── layer.conf
    │   └── machine/
    │       └── tcu-imx8m.conf  ← Custom hardware configuration
    ├── recipes-connectivity/
    │   ├── mosquitto/          ← MQTT broker
    │   └── mbim/               ← Cellular modem interface
    ├── recipes-tcu/
    │   ├── tcu-manager/        ← Your TCU manager daemon
    │   └── ota-service/        ← OTA update service
    └── recipes-security/
        └── tpm2-tools/         ← TPM for secure storage
```

**Key configuration files:**
```bash
# local.conf — machine and distro selection
MACHINE = "tcu-imx8m"
DISTRO = "poky-tcu"
PACKAGE_CLASSES = "package_ipk"  # or package_deb for apt-based

# bblayers.conf — enabled layers
BBLAYERS = " \
    /opt/yocto/poky/meta \
    /opt/yocto/poky/meta-poky \
    /opt/yocto/meta-openembedded/meta-oe \
    /opt/yocto/meta-freescale \
    /opt/yocto/meta-tcu \
"
```

**Recipe example (tcu-manager.bb):**
```bitbake
# meta-tcu/recipes-tcu/tcu-manager/tcu-manager_2.1.0.bb

DESCRIPTION = "TCU Manager daemon for telematics control unit"
LICENSE = "CLOSED"  # or "GPL-2.0"
LIC_FILES_CHKSUM = "..."

SRC_URI = "git://git.company.com/tcu-manager.git;branch=release/v2"
SRCREV = "a1b2c3d4..."

DEPENDS = "mosquitto libcurl openssl nlohmann-json"

inherit cmake systemd

SYSTEMD_SERVICE_${PN} = "tcu-manager.service"
SYSTEMD_AUTO_ENABLE = "enable"

do_configure() {
    cmake -DCMAKE_BUILD_TYPE=Release \
          -DTARGET_PLATFORM=imx8m \
          ..
}
```

**Automotive-specific Yocto considerations:**
```
1. SOTA (Software Over The Air): meta-updater (Uptane-compliant OTA)
2. Security: meta-security (dm-verity, TPM, AppArmor)
3. CAN: linux-can-utils, can-utils included in image
4. Real-time: PREEMPT_RT kernel config fragment
5. Automotive distro: AGL (Automotive Grade Linux) — Toyota/Honda use
6. IVI: GENIVI layers for infotainment
```

---

## ADVANCED QUESTIONS

---

### Q6. How do you debug a memory leak in a running Linux automotive process?

**Expert Answer:**
```bash
# 1. Identify leaking process (monitor RSS growth)
watch -n 5 'ps aux --sort=-rss | head -10'
# If tcu-manager RSS grows 1MB every hour → leak

# 2. Valgrind memcheck (not for production — 5-10x slowdown)
valgrind --leak-check=full --track-origins=yes ./tcu-manager

# 3. AddressSanitizer (preferred for testing — 2x overhead)
# Recompile with:
CXXFLAGS="-fsanitize=address,leak -g" cmake ...
# Run — LSAN (LeakSanitizer) reports leaks at exit or via signal

# 4. Production: Google gperftools heapprofile
# Link with -ltcmalloc
HEAPPROFILE=/tmp/tcu_heap ./tcu-manager
# After run:
pprof --pdf /usr/bin/tcu-manager /tmp/tcu_heap.0001.heap > heap.pdf

# 5. smaps analysis for mmap leaks
cat /proc/$(pidof tcu-manager)/smaps | grep -A5 "Anonymous"
# Watch 'Anonymous' pages growing → heap or mmap leak

# 6. strace to catch unmatched open/malloc patterns
strace -e trace=mmap,munmap,brk -p $(pidof tcu-manager) 2>&1 | head -100
```

**Common automotive memory leak patterns:**
```c
/* Pattern 1: Handler registered, never de-registered */
void on_can_msg(CANMsg *msg) {
    auto *handler = new MessageHandler(msg);  // Allocated
    /* handler is never deleted — leak per CAN message! */
    /* In production: 100 msgs/sec × 8 hours = 2.88M handlers leaked */
}

/* Fix: use RAII or stack allocation */
void on_can_msg_safe(const CANMsg *msg) {
    MessageHandler handler(msg);  // Stack allocated — auto-destroyed
    handler.process();
}

/* Pattern 2: std::shared_ptr cycle (both objects keep each other alive) */
struct Node {
    std::shared_ptr<Node> next;
    std::shared_ptr<Node> prev;  // Creates cycle!
};
/* Fix: use weak_ptr for back-reference */
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q7. Your automotive Linux TCU shows increasing boot time after 3 software updates (15s → 45s). How do you diagnose?

**Expert Answer:**

"This is a classic field issue with embedded Linux in automotive. The boot time regression usually has 2-3 compounding causes.

**Step 1 — Measure boot stages precisely:**
```bash
# Enable systemd boot timing
systemd-analyze
# Output: Startup finished in 1.234s (kernel) + 4.567s (initrd) + 39.1s (userspace) = 44.9s

systemd-analyze blame | head -20
# Shows which services are taking longest:
#   38.234s mqtt-client.service        ← THIS IS THE PROBLEM
#   1.234s  tcu-manager.service
#   0.567s  can-gateway.service
```

**Step 2 — Investigate mqtt-client 38-second startup:**
```bash
journalctl -u mqtt-client.service --since boot | head -50
# Shows: "Waiting for network... (attempt 1 of 10)"
# Root cause: after OTA update, the TLS certificate was rotated
# Old cert = /etc/certs/client.pem (worked instantly)
# New cert = /data/tcu/certs/client.pem (correct path)
# But symlink not updated → service tries old path, fails, retries with 3s backoff
# 3s × 10 attempts = 30s timeout before fallback
```

**Step 3 — Other common boot regression causes after OTA:**
```bash
# Check if new services were added
systemctl list-units --state=activating --no-legend | wc -l

# Check if filesystem grew (slow fsck)
dmesg | grep -i fsck
# After OTA: new ext4 partition mount → fsck runs → adds 20s for large partitions

# Check NvM migration (automotive-specific)
# If NvM layout changed in new SW, migration runs at first boot → adds time
journalctl -b -1 | grep -i "nvm\|nvram\|migrate"
```

**Fix for the cert symlink issue:**
```bash
# Add post-update hook in OTA service:
# ota-update.conf:
[Service]
ExecStartPost=/bin/sh -c 'ln -sf /data/tcu/certs/client.pem /etc/certs/client.pem'
ExecStartPost=/bin/systemctl restart mqtt-client.service
```

**Production Insight (Harman TCU, BMW iX project):** This exact pattern occurred after a security update that rotated certificates. The mqtt-client had a 5-second retry timeout with 6 retries → 30 seconds added to boot. The OTA post-install script was missing the symlink update step. Boot regression was caught in integration testing but not in unit testing because the unit test used a localhost mock broker."

---

## CHEAT SHEET — Embedded Linux

```
Key commands:
  ip link set can0 up bitrate 500000     ← Bring up CAN interface
  cansend can0 123#DEADBEEF              ← Send CAN frame
  candump can0                           ← Monitor all CAN traffic
  ip -details link show can0             ← Show CAN stats/errors

SocketCAN flow:
  socket(PF_CAN, SOCK_RAW, CAN_RAW) → bind(addr) → read/write(frame)

PREEMPT_RT:
  CONFIG_PREEMPT_RT=y → worst-case latency ~50-200μs
  SCHED_FIFO: real-time scheduling class
  mlockall(MCL_CURRENT|MCL_FUTURE): prevent page faults in RT code
  cyclictest: measure RT latency

Device driver essentials:
  alloc_chrdev_region() → register_chrdev_region() → cdev_add()
  copy_to_user() / copy_from_user() → safe kernel↔user data transfer
  wait_queue / wait_event_interruptible() → blocking reads
  request_irq() → interrupt handler registration

Memory debugging:
  valgrind --leak-check=full (test, 5-10x slow)
  -fsanitize=address,leak (ASan/LSan — preferred, 2x slow)
  smaps: /proc/PID/smaps — Anonymous pages = heap/mmap
  gperftools: production heap profiling

Boot analysis:
  systemd-analyze → total boot time breakdown
  systemd-analyze blame → per-service startup time
  journalctl -b → current boot log
  journalctl -b -1 → previous boot log

Yocto essentials:
  bitbake core-image-minimal → build base image
  bitbake -c devshell recipe → interactive shell in recipe context
  bitbake -g recipe → show task dependency graph
```
