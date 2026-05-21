from pathlib import Path
import csv
import textwrap


ROOT = Path("MG_HECTOR_INFOTAINMENT_VALIDATION")


MODULES = [
    ("01_AUTOMOTIVE_BASICS", "Automotive Basics", "vehicle networks, ECU roles, validation mindset"),
    ("02_INFOTAINMENT_ARCHITECTURE", "Infotainment Architecture", "IVI hardware, software, connectivity, audio and display domains"),
    ("03_BENCH_SETUP", "Bench Setup", "power, harnessing, ignition, CAN, Ethernet and lab workflow"),
    ("04_VECTOR_CANOE", "Vector CANoe", "configuration, measurement, rest bus simulation and test modules"),
    ("05_CAPL_PROGRAMMING", "CAPL Programming", "event-driven simulation, diagnostics and automation"),
    ("06_CAN_PROTOCOL", "CAN Protocol", "CAN frames, DBC signals, timing, bus load and trace analysis"),
    ("07_AUTOMOTIVE_ETHERNET", "Automotive Ethernet", "DoIP, SOME/IP, service discovery, VLANs and packet capture"),
    ("08_ANDROID_AUTOMOTIVE", "Android Automotive", "AAOS stack, services, adb, HAL, apps and vehicle properties"),
    ("09_IVI_FEATURES", "IVI Features", "radio, media, phone, navigation, UI, profiles and notifications"),
    ("10_BLUETOOTH_VALIDATION", "Bluetooth Validation", "pairing, reconnection, calling, A2DP, PBAP and stress cases"),
    ("11_WIFI_VALIDATION", "WiFi Validation", "hotspot, client mode, roaming, throughput and interruption tests"),
    ("12_USB_VALIDATION", "USB Validation", "enumeration, media indexing, projection, power and fault cases"),
    ("13_CARPLAY_ANDROID_AUTO", "CarPlay Android Auto", "projection protocol validation and recovery behavior"),
    ("14_AUDIO_VALIDATION", "Audio Validation", "routing, focus, latency, distortion, prompts and ducking"),
    ("15_VIDEO_VALIDATION", "Video Validation", "playback, camera video path, frame drops and latency"),
    ("16_NAVIGATION_SYSTEM", "Navigation System", "GNSS, map, route, guidance, dead reckoning and voice prompts"),
    ("17_REVERSE_CAMERA", "Reverse Camera", "reverse trigger, camera switching, guidelines and latency"),
    ("18_360_CAMERA_SYSTEM", "360 Camera System", "surround view stitching, calibration and fault injection"),
    ("19_CLUSTER_INTEGRATION", "Cluster Integration", "warnings, tell-tales, alerts and signal synchronization"),
    ("20_STEERING_SWITCH_CONTROLS", "Steering Switch Controls", "short press, long press, media, volume and voice buttons"),
    ("21_HVAC_INTEGRATION", "HVAC Integration", "climate signal display, controls and status synchronization"),
    ("22_CAN_SIGNAL_SIMULATION", "CAN Signal Simulation", "vehicle state models, timing and DBC-driven simulation"),
    ("23_UDS_DIAGNOSTICS", "UDS Diagnostics", "sessions, DIDs, DTCs, reset and security access"),
    ("24_ECU_FLASHING", "ECU Flashing", "programming session, erase, transfer data and recovery"),
    ("25_OTA_TESTING", "OTA Testing", "download, install, rollback, interruption and post-update validation"),
    ("26_PERFORMANCE_TESTING", "Performance Testing", "boot time, CPU, memory, UI latency and app launch KPIs"),
    ("27_STRESS_TESTING", "Stress Testing", "reboots, playback endurance, connect cycles and bus overload"),
    ("28_MEMORY_LEAK_ANALYSIS", "Memory Leak Analysis", "heap, native memory, threads, binder and resource leaks"),
    ("29_LOG_ANALYSIS", "Log Analysis", "CAN, logcat, kernel, Ethernet, ECU trace and correlation"),
    ("30_AUTOMATION_FRAMEWORK", "Automation Framework", "pytest, CANoe COM, adb, reports and CI pipelines"),
    ("31_PYTHON_AUTOMATION", "Python Automation", "test orchestration, parsers, CAN APIs and lab utilities"),
    ("32_TEST_CASE_DESIGN", "Test Case Design", "requirements, equivalence, boundary, negative and traceable tests"),
    ("33_REQUIREMENT_TRACEABILITY", "Requirement Traceability", "RTM, coverage, evidence and release gates"),
    ("34_DEFECT_MANAGEMENT", "Defect Management", "Jira-quality defects, severity, triage and retest workflow"),
    ("35_VECTOR_TOOLS", "Vector Tools", "CANalyzer, CANoe, CANape, vTESTstudio and DBC handling"),
    ("36_CANOE_AUTOMATION", "CANoe Automation", "test modules, XML reports, signal verification and regression"),
    ("37_HIL_SIL_SETUP", "HIL SIL Setup", "simulation layers, HIL racks, SIL stubs and limitations"),
    ("38_VEHICLE_SIGNAL_SIMULATION", "Vehicle Signal Simulation", "speed, gear, doors, power mode, lamps and network states"),
    ("39_POWER_MODE_VALIDATION", "Power Mode Validation", "KL15, KL30, ACC, crank, shutdown and low power mode"),
    ("40_SLEEP_WAKEUP_TESTING", "Sleep Wakeup Testing", "sleep current, wake triggers, CAN wakeup and retention"),
    ("41_BOOT_TIME_ANALYSIS", "Boot Time Analysis", "cold, warm, fast boot and Android initialization KPIs"),
    ("42_ANDROID_LOGCAT", "Android Logcat", "adb, filters, crash, ANR and event correlation"),
    ("43_LINUX_DEBUGGING", "Linux Debugging", "systemd, kernel logs, processes, sockets and shell diagnostics"),
    ("44_REAL_WORLD_ISSUES", "Real World Issues", "production issue patterns, RCA and escalation workflow"),
    ("45_INTERVIEW_PREPARATION", "Interview Preparation", "CANoe, CAPL, UDS, Android, network and debugging interviews"),
    ("46_SYSTEM_DESIGN", "System Design", "bench, automation, diagnostics and validation architecture"),
    ("47_CYBERSECURITY_BASICS", "Cybersecurity Basics", "threat model, secure diagnostics, OTA and interface hardening"),
    ("48_FUNCTIONAL_SAFETY", "Functional Safety", "safety goals, camera availability, warnings and validation evidence"),
    ("49_REAL_PROJECTS", "Real Projects", "end-to-end bench and automation projects"),
    ("50_CAPSTONE_BENCH_PROJECT", "Capstone Bench Project", "complete MG Hector-style IVI validation release simulation"),
]


SIGNALS = [
    ("0x100", "BCM_PowerMode", "PowerMode", "2", "10 ms", "0=OFF,1=ACC,2=IGN,3=CRANK"),
    ("0x101", "BCM_DoorStatus", "DriverDoorAjar", "1", "50 ms", "0=closed,1=open"),
    ("0x120", "VCU_VehicleSpeed", "VehicleSpeed_kph", "16", "20 ms", "0..240 kph, scale 0.01"),
    ("0x130", "TCU_GearStatus", "GearPosition", "4", "20 ms", "0=P,1=R,2=N,3=D"),
    ("0x180", "SWC_Buttons", "SWC_KeyCode", "8", "20 ms event", "volume, track, phone, voice"),
    ("0x220", "BCM_LampStatus", "TurnIndicator", "2", "100 ms", "left/right/hazard"),
    ("0x300", "IVI_Heartbeat", "IVI_AliveCounter", "4", "100 ms", "rolling counter"),
    ("0x301", "IVI_Status", "IVI_BootState", "3", "100 ms", "booting, ready, diag, shutdown"),
]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def module_slug(folder: str) -> str:
    return folder.lower()


