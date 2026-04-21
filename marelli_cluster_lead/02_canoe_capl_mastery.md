# CANoe & CAPL Mastery — Instrument Cluster Validation

> **Role:** Cluster Lead — Marelli / LTTS Bangalore
> **Focus:** Hands-on CANoe setup, CAPL scripting patterns,
>            automated test design, environment configuration for IC validation

---

## 1. CANoe Workspace Setup for Cluster Testing

### 1.1 Typical Configuration

```
CANoe Project for Instrument Cluster:
├── Network databases
│   ├── Powertrain.dbc         (Speed, RPM, Engine, Gear signals)
│   ├── Body.dbc               (BCM, Door, Seatbelt, Handbrake)
│   ├── ADAS.dbc               (ABS, SRS, TPMS, ADAS signals)
│   └── Diagnostic.dbc         (UDS request/response IDs)
│
├── CAPL Scripts
│   ├── test_01_telltale_validation.can
│   ├── test_02_speedometer.can
│   ├── test_03_fuel_gauge.can
│   ├── test_04_can_timeout.can
│   ├── test_05_power_mode.can
│   ├── test_06_odometer_nvm.can
│   └── libs/
│       ├── cluster_helpers.cin  (common functions)
│       └── uds_client.cin       (UDS send/receive)
│
├── Test Modules (XML / .vts)
│   └── IC_System_TestSuite.vts
│
├── Panel
│   └── ClusterSimPanel.xvp     (Sliders for speed/RPM, buttons for faults)
│
└── Logging configuration
    └── IC_Validation.clp       (Trigger-based logging: on fault, on test fail)
```

### 1.2 Hardware Setup

```
Hardware options for cluster HIL testing:

Option A — Vector CAN Interface (software-only simulation):
    PC → Vector VN1610/VN1630 → CAN bus → Cluster bench

Option B — dSPACE HIL:
    dSPACE SCALEXIO → real power supply + switch matrix → Cluster bench
    Uses ControlDesk panels

Option C — Bench (most common for cluster lead role):
    PC (CANoe) → CANcaseXL → CAN HS (500kbps) + LIN → Cluster ECU on bench
    Power supply: 12V (battery sim) + ignition switch
    USB: for UDS/diagnostics
```

---

## 2. CAPL Language — Deep Reference

### 2.1 Event Handlers

```capl
/* === PROGRAM LIFECYCLE === */
on start        { /* Test suite begins */ }
on stop         { /* Clean up, write results */ }
on preStart     { /* Set initial signal values before bus traffic */ }

/* === CAN EVENTS === */
on message 0x3B3            { /* Raw message ID */ }
on message VehicleSpeed     { /* DBC message name */ }
on message *                { /* ALL messages on bus */ }
on message CAN1.0x3B3       { /* Specific channel */ }

/* === SIGNAL EVENTS === */
on signal VehicleSpeed.VehicleSpeed     { /* Signal value changed */ }
on signal (VehicleSpeed) VehicleSpeed   { /* Alternate syntax */ }

/* === TIMER EVENTS === */
msTimer  fastTimer;   /* milliseconds */
timer    slowTimer;   /* seconds */
on timer fastTimer    { /* ms timer expired */ }

/* === ENVIRONMENT VARIABLES (Panel interaction) === */
on envVar SpeedSlider { /* Panel slider moved */ }

/* === KEYBOARD === */
on key 's'  { write("s pressed"); }
on key F1   { }

/* === ERROR FRAMES === */
on errorFrame { write("Error frame at %f ms", timeNow() / 10.0); }

/* === BUS STATISTICS === */
on busOff CAN1 { write("CAN1 BUS-OFF detected!"); }
```

### 2.2 Variables and Data Types

```capl
variables {
    /* Primitive types */
    int     counter     = 0;
    long    timestamp   = 0;
    float   speed_kmh   = 0.0;
    double  precise_val = 0.0;
    byte    raw_byte    = 0x00;
    char    status_char = 'A';

    /* Arrays */
    byte    frame_data[8];
    int     gauge_steps[12] = {0,10,20,30,40,60,80,100,120,140,160,200};

    /* String */
    char    test_name[64] = "SpeedometerTest_001";

    /* Message variable */
    message 0x3B3 vspd_msg;
    message VehicleSpeed speed_msg;

    /* Timers */
    msTimer  debounceTimer;
    msTimer  timeoutWatchdog;

    /* Test tracking */
    int  total_tests   = 0;
    int  pass_count    = 0;
    int  fail_count    = 0;
}
```

