# 03 — HIL/SIL Environments

## Overview

This module documents the **Hardware-in-the-Loop (HIL) and Software-in-the-Loop (SIL)** testing strategies, the Hardware Abstraction Layer (HAL) pattern, and CAN simulation infrastructure used in `adas_rt_cpp_project`.

---

## 1. V-Model Testing Levels in Automotive

```
Requirements
    │                                              ▲
    ▼                                              │
System Design ──────────────────────────► System Integration Test
    │                                              ▲
    ▼                                              │
Software Architecture ────────────────► Integration Test (HIL/SIL)
    │                                              ▲
    ▼                                              │
Module Design ──────────────────────── ► Unit Tests (GTest)
    │                                              ▲
    ▼                                              │
Source Code ─────────────────────────────────────►
```

This project covers all three levels:
- **Unit tests** (`tests/unit/`) — isolated module testing
- **SIL integration** (`tests/sil/`) — closed-loop scenario on host PC
- **HIL** — `SocketCanHal` + PREEMPT_RT setup for real hardware

---

## 2. SIL vs HIL — Detailed Comparison

| Dimension | SIL (Software-in-the-Loop) | HIL (Hardware-in-the-Loop) |
|-----------|---------------------------|---------------------------|
| **Hardware required** | Host PC only | Real ECU + HIL rack |
| **Real-time execution** | Simulated time (deterministic replay) | Real-time (hard RT, POSIX scheduling) |
| **Latency** | Not measured (sim time) | Measured and characterised |
| **Sensor data source** | Injected via `SimHal::injectFrame()` | Physical sensor / hardware stimuli |
| **CAN bus** | In-process (`SimHal`) or `vcan0` | Physical CAN (PEAK PCAN, Vector CANcase) |
| **Typical toolchain** | Bazel + GTest on any Linux/macOS | dSPACE SCALEXIO / NI PXI + INCA/CANoe |
| **Scenario repeatability** | Perfect (deterministic) | Near-perfect (within timing jitter) |
| **CI/CD integration** | Yes — runs in minutes | Not typically (requires hardware) |
| **Fault injection** | Trivial (`injectFault()`) | Hardware fault injection boards |
| **Use in ISO 26262** | V&V of software components | V&V of integrated ECU |

---

## 3. Hardware Abstraction Layer (HAL)

### 3.1 Interface Design

**File**: `src/hil_sil/hal.hpp`

```cpp
class IHal {
public:
    virtual ~IHal() = default;

    virtual bool open() = 0;
    virtual void close() = 0;

    // CAN
    virtual bool txCan(const CanFrame& frame) = 0;
    virtual void registerCanRxCallback(CanRxCallback cb) = 0;

    // GPS
    virtual void registerGpsCallback(GpsCallback cb) = 0;

    // IMU
    virtual void registerImuCallback(ImuCallback cb) = 0;

    virtual bool isSimulation() const = 0;
};
```

The algorithm code (`main.cpp`, sensor processing) depends **only on `IHal*`**. Swapping SIL→HIL means changing one line in main():

```cpp
// SIL
std::unique_ptr<IHal> hal = std::make_unique<SimHal>();

// HIL (SocketCAN backend)
std::unique_ptr<IHal> hal = std::make_unique<SocketCanHal>("vcan0");
```

### 3.2 Benefit: Zero Algorithm Changes for HIL/SIL Switch

Because ADAS algorithm code never calls hardware directly, the same binary can be tested at all levels. The HAL is the **only integration seam**.

---

## 4. SimHal — SIL Backend

**File**: `src/hil_sil/can_bus_sim.hpp/.cpp`

### 4.1 How It Works

```
Test/Main code                   SimHal                     ADAS algorithm
──────────────────────────────────────────────────────────────────────────
hal.injectFrame(ego_speed) ──►  rx_queue_ (SpscQueue)
                                         │
                                         ▼ dispatch callbacks
                                  canRxCallback(frame)  ──► decodeEgoSpeed()

algorithm calls txCan(cmd) ──►  tx_log_.push_back(frame)

test checks:                     hal.drainTxLog()  ──► assert steer angle
```

### 4.2 API Reference

```cpp
SimHal hal;
hal.open();

// Inject a sensor stimulus
CanFrame frame{};
frame.id = 0x100;   // EGO_SPEED
encodeSignal(frame, signals::EGO_SPEED, 22.22f);  // 80 km/h
hal.injectFrame(frame);

// Run algorithm for N cycles...

// Inspect what the algorithm transmitted
auto tx_log = hal.drainTxLog();
for (const auto& f : tx_log) {
    if (f.id == 0x200) {
        float steer = decodeSignal(f, signals::STEER_ANGLE);
        EXPECT_NEAR(steer, expected_steer, 0.01f);
    }
}

hal.close();
```

---

## 5. SocketCanHal — HIL Backend

**File**: `src/hil_sil/can_bus_sim.cpp` (conditional `#ifdef ADAS_USE_SOCKETCAN`)

### 5.1 Linux SocketCAN Architecture

```
ADAS process
   SocketCanHal
        │ socket(AF_CAN, SOCK_RAW, CAN_RAW)
        │ bind(vcan0 or can0)
        │
        ▼
   Linux kernel
        │ SocketCAN driver
        │
        ▼
   vcan0 (virtual, for SIL)  OR  can0 / can1 (real PEAK/Kvaser HW)
```

