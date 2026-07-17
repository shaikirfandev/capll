# Project: Industrial Sensor Hub Platform Driver

## What This Project Teaches

A production-grade Linux platform driver for a multi-channel sensor hub SoC peripheral found in industrial and automotive systems. The peripheral sits on the SoC's internal AHB/APB bus and exposes temperature, humidity, and pressure channels via MMIO registers, with a data-ready IRQ and optional DMA bulk-read.

This project uses **every concept** from the Linux Device Drivers learning guide:

| Concept | Where used |
|---|---|
| `platform_driver` + DT matching | `sensor_hub.c` probe/remove |
| MMIO register access (`ioread32`/`iowrite32`) | All register reads in driver |
| `devm_*` resource management | All allocations in probe |
| Char device (`cdev`, `file_operations`) | `/dev/sensor_hub0` read interface |
| `sysfs` attributes (`DEVICE_ATTR_RW`) | Per-channel enable, rate, threshold |
| IRQ handling + wait queue | Data-ready IRQ → wakes reader |
| `ioctl` | Calibration, channel select, flush |
| `copy_to_user` / `copy_from_user` | Safe kernel↔user data transfer |
| DMA (`dma_alloc_coherent`) | Bulk FIFO drain into DMA buffer |

## Project Structure

```
project_sensor_hub/
├── README.md                ← this file
├── kernel/
│   ├── sensor_hub.h         ← register map, structs, ioctl defs
│   ├── sensor_hub.c         ← full platform driver
│   └── Makefile
├── dts/
│   └── sensor-hub-overlay.dts   ← DT overlay for target board
└── userspace/
    ├── sensor_reader.c      ← reads samples via /dev/sensor_hub0
    ├── sysfs_monitor.c      ← polls sysfs attributes
    └── Makefile
```

## Hardware Model

```
SoC AHB Bus
    │
    ▼  base = 0x40080000, size = 0x1000
┌──────────────────────────────┐
│     SENSOR_HUB peripheral    │
│                              │
│  0x000  CTRL     (rw)        │  enable, reset, IRQ mask
│  0x004  STATUS   (ro)        │  channel ready bits, overflow
│  0x008  CH_SEL   (rw)        │  active channel (0–3)
│  0x00C  DATA     (ro)        │  16-bit sample (read clears)
│  0x010  FIFO_LVL (ro)        │  number of samples in FIFO
│  0x014  FIFO_DATA(ro)        │  burst FIFO read port
│  0x018  RATE     (rw)        │  sample rate (Hz, 1–1000)
│  0x01C  THR_HI   (rw)        │  high threshold → IRQ
│  0x020  THR_LO   (rw)        │  low threshold → IRQ
│  0x100  CAL[4]   (rw)        │  per-channel calibration offset
└──────────────────────────────┘
         │ IRQ line 55
         ▼
     GIC (ARM interrupt controller)
```

## Build

```bash
# Cross-compile kernel module (i.MX8 / ARM64)
cd kernel/
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- \
     KDIR=/path/to/kernel/build

# Native build (x86 dev machine with virt driver stub)
make KDIR=/lib/modules/$(uname -r)/build

# Build userspace tools
cd userspace/
make
```

## Run on Target

```bash
# Load driver
insmod sensor_hub.ko

# Verify
dmesg | tail -20
ls /dev/sensor_hub*
ls /sys/bus/platform/devices/40080000.sensor-hub/

# Read live samples
./sensor_reader /dev/sensor_hub0

# Monitor via sysfs
./sysfs_monitor /sys/bus/platform/devices/40080000.sensor-hub/
```