### 2.3 Output Functions

```capl
/* === SEND CAN MESSAGES === */
output(vspd_msg);                    /* Send once */

/* Periodic send via event */
on message *                         { /* Not ideal for periodic */ }

/* Best approach — use CAPL timer for periodic send */
msTimer periodicTimer;
on start { setTimer(periodicTimer, 10); }   /* 10ms cycle */
on timer periodicTimer {
    output(vspd_msg);
    setTimer(periodicTimer, 10);
}

/* === SIGNAL ACCESS === */
$VehicleSpeed::VehicleSpeed = 100.0;  /* Set signal value → auto-encodes in message */
float v = $VehicleSpeed::VehicleSpeed; /* Read current signal value */

/* === ENVIRONMENT VARIABLE === */
putValue(SpeedDisplay, 120.5);   /* Write to panel */
float x = getValue(SpeedDisplay);

/* === DIAGNOSTICS === */
diagRequest ClusterDiag.ReadDataByID rdbi;
rdbi.SendRequest();
/* See on diagResponse handler below */
```

### 2.4 Cluster-Specific CAPL Patterns

```capl
/* ======================================================
 * Pattern 1: Multi-step test with state machine
 * ====================================================== */
variables {
    int   testStep = 0;
    msTimer stepTimer;
    message 0x3B3 vspd;
    message 0x316 eng;
}

on start {
    write("=== Startup Self-Check Test ===");
    /* KL15 OFF state: no bus traffic */
    setTimer(stepTimer, 2000);
}

on timer stepTimer {
    switch(testStep) {
        case 0:
            /* Send KL15 ON via BCM message */
            message 0x3A0 bcm;
            bcm.IgnitionStatus = 1;
            output(bcm);
            write("Step 0: KL15 ON sent");
            testStep = 1;
            setTimer(stepTimer, 3000);  /* Wait 3s for bulb check */
            break;
        case 1:
            write("Step 1: Verify bulb check complete (all telltales OFF)");
            /* In real bench: use camera or UDS read */
            /* Here: inject DBC verification signal */
            testStep = 2;
            setTimer(stepTimer, 500);
            break;
        case 2:
            vspd.VehicleSpeed = 6000;   /* 60 km/h raw */
            output(vspd);
            eng.EngineRPM = 6000;       /* 1500 RPM raw = 6000 × 0.25 */
            output(eng);
            write("Step 2: Speed=60 km/h, RPM=1500 injected");
            testStep = 3;
            setTimer(stepTimer, 1000);
            break;
        case 3:
            write("Step 3: Verify gauges moved — manual or camera check");
            testResult("IC_StartupSequence", "passed");
            break;
    }
}

/* ======================================================
 * Pattern 2: Signal sweep for gauge linearity
 * ====================================================== */
variables {
    int    sweepStep   = 0;
    int    sweepValues[13] = {0,10,20,30,50,60,80,100,120,140,160,180,200};
    msTimer sweepTimer;
    message 0x3B3 spd;
}

on start {
    write("=== Speedometer Sweep Test ===");
    sweepStep = 0;
    setTimer(sweepTimer, 500);
}

on timer sweepTimer {
    if (sweepStep < elcount(sweepValues)) {
        int raw = sweepValues[sweepStep] * 100;  /* km/h → raw (factor 0.01) */
        spd.VehicleSpeed = raw;
        output(spd);
        write("Speed injected: %d km/h (raw=%d)", sweepValues[sweepStep], raw);
        sweepStep++;
        setTimer(sweepTimer, 1500);  /* 1.5s dwell per step → camera captures cluster */
    } else {
        write("=== Sweep Test Complete ===");
    }
}

/* ======================================================
 * Pattern 3: Telltale matrix test (all faults in sequence)
 * ====================================================== */
int telltaleStep = 0;
msTimer tlTimer;

on start { setTimer(tlTimer, 200); }

on timer tlTimer {
    switch(telltaleStep) {
        case 0: inject_abs_fault(1);   break;
        case 1: inject_abs_fault(0);   break;  /* Clear */
        case 2: inject_srs_fault(1);   break;
        case 3: inject_srs_fault(0);   break;
        case 4: inject_low_fuel(1);    break;
        case 5: inject_low_fuel(0);    break;
        case 6: inject_tpms_warn(1);   break;
        case 7: inject_tpms_warn(0);   break;
        default:
            write("Telltale matrix test complete. %d steps executed.", telltaleStep);
            return;
    }
    telltaleStep++;
    setTimer(tlTimer, 500);
}

/* Helper functions (inject fault signals) */
void inject_abs_fault(int state) {
    message 0x3A5 abs_msg;
    abs_msg.ABS_Fault = state;
    output(abs_msg);
    write("ABS_Fault = %d", state);
}

void inject_srs_fault(int state) {
    message 0x3A6 srs_msg;
    srs_msg.SRS_Fault = state;
    output(srs_msg);
}

void inject_low_fuel(int state) {
    message 0x34A fuel_msg;
    fuel_msg.LowFuelWarning = state;
    fuel_msg.FuelLevel_pct  = state ? 5 : 50;
    output(fuel_msg);
}

void inject_tpms_warn(int state) {
    message 0x3C0 tpms_msg;
    tpms_msg.TyreWarn = state;
    output(tpms_msg);
}

/* ======================================================
 * Pattern 4: CAN Timeout test (stop sending a message)
 * ====================================================== */
variables {
    msTimer txTimer;
    msTimer stopTimer;
    message 0x3B3 speedMsg;
    int sendActive = 1;
}

on start {
    speedMsg.VehicleSpeed = 5000;  /* 50 km/h */
    setTimer(txTimer, 10);
    setTimer(stopTimer, 5000);  /* Stop after 5 seconds */
    write("Speed TX started at 50 km/h");
}

on timer txTimer {
    if (sendActive == 1) {
        output(speedMsg);
        setTimer(txTimer, 10);
    }
}

on timer stopTimer {
    sendActive = 0;
    write("Speed TX STOPPED. Cluster timeout should trigger in ~200ms");
    /* Observe cluster: needle to 0 or '--', CAN network telltale activates */
    setTimer(stopTimer, 3000);  /* Check again in 3 seconds  */
}

/* ======================================================
 * Pattern 5: UDS Diagnostic Read (Odometer)
 * ====================================================== */
on start {
    diagRequest ClusterDiag.ReadDataByIdentifier rdbi_req;
    rdbi_req.suppressPosRspMsgIndicationBit = 0;
    rdbi_req.dataIdentifier = 0xF400;  /* Odometer DID (OEM specific) */
    rdbi_req.SendRequest();
    write("UDS READ odometer request sent (DID 0xF400)");
}

on diagResponse ClusterDiag.ReadDataByIdentifier {
    long odo_raw;
    if (this.IsPositiveResponse()) {
        odo_raw = this.GetParameter("Odometer_km");
        write("Odometer = %d km", odo_raw);
    } else {
        write("FAIL: Negative response NRC = 0x%X", this.NRC());
    }
}
```