def readme(folder: str, title: str, focus: str) -> str:
    return f"""
    # {title}

    This module is part of the MG Hector-style infotainment validation lab pack. It is written for bench validation engineers who need to connect CANoe, CAPL, Python, adb, diagnostic services and OEM release evidence into one working process.

    Scope: {focus}.

    Important lab note: MG Hector production networks, DBC files, security seeds, calibration data and camera/audio implementation details are OEM proprietary. The files here use representative OEM-style data so you can practice the workflow safely. Replace IDs, DIDs, signal names and timing with the project-specific database when you work on an actual program.

    ## Production Workflow

    1. Review the requirement and map it to vehicle state, signal, diagnostic and user interaction dependencies.
    2. Configure bench power, wakeup lines, CAN channels, Ethernet, USB and adb before powering the IVI.
    3. Run a smoke measurement in CANoe and verify heartbeat, network management and power mode behavior.
    4. Execute functional, negative, boundary, stress and recovery test cases.
    5. Capture synchronized evidence: CANoe trace, CANoe report, adb logcat, kernel logs, screenshots or video, and bench photos.
    6. Perform first-level RCA before raising a defect: input correctness, timing, bus load, ECU response, IVI service state, app state and persistence.

    ## Folder Contents

    - `01_theory_notes.md`: deep notes and validation reasoning.
    - `02_bench_setup_diagrams.md`: Mermaid diagrams for lab wiring and data flow.
    - `03_canoe_configuration_examples.md`: CANoe setup patterns.
    - `capl/`: CAPL simulation and checks.
    - `python/`: automation harness examples.
    - `logs/`: representative CAN traces for parser and RCA practice.
    - `uds/`: diagnostics requests, expected responses and negative cases.
    - `test_cases/`: OEM-style test cases.
    - `debugging/`: failure scenarios and RCA examples.
    - `reports/` and `traceability/`: validation evidence templates.
    """


def theory(title: str, focus: str) -> str:
    return f"""
    # Theory Notes: {title}

    ## Engineering View

    In production infotainment validation, {title.lower()} is never tested as an isolated feature only. It is validated as a chain of vehicle signals, middleware state, Android/Linux services, app behavior, persistence, user interaction and recovery behavior after power or connectivity disturbance.

    Core focus: {focus}.

    ## Automotive Use Case

    A customer action such as selecting reverse gear, pressing a steering switch, pairing a phone or starting navigation becomes a validation problem across:

    - Vehicle input source and signal timing.
    - Network delivery and timeout handling.
    - IVI service reaction time.
    - UI/audio/video output correctness.
    - Diagnostic state and DTC behavior.
    - Logs and evidence needed for production triage.

    ## MG Hector-Style Feature Explanation

    Use this as an MG Hector-style connected SUV infotainment bench. The representative head unit receives BCM, cluster, powertrain, HVAC, steering switch and camera gateway information over CAN and Ethernet. The IVI exposes user-facing features such as media, navigation, phone, projection, camera display, vehicle settings and connected services. Real program values must come from the released DBC, ARXML, diagnostic specification and system requirements.

    ## Bench Setup Workflow

    1. Confirm power rails: KL30 permanent battery, KL15 ignition, ACC/accessory if available and ground reference.
    2. Confirm communication: CAN termination, channel mapping, baud rate, database attachment and Ethernet link.
    3. Start CANoe measurement with rest bus nodes active before IVI wakeup when the test requires realistic network availability.
    4. Apply the vehicle state sequence and verify IVI response against KPI.
    5. Capture logs from CANoe and Android/Linux at the same timestamp.

    ## CANoe Setup

    - Assign network databases to physical or virtual CAN channels.
    - Model unavailable ECUs as rest bus simulation nodes.
    - Add panels for power mode, gear, speed, door, steering switch and DTC injection.
    - Enable BLF/ASC logging with test name, build ID and bench ID in the filename.
    - Use Test Setup or vTESTstudio for automated pass/fail verdicts.

    ## UDS Validation

    Basic diagnostic checks for each feature:

    - `0x10 0x03`: extended diagnostic session.
    - `0x22 DID`: read software, hardware, calibration and feature-specific DIDs.
    - `0x19 0x02`: read DTC by status mask after fault injection.
    - `0x11 0x01`: ECU reset only when the test plan allows it.

    ## Production Debugging

    Start with the evidence timeline. If the IVI output is wrong, verify input correctness first, then network timing, then service logs, then UI or app layer. A good RCA proves both the fault and the non-fault boundaries.

    ## OEM Validation Process

    - Requirement review and ambiguity closure.
    - Test design review with feature owner.
    - Bench dry run and environment baseline.
    - Formal execution with released build.
    - Defect triage with attached logs and reproduction rate.
    - Regression after fix and release sign-off.

    ## Interview Questions

    1. How would you prove the issue is in the IVI and not the simulated ECU?
    2. What evidence do you attach to a production defect?
    3. How do you handle a requirement that does not specify timeout behavior?
    4. What is the difference between functional, integration and system validation for this module?
    5. How do CANoe, CAPL and adb complement each other during RCA?

    ## Failure Scenarios

    - Missing or delayed CAN signal.
    - Incorrect power mode transition.
    - IVI service crash or ANR.
    - Timeout threshold mismatch between spec and implementation.
    - Persistence failure after sleep, wakeup or OTA.

    ## Performance Optimization

    Measure before optimizing. Track signal-to-output latency, CPU, memory, binder load, app launch time, frame drops and boot readiness. Keep KPIs tied to user-visible behavior and release gates.
    """


def bench_diagram(title: str) -> str:
    return f"""
    # Bench Setup Diagrams: {title}

    ## Infotainment Validation Bench

    ```mermaid
    flowchart LR
        PSU[Programmable DC Power Supply\\n12 V nominal, current limit] --> Harness[Bench Harness\\nKL30 KL15 ACC GND]
        Harness --> IVI[MG Hector-style IVI Head Unit]
        CANoe[Vector CANoe + VN Interface] <-->|CAN HS / CAN FD| Harness
        ETH[Ethernet TAP / Switch] <-->|100/1000BASE-T1 via media converter| IVI
        Phone[Reference Phones\\niOS and Android] <-->|BT/WiFi/USB| IVI
        Camera[Reverse/360 Camera Simulator] --> IVI
        Audio[Audio Analyzer / Speaker Load] <-->|Analog or Digital Audio| IVI
        ADB[Automation PC adb/logcat] <-->|USB/Ethernet adb| IVI
    ```

    ## Data and Evidence Flow

    ```mermaid
    sequenceDiagram
        participant CANoe
        participant IVI
        participant Phone
        participant Tester
        Tester->>CANoe: Start measurement and rest bus
        CANoe->>IVI: Power mode, gear, speed, doors, SWC
        Phone->>IVI: Connectivity or projection stimulus
        IVI-->>CANoe: IVI status, heartbeat, diagnostic responses
        IVI-->>Tester: UI/audio/video behavior
        Tester->>Tester: Correlate CAN trace, logcat, video and report
    ```

    ## Bench Safety Checklist

    - Use current limit before first power-up.
    - Verify pinout with continuity mode before connecting IVI.
    - Use 120 ohm total CAN termination across CAN-H and CAN-L.
    - Label every breakout: KL30, KL15, ACC, GND, CAN-H, CAN-L, Ethernet, USB and camera.
    - Keep a known-good baseline trace for every bench.
    """


