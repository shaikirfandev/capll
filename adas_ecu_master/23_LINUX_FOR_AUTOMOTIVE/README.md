# 23 — Linux for Automotive

> **Platforms:** Yocto Linux, QNX, AGL (Automotive Grade Linux), AUTOSAR Adaptive on Linux

---

## 23.1 Linux in Automotive ECUs

| Platform              | Use Case                                | ASIL Support |
|-----------------------|-----------------------------------------|--------------|
| Yocto Linux           | Infotainment, Adaptive ECUs, gateways   | Up to ASIL B (with PREEMPT_RT) |
| QNX Neutrino          | ADAS, instrument cluster, L3+           | ASIL D capable |
| AUTOSAR Adaptive      | L3+ domain controllers (runs on Linux/QNX) | With ASIL partition |
| Automotive Grade Linux (AGL) | IVI head unit, Android Auto/CarPlay | QM only |
| Real-Time Linux (PREEMPT_RT) | Robotics, ADAS prototype         | ASIL B prototype |

---

## 23.2 SocketCAN — CAN on Linux

```bash
# Load SocketCAN kernel modules
sudo modprobe can
sudo modprobe can_raw
sudo modprobe vcan         # Virtual CAN interface for testing

# Create virtual CAN interface (for HIL / desktop testing)
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# Configure real CAN hardware (Vector VN1630A or Peak USB)
sudo ip link set can0 up type can bitrate 500000 sample-point 0.875

# For CAN FD:
sudo ip link set can0 up type can bitrate 500000 dbitrate 2000000 fd on

# Monitor all frames:
candump vcan0

# Send a frame (ID 0x100, 8 bytes of data):
cansend vcan0 100#0102030405060708

# Log to file:
candump -l vcan0 log.asc
```

### C Code: SocketCAN Receive

```c
#include <linux/can.h>
#include <linux/can/raw.h>
#include <sys/socket.h>
#include <net/if.h>
#include <string.h>
#include <stdio.h>

int main(void) {
    int sock = socket(PF_CAN, SOCK_RAW, CAN_RAW);

    struct ifreq ifr;
    strcpy(ifr.ifr_name, "vcan0");
    ioctl(sock, SIOCGIFINDEX, &ifr);

    struct sockaddr_can addr = {
        .can_family  = AF_CAN,
        .can_ifindex = ifr.ifr_ifindex
    };
    bind(sock, (struct sockaddr*)&addr, sizeof(addr));

    struct can_frame frame;
    while (1) {
        ssize_t bytes = read(sock, &frame, sizeof(frame));
        if (bytes == sizeof(frame)) {
            printf("ID: 0x%03X  DLC: %d  Data:", frame.can_id, frame.can_dlc);
            for (int i = 0; i < frame.can_dlc; i++) {
                printf(" %02X", frame.data[i]);
            }
            printf("\n");
        }
    }
    return 0;
}
```

---

## 23.3 Real-Time Linux (PREEMPT_RT)

```bash
# Check if PREEMPT_RT is enabled:
uname -v | grep -i preempt

# Expected: #1 SMP PREEMPT_RT ...

# Set task real-time priority (SCHED_FIFO, priority 80):
#include <sched.h>
struct sched_param sp = { .sched_priority = 80 };
sched_setscheduler(0, SCHED_FIFO, &sp);

# Lock all current and future memory pages (prevents page faults in RT task):
#include <sys/mman.h>
mlockall(MCL_CURRENT | MCL_FUTURE);

# Latency measurement:
cyclictest --priority=80 --policy=fifo --interval=1000 --loops=10000
# Target: max latency < 100 µs on PREEMPT_RT kernel
```

---

## 23.4 Yocto Build for Automotive

```bash
# Set up Yocto Kirkstone (used in many automotive programs):
git clone git://git.yoctoproject.org/poky.git -b kirkstone
cd poky
source oe-init-build-env build-automotive

# Add meta-automotive layer (AGL or GENIVI):
bitbake-layers add-layer ../meta-agl

# Configure local.conf:
MACHINE = "raspberrypi4"          # or "nxp-s32g" for automotive SoC
DISTRO  = "agl-demo"
IMAGE_FEATURES += "ssh-server-openssh"

# Add SocketCAN support:
IMAGE_INSTALL:append = " kernel-module-can-raw iproute2 can-utils"

# Build minimal automotive image:
bitbake agl-demo-platform
```

---

## 23.5 systemd Service for AUTOSAR Adaptive

```ini
# /etc/systemd/system/adas_adaptive.service
[Unit]
Description=ADAS Adaptive Application
After=network.target can0-up.service

[Service]
Type=simple
ExecStartPre=/sbin/ip link set can0 up type can bitrate 500000
ExecStart=/usr/bin/adas_adaptive_app
Restart=on-failure
RestartSec=1s
# RT priority for the process
CPUSchedulingPolicy=fifo
CPUSchedulingPriority=50
# Restrict memory (ECU simulation)
MemoryMax=256M
# Watchdog support
WatchdogSec=5s
NotifyAccess=main

[Install]
WantedBy=multi-user.target
```

---

## 23.6 AUTOSAR Adaptive on Linux

```
AUTOSAR Adaptive Functional Clusters on Linux:
  ara::com   → SOME/IP over UDP/TCP (vsomeip library)
  ara::diag  → DoIP over Ethernet (ISO 13400)
  ara::log   → DLT (Diagnostic Log and Trace) over UDP
  ara::exec  → ExecutionManager (manages app process lifecycle)
  ara::nm    → Network Management (SOME/IP-SD)
  
Start sequence:
  1. Bootstrap (bootloader)
  2. OS init (Linux/QNX kernel)
  3. Platform services (ara::exec, ara::com, ara::diag)
  4. ADAS applications (camera processor, path planner, ACC)
  
Shutdown: ExecutionManager sends SIGTERM to all apps → apps save state → OS shutdown
```

---

## 23.7 Interview Questions

**L1:**
1. What is SocketCAN and how do you receive a CAN frame in C on Linux?
2. What is the difference between SCHED_FIFO and SCHED_OTHER?
3. What is Yocto and why is it used in automotive?

**L2:**
4. How does PREEMPT_RT improve Linux for automotive applications?
5. How would you configure a CAN FD interface on Linux?
6. What is the role of ExecutionManager in AUTOSAR Adaptive?

**L3:**
7. How would you partition a Yocto image for safety-critical ADAS processing?
8. Design the startup sequence for an AUTOSAR Adaptive gateway ECU on Linux.
9. What are the limitations of Linux for ASIL-D applications?
10. How is DLT (Diagnostic Log and Trace) used in AUTOSAR Adaptive debugging?