---

## 3. CANoe Test Module — Formal Test Execution

### 3.1 Test Module Structure

```capl
/* === Test Module: IC_Speedometer_TestModule.can === */
testcase TC_SPD_001_Accuracy_60kph () {
    float injected_kmh = 60.0;
    float displayed_kmh;
    float tolerance    = 3.0;   /* EU Reg 39: ±3 km/h */

    /* Action */
    $VehicleSpeed::VehicleSpeed = injected_kmh;
    TestWaitForTimeout(2000);   /* 2s for cluster to update */

    /* Read back cluster display value via UDS */
    displayed_kmh = read_cluster_speed_via_uds();

    /* Evaluate */
    if (abs(displayed_kmh - injected_kmh) <= tolerance) {
        TestStep("Speed accuracy at 60 km/h", "passed",
                 "Displayed=%.1f, Injected=%.1f, Tol=±%.1f", displayed_kmh, injected_kmh, tolerance);
    } else {
        TestStep("Speed accuracy at 60 km/h", "failed",
                 "Displayed=%.1f, Injected=%.1f, Delta=%.1f", displayed_kmh, injected_kmh,
                 abs(displayed_kmh - injected_kmh));
    }
}

testcase TC_TEL_001_ABS_Activation () {
    /* Precondition */
    $ABS_Status::ABS_Fault = 0;
    TestWaitForTimeout(500);

    /* Stimulate */
    $ABS_Status::ABS_Fault = 1;
    TestWaitForTimeout(200);   /* 200ms activation expected */

    /* Check (via UDS or direct feedback) */
    int absTellStatus = read_telltale_status_via_uds(TELL_ABS);
    TestStepPass("ABS Telltale activation", (absTellStatus == 1) ? "passed" : "failed",
                 "ABS telltale status = %d", absTellStatus);

    /* Cleanup */
    $ABS_Status::ABS_Fault = 0;
}

testcase TC_NVM_001_Odometer_Retention () {
    long odo_before = read_odometer_uds();

    /* Simulate driving: inject 60km/h for 1 min = 1 km */
    $VehicleSpeed::VehicleSpeed = 60.0;
    TestWaitForTimeout(60000);   /* 60 seconds */
    $VehicleSpeed::VehicleSpeed = 0.0;

    /* Key off and on */
    simulate_kl15_off();
    TestWaitForTimeout(3000);
    simulate_kl15_on();
    TestWaitForTimeout(3000);

    long odo_after = read_odometer_uds();
    float delta = odo_after - odo_before;

    /* Expect 1.0 km (±0.1 km tolerance) */
    TestStepPass("Odometer NVM retention",
                 (delta >= 0.9 && delta <= 1.1) ? "passed" : "failed",
                 "Before=%d After=%d Delta=%.2f km", odo_before, odo_after, delta);
}
```