def canoe_config(title: str) -> str:
    return f"""
    # CANoe Configuration Examples: {title}

    ## Configuration Layout

    - Networks: `BodyCAN`, `InfoCAN`, optional `DiagCAN`, optional `Ethernet`.
    - Databases: representative DBC files for BCM, VCU, TCU, SWC, Cluster and IVI.
    - Simulation Setup: rest bus nodes for BCM, VCU, TCU, SWC, Cluster and Camera Gateway.
    - Measurement Setup: Trace, Graphics, Data, Diagnostics, Write and Logging blocks.
    - Test Setup: smoke tests, functional tests, negative tests, stress tests and diagnostics tests.

    ## Recommended Logging

    - Format: BLF for formal evidence, ASC for readable training examples.
    - Naming: `BenchID_BuildID_Feature_TestCase_Timestamp`.
    - Always log from 10 seconds before stimulus until 10 seconds after expected stable state.

    ## Rest Bus Simulation Signals

    | Node | Message | Signals | Purpose |
    | --- | --- | --- | --- |
    | BCM | `BCM_PowerMode` | `PowerMode` | OFF/ACC/IGN/CRANK transitions |
    | TCU | `TCU_GearStatus` | `GearPosition` | Reverse camera and cluster validation |
    | VCU | `VCU_VehicleSpeed` | `VehicleSpeed_kph` | speed-dependent lockouts and navigation |
    | SWC | `SWC_Buttons` | `SWC_KeyCode` | steering controls |
    | IVI | `IVI_Status` | `IVI_BootState` | readiness and heartbeat verification |

    ## Automated Verdict Pattern

    1. Set initial vehicle state.
    2. Wait for stable IVI heartbeat.
    3. Inject stimulus.
    4. Measure response in CAN, diagnostics and Android logs.
    5. Apply timeout and tolerance.
    6. Save verdict with evidence references.
    """


def capl_script(folder: str, title: str) -> str:
    node_name = folder.replace("-", "_")
    return f"""
    /* Representative CAPL script for {title}.
       Replace message and signal names with project DBC names before vehicle use. */

    variables
    {{
      msTimer tPowerMode;
      msTimer tVehicleSpeed;
      msTimer tHeartbeatCheck;
      int gPowerMode = 0;       // 0 OFF, 1 ACC, 2 IGN, 3 CRANK
      int gGear = 0;            // 0 P, 1 R, 2 N, 3 D
      long gSpeedRaw = 0;       // speed * 100
      int gAlive = 0;
    }}

    on start
    {{
      write(\"{title}: starting representative rest bus simulation\");
      setTimer(tPowerMode, 10);
      setTimer(tVehicleSpeed, 20);
      setTimer(tHeartbeatCheck, 100);
    }}

    on timer tPowerMode
    {{
      message BCM_PowerMode msg;
      msg.PowerMode = gPowerMode;
      msg.AliveCounter = gAlive & 0x0F;
      output(msg);
      setTimer(tPowerMode, 10);
    }}

    on timer tVehicleSpeed
    {{
      message VCU_VehicleSpeed spd;
      spd.VehicleSpeed_kph = gSpeedRaw;
      output(spd);
      setTimer(tVehicleSpeed, 20);
    }}

    on timer tHeartbeatCheck
    {{
      gAlive++;
      if (gAlive > 15) gAlive = 0;
      setTimer(tHeartbeatCheck, 100);
    }}

    void setIgnitionOn()
    {{
      gPowerMode = 2;
      write(\"PowerMode -> IGN\");
    }}

    void setAccessory()
    {{
      gPowerMode = 1;
      write(\"PowerMode -> ACC\");
    }}

    void setIgnitionOff()
    {{
      gPowerMode = 0;
      gSpeedRaw = 0;
      write(\"PowerMode -> OFF\");
    }}

    void setReverseGear()
    {{
      message TCU_GearStatus gear;
      gGear = 1;
      gear.GearPosition = gGear;
      output(gear);
      write(\"Gear -> Reverse\");
    }}

    void setVehicleSpeed(float speedKph)
    {{
      gSpeedRaw = (long)(speedKph * 100.0);
      write(\"VehicleSpeed -> %.2f kph\", speedKph);
    }}

    on key 'i' {{ setIgnitionOn(); }}
    on key 'a' {{ setAccessory(); }}
    on key 'o' {{ setIgnitionOff(); }}
    on key 'r' {{ setReverseGear(); }}
    on key '5' {{ setVehicleSpeed(5.0); }}
    """


def python_script(folder: str, title: str) -> str:
    class_name = "".join(part.title() for part in folder.lower().split("_") if part and not part.isdigit())
    return f'''\
#!/usr/bin/env python3
"""
Representative Python automation helper for {title}.

It is intentionally bench-safe: by default it parses logs and prints actions.
Connect it to CANoe COM, python-can or adb only after lab configuration review.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import time


@dataclass
class Verdict:
    test_id: str
    result: str
    evidence: str
    notes: str = ""


class {class_name}BenchAutomation:
    def __init__(self, bench_id: str = "MGH_BENCH_01") -> None:
        self.bench_id = bench_id

    def adb(self, *args: str, timeout: int = 20) -> str:
        cmd = ["adb", *args]
        try:
            return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=timeout)
        except Exception as exc:
            return f"ADB_NOT_AVAILABLE: {{exc}}"

    def mark_event(self, name: str) -> None:
        print(f"[{{time.strftime('%Y-%m-%d %H:%M:%S')}}] {{self.bench_id}} EVENT {{name}}")

    def parse_asc_for_message(self, asc_path: Path, can_id: str) -> int:
        pattern = re.compile(rf"\\b{{re.escape(can_id)}}\\b", re.IGNORECASE)
        count = 0
        for line in asc_path.read_text(errors="ignore").splitlines():
            if pattern.search(line):
                count += 1
        return count

    def verify_log_contains(self, log_path: Path, keyword: str) -> Verdict:
        text = log_path.read_text(errors="ignore") if log_path.exists() else ""
        result = "PASS" if keyword in text else "FAIL"
        return Verdict("LOG_KEYWORD_CHECK", result, str(log_path), f"keyword={{keyword}}")


def main() -> None:
    auto = {class_name}BenchAutomation()
    auto.mark_event("{title} dry run")
    print("Connect CANoe COM, python-can and adb adapters according to the lab interface document.")


if __name__ == "__main__":
    main()
'''


def asc_log(title: str) -> str:
    return f"""
    date Thu May 21 10:00:00.000 2026
    base hex  timestamps absolute
    internal events logged
    // Representative OEM-style CAN trace for {title}; not extracted from a production vehicle.
       0.000000 1  100             Rx   d 8  02 00 00 00 00 00 00 00  // BCM_PowerMode IGN
       0.010000 1  300             Rx   d 8  01 00 00 00 00 00 00 00  // IVI_Heartbeat alive=1
       0.020000 1  120             Rx   d 8  00 00 00 00 00 00 00 00  // VehicleSpeed 0 kph
       0.050000 1  101             Rx   d 8  00 00 00 00 00 00 00 00  // Driver door closed
       0.100000 1  301             Rx   d 8  02 00 00 00 00 00 00 00  // IVI boot state ready
       1.000000 1  130             Rx   d 8  01 00 00 00 00 00 00 00  // Gear reverse
       1.065000 1  301             Rx   d 8  05 00 00 00 00 00 00 00  // IVI camera view active
       2.000000 1  180             Rx   d 8  10 00 00 00 00 00 00 00  // SWC volume up short press
       2.080000 1  300             Rx   d 8  07 00 00 00 00 00 00 00  // IVI heartbeat alive=7
    """


def uds_examples(title: str) -> str:
    return f"""
    # UDS Examples: {title}

    These examples use representative diagnostic identifiers. Replace with the released diagnostic specification.

    ## Session Control

    | Step | Request | Expected Positive Response | Purpose |
    | --- | --- | --- | --- |
    | Default session | `10 01` | `50 01` | Return ECU to normal diagnostic behavior |
    | Extended session | `10 03` | `50 03` | Enable deeper IVI diagnostic reads |
    | Programming session | `10 02` | `50 02` | Used only for flashing or OTA recovery validation |

    ## DID Reads

    | DID | Request | Expected | Validation Use |
    | --- | --- | --- | --- |
    | `F180` | `22 F1 80` | bootloader/software ID | release evidence |
    | `F187` | `22 F1 87` | manufacturer spare part number | ECU identification |
    | `F190` | `22 F1 90` | VIN | vehicle personalization and traceability |
    | `D100` | `22 D1 00` | IVI boot KPI snapshot | performance validation |
    | `D200` | `22 D2 00` | connectivity state | feature validation |

    ## DTC Validation

    - Inject signal timeout in CANoe.
    - Wait for diagnostic debounce time.
    - Send `19 02 FF`.
    - Verify DTC status bit and aging behavior.
    - Remove fault, perform recovery sequence and clear DTC only if test plan requires `14 FF FF FF`.

    ## Negative Responses to Expect

    - `7F 22 31`: request out of range for unsupported DID.
    - `7F 27 35`: invalid key during security access.
    - `7F 31 22`: conditions not correct when routine is requested in wrong power mode.
    """


