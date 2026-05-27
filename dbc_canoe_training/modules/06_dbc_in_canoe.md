# Module 06 — Using DBC in CANoe

> **Level**: Intermediate  
> **Duration**: ~4 hours  
> **Goal**: Configure CANoe with a DBC file, set up simulation, monitor signals, and run automated tests.

---

## 6.1 CANoe Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           CANoe Application                               │
├──────────────┬──────────────────────────────────────────────────────────┤
│              │                 Measurement Setup Window                   │
│  Network     │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  Database    │  │  Nodes    │  │  Buses   │  │  Panels  │               │
│  (.dbc)      │  │ (CAPL)   │  │(CAN cfg) │  │  (UI)    │               │
│  ─────────   │  └──────────┘  └──────────┘  └──────────┘               │
│  Messages    │       │              │                                     │
│  Signals     │       ▼              ▼                                     │
│  Nodes       │  ┌─────────────────────────────────┐                     │
│  Attributes  │  │      CAN Bus (Virtual / HW)      │                     │
│              │  │  ← CAN Interface (PCAN / VN1630) │                     │
└──────────────┴──┴─────────────────────────────────┴─────────────────────┘
```

### Key CANoe Windows

| Window | Purpose |
|--------|---------|
| **Measurement Setup** | Configure nodes, buses, hardware |
| **Trace** | Real-time decoded CAN frame list |
| **Graphics** | Signal value over time (oscilloscope-like) |
| **Write** | CAPL write() output, debug messages |
| **Data** | Variable/signal value table |
| **Statistics** | Bus load, error counts |
| **Test Report** | Automated test pass/fail results |

---

## 6.2 Importing DBC into CANoe

### Step-by-Step

```
1. Open CANoe
2. File → New Configuration (or open existing .cfg)
3. In Measurement Setup window:
   → Right-click on CAN network icon (the bus symbol)
   → Properties...
   → "Databases" tab
   → Click "Add" button
   → Browse to your .dbc file
   → Click Open
   → Click OK

4. CANoe will load:
   ✓ All messages with their IDs
   ✓ All signals with decoding info
   ✓ Node names for simulation
   ✓ Attributes (cycle time, send type)

5. Save configuration: File → Save As → [project].cfg
```

### Adding DBC via Drag-and-Drop

```
Simply drag the .dbc file from Windows Explorer
and drop it onto the CANoe Measurement Setup window.
```

### Multiple DBC Files (Multiple Buses)

```
For a vehicle with CAN-HS1, CAN-HS2, and CAN-FD1:
  1. Create separate DBC file per bus
  2. In CANoe Measurement Setup:
     → Add CAN network 1 → assign CAN-HS1.dbc
     → Add CAN network 2 → assign CAN-HS2.dbc
     → Add CAN FD network → assign CAN_FD1.dbc
  3. Configure hardware channels per network
```

---

## 6.3 Network Hardware Configuration

### Virtual CAN (No Hardware)

```
Use for simulation / development without hardware:
1. File → Hardware → Hardware Configuration
2. Set channel to: "Virtual CAN Channel 1"
3. Set bitrate: 500000
4. OK
```

### Physical Hardware (VN1630, VN1640, PCAN)

```
1. File → Hardware → Hardware Configuration
2. Select detected device (VN1630 Channel 1)
3. Set bitrate to match vehicle bus: 500000 or 1000000
4. For CAN FD: set nominal bitrate (500K) AND data bitrate (2M, 5M, or 8M)
5. Apply
```

### CAN FD Configuration

```
Hardware → Properties → CAN FD:
  Nominal bitrate:  500 Kbps
  Data bitrate:     2000 Kbps (or 5000, 8000)
  Transceiver:      HS (High Speed)
  FD ISO:           ON (ISO 11898-1:2015) ← most modern ECUs
  FD non-ISO:       OFF (legacy Bosch spec)
