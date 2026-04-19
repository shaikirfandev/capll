# Model-Based Testing Guide
## MIL | SIL | PIL | HIL | Simulink | dSPACE | AUTOSAR

---

## 1. V-Model Test Levels

```
       Requirements
      /             \
   System Design   System Test (HIL)
    /           \  /           \
  Component    Integration   SIL/PIL
   Design       Test
    /
  Implementation ──── Unit Test (MIL/SIL)
```

---

## 2. MIL — Model in the Loop

**What:** Test the Simulink/model algorithm in simulation — no real code generated.

```
[Simulink Model] ←→ [Simulated Plant Model]
(controller)         (vehicle dynamics)

Environment: MATLAB/Simulink with Stateflow
```

**Purpose:** Verify algorithm logic early, fast iteration, no hardware needed.

**Testing:**
- Script-driven test cases from Simulink Test
- Coverage via Simulink Coverage
- Signal Builder / Test Sequence blocks

**Example MIL test:**
```matlab
% MATLAB script: MIL test for engine idle control
sim('EngineIdleController');  % Run model
assert(max(out.EngineSpeed.Data) < 950, 'Speed exceeded max idle');
assert(min(out.EngineSpeed.Data) > 650, 'Speed fell below min idle');
```

---

## 3. SIL — Software in the Loop

**What:** Auto-generated C code from Simulink runs on host PC (not on ECU target).

```
[Generated C Code] ←→ [Simulated Plant Model]
(controller C code)     (Simulink plant)

Tool: Embedded Coder → generated code runs via S-Function wrapper
```

**Purpose:** Verify that generated code behavior matches model — catch code generation issues.

**Key Step:** Run Embedded Coder, wrap generated `.c` in SIL harness, re-run same tests.

---

## 4. PIL — Processor in the Loop

**What:** Generated code runs on **real ECU target processor** but no physical I/O — I/O simulated over serial/Ethernet link.

```
[Host PC]              [Target ECU Processor]
[Plant Simulation] ←→  [Generated C Code]
                        RS232/USB/Ethernet link
```

**Purpose:** Verify timing on actual silicon — detect processor-specific issues (word size, FPU, compiler optimizations).

---

## 5. HIL — Hardware in the Loop

**What:** Real ECU connected to a **real-time plant simulator** that emulates the vehicle.

```
┌──────────────────┐     CAN/LIN/FlexRay      ┌──────────────────┐
│  HIL Simulator   │ ──────────────────────→  │   Real ECU       │
│  (dSPACE/NI VeriStand) │ ←────────────────── │  (production HW) │
│  - Vehicle model │     Analog I/O signals    │  - Real software │
│  - Sensor models │ ──→ Voltage, PWM ──────→  │  - Real OS       │
│  - Actuator load │                           │                  │
└──────────────────┘                           └──────────────────┘
```

**Purpose:** Full ECU validation with real-time constraints — closest to real vehicle without driving.

---

## 6. Comparison Table

| Aspect | MIL | SIL | PIL | HIL |
|--------|-----|-----|-----|-----|
| Code | Model only | Generated C | Generated C | Production C |
| Hardware | None | None | Target CPU only | Full ECU + Simulator |
| Real-time | No | No | Partial | Yes |
| Speed | Very fast | Fast | Slower | Realtime |
| Cost | Low | Low | Medium | High |
| Fault injection | Easy | Medium | Medium | Full |
| Coverage | Algorithm | Code gen | CPU timing | Full system |
| Tools | Simulink | Embedded Coder | Processor board | dSPACE/NI/Speedgoat |

---

## 7. dSPACE HIL Setup

### Common dSPACE Hardware
- **SCALEXIO** — modular HIL for complex systems
- **DS1006/DS1007** — processor board for plant model
- **DS5203** — FPGA I/O board
- **DS2202/DS4302** — CAN/LIN interface boards

### Workflow
```
1. Build plant model in Simulink (vehicle dynamics, sensors)
2. Compile with dSPACE RTI (Real-Time Interface) for SCALEXIO
3. Connect ECU harness to HIL I/O boards
4. Run ControlDesk for signal monitoring/control
5. Execute automated test sequences via MATLAB/ControlDesk API
```

### ControlDesk Python API
```python
import controldesk

# Connect to dSPACE
cd = controldesk.ControlDesk()
cd.connect()

# Read signal
speed = cd.Signal('Model Root/VehicleSpeed').value
print(f"Vehicle Speed: {speed}")

# Write setpoint
cd.Signal('Model Root/SpeedSetpoint').value = 80.0  # km/h

# Start recording
cd.Recorder['VehicleData'].start()
import time; time.sleep(10)
cd.Recorder['VehicleData'].stop()
```

---

## 8. AUTOSAR Software Component Testing

```
AUTOSAR SWC architecture:
┌─────────────────────────────────┐
│        Application SWC          │
│  Input Ports → Logic → Output   │
└─────────────────────────────────┘
          ↕ RTE (Runtime Environment)
┌─────────────────────────────────┐
│   BSW / OS / MCAL               │
└─────────────────────────────────┘

SWC Unit Testing with TESSY/VectorCAST:
- Mock RTE generated automatically
- Feed test data through Rte_Read_* stubs
- Check Rte_Write_* call values
- Measure MC/DC coverage
```

---

## 9. Fault Injection Testing

HIL enables systematic fault injection:

| Fault Type | How Injected | Example |
|-----------|-------------|---------|
| **Signal out of range** | Override sensor value | Coolant temp = 200°C |
| **Open circuit** | Break analog input | Speed sensor = high-impedance |
| **Short to ground** | Short to 0V | ABS wheel speed = 0V |
| **Short to battery** | Short to 12V | CAN-H = +12V ‒CANH short |
| **Bus flooding** | Inject high-rate messages | 10,000 msg/s on CAN |
| **Power interruption** | Interrupt ECU supply | KL30 cut during write |

---

## 10. Interview Q&A

**Q: What is the key difference between SIL and PIL?**
> SIL runs generated code on the host PC processor — fast, easy to debug. PIL runs the same code on the actual target ECU processor, exposing timing differences, word-size issues, and compiler-specific behavior. PIL catches bugs that SIL misses because the x86 host may hide issues present on ARM/PowerPC/TriCore targets.

**Q: Why is HIL more expensive than SIL/MIL?**
> HIL requires a real-time simulator (dSPACE/NI hardware, $50k–$500k), a real ECU, wiring harnesses, I/O conditioning boards, and real-time plant models validated against physical test data. Setup and maintenance costs are high, but HIL provides the highest confidence level before vehicle testing.

**Q: What is requirements-based testing vs coverage-based testing?**
> Requirements-based testing (RBT) verifies that every functional requirement has at least one test case. Structural coverage testing (MC/DC, branch coverage) verifies that all code paths are exercised. Both are required by ISO 26262 ASIL C/D — requirements coverage alone cannot guarantee code correctness, and structural coverage alone cannot guarantee all requirements are tested.

**Q: At which V-model level would you find a timing bug in auto-generated code?**
> Likely at **PIL** level — where the code runs on the actual target processor with real clock speeds and interrupt latencies. MIL and SIL run on host PC which has different timing characteristics, so processor-specific timing bugs only surface when running on target silicon.
