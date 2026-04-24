# ADAS ECU — Embedded C++ Application

A complete, production-realistic **ADAS ECU** implemented in C++17 for an ARM Cortex-M4 microcontroller.
Demonstrates the real C++ patterns used in automotive ECU development: hardware abstraction, cyclic executive scheduler, CAN bus driver, sensor fusion, ADAS feature state machines, and AUTOSAR-aligned diagnostics.

---

## Architecture

```
main.cpp
  │
  ├── HAL (Hardware Abstraction Layer)
  │   ├── hal_types.hpp     — Foundation types: Status, EcuMode, physical units, macros
  │   └── hal_timer.cpp     — SysTick counter (embedded) / std::chrono (simulation)
  │
  ├── Drivers
  │   ├── can_driver.cpp    — bxCAN peripheral driver with Rx ring buffer
  │   └── can_messages.hpp  — CAN signal codec: 16 messages, factor/offset encoding
  │
  ├── RTOS
  │   └── scheduler.cpp     — Cyclic executive (no OS), overrun detection
  │
  ├── Features
  │   ├── sensor_fusion.cpp — World model: fuses radar + camera + speed + steering
  │   ├── acc_controller.cpp — ACC with PID speed-hold + following control + AEB
  │   ├── lka_controller.cpp — LKA torque steering + LDW warning
  │   ├── bsd_controller.cpp — BSD blind spot detection + indicator alert
  │   ├── parking_controller.cpp — Parking distance zones + auto-brake
  │   └── hha_controller.cpp — Hill Hold Assist with brake pressure ramp
  │
  └── Diagnostics
      └── dtc_manager.cpp   — AUTOSAR Dem-aligned DTC storage, UDS 0x14/0x19 support
```

### Task Cycle Times

| Task | Period | Runs |
|------|--------|------|
| `Task_FastSensors` | 10 ms | CAN Rx decode |
| `Task_Control` | 20 ms | SensorFusion + ACC + LKA + BSD |
| `Task_MediumCycle` | 50 ms | Parking + HHA + LDW |
| `Task_Diagnostics` | 100 ms | DTC end-of-cycle |
| `Task_Background` | 1000 ms | Health logging, scheduler stats |

### CAN Message Map

| ID | Period | Signal | Direction |
|----|--------|--------|-----------|
| 0x100 | 10ms | VehicleSpeed | ← ABS |
| 0x101 | 10ms | SteeringAngle | ← EPS |
| 0x102 | 10ms | WheelSpeeds | ← ABS |
| 0x200 | 20ms | RadarObject | ← Radar |
| 0x201 | 20ms | CameraLane | ← Camera |
| 0x202 | 20ms | BSD_Radar | ← BSD radar |
| 0x203 | 50ms | Ultrasonic | ← Park sensors |
| 0x300 | 20ms | ACC_Status | → bus |
| 0x301 | 20ms | ACC_Control | → throttle/brake |
| 0x302 | 20ms | LKA_Status | → bus |
| 0x303 | 20ms | LKA_TorqueCmd | → EPS |
| 0x304 | 20ms | BSD_Status | → bus |
| 0x305 | 50ms | Park_Status | → bus |
| 0x306 | 20ms | HHA_Status | → bus |
| 0x400 | 20ms | DriverInputs | ← BCM |
| 0x401 | 20ms | GearShifter | ← TCU |
| 0x500 | 100ms | LDW_Warning | → HMI |

---

## Key Embedded C++ Patterns Demonstrated

### No Dynamic Memory
```cpp
// All arrays are fixed-size compile-time constants — no std::vector, no new/delete
static constexpr uint8_t MAX_TASKS = 16;
TaskDescriptor tasks_[MAX_TASKS];
```

### PACKED Structs for DMA / Hardware Register Access
```cpp
struct PACKED CanFrame {
    uint32_t id;
    uint8_t  dlc;
    uint8_t  data[8];
};
```

### Singleton Pattern — Embedded Safe
```cpp
static AccController& instance() {
    static AccController inst;  // Only one — initialized once at startup
    return inst;
}
AccController(const AccController&) = delete;
AccController& operator=(const AccController&) = delete;
```

### Volatile ISR Counter (SysTick)
```cpp
extern "C" void SysTick_Handler() {
    g_tick++;   // volatile — compiler cannot cache this
}
```

### PID Controller with Anti-Windup (ACC)
```cpp
float error    = set_speed_mps - vehicle.speed_mps;
integral_     += error * dt;
integral_      = clamp(integral_, -MAX_INTEGRAL, MAX_INTEGRAL);  // Anti-windup
float output   = KP*error + KI*integral_ + KD*(error - prev_error_) / dt;
```