def test_cases(title: str) -> str:
    return """TestID,Requirement,Precondition,Stimulus,Expected_Result,Evidence,Priority
TC_SMOKE_001,IVI shall publish heartbeat,KL30 and KL15 stable,Start CANoe measurement,IVI heartbeat present within timeout,CANoe BLF and report,P0
TC_FUNC_001,Feature shall respond to valid vehicle signal,IVI ready and rest bus active,Inject nominal signal sequence,Correct UI/audio/video/CAN response observed,CAN trace plus logcat,P0
TC_NEG_001,Feature shall fail gracefully on missing input,IVI ready,Stop required CAN message,Timeout handling and DTC behavior match spec,CAN trace plus DTC read,P1
TC_BOUND_001,Feature shall handle boundary values,IVI ready,Inject min max and invalid ranges,No crash and defined UI behavior,CAN trace plus screen evidence,P1
TC_STRESS_001,Feature shall remain stable over endurance,IVI ready,Repeat stimulus 500 cycles,No crash memory leak or permanent fault,Automation report,P1
"""


def workflows(title: str) -> str:
    return f"""
    # OEM Validation Workflow: {title}

    ## Entry Criteria

    - Released build installed or flashed.
    - Bench ID, harness revision, power supply model and CAN interface logged.
    - DBC, diagnostic spec and test procedure versions frozen.
    - Known issues reviewed before execution.

    ## Execution

    1. Bench health check: power, CAN, Ethernet, adb, audio, camera and USB.
    2. Baseline capture: boot, heartbeat, DIDs, DTC snapshot and software version.
    3. Feature execution: nominal, negative, boundary, stress and recovery.
    4. Log package: CANoe BLF/ASC, logcat, kernel log, report XML/PDF, screenshots/video.
    5. Defect triage: isolate stimulus, reproduction rate and suspected layer.

    ## Exit Criteria

    - All P0/P1 cases pass or have approved deviations.
    - No open critical defects for release candidate.
    - Regression cases executed after every fix.
    - Traceability matrix updated with evidence path.
    """


def debugging(title: str) -> str:
    return f"""
    # Debugging Scenarios: {title}

    ## Scenario 1: Correct CAN Input, No IVI Reaction

    - Verify CANoe is transmitting on the physical channel, not only simulation bus.
    - Confirm DBC signal endian, scale and cycle time.
    - Check IVI network management and awake state.
    - Review logcat for service subscription failure or permission issue.
    - Read DTCs for communication timeout or invalid signal.

    ## Scenario 2: Intermittent Failure

    - Repeat with timestamps synchronized.
    - Capture bus load and error frames.
    - Compare passing and failing traces.
    - Check Android CPU, memory and binder latency.
    - Record reproduction rate and environmental conditions.

    ## Scenario 3: Works on Bench, Fails in Vehicle

    - Compare bench DBC against vehicle database version.
    - Check missing gateway messages, wakeup order and network management.
    - Confirm camera/audio/USB physical variants.
    - Validate power supply behavior against crank and sleep profile.
    """


def rca(title: str) -> str:
    return f"""
    # Root Cause Analysis Template: {title}

    ## Problem Statement

    During {title.lower()} validation, the IVI behavior deviated from requirement under a defined bench state.

    ## Evidence Timeline

    | Time | Evidence | Observation |
    | --- | --- | --- |
    | T-10 s | CANoe trace | Rest bus active |
    | T0 | Stimulus | Vehicle signal injected |
    | T+X ms | IVI response | Missing, delayed or incorrect behavior |
    | T+Y s | UDS/logcat | DTC or service log confirms layer |

    ## Five-Why Pattern

    1. Why did the user-visible behavior fail?
    2. Why did the IVI service not produce the expected output?
    3. Why was the input, state or dependency invalid?
    4. Why did validation not catch it earlier?
    5. What prevention action closes the gap?

    ## Corrective Actions

    - Software fix or calibration change.
    - Test case update for regression.
    - Bench simulation correction if the bench caused the fault.
    - Requirement clarification when timing or state behavior is ambiguous.
    """


def interview(title: str) -> str:
    return f"""
    # Interview Questions: {title}

    1. Explain how you would validate {title.lower()} from requirement to release evidence.
    2. What CANoe windows or tools would you use during live debugging?
    3. Write a CAPL approach to simulate the main vehicle input for this feature.
    4. How do you distinguish application bug, middleware bug, signal issue and bench issue?
    5. Which UDS services are useful for this module and why?
    6. What failure injection cases would you automate first?
    7. How would you report a production issue to an OEM release board?
    8. What KPIs would you track for customer-visible quality?
    """


def production(title: str) -> str:
    return f"""
    # Production Issue Examples: {title}

    ## Issue A: Timeout After Wakeup

    Symptom: Feature unavailable for the first few seconds after ignition on.

    Likely causes: delayed dependency service, missing wakeup message, network management startup order, slow storage mount or Android service not ready.

    RCA evidence: power mode trace, IVI boot state, logcat service timestamps, DTC snapshot and reproduction video.

    ## Issue B: Wrong State After Sleep

    Symptom: IVI displays stale state or ignores the first user action after wakeup.

    Likely causes: cached vehicle property not invalidated, missed CAN frame during suspend, app state restoration issue or race in service binding.

    ## Issue C: Regression After OTA

    Symptom: Feature passed in previous release but fails after software update.

    Likely causes: changed permissions, updated middleware API, config migration failure or incompatible calibration.
    """


def report_template(title: str) -> str:
    return f"""
    # Validation Report Template: {title}

    | Field | Value |
    | --- | --- |
    | Program | MG Hector-style IVI validation |
    | Feature | {title} |
    | Bench ID | MGH_BENCH_01 |
    | Build ID | TBD |
    | CANoe Config | TBD |
    | DBC Version | TBD |
    | Tester | TBD |
    | Date | TBD |

    ## Summary

    - Total cases:
    - Passed:
    - Failed:
    - Blocked:
    - Open defects:

    ## Evidence

    - CANoe trace:
    - CANoe XML/PDF report:
    - adb logcat:
    - kernel log:
    - screenshots/video:
    - diagnostic readout:

    ## Release Recommendation

    State whether the feature is acceptable for integration, needs retest, or must be blocked for release.
    """


def traceability() -> str:
    return """RequirementID,Requirement,TestID,Evidence,Status,DefectID
REQ-IVI-BOOT-001,IVI shall publish heartbeat after ignition,TC_SMOKE_001,logs/sample_can.asc,Not Run,
REQ-IVI-FEAT-001,Feature shall react to valid signal,TC_FUNC_001,report template,Not Run,
REQ-IVI-DIAG-001,ECU shall report DTC for missing required signal,TC_NEG_001,UDS readout,Not Run,
REQ-IVI-PERF-001,Feature response shall meet KPI,TC_BOUND_001,performance report,Not Run,
"""


def vehicle_signals_csv() -> str:
    output = ["CAN_ID,Message,Signal,Length,Cycle,Description"]
    for row in SIGNALS:
        output.append(",".join(row))
    return "\n".join(output) + "\n"


def performance(title: str) -> str:
    return f"""
    # Performance Optimization: {title}

    ## KPIs

    - Signal-to-UI latency.
    - Input-to-audio latency where audio is involved.
    - Frame drop count for video or UI animation.
    - CPU, memory, binder thread and IO pressure during stimulus.
    - Recovery time after sleep, wakeup, USB reconnect or phone reconnect.

    ## Measurement Pattern

    1. Timestamp stimulus in CANoe.
    2. Timestamp IVI state change in CAN, logcat or screen capture.
    3. Compute P50, P95 and worst-case latency over repeated runs.
    4. Compare against KPI and build-to-build trend.
    5. File performance defects with raw evidence and environment metadata.
    """