### 5.2 Setup Virtual CAN (vcan0)

```bash
# Load vcan kernel module
sudo modprobe vcan

# Create virtual interface
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# Verify
ip link show vcan0
# vcan0: <NOARP,UP,LOWER_UP,ECHO> mtu 16 ...

# Monitor traffic in another terminal
candump vcan0 -td -a
```

### 5.3 Real CAN Setup (PEAK PCAN-USB)

```bash
# Load PEAK Linux driver
sudo modprobe peak_usb

# Configure interface
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0

# Verify
ip -details link show can0
```

---

## 6. CAN Signal Encoding/Decoding

### 6.1 Signal Table

| Signal Name | CAN ID | Start Bit | Length | Scale | Offset | Unit |
|-------------|--------|-----------|--------|-------|--------|------|
| EGO_SPEED | 0x100 | 0 | 16 | 0.01 | 0 | m/s |
| EGO_ACCEL | 0x101 | 0 | 16 | 0.001 | -32.768 | m/s² |
| THROTTLE | 0x200 | 0 | 8 | 0.01 | 0 | fraction (0–1) |
| BRAKE | 0x200 | 8 | 8 | 0.01 | 0 | fraction (0–1) |
| STEER_ANGLE | 0x200 | 16 | 16 | 0.01 | -327.68 | degrees |
| DTC_ID | 0x400 | 0 | 16 | 1 | 0 | DTC code |
| DTC_STATUS | 0x400 | 16 | 8 | 1 | 0 | 0=inactive,1=pending,2=active |

### 6.2 Encode/Decode Function

```cpp
// Encode physical value into CAN frame bytes
void encodeSignal(CanFrame& frame, const Signal& sig, float phys) {
    uint16_t raw = static_cast<uint16_t>((phys - sig.offset) / sig.scale);
    // Pack raw into frame.data[] at sig.start_bit, sig.length
    // (little-endian bit-field packing)
}

// Decode raw bytes to physical value
float decodeSignal(const CanFrame& frame, const Signal& sig) {
    uint16_t raw = extractBits(frame.data, sig.start_bit, sig.length);
    return raw * sig.scale + sig.offset;
}
```

---

## 7. SIL Test Harness Architecture

**File**: `tests/sil/sil_test_harness.cpp`

### 7.1 Component Diagram

```
SIL Test Driver
    │
    ├── SimHal (in-process CAN)
    ├── VehicleModel (point-mass kinematic integrator)
    │       v(t+dt) = v(t) + a(t)*dt
    │       x(t+dt) = x(t) + v(t)*dt
    │
    ├── ADAS Pipeline (ObjectDetector, SensorFusion, PathPlanner, Controller)
    │
    └── Scenario Injector
            inject radar detection at t=1s, range=40m
```

### 7.2 AEB Scenario Pass Criteria

```
1. AEB behavior decision triggered within 2 s of obstacle injection
2. Vehicle stops (speed < 2 m/s) before reaching obstacle
3. Final separation > 0 m (no collision)
4. No DTC faults generated (clean run)
```

### 7.3 Test Output Example

```
[SIL] t=0.00s  ego_v=22.22m/s  obj_dist=inf
[SIL] t=1.00s  RADAR injected: range=40.0m
[SIL] t=2.80s  Track confirmed: id=1 px=37.2m
[SIL] t=3.15s  TTC=1.42s < 1.5s → AEB triggered
[SIL] t=5.05s  ego_v=0.0m/s  obj_dist=8.3m  [PASS]
```

---

## 8. Industry Tool Context

### 8.1 dSPACE Integration

In production automotive development, the HIL test would run on:

| dSPACE Component | Role |
|-----------------|------|
| SCALEXIO Processing Unit | Real-time simulation host (multi-core Xeon) |
| SCALEXIO I/O boards | CAN/LIN/FlexRay interfaces to real ECU |
| ControlDesk | GUI for stimulation vectors and signal monitoring |
| AutomationDesk | Scripted test sequences (Python API) |

The `IHal` interface in this project maps cleanly to the dSPACE MIL/SIL/HIL switch pattern.

### 8.2 CANoe Integration

Vector CANoe is the industry-standard CAN test tool. The `SocketCanHal` could be replaced by a CANoe-based HAL that wraps the Vector XL driver API:

```cpp
class VectorCanHal : public IHal {
    // Uses XL_OpenDriver() / XL_ConnectChannel() / XL_Transmit()
    // Callbacks via XL_SetNotification() event handle
};
```

CAPL test nodes in CANoe can validate the `0x200` control command frames from the ADAS ECU.

---

## 9. Test Automation Integration (CI/CD)

```yaml
# .github/workflows/sil.yml (example)
name: SIL Tests
on: [push, pull_request]
jobs:
  sil:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v3
      - name: Install Bazel
        run: ...
      - name: Run Unit Tests
        run: bazel test //tests/unit/... --test_output=short
      - name: Run SIL AEB Scenario
        run: bazel test //tests/sil:sil_aeb_scenario --test_output=all
```

The SIL test runs in ~5 seconds on a CI host — no hardware required.

---

*See also*: [05_Embedded_Linux.md](05_Embedded_Linux.md) for HIL setup on PREEMPT_RT targets.  
*See also*: [06_Debugging_Integration.md](06_Debugging_Integration.md) for fault injection and debugging.