---

## 4. Common CANoe Panels for Cluster Testing

```
Panel Design for Cluster Lead:

[Vehicle Speed]    Slider 0–300 km/h  → mapped to $VehicleSpeed::VehicleSpeed
[Engine RPM]       Slider 0–8000 RPM  → mapped to $EngineStatus::EngineRPM
[Fuel Level]       Slider 0–100 %     → mapped to $FuelLevel::FuelLevel_pct
[Gear]             Dropdown P/R/N/D/1–6 → mapped to $TCU_Info::CurrentGear

[FAULTS]
[ABS Fault]        Toggle → $ABS_Status::ABS_Fault
[SRS Fault]        Toggle → $SRS_Status::SRS_Fault
[Low Fuel]         Button → sets FuelLevel < reserve threshold
[TPMS FL Low]      Toggle → $TPMS_Status::TyrePressure_FL

[POWER]
[KL15 ON/OFF]      Button → sends BCM ignition signal
[Battery Disc]     Button → stops all CAN TX (simulate disconnect)

[RUN TESTS]
[Run All Tests]    Button → triggers Test Module execution
[Run Telltale]     Button → triggers individual test group
```

---

## 5. CAPL Library Functions (.cin) — Reusable Across Tests

```capl
/* === File: libs/cluster_helpers.cin === */

/* Read cluster displayed speed via UDS (OEM DID 0xF110 example) */
float read_cluster_speed_via_uds() {
    diagRequest ClusterDiag.ReadDataByIdentifier req;
    req.dataIdentifier = 0xF110;
    req.SendRequest();
    /* Block and return — simplified for illustration */
    return getDiagResponseFloat("DisplayedSpeed_kmh");
}

/* Read telltale status byte via UDS */
int read_telltale_status_via_uds(int telltale_id) {
    diagRequest ClusterDiag.ReadDataByIdentifier req;
    req.dataIdentifier = 0xF120;
    req.SendRequest();
    return getDiagResponseBit("TelltaleStatus", telltale_id);
}

/* Read odometer via UDS DID 0xF400 */
long read_odometer_uds() {
    diagRequest ClusterDiag.ReadDataByIdentifier req;
    req.dataIdentifier = 0xF400;
    req.SendRequest();
    return getDiagResponseLong("Odometer_km");
}

/* KL15 control via BCM message */
void simulate_kl15_on() {
    message 0x3A0 bcm;
    bcm.IgnitionStatus = 1;
    output(bcm);
    write("[POWER] KL15 ON sent");
}

void simulate_kl15_off() {
    message 0x3A0 bcm;
    bcm.IgnitionStatus = 0;
    output(bcm);
    write("[POWER] KL15 OFF sent");
}

/* Log test result to custom output */
void log_test_result(char name[], int passed, char detail[]) {
    if (passed) {
        write("PASS | %s | %s", name, detail);
    } else {
        write("FAIL | %s | %s", name, detail);
    }
}
```