def root_files() -> None:
    write(ROOT / "README.md", """
    # MG Hector Infotainment Validation

    Complete folder-based study material and lab project setup for MG Hector-style infotainment validation using Vector CANoe, CAPL, Python automation, diagnostics and Android/Linux debugging.

    This package simulates a real OEM validation lab. It deliberately uses representative network IDs, DIDs and traces because production MG Hector databases, security algorithms and ECU implementations are proprietary. The workflow, evidence structure, automation patterns and debugging methods are the important production skills.

    ## How To Use This Pack

    1. Start with `DAILY_LEARNING_ROADMAP.md` and `WEEKLY_MILESTONES.md`.
    2. Build the bench mentally using `03_BENCH_SETUP`, then configure CANoe with `04_VECTOR_CANOE`.
    3. Practice CAPL in `05_CAPL_PROGRAMMING`, diagnostics in `23_UDS_DIAGNOSTICS` and automation in `30_AUTOMATION_FRAMEWORK`.
    4. Execute feature labs from `09_IVI_FEATURES` through `25_OTA_TESTING`.
    5. Use `44_REAL_WORLD_ISSUES` and `45_INTERVIEW_PREPARATION` for production debugging and interview readiness.

    ## Expected Outcome

    After completing the pack you should be able to set up a bench, configure CANoe, write CAPL, run UDS diagnostics, automate infotainment tests, debug Android/Linux issues, analyze CAN logs, produce OEM-quality validation reports and discuss production issues confidently in interviews.
    """)

    write(ROOT / "DAILY_LEARNING_ROADMAP.md", """
    # Daily Learning Roadmap

    ## 60-Day Plan

    | Days | Focus | Lab Output |
    | --- | --- | --- |
    | 1-5 | Automotive basics, CAN, DBC and IVI architecture | Draw ECU map and decode sample ASC logs |
    | 6-10 | Bench setup and power modes | Build bench checklist and power transition matrix |
    | 11-15 | CANoe configuration and trace analysis | Create rest bus simulation blueprint |
    | 16-22 | CAPL programming | Implement ignition, gear, speed, door and SWC simulation |
    | 23-28 | UDS diagnostics and DTC validation | Build DID/DTC diagnostic checklist |
    | 29-35 | IVI features, Bluetooth, USB, projection and audio | Execute feature test matrices |
    | 36-42 | Camera, cluster, steering and HVAC integration | Run cross-ECU integration scenarios |
    | 43-49 | Android logcat, Linux debugging and performance | Correlate CAN + logcat + boot KPIs |
    | 50-55 | Automation framework and CANoe automation | Build pytest-based regression pack |
    | 56-60 | Capstone bench release simulation | Produce release report and interview STAR stories |
    """)

    write(ROOT / "WEEKLY_MILESTONES.md", """
    # Weekly Milestones

    | Week | Milestone | Review Gate |
    | --- | --- | --- |
    | 1 | Understand IVI architecture and vehicle network basics | Explain IVI ECU dependencies without notes |
    | 2 | Design bench wiring, power and CANoe topology | Produce bench diagram and troubleshooting guide |
    | 3 | Build CAPL rest bus simulation | Simulate ignition, speed, gear and SWC |
    | 4 | Execute diagnostics and fault injection | Show DTC setting and clearing evidence |
    | 5 | Validate connectivity and media features | Pairing, USB, audio and projection reports |
    | 6 | Validate camera, cluster and power modes | Latency and wakeup evidence |
    | 7 | Automate regression and parse logs | pytest report and CAN trace parser output |
    | 8 | Capstone release run | OEM-style validation report and defect triage notes |
    """)

    write(ROOT / "BENCH_EXERCISES.md", """
    # Bench Exercises

    1. Build a power mode matrix for OFF, ACC, IGN, CRANK, sleep and wakeup.
    2. Measure CAN termination and document expected resistance.
    3. Create a CANoe panel with power, gear, speed, door and steering switch controls.
    4. Capture a baseline boot trace and mark IVI ready time.
    5. Simulate reverse gear and measure camera view activation latency.
    6. Inject missing BCM power message and verify IVI timeout behavior.
    7. Run sleep/wakeup cycles and verify no stale UI state.
    8. Package evidence as if sending to an OEM defect triage board.
    """)

    write(ROOT / "CAPL_CODING_CHALLENGES.md", """
    # CAPL Coding Challenges

    1. Implement a rolling alive counter and checksum stub for `BCM_PowerMode`.
    2. Add speed ramp from 0 to 120 kph in 1 kph steps every 100 ms.
    3. Simulate short press and long press for steering voice button.
    4. Stop one cyclic message for 5 seconds to trigger timeout DTC.
    5. Create a diagnostic request sequence for session, DID read and DTC read.
    6. Add verdict logic for reverse camera activation within 700 ms.
    7. Write a CAPL function that toggles driver door open/close 100 times.
    8. Build a bus-load stress function using additional dummy frames.
    """)

    write(ROOT / "DEBUGGING_LABS.md", """
    # Debugging Labs

    | Lab | Fault | Expected Skill |
    | --- | --- | --- |
    | DL-01 | IVI heartbeat missing after ignition | Power and CAN startup RCA |
    | DL-02 | Reverse camera black screen | Gear signal, camera input and video service correlation |
    | DL-03 | Bluetooth reconnect failure | Phone logs, IVI logs and state persistence |
    | DL-04 | Audio lag during navigation prompt | Audio focus and latency measurement |
    | DL-05 | Sleep current high | Wake source and process activity investigation |
    | DL-06 | OTA rollback not triggered | Update state machine and recovery validation |
    | DL-07 | CAN timeout DTC not set | Fault injection timing and diagnostic debounce |
    | DL-08 | Boot loop after update | logcat, kernel and recovery partition evidence |
    """)

    write(ROOT / "AUTOMATION_ASSIGNMENTS.md", """
    # Automation Assignments

    1. Create a Python parser that counts key CAN IDs in ASC logs.
    2. Use pytest fixtures for bench setup, ignition on, ignition off and log collection.
    3. Add adb logcat collection with test case name and timestamp.
    4. Generate a JUnit XML report for CI ingestion.
    5. Add CANoe COM hooks for starting measurement and setting environment variables.
    6. Implement a stress runner for 500 Bluetooth reconnect or USB reconnect cycles.
    7. Generate RTM status from test result CSV.
    8. Create a release dashboard summary: pass, fail, blocked and open defects.
    """)

    write(ROOT / "INTERVIEW_PREPARATION_PLAN.md", """
    # Interview Preparation Plan

    ## Daily Routine

    - Explain one vehicle signal path aloud.
    - Write one CAPL function without looking at notes.
    - Analyze five lines from a CAN trace.
    - Answer one UDS question with service ID, use case and failure mode.
    - Convert one issue into STAR format: situation, task, action, result.

    ## Must-Know Topics

    CANoe architecture, CAPL events, DBC signal scaling, UDS services, Android logcat, Linux process debugging, power modes, reverse camera, Bluetooth, USB, OTA, issue triage, traceability and release evidence.
    """)

    write(ROOT / "LAB_SAFETY_AND_ASSUMPTIONS.md", """
    # Lab Safety And Assumptions

    - This is a study and simulation package, not an official MG Motor service manual.
    - Use current limiting and correct fusing on physical benches.
    - Never connect unknown harness pins directly to an ECU.
    - Never use real seed/key, VIN or customer data in training material.
    - Treat all sample CAN logs and DIDs as representative, not vehicle-authentic.
    - Replace every sample identifier with the released project database before production use.
    """)

    write(ROOT / "requirements_master.csv", traceability())