```

---

## 6.4 Simulation Setup — Node Configuration

### IL Node (Interaction Layer) — Auto-transmits Messages

CANoe can auto-transmit messages based on DBC attributes (GenMsgCycleTime, GenMsgSendType):

```
1. Measurement Setup → Add Node
2. Node type: "IL" (Interaction Layer)
3. Assign database: ADAS_HS1.dbc
4. Assign to bus: CAN 1
5. Node name: e.g., "AEB_Sim"

IL automatically:
  - Transmits all messages where ILUsed=Yes on the Tx node
  - Uses GenMsgCycleTime for timing
  - Uses GenSigStartValue for initial signal values
```

### CAPL Node — Custom Simulation Logic

```
1. Measurement Setup → Add Node
2. Node type: "CAPL"
3. Assign CAPL script file (.can)
4. Assign to bus and database
5. Configure in node properties

CAPL node can:
  - Override signal values
  - React to incoming messages
  - Generate test stimuli
  - Log specific signals
```

---

## 6.5 Trace Window — Real-Time Message Decoding

The Trace window shows all CAN frames in real-time with signal decoding.

### Trace Window Columns

```
┌────────┬───────┬──────┬────┬──────────┬──────────────────────────────────────┐
│ Time   │ Ch    │ ID   │ DLC│ Raw Data │ Decoded Signals                      │
├────────┼───────┼──────┼────┼──────────┼──────────────────────────────────────┤
│0.020.0 │ CAN 1 │ 0244 │ 8  │ 01 0A 70 │ AEB_Req: AEB_Active=1 Decel=1.0m/s² │
│        │       │      │    │ 27 00 05 │ Dist=0.99m TTC=0.50s State=WARNING   │
│0.030.0 │ CAN 1 │ 0300 │ 8  │ F0 05 00 │ VehicleStatus: EngSpeed=381.0rpm     │
│0.040.0 │ CAN 1 │ 0200 │ 8  │ D0 07 D0 │ WheelSpeed: FL=20.0 FR=20.0 ...     │
└────────┴───────┴──────┴────┴──────────┴──────────────────────────────────────┘
```

### Trace Window Configuration

```
Right-click → Column Configuration:
  ☑ Time
  ☑ Channel
  ☑ ID
  ☑ Name (shows message name from DBC)
  ☑ DLC
  ☑ Data (hex bytes)
  ☑ Signals (decoded values)
  ☑ Cycle time (time since last same ID)
  ☑ Dir (Tx/Rx)

Filter: Show only selected IDs
  → Trace → Filter → Add Message ID filter
  → Enter 0x244 to show only AEB_Req

Trigger: Start capture on specific event
  → Trace → Trigger → On message 0x244 with AEB_Active=1
```

---

## 6.6 Graphics Window — Signal Visualization

The Graphics window shows signal values over time as waveforms.

### Adding Signals to Graphics

```
1. Open Graphics window: Measurement → Graphics
2. Click "Signal" (magnifying glass icon)
3. Browse DBC database → select signal
   Example: AEB_Req → AEB_Decel_Req
4. Configure display:
   - Y-axis range: 0 to 30 (m/s²)
   - Color: Red
   - Interpolation: Step (for discrete signals) / Linear (for continuous)
5. Repeat for multiple signals on same or separate graphs

Useful multi-signal setups:
  Graph 1: WheelSpeed_FL, WheelSpeed_FR, WheelSpeed_RL, WheelSpeed_RR
  Graph 2: AEB_Active, AEB_State (enum display)
  Graph 3: EngineSpeed (RPM), ThrottlePos (%)
  Graph 4: SteeringAngle (degrees) with center line at 0
```

### Statistics in Graphics

```
Right-click on signal trace → Statistics:
  Min value, Max value, Mean, RMS
  Used to verify signal ranges against DBC specification
```

---

## 6.7 Write Window and Logging

### Write Window

Displays CAPL `write()` and `writeEx()` output:

```
Example CAPL code:
on message AEB_Req {
  write("[%f] AEB_Active=%d Decel=%.2f m/s2 Dist=%.2f m",
        this.time/100000.0,
        this.AEB_Active,
        this.AEB_Decel_Req * 0.1,
        this.AEB_Obj_Distance * 0.01);
}

