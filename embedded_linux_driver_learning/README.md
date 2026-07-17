# Embedded Linux Driver & Kernel Development — Complete Learning Guide

> **Target Profile:** Engineer with 5+ years of experience in Embedded Linux Driver/Kernel Development  
> **Structure:** Basic → Intermediate → Advanced for every domain  
> **Coverage:** All 16 job-requirement domains fully addressed

---

## Folder Structure

```
embedded_linux_driver_learning/
├── 00_learning_roadmap/          ← Start Here: Full learning path & timeline
├── 01_c_programming_mastery/     ← Strong C skills: basics to kernel-style C
├── 02_linux_kernel_fundamentals/ ← Kernel architecture, modules, internals
├── 03_linux_device_drivers/      ← Core driver model, char/block/platform/PCI
├── 04_graphics_drivers/          ← DRM/KMS, OpenGL, Vulkan, Mesa
├── 05_multimedia_video_drivers/  ← V4L2, GStreamer, VAAPI, VDPAU
├── 06_power_management/          ← System sleep: S3, S0ix, Runtime PM
├── 07_display_drivers/           ← X11, Wayland, Weston, Display pipeline
├── 08_audio_subsystem/           ← ALSA, ASoC, I2S/TDM protocols
├── 09_yocto_development/         ← Yocto/BitBake, layers, custom BSP
├── 10_virtualization/            ← Xen, KVM, QNX hypervisor
├── 11_ethernet_network_drivers/  ← Network driver model, NAPI, ethtool
├── 12_ipc_dma/                   ← IPC mechanisms, DMA engine, IOMMU
├── 13_system_debugging/          ← GDB, KGDB, ftrace, perf, crash
└── 14_opensource_contribution/   ← Linux community, patch submission, git
```

---

## Domain Coverage Map

| # | Job Requirement | Folder |
|---|----------------|--------|
| 1 | Embedded Linux driver/kernel development | `02_linux_kernel_fundamentals` + `03_linux_device_drivers` |
| 2 | Strong C development skills | `01_c_programming_mastery` |
| 3 | Driver development domain | `03_linux_device_drivers` |
| 4 | Graphics: DRM/KMS, OpenGL, Vulkan, Mesa | `04_graphics_drivers` |
| 5 | Multimedia: VAAPI, VDPAU, GStreamer, V4L2 | `05_multimedia_video_drivers` |
| 6 | Power management: S3, S0ix | `06_power_management` |
| 7 | Display: X, Wayland, Weston | `07_display_drivers` |
| 8 | Audio: ALSA, ASoC, I2S/TDM | `08_audio_subsystem` |
| 9 | Yocto development | `09_yocto_development` |
| 10 | Virtualization: Xen, KVM, QNX | `10_virtualization` |
| 11 | Ethernet / Network drivers | `11_ethernet_network_drivers` |
| 12 | IPC, DMA driver development | `12_ipc_dma` |
| 13 | Kernel mode driver programming | `03_linux_device_drivers` |
| 14 | Linux Device driver programming | `03_linux_device_drivers` |
| 15 | Linux community & Open Source | `14_opensource_contribution` |
| 16 | System knowledge & System Debugging | `13_system_debugging` |

---

## Prerequisites

- Basic programming knowledge (any language)
- Familiarity with command line / bash
- Linux installed (Ubuntu 20.04+ recommended) or a VM
- Recommended hardware: Raspberry Pi 4, BeagleBone, or any ARM dev board

## Recommended Study Order

1. `01_c_programming_mastery` (Weeks 1–4)
2. `02_linux_kernel_fundamentals` (Weeks 5–8)
3. `03_linux_device_drivers` (Weeks 9–14)
4. Then branch into your chosen domain (Weeks 15+)
5. `13_system_debugging` runs in parallel with everything
6. `14_opensource_contribution` starts after your first real driver

---

## Quick Reference Commands

```bash
# Build a kernel module
make -C /lib/modules/$(uname -r)/build M=$PWD modules

# Load/unload a module
sudo insmod my_driver.ko
sudo rmmod my_driver

# Check kernel log
dmesg | tail -50
journalctl -k -f

# Check loaded modules
lsmod | grep my_driver

# View device tree
dtc -I fs /sys/firmware/devicetree/base

# Debug with ftrace
echo function > /sys/kernel/debug/tracing/current_tracer
cat /sys/kernel/debug/tracing/trace
```