def generic_module(folder: str, title: str, focus: str) -> None:
    base = ROOT / folder
    write(base / "README.md", readme(folder, title, focus))
    write(base / "01_theory_notes.md", theory(title, focus))
    write(base / "02_bench_setup_diagrams.md", bench_diagram(title))
    write(base / "03_canoe_configuration_examples.md", canoe_config(title))
    write(base / "capl" / f"{module_slug(folder)}_simulation.can", capl_script(folder, title))
    write(base / "python" / f"{module_slug(folder)}_automation.py", python_script(folder, title))
    write(base / "logs" / f"{module_slug(folder)}_sample_can.asc", asc_log(title))
    write(base / "uds" / f"{module_slug(folder)}_uds_examples.md", uds_examples(title))
    write(base / "test_cases" / f"{module_slug(folder)}_test_cases.csv", test_cases(title))
    write(base / "workflows" / "oem_validation_workflow.md", workflows(title))
    write(base / "debugging" / "debugging_scenarios.md", debugging(title))
    write(base / "debugging" / "root_cause_analysis.md", rca(title))
    write(base / "interview" / "interview_questions.md", interview(title))
    write(base / "production_issue_examples.md", production(title))
    write(base / "reports" / "validation_report_template.md", report_template(title))
    write(base / "traceability" / "requirements_traceability.csv", traceability())
    write(base / "signals" / "vehicle_signal_examples.csv", vehicle_signals_csv())
    write(base / "PERFORMANCE_OPTIMIZATION.md", performance(title))