Output in Write window:
  [0.0200] AEB_Active=1 Decel=1.00 m/s2 Dist=0.99 m
```

### Logging — MDF4 (.mf4) and ASC (.asc)

```
Setup logging:
  Measurement → Logging
  Add Logging Block:
    File format: MDF 4.1 (.mf4) ← recommended, binary, compact
                 ASC (.asc)     ← text format, easy to parse
    File path: [date]_[test_name].mf4
    
Start/Stop trigger:
    Manual (button) or on CAN message condition

After measurement:
    File → Open → open .mf4 in CANoe for replay
    Or: use MDF Converter for offline analysis
```

---

## 6.8 Panel Design — HMI Simulation

CANoe panels simulate vehicle HMI displays:

### Creating a Simple Dashboard Panel

```
1. View → Panels → Panel Editor
2. Add controls:
   
   Speedometer:
   → Insert → Gauge Instrument
   → Properties: Link to signal "WheelSpeed.WheelSpeed_FL" (or VehicleStatus.EngineSpeed)
   → Range: 0–200 km/h
   → Position: 100, 100
   
   RPM Gauge:
   → Insert → Gauge → link EngineSpeed → Range: 0–8000 rpm
   
   AEB Status Light:
   → Insert → LED Indicator
   → Link to AEB_Req.AEB_Active
   → Color when=1: Red, when=0: Gray
   → Label: "AEB ACTIVE"
   
   Door Status:
   → Insert → LED × 4 (FL, FR, RL, RR)
   → Link BCM_Status.DoorFL_Status, condition = "not 0 (open)"
   
3. File → Save Panel As: Dashboard_Sim_v1.xvp
4. In CANoe: Measurement → Panels → Add Panel → load .xvp
```

---

## 6.9 Replay Blocks — Replaying Logged Data

```
1. Measurement Setup → Add Replay Block
2. Select .blf or .asc file (logged CAN data)
3. Configure:
   Bus: CAN 1
   Start: Beginning of file
   Speed: 1× (real-time)
4. Start measurement → Replay block sends frames as if live

Use cases:
  - Replay field-recorded data for offline analysis
  - Reproduce intermittent bugs without vehicle
  - Run DBC validation against logged data
  - Test CAPL scripts with real vehicle traffic
```

---

## 6.10 Diagnostics Integration — UDS over CAN

### Setting Up UDS Diagnostics in CANoe

```
1. File → New → Add Diagnostic Description (.cdd or .odx)
   Or import ECU description from CANdelaStudio

2. Add Diagnostic Window:
   View → Diagnostics → Diagnostic Console

3. Configure ECU communication:
   ECU: AEB_ECU
   Request ID:  0x7E0
   Response ID: 0x7E8
   Transport:   ISO 15765-2 (ISO-TP over CAN)

4. In Diagnostic Console:
   → Select service: ReadDataByIdentifier (0x22)
   → DID: 0xF186 (Active Diagnostic Session)
   → Send → View response
```

### CAPL Diagnostic Example

```capl
on message DiagnosticResponse {
  if(this.byte(0) == 0x7F) {  // Negative Response
    write("NRC: 0x%02X for service 0x%02X", this.byte(2), this.byte(1));
  } else {
    write("Positive response received");
  }
}
```

---

## 6.11 Complete CANoe Lab — AEB Simulation

### Objective
Simulate an AEB event and verify signal behavior.

### Lab Setup

```
Files needed:
  ADAS_HS1.dbc  (created in Module 04/05)
  AEB_Sim.can   (CAPL simulation script)
  Dashboard.xvp (optional panel)

CANoe configuration:
  Network: CAN 1 (Virtual), 500 Kbps
  Database: ADAS_HS1.dbc
  Node 1: AEB_Sim (CAPL) — simulates AEB ECU
  Node 2: Vehicle_Sim (IL) — simulates other ECUs