### State Machine (ACC)
```cpp
enum class State : uint8_t { OFF, STANDBY, ACTIVE, OVERRIDE, FAULT };

void AccController::tick(…) {
    runAEB(vehicle, target);   // Always evaluated — safety critical
    switch (state_) {
        case State::STANDBY:  handleStandby(driver);       break;
        case State::ACTIVE:   handleActive(vehicle, target); break;
        …
    }
}
```

### CAN Signal Encoding (factor/offset)
```cpp
// Decode: physical = raw * factor + offset
float speed_kph = static_cast<float>((f.data[1] << 8) | f.data[0]) * 0.01f;

// Encode: raw = (physical - offset) / factor
uint16_t raw = static_cast<uint16_t>(speed_kph / 0.01f);
```

### Cyclic Executive Scheduler
```cpp
void Scheduler::dispatch() {
    TickType_t now = Timer::getTick();
    for (auto& t : tasks_) {
        if (now - t.last_run >= t.period_ms) {
            TickType_t t0 = Timer::getTick();
            t.func();
            uint32_t exec = Timer::elapsed(t0);
            if (exec > t.period_ms) t.overrun_count++;
            t.last_run = now;
        }
    }
}
```

---

## Build

### Simulation (run on any laptop)
```bash
cd adas_ecu_cpp
mkdir build_sim && cd build_sim
cmake -DBUILD_SIMULATION=ON -DCMAKE_BUILD_TYPE=Debug ..
make -j$(nproc)
./adas_ecu_sim
```

### Embedded — ARM Cortex-M4 (STM32F4 / NXP S32K)
```bash
# Requires arm-none-eabi-g++ from Arm GNU Toolchain
cd adas_ecu_cpp
mkdir build_hw && cd build_hw
cmake -DEMBEDDED_TARGET=ON -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
# Flash adas_ecu.elf with J-Link / OpenOCD
arm-none-eabi-size adas_ecu.elf
```

### With Unit Tests
```bash
mkdir build_test && cd build_test
cmake -DBUILD_SIMULATION=ON -DBUILD_TESTS=ON ..
make -j$(nproc)
ctest --output-on-failure
```

---

## Simulation Output Example

```
╔══════════════════════════════════════════════════╗
║  ADAS ECU Firmware  v1.0.0                       ║
║  Mode: SIMULATION                                ║
╚══════════════════════════════════════════════════╝

[MAIN] Entering main loop

══════════════════════════════════════════════════
  ADAS ECU  tick=1000      speed=50.0 km/h
  ACC: state=2   set=80km/h  AEB=0
  LKA: state=2   torque=0.15 Nm  LDW=0
  Target: dist=75.3m  relV=-2.50m/s  TTC=30.12s
  DTCs: active=0  confirmed=0
  Scheduler tasks (5):
    FastSensors            period=10ms  overruns=0 maxExec=1ms
    Control                period=20ms  overruns=0 maxExec=3ms
    MediumCycle            period=50ms  overruns=0 maxExec=1ms
    Diagnostics            period=100ms overruns=0 maxExec=0ms
    Background             period=1000ms overruns=0 maxExec=0ms
══════════════════════════════════════════════════
```

---

## AUTOSAR Alignment

| AUTOSAR Module | This Implementation |
|----------------|---------------------|
| Dem (Diagnostic Event Manager) | `DtcManager` — fail/pass trip counters, status bitfield |
| Com (Communication) | `can_messages.hpp` — signal encoding/decoding |
| CanIf (CAN Interface) | `CanDriver` — frame transmit/receive + filters |
| Os (Operating System) | `Scheduler` — cyclic executive (no OS required) |
| Rte (Runtime Environment) | Global message structs in `main.cpp` |

---

## DTC List

| DTC ID | Description |
|--------|-------------|
| `RADAR_COMM_LOSS` | Radar message timeout > 500ms |
| `CAMERA_COMM_LOSS` | Camera lane message timeout > 2s |
| `ACC_INTERNAL_FAULT` | ACC state machine fault latched |
| `LKA_TORQUE_OVERLOAD` | LKA torque demand exceeds safe limit |
| `BSD_SENSOR_FAULT` | BSD radar input invalid |
| `PARKING_SENSOR_FAULT` | Ultrasonic sensor signals invalid |
| `HHA_ACTUATOR_FAULT` | HHA brake actuator not responding |
| `TASK_OVERRUN` | Scheduler task exceeded its period |
| `ECU_UNDER_VOLTAGE` | Supply voltage below threshold |
| `CAN_BUS_OFF` | CAN bus-off error detected |

---

## File Count

| Layer | Files |
|-------|-------|
| HAL | 4 (2 headers, 2 source) |
| Drivers | 4 (3 headers, 1 source) |
| RTOS | 2 (1 header, 1 source) |
| Features | 12 (6 headers, 6 source) |
| Diagnostics | 2 (1 header, 1 source) |
| Application | 1 (`main.cpp`) |
| Build | 1 (`CMakeLists.txt`) |
| **Total** | **26** |