---

## 6. Common CAPL Interview Questions & Answers

| Question | Answer |
|---|---|
| What is `on message *`? | Handler triggered for every received CAN message on the bus |
| Difference between `output()` and cyclic send? | `output()` is one-shot. Cyclic requires a timer loop re-calling `output()` |
| How do you access a signal value? | `$MessageName::SignalName` or `getValue()` from environment variable |
| What is a `.cin` file? | A CAPL include file — reusable library of functions shared across CAPL scripts |
| How do you inject a fault message? | Declare message variable, set fault signal bit = 1, call `output()` |
| How do you simulate CAN timeout? | Stop the timer loop sending that message — ECU sees no frames → timeout |
| What is `TestWaitForTimeout`? | CAPL test module function that pauses test execution for N milliseconds |
| What is `testcase`? | A CAPL test module test function that runs as a formal test step with pass/fail |
| How to read UDS data in CAPL? | Use `diagRequest` object, call `SendRequest()`, handle `on diagResponse` |
| What does `elcount()` do? | Returns the number of elements in an array |
| How to write to trace window? | `write("message %d", value);` |
| What is `putValue()`? | Writes a value to a CANoe environment variable (panel/system variable) |

---

---

## 7. Advanced CAPL Techniques

### 7.1 Environment Variables and System Variables

```capl
/*
Environment variables (EnvVar) are shared between CAPL, Panels, and Symbols.
System variables (SysVar) are in the ::namespace and are available across
all measurement setups in the same CANoe project.
*/

/* Declare in CAPL (also must be defined in CANoe Symbols window): */
variables {
    msTimer  pollTimer;
    int      g_test_running = 0;
}

/* READ an environment variable (set by Panel slider): */
on envVar SpeedSlider {
    float speed = getValue(this);
    $VehicleSpeed::VehicleSpeed = speed;
}

/* WRITE to a system variable (to update Panel display): */
on timer pollTimer {
    float displayed = $VehicleSpeed::VehicleSpeed;
    putValue(sysvar::ClusterDisplay::SpeedReading, displayed);
    setTimer(pollTimer, 100);   /* poll every 100ms */
}

/* Trigger on system variable change: */
on sysvar ClusterDisplay::FaultButtonPressed {
    if (getValue(this) == 1) {
        inject_abs_fault();
    }
}
```

### 7.2 CAPL Error Handling and Defensive Coding

```capl
/*
CAPL has no exceptions. You must handle errors manually.
Best practices for robust cluster test scripts:
*/

/* 1. Always check diagResponse result code */
on diagResponse ClusterDiag.ReadDataByIdentifier {
    if (this.result != 0) {
        write("ERROR: UDS response failed, result code = %d", this.result);
        TestStepFail("UDS_Read", "Diagnostic request did not receive positive response");
        return;
    }
    /* proceed with data extraction */
}

/* 2. Guard against zero division in signal scaling */
float safe_decode_speed(long raw_value, float factor) {
    if (factor == 0.0) {
        write("ERROR: factor is zero — DBC error");
        return -1.0;
    }
    return raw_value * factor;
}

/* 3. Timeout guard on expected CAN response */
msTimer responseTimeout;
int    g_response_received = 0;

void wait_for_response_or_timeout(int timeout_ms) {
    g_response_received = 0;
    setTimer(responseTimeout, timeout_ms);
}

on timer responseTimeout {
    if (!g_response_received) {
        write("TIMEOUT: Expected response not received within timer period");
        TestStepFail("ResponseTimeout", "No CAN response within expected window");
    }
}

on message 0x726 {  /* Cluster UDS response */
    g_response_received = 1;
    cancelTimer(responseTimeout);
}
```