```

### AEB_Sim.can (Simplified)

```capl
variables {
  msTimer aebTimer;
  float   objDistance = 100.0;    // Initial 100m
  float   vehicleSpeed = 80.0;    // 80 km/h
}

on start {
  setTimer(aebTimer, 20);  // 20ms cycle
}

on timer aebTimer {
  message AEB_Req msg;
  float ttc;
  
  // Simulate approaching obstacle
  objDistance -= (vehicleSpeed / 3.6 * 0.020);  // Distance decreases
  if(objDistance < 0) objDistance = 0;
  
  // Calculate TTC
  ttc = (vehicleSpeed > 0) ? (objDistance / (vehicleSpeed / 3.6)) : 0;
  
  // Set signal values
  msg.AEB_Active      = (ttc < 1.5 && objDistance < 20) ? 1 : 0;
  msg.AEB_Decel_Req   = (msg.AEB_Active) ? 50 : 0;  // raw 50 = 5.0 m/s²
  msg.AEB_Obj_Distance = (word)(objDistance / 0.01);  // raw
  msg.AEB_TTC         = (byte)(ttc / 0.01);
  msg.AEB_State       = (ttc < 1.0) ? 3 :
                        (ttc < 2.0) ? 2 :
                        (ttc < 3.0) ? 1 : 0;
  
  // Alive counter
  static int counter = 0;
  msg.Alive_Ctr_AEB = counter;
  counter = (counter + 1) % 15;
  
  output(msg);
  setTimer(aebTimer, 20);
}
```

### Expected Results in CANoe

```
Graphics window should show:
  - AEB_Obj_Distance: decreasing from 100m to 0m
  - AEB_TTC: decreasing as vehicle approaches
  - AEB_State: transitions 0→1→2→3 as TTC drops
  - AEB_Active: goes HIGH when TTC < 1.5s and dist < 20m
  - AEB_Decel_Req: jumps to 5.0 m/s² when active
```

---

## 6.12 CANoe Signal Access from CAPL

### Reading Signals (Two Methods)

```capl
// Method 1: Direct signal access (requires DBC)
on message AEB_Req {
  float decel;
  decel = this.AEB_Decel_Req * 0.1;   // Manual scaling
  // or:
  decel = getValue(AEB_Req::AEB_Decel_Req);  // Auto-scaled
}

// Method 2: Environment variable (sysvar)
// After assigning signal to sysvar in CANoe:
on sysvar sysvar::AEB_Decel_Req {
  write("AEB decel = %.2f m/s2", this.value);
}
```

### Writing Signal Values

```capl
// Set signal value and transmit
void SendAEB(float decel_ms2) {
  message AEB_Req msg;
  msg.AEB_Active    = (decel_ms2 > 0) ? 1 : 0;
  msg.AEB_Decel_Req = (byte)(decel_ms2 / 0.1);  // physical → raw
  output(msg);
}
```

---

## 6.13 CANoe Bus Statistics Window

```
View → Measurement → Statistics

Shows:
  Bus Load (%): current and peak
  Frame count: per message ID
  Error frames: total count
  Cycle violations: messages arriving too early/late

Use for:
  ✓ Verifying cycle times match DBC specification
  ✓ Detecting missing messages (timeout detection)
  ✓ Bus load analysis before adding new messages
```

---

## Module 06 — Knowledge Check

1. What file format does CANoe use to store its project configuration?
2. How do you add a second DBC file for a second CAN bus in CANoe?
3. What does "IL" node type do in CANoe Measurement Setup?
4. What two logging formats does CANoe support for CAN data?
5. In the Trace window, what does "Cycle time" column show?
6. Which CANoe window shows CAPL `write()` output?

**Answers:**
1. `.cfg` (CANoe Configuration file)
2. Add a second CAN network in Measurement Setup, then assign the second DBC file to it
3. Interaction Layer — auto-transmits messages using DBC cycle time and initial values
4. MDF4 (`.mf4`) binary format and ASC (`.asc`) text format
5. Time elapsed since the last occurrence of the same message ID
6. Write window
