# Embedded Linux Driver/Kernel Engineer — Learning Roadmap

## Phase 1: Foundation (Months 1–3)

### Month 1 — C Mastery + Linux Basics
- [ ] Pointers, pointer arithmetic, function pointers
- [ ] Memory management (malloc/free, stack vs heap)
- [ ] Bitwise operations (critical for driver programming)
- [ ] Linux file system navigation, shell scripting
- [ ] `git` basics — clone, branch, commit, patch

### Month 2 — Kernel Fundamentals
- [ ] Kernel architecture: monolithic vs microkernel
- [ ] Kernel compilation, menuconfig, defconfig
- [ ] Writing first kernel module (hello world)
- [ ] Kernel data structures: list_head, rbtree, hash tables
- [ ] Kernel memory: kmalloc, vmalloc, GFP flags
- [ ] Synchronization: spinlocks, mutexes, semaphores, RCU

### Month 3 — Core Driver Model
- [ ] Linux device model (bus/device/driver)
- [ ] Character device driver (full implementation)
- [ ] Platform driver + Device Tree
- [ ] Interrupt handling (request_irq, tasklets, workqueues)
- [ ] Sysfs, procfs, debugfs interfaces

---

## Phase 2: Domain Specialization (Months 4–7)

### Pick ONE primary domain first:

| Domain | Folder | Priority |
|--------|--------|----------|
| Graphics (DRM/KMS) | `04_graphics_drivers` | High (Intel/AMD/ARM GPU) |
| Multimedia (V4L2) | `05_multimedia_video_drivers` | High (Camera/Video) |
| Audio (ALSA/ASoC) | `08_audio_subsystem` | High (Embedded audio) |
| Display (Wayland) | `07_display_drivers` | Medium |
| Power Mgmt | `06_power_management` | Medium |
| Networking | `11_ethernet_network_drivers` | Medium |

### Month 4–5 — Primary Domain (Basics → Intermediate)
- Complete the `01_basics` and `02_intermediate` sections of your domain

### Month 6–7 — Primary Domain (Advanced)
- Complete `03_advanced` and all labs/projects

---

## Phase 3: Systems Knowledge (Months 8–10)

### Month 8 — Virtualization + Yocto
- [ ] KVM: kvm-tool, libvirt, virtio drivers
- [ ] Xen: dom0/domU, paravirtualization
- [ ] Yocto: `bitbake core-image-minimal`
- [ ] Custom layer, custom recipe, custom BSP

### Month 9 — Advanced Debugging
- [ ] KGDB + GDB remote debugging
- [ ] ftrace: function_graph, latency tracing
- [ ] perf: cpu-clock, cache-misses, branch-misses
- [ ] crash dump analysis with `crash` tool
- [ ] Dynamic debug: `pr_debug`, `dev_dbg`

### Month 10 — IPC, DMA, Second Domain
- [ ] DMA engine API, coherent vs streaming DMA
- [ ] IOMMU, dma-buf sharing
- [ ] IPC: shared memory, message queues, netlink
- [ ] Start second domain specialization

---

## Phase 4: Open Source & Community (Month 11–12)

- [ ] Read kernel documentation (Documentation/*)
- [ ] Subscribe to LKML, DRI-devel, or domain mailing list
- [ ] Write a bug report or fix a documented bug
- [ ] Submit first patch (even a typo fix counts)
- [ ] Get familiar with `checkpatch.pl`, `sparse`, `smatch`

---

## Interview Preparation Milestones

### Junior–Mid (2–3 yrs)
- Explain Linux driver model (bus/device/driver)
- Implement a char driver from scratch
- Explain spinlock vs mutex
- Describe DMA memory types

### Senior (5+ yrs)
- Debug a kernel oops from a crash dump
- Explain RCU (Read-Copy-Update) locking
- Describe DRM/KMS pipeline from fbdev to user space
- Design a V4L2 capture driver architecture
- Explain S0ix vs S3 power states
- Xen Dom0 driver model for split drivers

---

## Key Resources

| Resource | Link/Location |
|----------|--------------|
| LDD3 (Linux Device Drivers 3rd Ed) | Free at lwn.net/Kernel/LDD3 |
| Kernel documentation | https://kernel.org/doc/html/latest/ |
| Bootlin training slides | Free PDF at bootlin.com/training |
| The Linux Kernel (Robert Love) | Book |
| Understanding the Linux Kernel (Bovet) | Book |
| DRM developer docs | https://dri.freedesktop.org/docs/drm/ |
| V4L2 spec | https://linuxtv.org/downloads/v4l-dvb-apis/ |
| ALSA developer docs | https://alsa-project.org/wiki/ALSA_Development |

---

## Tools to Master

```
GDB / KGDB          — kernel & user space debugging
ftrace              — function/latency tracing
perf                — performance analysis
valgrind            — user space memory analysis
sparse              — kernel static analysis
smatch              — semantic C checker
checkpatch.pl       — kernel patch style checker
buildroot           — embedded Linux build (alternative to Yocto)
bitbake             — Yocto build tool
qemu                — kernel/driver testing without hardware
dtc / fdtdump       — device tree compiler/viewer
devmem2             — read/write physical memory (debug)
i2cdetect / i2cdump — I2C bus debugging
```