### 7.3 CAPL — Multi-Channel Handling

```capl
/*
CANoe can have multiple CAN channels (CH1 = Powertrain, CH2 = Body).
In CAPL, channel is accessed via message object properties.
*/

variables {
    message 0x3B3 speed_msg;     /* auto-routes to channel per DBC assignment */
    message CAN1.0x3B3 speed_ch1; /* explicit channel 1 */
    message CAN2.0x3A0 bcm_ch2;  /* explicit channel 2 */
}

on start {
    speed_ch1.VehicleSpeed = 5000;  /* raw = 50 km/h */
    output(speed_ch1);              /* sends on CAN channel 1 only */

    bcm_ch2.IgnitionStatus = 1;
    output(bcm_ch2);                /* sends on CAN channel 2 only */
}

/* Listen to a specific channel: */
on message CAN2.* {
    write("Body bus message: 0x%X  DLC=%d", this.id, this.dlc);
}
```

### 7.4 CAPL — Structured Test Parametrisation

```capl
/*
Run the same test logic with different input parameters.
Use arrays to drive test tables — avoids copy-paste of test code.
*/

typedef struct {
    float  inject_kmh;
    float  expected_kmh;
    float  tolerance;
    char   tc_id[16];
} SpeedTestPoint_t;

SpeedTestPoint_t speed_tests[8] = {
    {  0.0,   0.0, 2.0, "TC_SPD_001"},
    { 30.0,  30.0, 2.0, "TC_SPD_002"},
    { 60.0,  60.0, 2.0, "TC_SPD_003"},
    {100.0, 100.0, 3.0, "TC_SPD_004"},
    {120.0, 120.0, 3.0, "TC_SPD_005"},
    {160.0, 160.0, 4.0, "TC_SPD_006"},
    {200.0, 200.0, 5.0, "TC_SPD_007"},
    {250.0, 250.0, 5.0, "TC_SPD_008"}
};

testcase TC_SPD_SWEEP () {
    int i;
    for (i = 0; i < elcount(speed_tests); i++) {
        SpeedTestPoint_t pt = speed_tests[i];

        /* Inject signal */
        $VehicleSpeed::VehicleSpeed = pt.inject_kmh;
        TestWaitForTimeout(500);

        /* Read back (via UDS or system variable from panel) */
        float displayed = getValue(sysvar::ClusterDisplay::SpeedReading);

        float diff = displayed - pt.expected_kmh;
        if (diff < 0) diff = -diff;  /* abs() */

        if (diff <= pt.tolerance) {
            TestStep(pt.tc_id, "passed", "Inject=%.1f Display=%.1f Tol=±%.1f",
                     pt.inject_kmh, displayed, pt.tolerance);
        } else {
            TestStep(pt.tc_id, "failed",
                     "Inject=%.1f Display=%.1f Error=%.1f > Tol=%.1f",
                     pt.inject_kmh, displayed, diff, pt.tolerance);
        }
    }
}
```

---

## 8. CANoe Logging Configuration for Cluster Testing

### 8.1 Trigger-Based Logging

```
Goal: Capture only the relevant window around a failure event.
      Avoids multi-GB log files from full test runs.

CANoe Logging Block Trigger Setup:

Pre-trigger: 5 seconds  (captures events BEFORE failure)
Post-trigger: 10 seconds (captures recovery behaviour)

Trigger conditions (any of):
  - CAN Error Frame received
  - Message 0x3B3 not received for > 200ms  (timeout)
  - Signal ABS_Fault transitions from 0→1
  - User-defined CAPL trigger: call triggerLogging() from testcase

CAPL trigger call:
  triggerStart();   /* begins logging from pre-trigger buffer */
  /* ... test action ... */
  triggerStop();    /* ends logging and saves file */
```

