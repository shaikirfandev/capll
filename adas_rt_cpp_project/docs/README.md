# Documentation Index

This directory contains the detailed documentation for `adas_rt_cpp_project`.

## Structure

| File | Content |
|------|---------|
| [../SINGLE_SOURCE_OF_TRUTH.md](../SINGLE_SOURCE_OF_TRUTH.md) | **Master reference** — full project overview, architecture, all modules, quick-start |
| [01_CPP_Development.md](01_CPP_Development.md) | C++17 features, memory management, templates, type safety, MISRA alignment |
| [02_ADAS_Domain.md](02_ADAS_Domain.md) | ADAS pipeline, sensor types, EKF math, JMT planning, Stanley control |
| [03_HIL_SIL_Environments.md](03_HIL_SIL_Environments.md) | SIL vs HIL comparison, HAL pattern, SimHal, SocketCAN, CAN signal encoding |
| [04_Bazel_Build_System.md](04_Bazel_Build_System.md) | Workspace layout, BUILD file anatomy, configs, test commands, dependency pinning |
| [05_Embedded_Linux.md](05_Embedded_Linux.md) | PREEMPT_RT, isolcpus, mlockall, IRQ affinity, cross-compilation, deployment |
| [06_Debugging_Integration.md](06_Debugging_Integration.md) | GDB Python commands, ASan, TSan, logging, DTC fault lifecycle |
| [07_Multithreading_Realtime.md](07_Multithreading_Realtime.md) | SCHED_FIFO, lock-free SPSC queue, work-stealing pool, jitter budget |

## Skill-to-Document Mapping

| Skill Area | Primary Doc | Supporting Docs |
|-----------|-------------|----------------|
| C++ Development | [01](01_CPP_Development.md) | [07](07_Multithreading_Realtime.md) |
| ADAS Domain | [02](02_ADAS_Domain.md) | [03](03_HIL_SIL_Environments.md) |
| HIL/SIL | [03](03_HIL_SIL_Environments.md) | [06](06_Debugging_Integration.md) |
| Bazel Build System | [04](04_Bazel_Build_System.md) | [01](01_CPP_Development.md) |
| Embedded Linux | [05](05_Embedded_Linux.md) | [07](07_Multithreading_Realtime.md) |
| Debugging & Integration | [06](06_Debugging_Integration.md) | [03](03_HIL_SIL_Environments.md) |
| Multi-threading & Real-Time | [07](07_Multithreading_Realtime.md) | [05](05_Embedded_Linux.md) |