def add_deep_dives() -> None:
    write(ROOT / "03_BENCH_SETUP" / "MG_HECTOR_BENCH_ARCHITECTURE.md", """
    # MG Hector-Style Bench Architecture

    ## Representative ECU Topology

    | Domain | ECU/Node | IVI Dependency |
    | --- | --- | --- |
    | Body | BCM | power mode, doors, lamps, vehicle lock state |
    | Powertrain | VCU/ECM/TCU | speed, gear, engine state |
    | Cockpit | Cluster | warnings, tell-tales, trip and alert sync |
    | Controls | Steering switch module | media, phone, volume, voice button |
    | Comfort | HVAC controller | climate display and control feedback |
    | Vision | Reverse/360 camera ECU | video stream, camera state, diagnostic faults |
    | Connectivity | TCU/telematics | OTA, connected services, emergency call status |
    | Infotainment | IVI head unit | UI, audio, projection, navigation, vehicle settings |

    ## Bench Bring-Up Sequence

    1. Connect power supply with current limit set low for first power-up.
    2. Verify harness pinout, ground continuity and CAN termination.
    3. Connect Vector interface and start CANoe in listen-only for sanity check.
    4. Enable rest bus simulation and cyclic messages.
    5. Apply KL30, then ACC/KL15 according to the test case.
    6. Confirm IVI heartbeat, boot status and diagnostic response.
    7. Capture software version DIDs and initial DTC snapshot.

    ## Troubleshooting Rules

    - No power draw: check fuse, ground, KL30 and connector seating.
    - High current: power down, inspect harness and current limit, isolate peripherals.
    - No CAN traffic: check channel mapping, transceiver, termination and bus wakeup.
    - IVI boots but feature absent: verify feature coding, region config, service logs and dependent ECU simulation.
    """)

    write(ROOT / "03_BENCH_SETUP" / "ECU_COMMUNICATION_MAP.csv", """Source,Destination,Protocol,Data,Validation_Purpose
BCM,IVI,CAN,PowerMode DoorStatus LampStatus,Wakeup UI state timeout DTC
TCU,IVI,CAN,GearPosition,Reverse camera trigger
VCU,IVI,CAN,VehicleSpeed,Speed lockouts navigation dead reckoning
SWC,IVI,CAN,Button events,Media phone voice control
IVI,Cluster,CAN,Media warning status,Cluster sync validation
CameraGW,IVI,Ethernet/LVDS/Analog,Video and camera status,Reverse and 360 camera validation
TCU/Telematics,IVI,Ethernet/CAN,OTA connectivity state,OTA and connected services
""")

    write(ROOT / "04_VECTOR_CANOE" / "CANOE_PROJECT_BLUEPRINT.md", """
    # CANoe Project Blueprint

    ## Recommended Config

    - `MGH_IVI_Bench.cfg`: main configuration.
    - `Databases/`: BodyCAN, InfoCAN, DiagCAN DBC placeholders.
    - `CAPL/`: rest bus simulation nodes and test helpers.
    - `Panels/`: power, gear, speed, doors, SWC, diagnostics and fault injection.
    - `TestModules/`: smoke, feature, diagnostics, stress and regression groups.
    - `Logs/`: BLF formal logs and ASC training logs.

    ## Measurement Setup

    Trace -> Graphics -> Data -> Diagnostics -> Write -> Logging.

    ## Test Setup Groups

    - Smoke: boot, heartbeat, DID read and DTC no-fault baseline.
    - Feature: IVI feature tests by module.
    - Negative: missing messages, invalid ranges, bus off and peripheral disconnect.
    - Stress: cycle, endurance and overload.
    - Regression: P0/P1 release gate tests.
    """)

    write(ROOT / "05_CAPL_PROGRAMMING" / "capl" / "ignition_door_speed_steering_simulation.can", """
    variables
    {
      msTimer t10ms;
      msTimer t20ms;
      int powerMode = 0;
      int doorOpen = 0;
      int swcKey = 0;
      long speedRaw = 0;
    }

    on start
    {
      setTimer(t10ms, 10);
      setTimer(t20ms, 20);
      write("MG Hector-style IVI vehicle signal simulator started");
    }

    on timer t10ms
    {
      message BCM_PowerMode pwr;
      pwr.PowerMode = powerMode;
      output(pwr);

      message BCM_DoorStatus door;
      door.DriverDoorAjar = doorOpen;
      output(door);

      setTimer(t10ms, 10);
    }

    on timer t20ms
    {
      message VCU_VehicleSpeed spd;
      spd.VehicleSpeed_kph = speedRaw;
      output(spd);
      setTimer(t20ms, 20);
    }

    void sendSwc(int keyCode, int durationMs)
    {
      message SWC_Buttons btn;
      btn.SWC_KeyCode = keyCode;
      btn.PressDuration_ms = durationMs;
      output(btn);
    }

    on key 'i' { powerMode = 2; }
    on key 'o' { powerMode = 0; speedRaw = 0; }
    on key 'd' { doorOpen = !doorOpen; }
    on key '+' { sendSwc(0x10, 100); }    // volume up short press
    on key 'v' { sendSwc(0x40, 1200); }   // voice long press
    """)

    write(ROOT / "09_IVI_FEATURES" / "IVI_FEATURE_TEST_MATRIX.md", """
    # IVI Feature Test Matrix

    | Feature | Nominal | Negative | Boundary | Stress | Evidence |
    | --- | --- | --- | --- | --- | --- |
    | Radio | Tune valid station | Weak signal | band edge frequency | 200 station changes | audio log, screen video |
    | Media Player | Play indexed USB file | corrupt file | max file count | 8 h playback | logcat, audio trace |
    | Bluetooth Audio | A2DP playback | phone disconnect | codec switch | 500 reconnect cycles | BT snoop, logcat |
    | Phone | Incoming/outgoing call | call drop | contact name length | repeated call cycles | HFP logs |
    | Navigation | Route guidance | GNSS loss | route recalculation | long route | location logs |
    | Voice Assistant | Wake word/button | no network | noisy cabin | repeated commands | audio and app logs |
    | Touchscreen | tap/swipe | rapid touches | screen corners | 1000 interactions | screen recording |
    | Theme | day/night switch | invalid config | low voltage switch | repeated switching | screenshot diff |
    | Language | change locale | missing string | long translation | repeated changes | UI checklist |
    """)

    write(ROOT / "10_BLUETOOTH_VALIDATION" / "BLUETOOTH_STRESS_SCENARIOS.md", """
    # Bluetooth Stress Scenarios

    1. Pair phone, power cycle IVI, verify auto reconnect within KPI.
    2. Pair five devices, switch priority, verify last connected behavior.
    3. Start A2DP playback, inject CAN sleep request, wake and verify playback state.
    4. Run active call, switch to reverse camera and verify audio focus policy.
    5. Sync 5000 contacts and verify no UI freeze or ANR.
    6. Move phone out of range for 60 seconds, return and verify recovery.
    7. Toggle phone Bluetooth 100 times and collect HCI snoop/logcat evidence.
    """)

    write(ROOT / "13_CARPLAY_ANDROID_AUTO" / "PROJECTION_FAILURE_INJECTION.md", """
    # Projection Failure Injection

    | Case | Injection | Expected Behavior |
    | --- | --- | --- |
    | USB unplug during launch | Disconnect cable before projection ready | IVI returns to previous screen and offers reconnect |
    | Phone locked | Start projection with locked phone | Clear user prompt, no crash |
    | Cable quality issue | Use controlled USB drop or hub reset | Graceful disconnect and reconnect |
    | Permission revoked | Remove projection permission on phone | IVI shows actionable message |
    | Power mode off | Turn KL15 off during projection | Projection stops, state restores after wake if supported |
    | Audio focus conflict | Start navigation prompt during media | Correct ducking and focus behavior |
    """)

    write(ROOT / "17_REVERSE_CAMERA" / "REVERSE_CAMERA_LATENCY_WORKFLOW.md", """
    # Reverse Camera Latency Workflow

    ## KPI Measurement

    - T0: CANoe transmits `GearPosition = R`.
    - T1: IVI publishes camera active state or screen capture detects camera frame.
    - Latency: `T1 - T0`.
    - Repeat: 30 cold, 30 warm, 30 after sleep/wakeup.

    ## Fault Injection

    - Reverse signal missing.
    - Camera video absent.
    - Camera gateway reports fault.
    - Gear toggles R-D-R quickly.
    - Low voltage during camera activation.

    ## Pass Criteria

    Camera view activates within KPI, no stale frame after gear out of reverse, dynamic guidelines follow steering input if supported, and DTC behavior matches diagnostic specification.
    """)

    write(ROOT / "19_CLUSTER_INTEGRATION" / "CLUSTER_ALERT_SYNC.md", """
    # Cluster Alert Synchronization

    Validate that IVI and cluster present warnings consistently. Typical checks include warning text, icon/tell-tale state, priority, chime policy, acknowledgement behavior and timeout.

    ## Example Alert Flow

    1. CANoe injects `DoorAjar = 1` while ignition is ON.
    2. Cluster warning appears.
    3. IVI vehicle status page shows door open.
    4. Chime routing follows audio focus policy.
    5. Clearing the signal removes both warnings within KPI.
    """)

    write(ROOT / "20_STEERING_SWITCH_CONTROLS" / "SWC_SHORT_LONG_PRESS_VALIDATION.md", """
    # Steering Switch Short/Long Press Validation

    | Button | Short Press Expected | Long Press Expected |
    | --- | --- | --- |
    | Volume Up | volume +1 step | repeated volume increase |
    | Track Next | next track/station | seek/fast forward if supported |
    | Phone | accept/end call | reject or phone menu if specified |
    | Voice | voice assistant start | alternate assistant/projection assistant if specified |

    Validate debounce, repeated frame handling, stuck button timeout and priority during reverse camera or call state.
    """)

    write(ROOT / "23_UDS_DIAGNOSTICS" / "UDS_AUTOMATION_FRAMEWORK.md", """
    # UDS Automation Framework

    ## Service Coverage

    - `0x10`: diagnostic session control.
    - `0x11`: ECU reset.
    - `0x14`: clear diagnostic information.
    - `0x19`: read DTC information.
    - `0x22`: read data by identifier.
    - `0x27`: security access, stubbed only in training.
    - `0x2E`: write data by identifier, restricted to approved bench cases.
    - `0x31`: routine control.

    ## Automation Rules

    - Never brute force seed/key.
    - Always restore default session after tests.
    - Capture precondition, request, response, NRC and timing.
    - Keep destructive services behind an explicit safety flag.
    """)

    write(ROOT / "25_OTA_TESTING" / "OTA_FAILURE_AND_RECOVERY_MATRIX.md", """
    # OTA Failure And Recovery Matrix

    | Phase | Failure Injection | Expected Recovery |
    | --- | --- | --- |
    | Download | network loss | pause/resume or retry with user-visible state |
    | Verification | package hash mismatch | reject package and keep current version |
    | Install | KL15 off | follow power policy and resume or rollback |
    | First boot | service crash | rollback or safe mode per spec |
    | Post-update | config migration failure | preserve critical user data or reset with notice |
    """)

    write(ROOT / "26_PERFORMANCE_TESTING" / "PERFORMANCE_BENCHMARK_FRAMEWORK.md", """
    # Performance Benchmark Framework

    ## KPIs

    - Cold boot to first usable home screen.
    - Warm boot to media available.
    - Reverse gear to first camera frame.
    - App launch time for radio, media, phone, navigation and settings.
    - Touch response latency.
    - CPU, memory, IO and frame drops during stress.

    ## Evidence

    Use CANoe timestamps for vehicle stimulus, logcat markers for service readiness, `dumpsys` for Android metrics and video capture for visual confirmation.
    """)

    write(ROOT / "27_STRESS_TESTING" / "STRESS_TEST_SCENARIOS.md", """
    # Stress Test Scenarios

    - Continuous reboot testing: 200 ignition cycles with DTC and boot KPI capture.
    - Long-duration playback: 12 h USB or Bluetooth audio with memory trend.
    - Repeated connect/disconnect: USB, Bluetooth, WiFi and projection cycles.
    - Multi-device pairing: device priority, reconnect order and profile conflict.
    - Rapid signal changes: gear, speed, doors, power mode and SWC spam.
    - CAN bus overload: controlled high bus load with graceful degradation checks.
    """)

    write(ROOT / "28_MEMORY_LEAK_ANALYSIS" / "ANDROID_MEMORY_ANALYSIS_WORKFLOW.md", """
    # Android Memory Analysis Workflow

    1. Capture baseline: `adb shell dumpsys meminfo`.
    2. Start feature stress case and collect memory every minute.
    3. Capture heap dump for suspected process.
    4. Compare Java heap, native heap, graphics, ashmem, binder and thread count.
    5. Correlate memory growth with user actions and logs.
    6. Confirm leak by repeated cycles and recovery after process restart.
    """)

    write(ROOT / "29_LOG_ANALYSIS" / "LOG_CORRELATION_PLAYBOOK.md", """
    # Log Correlation Playbook

    ## Evidence Sources

    - CANoe BLF/ASC: vehicle stimulus and ECU messages.
    - Android logcat: framework, app and service logs.
    - Kernel logs: driver, USB, audio, camera and filesystem events.
    - Ethernet pcap: DoIP, SOME/IP, OTA and service discovery.
    - CANoe diagnostic log: UDS request/response timing.

    ## Method

    Normalize timestamps, mark T0 stimulus, identify first incorrect state, then walk backward to the earliest abnormal dependency.
    """)

    write(ROOT / "30_AUTOMATION_FRAMEWORK" / "FRAMEWORK_BLUEPRINT.md", """
    # Full Infotainment Automation Framework

    ```text
    automation/
      config/bench.yaml
      adapters/canoe.py
      adapters/adb.py
      adapters/diagnostics.py
      adapters/can_log.py
      tests/test_boot.py
      tests/test_reverse_camera.py
      tests/test_bluetooth.py
      reports/
      evidence/
    ```

    ## Design

    - pytest controls test flow and verdicts.
    - CANoe COM starts/stops measurement and drives environment variables.
    - CAPL provides fast real-time vehicle signal simulation.
    - adb collects logcat, dumpsys and screenshots.
    - Diagnostic adapter reads DIDs and DTCs.
    - Report generator links every verdict to evidence files.
    """)

    write(ROOT / "36_CANOE_AUTOMATION" / "CANOE_REGRESSION_SUITE.md", """
    # CANoe Regression Suite

    ## Suites

    - `SmokeSuite`: boot, heartbeat, software DID, no critical DTC.
    - `PowerSuite`: KL15/KL30, ACC, crank, shutdown, sleep and wakeup.
    - `FeatureSuite`: IVI, Bluetooth, USB, projection, camera, cluster and SWC.
    - `DiagSuite`: DID, DTC, sessions, reset and negative responses.
    - `StressSuite`: cycle and endurance tests.

    ## Report Rule

    Every automated test shall output XML/JUnit plus a human-readable summary with trace file name, build ID and bench ID.
    """)

    write(ROOT / "39_POWER_MODE_VALIDATION" / "POWER_CYCLE_SIMULATIONS.md", """
    # Power Cycle Simulations

    | State | KL30 | KL15 | ACC | Expected IVI |
    | --- | --- | --- | --- | --- |
    | Vehicle off | ON | OFF | OFF | sleep or retained low-power state |
    | Accessory | ON | OFF | ON | limited infotainment mode |
    | Ignition | ON | ON | ON | full feature availability |
    | Crank | ON | transient | transient | no corruption, defined audio/camera behavior |
    | Low voltage | below threshold | variable | variable | warning, graceful shutdown or inhibit |
    """)

    write(ROOT / "40_SLEEP_WAKEUP_TESTING" / "SLEEP_WAKEUP_VALIDATION.md", """
    # Sleep Wakeup Validation

    Validate entry current, wake source, wake latency, retained state and diagnostic behavior.

    Wake triggers: CAN wakeup, door unlock, ignition, USB insert, phone reconnect if specified and remote command if telematics is integrated.

    Evidence: current trace, CAN wake frame, IVI boot/wake logs, DTC snapshot and user-visible state.
    """)

    write(ROOT / "41_BOOT_TIME_ANALYSIS" / "BOOT_KPI_VALIDATION.md", """
    # Boot KPI Validation

    - Cold boot: power removed long enough to clear volatile state.
    - Warm boot: reboot without full power removal.
    - Fast boot: resume from suspend or retained low-power state.
    - Ready definitions: heartbeat, home UI, audio available, reverse camera available, diagnostics available.
    """)

    write(ROOT / "42_ANDROID_LOGCAT" / "ADB_LOGCAT_CHEATSHEET.md", """
    # adb logcat Cheatsheet

    ```bash
    adb devices
    adb shell getprop ro.build.fingerprint
    adb logcat -c
    adb logcat -v threadtime > evidence/logcat.txt
    adb shell dumpsys activity processes
    adb shell dumpsys meminfo
    adb shell dumpsys cpuinfo
    adb bugreport evidence/bugreport.zip
    ```

    For crash/ANR: capture `logcat`, `dropbox`, `tombstones`, `anr` traces if access is available and build policy permits.
    """)

    write(ROOT / "43_LINUX_DEBUGGING" / "LINUX_IVI_DEBUGGING_CHEATSHEET.md", """
    # Linux IVI Debugging Cheatsheet

    ```bash
    ps -A
    top -H
    dmesg -T
    journalctl -b
    systemctl --failed
    ip addr
    ss -tulpn
    df -h
    mount
    ```

    Use process, service, kernel, filesystem and network evidence to separate app-layer problems from platform and driver problems.
    """)

    write(ROOT / "44_REAL_WORLD_ISSUES" / "OEM_ISSUE_RCA_CATALOG.md", """
    # OEM Issue RCA Catalog

    | Issue | First Evidence | Likely Layers | RCA Direction |
    | --- | --- | --- | --- |
    | Bluetooth disconnects | BT snoop, logcat, phone matrix | profile, RF, state machine | reconnect state and profile conflict |
    | Audio lag | audio timestamp, CPU, focus logs | audio HAL, DSP, app | buffer and focus chain |
    | CAN timeout | CAN trace, DTC | network, gateway, IVI timeout | missing cyclic frame or debounce mismatch |
    | Black screen | boot logs, display service | graphics, power, app | display init and compositor |
    | Reverse camera freeze | video capture, gear trace | camera ECU, driver, UI | stale frame and stream reset |
    | Navigation crash | tombstone, route steps | app, map, GNSS | reproduction route and memory |
    | Touchscreen lag | screen video, CPU | UI thread, input driver | frame timing and main thread block |
    | Boot loop | kernel, recovery logs | OTA, filesystem, service crash | rollback and boot reason |
    | Sleep current issue | current trace, wake locks | app, kernel, CAN wake | wakelock and wake source |
    | OTA corruption | update logs, hash | package, storage, rollback | verification and A/B state |
    | Memory leak | meminfo trend | app, native, graphics | heap and cycle correlation |
    | Voice assistant failure | mic/audio logs | network, ASR, audio focus | capture path and service state |
    """)

    write(ROOT / "45_INTERVIEW_PREPARATION" / "SENIOR_LEVEL_QA.md", """
    # Senior-Level Interview Q&A

    ## CANoe

    Q: How do you validate a feature when the dependent ECU is unavailable?
    A: Build rest bus simulation in CANoe using the released DBC, model cyclic timing, counters and timeouts, then prove the simulation with a baseline trace before feature execution.

    ## CAPL

    Q: What CAPL event types matter most for IVI validation?
    A: `on start`, `on timer`, `on message`, `on key`, diagnostic callbacks and test module functions. IVI benches commonly use timers for cyclic ECU simulation and `on key` or panels for manual stimuli.

    ## UDS

    Q: Which services do you use before filing a defect?
    A: Read software DIDs, read DTC snapshot, session control if needed, and avoid destructive services unless the test procedure requires them.

    ## Production Debugging

    Q: Reverse camera is black after gear R. How do you debug?
    A: Verify gear signal timing in CANoe, camera input status, IVI camera service logs, display layer state, DTCs and reproduce across cold/warm/sleep states. Attach trace, video and logs.
    """)

    write(ROOT / "49_REAL_PROJECTS" / "PROJECT_PORTFOLIO.md", """
    # Real Project Portfolio

    1. Complete infotainment bench setup: diagram, pin checklist, power profile and smoke test report.
    2. CANoe rest bus simulation: BCM, VCU, TCU, SWC, Cluster and IVI status nodes.
    3. Bluetooth automation framework: pairing, reconnect, call and A2DP stress suite.
    4. Reverse camera validation setup: gear simulation, latency measurement and fault injection.
    5. OTA testing framework: download, install, interruption, rollback and post-update validation.
    6. Android Auto validation suite: projection launch, reconnect, audio focus and failure injection.
    7. Steering switch simulation: short/long press and stuck button tests.
    8. Vehicle signal simulator: speed, gear, doors, lamps and power state model.
    9. Full infotainment automation framework: pytest, CANoe, adb, diagnostics and reports.
    """)

    write(ROOT / "50_CAPSTONE_BENCH_PROJECT" / "CAPSTONE_RELEASE_SIMULATION.md", """
    # Capstone Bench Project

    ## Objective

    Execute an MG Hector-style IVI release validation cycle on a bench using CANoe, CAPL, Python, UDS and Android/Linux logs.

    ## Deliverables

    - Bench architecture diagram and safety checklist.
    - CANoe rest bus simulation and panel plan.
    - CAPL scripts for power, gear, speed, door and SWC.
    - Feature test reports for Bluetooth, USB, projection, reverse camera, cluster, steering and OTA.
    - Diagnostic evidence: software DIDs, DTC baseline and fault injection DTC.
    - Automation report with pass/fail verdicts and evidence paths.
    - RCA document for at least three injected production issues.
    - Interview STAR stories based on your capstone work.
    """)


def main() -> None:
    ROOT.mkdir(exist_ok=True)
    root_files()
    for folder, title, focus in MODULES:
        generic_module(folder, title, focus)
    add_deep_dives()

    # Add one CSV index for navigation.
    index_path = ROOT / "MODULE_INDEX.csv"
    with index_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Folder", "Title", "Focus"])
        writer.writerows(MODULES)


if __name__ == "__main__":
    main()