### 8.2 Logging Filter Configuration

```
To keep log files manageable, exclude irrelevant messages:

Include:
  - 0x3B3 (VehicleSpeed) — 10ms cycle, core signal
  - 0x316 (EngineStatus) — 10ms cycle
  - 0x34A (FuelLevel) — 100ms cycle
  - 0x3A5, 0x3A6, 0x3A0, 0x3C0 — all fault/status messages
  - 0x7xx range — UDS diagnostic messages

Exclude:
  - 0x400–0x4FF — Infotainment heartbeat (irrelevant for IC HW validation)
  - 0x600+ — System-level keep-alive (noisy, low value)

CANoe Filter File: IC_Validation_filter.clf
  Applied to Trace window AND to logging block simultaneously
```

---

## 9. CANoe XML Test Report Structure

```
When using CANoe Test Module (.vts), results are auto-generated in:
  - HTML report
  - XML (parsable by CI tools)
  - PDF (for OEM delivery)

Typical test result XML structure:

<TestReport>
  <TestSuite name="IC_System_TestSuite">
    <TestCase id="TC_SPD_001" name="Speed 60kmh" result="Pass">
      <TestStep id="1" result="Pass" timestamp="09:14:22.341">
        Inject 60 km/h — VehicleSpeed raw = 6000
      </TestStep>
      <TestStep id="2" result="Pass" timestamp="09:14:22.842">
        Display reads 60 km/h — within ±2 km/h tolerance
      </TestStep>
    </TestCase>
    <TestCase id="TC_TEL_001" name="ABS Telltale Active" result="Fail">
      <TestStep id="1" result="Fail" timestamp="09:16:05.100">
        Expected: ABS telltale ON. Actual: telltale OFF.
        Defect: CLU-1024
      </TestStep>
    </TestCase>
  </TestSuite>
  <Summary total="2" pass="1" fail="1" passRate="50.0%"/>
</TestReport>

Parse XML in Python for CI dashboard:
  import xml.etree.ElementTree as ET
  tree = ET.parse("IC_TestReport.xml")
  root = tree.getroot()
  for tc in root.findall(".//TestCase"):
      print(tc.attrib["id"], tc.attrib["result"])
```

---

## 10. CANoe vs CANalyzer — When to Use What

| Feature | CANoe | CANalyzer |
|---|---|---|
| CAPL scripting | ✅ Full support | ✅ Limited (no test module) |
| Test Modules (.vts) | ✅ Yes | ❌ No |
| Simulation nodes | ✅ Can simulate ECUs | ❌ No |
| Diagnostic (UDS) | ✅ via Diagnostics window | ✅ Basic |
| Logging | ✅ Trigger-based, filtered | ✅ Basic logging |
| Panel / UI | ✅ Panels with sliders/buttons | ❌ No |
| LIN bus | ✅ With LIN add-on | ✅ LIN version available |
| Use case | Full test automation | Quick trace analysis |
| Licence cost | Higher | Lower |

**Cluster Lead Practice:** Use CANoe for all test automation and execution. Use CANalyzer for quick ad-hoc bus monitoring when CANoe workspace is being prepared.

---

## 11. Frequently Made CAPL Mistakes to Avoid

| Mistake | Problem | Correct Approach |
|---|---|---|
| Not cancelling timer before restart | Timer callback fires multiple times | `cancelTimer(t); setTimer(t, 200);` |
| Using `=` in `on message` condition | No condition filter in CAPL message handler | Use `if (this.signal == x)` inside handler |
| Accessing signal from wrong channel | Reads wrong bus signal | Use `CAN1.` prefix or verify DBC channel assignment |
| Blocking in `on message` handler | Causes bus queue backlog | Keep handlers short — use timer for delays |
| Not resetting state flags between tests | Previous test state leaks into next | `resetVars()` call in `on stop` or between testcases |
| Hardcoding CAN IDs without DBC names | Script breaks when DBC version changes | Always use DBC symbolic name `VehicleSpeed` not `0x3B3` |

---

*File: 02_canoe_capl_mastery.md | marelli_cluster_lead series*
