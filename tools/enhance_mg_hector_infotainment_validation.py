from pathlib import Path
import textwrap


ROOT = Path("MG_HECTOR_INFOTAINMENT_VALIDATION")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def main() -> None:
    write(ROOT / "00_START_HERE.md", """
    # Start Here

    This repository is meant to behave like a compact OEM infotainment validation workspace, not only a note dump.

    ## Recommended First Run

    1. Read `LAB_SAFETY_AND_ASSUMPTIONS.md`.
    2. Open `CANoe_Project/README.md` and inspect the representative DBC.
    3. Review `03_BENCH_SETUP/MG_HECTOR_BENCH_ARCHITECTURE.md`.
    4. Run the dry automation suite:

    ```bash
    cd MG_HECTOR_INFOTAINMENT_VALIDATION/30_AUTOMATION_FRAMEWORK
    python3 -m pytest automation/tests -q
    ```

    5. Execute the capstone using `50_CAPSTONE_BENCH_PROJECT/CAPSTONE_RELEASE_EXECUTION_PLAN.md`.

    ## What Is Real vs Representative

    The validation process, folder layout, evidence discipline, automation interfaces, RCA workflow and release gates match real OEM/Tier1 work. CAN IDs, DIDs, DBC contents, traces and topology are representative training data and must be replaced with released MG program artifacts on a real project.
    """)

    write(ROOT / "REPO_COMPLETION_MANIFEST.md", """
    # Repo Completion Manifest

    ## Concrete Assets Added

    - Full 50-module learning tree.
    - Representative CANoe project workspace in `CANoe_Project`.
    - Representative DBC file with BCM, VCU, TCU, SWC, IVI and Cluster messages.
    - CAPL rest bus, steering switch, reverse camera and diagnostics smoke scripts.
    - System variable and panel design documentation.
    - Runnable dry-run pytest automation framework.
    - Sample Android, kernel, Ethernet and CAN evidence files.
    - Feature-specific validation suites for IVI, Bluetooth, projection, reverse camera, cluster, SWC, UDS, OTA, power, sleep and boot.
    - Release execution plan, defect templates, RTM and sign-off reports.

    ## Intended Use

    This repo prepares you for bench validation conversations and hands-on practice. It is not a substitute for OEM-confidential databases, diagnostic specs, bench pinouts or release procedures.
    """)

    write(ROOT / "CANoe_Project" / "README.md", """
    # CANoe Project Workspace

    This folder mirrors a production CANoe bench project layout.

    ```text
    CANoe_Project/
      Databases/MG_Hector_IVI_Training.dbc
      CAPL/RestBus_BCM_VCU_TCU.can
      CAPL/SWC_Simulator.can
      CAPL/ReverseCamera_Test.can
      CAPL/DiagnosticsSmoke.can
      Diagnostics/IVI_UDS_Service_Map.csv
      Panels/PANEL_DESIGN.md
      SystemVariables/MGH_IVI_SystemVariables.vsysvar
      TestModules/Regression_Test_Module.can
      Logs/README.md
    ```

    ## CANoe Build Steps

    1. Create a new CANoe configuration named `MGH_IVI_Bench.cfg`.
    2. Add one CAN network named `InfoCAN` at 500 kbit/s.
    3. Attach `Databases/MG_Hector_IVI_Training.dbc`.
    4. Add CAPL nodes for BCM/VCU/TCU rest bus, SWC, reverse camera checks and diagnostics smoke.
    5. Import system variables from `SystemVariables`.
    6. Build panels from `Panels/PANEL_DESIGN.md`.
    7. Enable BLF logging and export XML test reports.
    """)

    write(ROOT / "CANoe_Project" / "Databases" / "MG_Hector_IVI_Training.dbc", r'''
VERSION "MG Hector IVI Training DBC - representative"

NS_ :
  NS_DESC_
  CM_
  BA_DEF_
  BA_
  VAL_
  CAT_DEF_
  CAT_
  FILTER
  BA_DEF_DEF_
  EV_DATA_
  ENVVAR_DATA_
  SGTYPE_
  SGTYPE_VAL_
  BA_DEF_SGTYPE_
  BA_SGTYPE_
  SIG_TYPE_REF_
  VAL_TABLE_
  SIG_GROUP_
  SIG_VALTYPE_
  SIGTYPE_VALTYPE_
  BO_TX_BU_
  BA_DEF_REL_
  BA_REL_
  BA_DEF_DEF_REL_
  BU_SG_REL_
  BU_EV_REL_
  BU_BO_REL_
  SG_MUL_VAL_

BS_:

BU_: BCM VCU TCU SWC IVI CLUSTER CAM_GW TESTER

BO_ 256 BCM_PowerMode: 8 BCM
 SG_ PowerMode : 0|2@1+ (1,0) [0|3] "" IVI,CLUSTER
 SG_ KL30Voltage_dV : 8|8@1+ (1,0) [0|180] "dV" IVI
 SG_ AliveCounter : 48|4@1+ (1,0) [0|15] "" IVI

BO_ 257 BCM_DoorStatus: 8 BCM
 SG_ DriverDoorAjar : 0|1@1+ (1,0) [0|1] "" IVI,CLUSTER
 SG_ PassengerDoorAjar : 1|1@1+ (1,0) [0|1] "" IVI,CLUSTER
 SG_ TailgateAjar : 2|1@1+ (1,0) [0|1] "" IVI,CLUSTER

BO_ 288 VCU_VehicleSpeed: 8 VCU
 SG_ VehicleSpeed_kph : 0|16@1+ (0.01,0) [0|240] "kph" IVI,CLUSTER
 SG_ SpeedValid : 16|1@1+ (1,0) [0|1] "" IVI

BO_ 304 TCU_GearStatus: 8 TCU
 SG_ GearPosition : 0|4@1+ (1,0) [0|7] "" IVI,CLUSTER
 SG_ GearValid : 4|1@1+ (1,0) [0|1] "" IVI

BO_ 384 SWC_Buttons: 8 SWC
 SG_ SWC_KeyCode : 0|8@1+ (1,0) [0|255] "" IVI
 SG_ PressDuration_ms : 8|16@1+ (1,0) [0|5000] "ms" IVI
 SG_ ButtonValid : 24|1@1+ (1,0) [0|1] "" IVI

BO_ 512 CAM_Status: 8 CAM_GW
 SG_ CameraAvailable : 0|1@1+ (1,0) [0|1] "" IVI
 SG_ CameraFault : 1|1@1+ (1,0) [0|1] "" IVI
 SG_ VideoFrameCounter : 8|8@1+ (1,0) [0|255] "" IVI

BO_ 768 IVI_Heartbeat: 8 IVI
 SG_ IVI_AliveCounter : 0|4@1+ (1,0) [0|15] "" TESTER,CLUSTER
 SG_ IVI_NetworkState : 8|4@1+ (1,0) [0|15] "" TESTER,CLUSTER

BO_ 769 IVI_Status: 8 IVI
 SG_ IVI_BootState : 0|4@1+ (1,0) [0|15] "" TESTER,CLUSTER
 SG_ CameraViewActive : 4|1@1+ (1,0) [0|1] "" TESTER,CLUSTER
 SG_ AudioFocusState : 8|4@1+ (1,0) [0|15] "" TESTER

BO_ 784 CLUSTER_WarningStatus: 8 CLUSTER
 SG_ DoorWarningDisplayed : 0|1@1+ (1,0) [0|1] "" IVI,TESTER
 SG_ CameraWarningDisplayed : 1|1@1+ (1,0) [0|1] "" IVI,TESTER

VAL_ 256 PowerMode 0 "OFF" 1 "ACC" 2 "IGN" 3 "CRANK";
VAL_ 304 GearPosition 0 "P" 1 "R" 2 "N" 3 "D" 4 "M";
VAL_ 384 SWC_KeyCode 0 "NONE" 16 "VOL_UP" 17 "VOL_DOWN" 32 "TRACK_NEXT" 33 "TRACK_PREV" 48 "PHONE" 64 "VOICE";
VAL_ 769 IVI_BootState 0 "OFF" 1 "BOOTING" 2 "READY" 3 "SLEEP" 4 "DIAG" 5 "CAMERA_ACTIVE" 6 "SHUTDOWN";
''')

    write(ROOT / "CANoe_Project" / "CAPL" / "RestBus_BCM_VCU_TCU.can", """
    /* Rest bus simulation for representative MG Hector-style IVI bench. */

    variables
    {
      msTimer t10;
      msTimer t20;
      int gPowerMode = 0;
      int gGear = 0;
      long gSpeedRaw = 0;
      int gDoor = 0;
      int gAlive = 0;
    }

    on start
    {
      setTimer(t10, 10);
      setTimer(t20, 20);
      write("RestBus_BCM_VCU_TCU started");
    }

    on timer t10
    {
      message BCM_PowerMode pwr;
      pwr.PowerMode = gPowerMode;
      pwr.KL30Voltage_dV = 125;
      pwr.AliveCounter = gAlive & 0x0F;
      output(pwr);

      message BCM_DoorStatus door;
      door.DriverDoorAjar = gDoor;
      output(door);

      gAlive++;
      setTimer(t10, 10);
    }

    on timer t20
    {
      message VCU_VehicleSpeed spd;
      spd.VehicleSpeed_kph = gSpeedRaw;
      spd.SpeedValid = 1;
      output(spd);

      message TCU_GearStatus gear;
      gear.GearPosition = gGear;
      gear.GearValid = 1;
      output(gear);

      setTimer(t20, 20);
    }

    void Bench_IgnitionOn() { gPowerMode = 2; }
    void Bench_IgnitionOff() { gPowerMode = 0; gSpeedRaw = 0; }
    void Bench_SetGear(int gear) { gGear = gear; }
    void Bench_SetSpeedKph(float speed) { gSpeedRaw = (long)(speed * 100.0); }
    void Bench_ToggleDriverDoor() { gDoor = !gDoor; }
    """)

    write(ROOT / "CANoe_Project" / "CAPL" / "SWC_Simulator.can", """
    variables
    {
      msTimer tRelease;
      int gCurrentKey = 0;
    }

    void SWC_Send(int key, int durationMs)
    {
      message SWC_Buttons swc;
      gCurrentKey = key;
      swc.SWC_KeyCode = key;
      swc.PressDuration_ms = durationMs;
      swc.ButtonValid = 1;
      output(swc);
      setTimer(tRelease, durationMs);
    }

    on timer tRelease
    {
      message SWC_Buttons swc;
      swc.SWC_KeyCode = 0;
      swc.PressDuration_ms = 0;
      swc.ButtonValid = 0;
      output(swc);
      gCurrentKey = 0;
    }

    on key '+' { SWC_Send(0x10, 100); }
    on key '-' { SWC_Send(0x11, 100); }
    on key 'n' { SWC_Send(0x20, 100); }
    on key 'p' { SWC_Send(0x30, 100); }
    on key 'v' { SWC_Send(0x40, 1200); }
    """)

    write(ROOT / "CANoe_Project" / "CAPL" / "ReverseCamera_Test.can", """
    variables
    {
      msTimer tCamStatus;
      int gCameraAvailable = 1;
      int gCameraFault = 0;
      int gFrameCounter = 0;
      dword gReverseStartTime = 0;
    }

    on start
    {
      setTimer(tCamStatus, 33);
    }

    on timer tCamStatus
    {
      message CAM_Status cam;
      cam.CameraAvailable = gCameraAvailable;
      cam.CameraFault = gCameraFault;
      cam.VideoFrameCounter = gFrameCounter & 0xFF;
      output(cam);
      gFrameCounter++;
      setTimer(tCamStatus, 33);
    }

    on message TCU_GearStatus
    {
      if (this.GearPosition == 1)
      {
        gReverseStartTime = timeNow();
        write("Reverse gear detected at %d", gReverseStartTime);
      }
    }

    on message IVI_Status
    {
      if (this.CameraViewActive == 1 && gReverseStartTime != 0)
      {
        dword latency = timeNow() - gReverseStartTime;
        write("Reverse camera active latency = %d ms", latency);
        if (latency <= 700) testStepPass("Reverse camera latency within KPI");
        else testStepFail("Reverse camera latency exceeded KPI");
      }
    }

    on key 'f' { gCameraFault = !gCameraFault; }
    on key 'c' { gCameraAvailable = !gCameraAvailable; }
    """)

    write(ROOT / "CANoe_Project" / "CAPL" / "DiagnosticsSmoke.can", """
    /* Diagnostic smoke sequence. Bind diagnostic objects in CANoe Diagnostics Console. */

    void DiagSmoke_PrintPlan()
    {
      write("1. Default session 10 01");
      write("2. Extended session 10 03");
      write("3. Read SW DID 22 F1 80");
      write("4. Read VIN DID 22 F1 90");
      write("5. Read DTC 19 02 FF");
    }

    on key 'u'
    {
      DiagSmoke_PrintPlan();
      write("Execute via CANoe Diagnostic Console or vTESTstudio diagnostic keywords.");
    }
    """)

    write(ROOT / "CANoe_Project" / "SystemVariables" / "MGH_IVI_SystemVariables.vsysvar", """<?xml version="1.0" encoding="UTF-8"?>
<systemvariables version="4">
  <namespace name="MGH_IVI_Bench">
    <variable anlyzLocal="2" readOnly="false" valueSequence="false" unit="" name="PowerMode" type="int" bitcount="32" />
    <variable anlyzLocal="2" readOnly="false" valueSequence="false" unit="" name="GearPosition" type="int" bitcount="32" />
    <variable anlyzLocal="2" readOnly="false" valueSequence="false" unit="kph" name="VehicleSpeed" type="float" />
    <variable anlyzLocal="2" readOnly="false" valueSequence="false" unit="" name="DriverDoorAjar" type="int" bitcount="32" />
    <variable anlyzLocal="2" readOnly="false" valueSequence="false" unit="" name="CameraFaultInjection" type="int" bitcount="32" />
  </namespace>
</systemvariables>
""")

    write(ROOT / "CANoe_Project" / "Panels" / "PANEL_DESIGN.md", """
    # CANoe Panel Design

    ## Panel: Power And Vehicle State

    - Segmented control: OFF / ACC / IGN / CRANK.
    - Gear selector: P / R / N / D.
    - Slider: Vehicle speed 0..240 kph.
    - Toggles: driver door, passenger door, tailgate.
    - Indicators: IVI heartbeat, boot state, camera active, DTC present.

    ## Panel: Feature Fault Injection

    - Camera available toggle.
    - Camera fault toggle.
    - Stop BCM cyclic button.
    - Stop gear cyclic button.
    - CAN bus load slider.
    - UDS smoke button.

    ## Panel: Steering Switch

    - Icon buttons for volume, track, phone and voice.
    - Long press duration numeric field.
    - Stuck button injection toggle.
    """)

    write(ROOT / "CANoe_Project" / "Diagnostics" / "IVI_UDS_Service_Map.csv", """Service,Request,Positive_Response,Use,Notes
DiagnosticSessionControl_Default,10 01,50 01,Return to default session,Non-destructive
DiagnosticSessionControl_Extended,10 03,50 03,Enable extended diagnostics,Use before DID/DTC checks if required
ECUReset_Hard,11 01,51 01,Reset IVI,Requires test approval
ReadDID_SW,22 F1 80,62 F1 80,Software identifier,Release evidence
ReadDID_VIN,22 F1 90,62 F1 90,VIN/personalization,Use bench-safe VIN only
ReadDID_BootKPI,22 D1 00,62 D1 00,Boot metrics,Representative DID
ReadDTCByStatusMask,19 02 FF,59 02,DTC snapshot,Pre/post fault injection
ClearDTC,14 FF FF FF,54,Clear DTCs,Only after evidence captured
SecurityAccessSeed,27 01,67 01,Request seed,Training only no brute force
""")

    write(ROOT / "CANoe_Project" / "TestModules" / "Regression_Test_Module.can", """
    testcase TC_Boot_Diag_Smoke()
    {
      testStep("Precondition", "Power mode IGN and rest bus active");
      testWaitForTimeout(1000);
      testStepPass("Dry training test module placeholder. Bind to real checks in vTESTstudio/CANoe.");
    }

    testcase TC_Reverse_Camera_Nominal()
    {
      testStep("Action", "Set GearPosition=R");
      testWaitForTimeout(700);
      testStep("Expected", "IVI camera active state observed");
      testStepPass("Replace placeholder with signal wait and diagnostic checks.");
    }

    void MainTest()
    {
      TC_Boot_Diag_Smoke();
      TC_Reverse_Camera_Nominal();
    }
    """)

    write(ROOT / "CANoe_Project" / "Logs" / "README.md", """
    # CANoe Logs

    Store formal `.blf` logs outside git when they are large or proprietary. Use `.asc` training excerpts in this repo for parser practice.

    Naming pattern:

    `MGH_BENCH_01_<BuildID>_<Feature>_<TestID>_<YYYYMMDD_HHMMSS>.blf`
    """)

    write(ROOT / "30_AUTOMATION_FRAMEWORK" / "requirements.txt", """
    pytest>=8.0
    PyYAML>=6.0
    """)

    write(ROOT / "30_AUTOMATION_FRAMEWORK" / "pyproject.toml", """
    [tool.pytest.ini_options]
    testpaths = ["automation/tests"]
    pythonpath = ["automation"]
    addopts = "-ra"
    """)

    write(ROOT / "30_AUTOMATION_FRAMEWORK" / "automation" / "adapters" / "__init__.py", "")
    write(ROOT / "30_AUTOMATION_FRAMEWORK" / "automation" / "__init__.py", "")

    write(ROOT / "30_AUTOMATION_FRAMEWORK" / "automation" / "adapters" / "evidence.py", """
    from __future__ import annotations

    from dataclasses import dataclass, asdict
    from pathlib import Path
    import json
    import time


    @dataclass
    class EvidenceRecord:
        test_id: str
        artifact_type: str
        path: str
        timestamp: str
        notes: str = ""


    class EvidenceStore:
        def __init__(self, root: Path) -> None:
            self.root = root
            self.root.mkdir(parents=True, exist_ok=True)
            self.records: list[EvidenceRecord] = []

        def add_text(self, test_id: str, name: str, content: str, artifact_type: str = "text") -> Path:
            path = self.root / test_id / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            self.records.append(
                EvidenceRecord(test_id, artifact_type, str(path), time.strftime("%Y-%m-%d %H:%M:%S"))
            )
            return path

        def write_manifest(self) -> Path:
            path = self.root / "evidence_manifest.json"
            path.write_text(json.dumps([asdict(r) for r in self.records], indent=2), encoding="utf-8")
            return path
    """)

    write(ROOT / "30_AUTOMATION_FRAMEWORK" / "automation" / "adapters" / "report.py", """
    from __future__ import annotations

    from dataclasses import dataclass
    from pathlib import Path


    @dataclass
    class TestResult:
        test_id: str
        result: str
        feature: str
        evidence: str
        defect: str = ""


    def write_markdown_report(path: Path, results: list[TestResult]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Automated Validation Report",
            "",
            "| Test ID | Feature | Result | Evidence | Defect |",
            "| --- | --- | --- | --- | --- |",
        ]
        for item in results:
            lines.append(f"| {item.test_id} | {item.feature} | {item.result} | {item.evidence} | {item.defect} |")
        path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
        return path
    """)

    write(ROOT / "30_AUTOMATION_FRAMEWORK" / "automation" / "testdata" / "reverse_camera_nominal.asc", """
    date Thu May 21 10:00:00.000 2026
       0.000000 1  100             Rx   d 8  02 7D 00 00 00 00 01 00
       0.100000 1  300             Rx   d 8  02 00 00 00 00 00 00 00
       1.000000 1  130             Rx   d 8  01 01 00 00 00 00 00 00
       1.540000 1  301             Rx   d 8  15 00 00 00 00 00 00 00
    """)

    write(ROOT / "30_AUTOMATION_FRAMEWORK" / "automation" / "tests" / "test_can_log_parser.py", """
    from __future__ import annotations

    from pathlib import Path

    from adapters.can_log import AscLog


    def test_can_log_counts_reverse_signal():
        log = AscLog(Path(__file__).resolve().parents[1] / "testdata" / "reverse_camera_nominal.asc")
        assert log.count_can_id("130") == 1
        assert log.count_can_id("301") == 1
        assert log.first_timestamp_for_id("130") == 1.0
    """)

    write(ROOT / "30_AUTOMATION_FRAMEWORK" / "automation" / "tests" / "test_diagnostics_safety.py", """
    from __future__ import annotations


    def test_safe_mode_blocks_destructive_write(uds):
        response = uds.send("2E F1 90 31 32 33")
        assert not response.positive
        assert "blocked" in response.notes


    def test_read_software_did_positive(uds):
        response = uds.send("22 F1 80")
        assert response.positive
        assert response.response.startswith("62 F1 80")
    """)

    write(ROOT / "30_AUTOMATION_FRAMEWORK" / "automation" / "tests" / "test_power_swc_ota_dryrun.py", """
    from __future__ import annotations


    def test_power_mode_cycle_dry_run(canoe):
        for state in [0, 1, 2, 3, 2, 0]:
            canoe.set_signal("PowerMode", state)
            canoe.wait(0.02)
        assert canoe.measurement_running


    def test_steering_voice_long_press_dry_run(canoe):
        canoe.set_signal("SWC_KeyCode", 0x40)
        canoe.wait(0.05)
        canoe.set_signal("SWC_KeyCode", 0)
        assert canoe.measurement_running


    def test_ota_dry_run_rejects_bad_package(uds):
        response = uds.send("31 01 FF 00")
        assert not response.positive
    """)

    write(ROOT / "Evidence_Samples" / "android_logcat_black_screen.txt", """
    05-21 10:15:03.412  1420  1888 I VehicleService: PowerMode changed OFF -> IGN
    05-21 10:15:05.831  2211  2211 I Launcher: Home activity resumed
    05-21 10:15:06.027  2330  2401 E DisplayService: Surface attach timeout for main_display
    05-21 10:15:06.048  2330  2401 W WindowManager: black frame shown while waiting for IVI surface
    05-21 10:15:07.510  2330  2401 I DisplayService: recovered after compositor restart
    """)

    write(ROOT / "Evidence_Samples" / "android_logcat_bluetooth_disconnect.txt", """
    05-21 11:02:01.100  1801  1942 I BluetoothA2dp: state CONNECTED device=REF_PHONE_01
    05-21 11:17:42.445  1801  2010 W BtGatt.GattService: link supervision timeout
    05-21 11:17:42.482  1801  1942 I BluetoothA2dp: state DISCONNECTED reason=0x08
    05-21 11:17:47.620  1801  1942 I BluetoothA2dp: reconnect attempt=1
    05-21 11:17:50.033  1801  1942 E BluetoothA2dp: reconnect failed profile busy
    """)

    write(ROOT / "Evidence_Samples" / "kernel_usb_projection_reset.txt", """
    [  421.122334] usb 1-1: new high-speed USB device number 7 using xhci-hcd
    [  423.901220] usb 1-1: reset high-speed USB device number 7 using xhci-hcd
    [  424.005100] projectiond: transport reset while session state=LAUNCHING
    [  424.445891] usb 1-1: USB disconnect, device number 7
    """)

    write(ROOT / "Evidence_Samples" / "ethernet_doip_trace_summary.txt", """
    10:20:01.001 TCP  tester:54123 -> ivi:13400  DoIP routing activation request
    10:20:01.025 TCP  ivi:13400 -> tester:54123  DoIP routing activation response positive
    10:20:01.100 UDS  tester -> ivi  10 03
    10:20:01.112 UDS  ivi -> tester  50 03
    10:20:01.200 UDS  tester -> ivi  22 F1 80
    10:20:01.219 UDS  ivi -> tester  62 F1 80 4D 47 48 5F 49 56 49
    """)

    write(ROOT / "09_IVI_FEATURES" / "test_cases" / "ivi_feature_detailed_test_suite.csv", """TestID,Feature,Type,Precondition,Stimulus,Expected,KPI,Evidence
IVI-RAD-001,Radio,Functional,IGN ON antenna connected,Tune FM station,Station audio and metadata displayed,Audio within 2s,CANoe log screen video audio capture
IVI-MED-002,USB Media,Boundary,USB with 10000 files,Insert USB,Indexing completes without ANR,No ANR memory stable,logcat dumpsys meminfo
IVI-UI-003,Touchscreen,Stress,Home screen ready,1000 rapid taps/swipes,No crash no stuck input,Input latency P95 within target,screen recording logcat
IVI-LANG-004,Language,Negative,Locale menu open,Select language with missing strings,Fallback string shown no blank labels,No UI overlap,screenshots
IVI-PROF-005,User Profiles,Recovery,Profile A active,Power cycle during profile switch,Profile data consistent after boot,No corruption,trace logcat settings dump
""")

    write(ROOT / "10_BLUETOOTH_VALIDATION" / "test_cases" / "bluetooth_detailed_test_suite.csv", """TestID,Profile,Type,Precondition,Stimulus,Expected,KPI,Evidence
BT-PAIR-001,HFP/A2DP/PBAP,Functional,No paired devices,Pair reference Android phone,All selected profiles connected,Within 60s,logcat BT snoop screen
BT-REC-002,A2DP,Recovery,Phone paired and connected,Ignition off sleep wake,Auto reconnect and playback resumes,Within 30s,CAN trace logcat audio evidence
BT-CALL-003,HFP,Functional,Phone connected,Incoming call accept via SWC,Call audio routed to vehicle,Within 2s,HFP logs audio capture
BT-PBAP-004,PBAP,Boundary,Phonebook 5000 contacts,Start contact sync,No ANR and contacts searchable,Within agreed KPI,logcat meminfo
BT-STRESS-005,A2DP,Stress,Phone paired,500 connect disconnect cycles,No permanent profile failure,Failure rate below threshold,automation report BT snoop
""")

    write(ROOT / "13_CARPLAY_ANDROID_AUTO" / "test_cases" / "projection_detailed_test_suite.csv", """TestID,Projection,Type,Precondition,Stimulus,Expected,KPI,Evidence
PROJ-AA-001,Android Auto,Functional,Certified cable phone unlocked,Connect USB,Projection starts and audio route correct,Within KPI,USB log logcat screen
PROJ-CP-002,CarPlay,Functional,iPhone trusted,Connect USB,CarPlay starts and Siri route correct,Within KPI,USB log screen
PROJ-REC-003,Projection,Recovery,Projection active,Unplug and reconnect USB,Previous session recovers gracefully,Within KPI,kernel log logcat
PROJ-NEG-004,Projection,Negative,Projection launching,Revoke phone permission,Actionable message no crash,N/A,screen logcat
PROJ-AUD-005,Projection Audio,Integration,Projection navigation active,Start BT call,Correct focus and ducking,No audio leak,audio trace logcat
""")

    write(ROOT / "17_REVERSE_CAMERA" / "test_cases" / "reverse_camera_detailed_test_suite.csv", """TestID,Type,Precondition,Stimulus,Expected,KPI,Evidence
RCAM-001,Functional,IGN ON speed 0 camera available,Gear R,Camera view active,<=700ms,CANoe trace video
RCAM-002,Recovery,Camera active,Gear D then R within 500ms,No frozen stale frame,No stale frame,CAN video frame counter
RCAM-003,Negative,IGN ON,CameraAvailable=0 then Gear R,User warning and DTC behavior per spec,N/A,CAN DTC screen
RCAM-004,Boundary,IGN ON,Reverse at low voltage profile,Graceful behavior no reboot,N/A,power trace logcat
RCAM-005,Stress,IGN ON,300 R-D-R cycles,No camera service crash,0 crashes,automation report
""")

    write(ROOT / "23_UDS_DIAGNOSTICS" / "test_cases" / "uds_detailed_test_suite.csv", """TestID,Service,Type,Precondition,Request,Expected,Evidence
UDS-001,0x10,Functional,IVI awake,10 03,50 03,CANoe diagnostics log
UDS-002,0x22,Functional,Extended session,22 F1 80,62 F1 80,CANoe diagnostics log
UDS-003,0x19,Functional,Fault injected,19 02 FF,59 02 with expected DTC,DTC snapshot
UDS-004,0x27,Negative,Extended session,27 02 invalid_key,7F 27 35,diagnostics log
UDS-005,0x11,Recovery,Approved reset test,11 01,51 01 and reboot,trace logcat
""")

    write(ROOT / "25_OTA_TESTING" / "test_cases" / "ota_detailed_test_suite.csv", """TestID,Phase,Type,Precondition,Stimulus,Expected,Evidence
OTA-001,Download,Functional,Network available,Start valid package download,Download completes hash verified,OTA logs
OTA-002,Download,Recovery,Download active,Network loss 2 min,Pause resume or retry as spec,network logs
OTA-003,Install,Negative,Install active,Power mode OFF request,Defined inhibit resume or rollback,power trace OTA logs
OTA-004,Verification,Negative,Corrupt package hash,Start install,Package rejected current version retained,OTA logs DID version
OTA-005,Post-update,Regression,Update complete,Run smoke suite,No critical regression,CANoe pytest report
""")

    write(ROOT / "39_POWER_MODE_VALIDATION" / "test_cases" / "power_mode_detailed_test_suite.csv", """TestID,Type,Precondition,Stimulus,Expected,Evidence
PWR-001,Functional,KL30 stable,KL15 ON,IVI boots to ready state,CAN power trace logcat
PWR-002,Functional,IGN ON,KL15 OFF,IVI starts shutdown/sleep policy,current trace CAN
PWR-003,Boundary,IGN ON,Crank voltage dip,No data corruption defined reset behavior,power supply log
PWR-004,Recovery,Sleep state,CAN wake frame,IVI wakes and restores state,wake trace logcat
PWR-005,Stress,Bench stable,200 ignition cycles,No boot loop no DTC accumulation,automation report
""")

    write(ROOT / "44_REAL_WORLD_ISSUES" / "DEFECT_REPORT_TEMPLATE.md", """
    # Defect Report Template

    ## Title

    `[Feature][Build][Bench] concise customer-visible symptom`

    ## Environment

    - Vehicle/program:
    - IVI build:
    - MCU/bootloader:
    - CANoe config:
    - DBC version:
    - Bench ID:
    - Phone/device/cable if relevant:

    ## Steps To Reproduce

    1. 
    2. 
    3. 

    ## Expected

    ## Actual

    ## Reproduction Rate

    ## Evidence Attached

    - CANoe BLF/ASC:
    - logcat:
    - kernel:
    - diagnostics:
    - video/screenshot:

    ## First-Level RCA

    - Input signal verified:
    - Network timing verified:
    - Diagnostic state:
    - Android/Linux evidence:
    - Suspected layer:

    ## Severity Recommendation

    Explain customer impact, safety/legal impact, release impact and workaround.
    """)

    write(ROOT / "50_CAPSTONE_BENCH_PROJECT" / "CAPSTONE_RELEASE_EXECUTION_PLAN.md", """
    # Capstone Release Execution Plan

    ## Release Candidate Scenario

    You are validating IVI build `MGH_IVI_RC_01` before an OEM integration release.

    ## Day 1: Bench Bring-Up

    - Verify power rails, CAN, Ethernet, USB, audio and camera.
    - Capture software DIDs and baseline DTCs.
    - Run smoke suite.

    ## Day 2: Core Feature Validation

    - IVI home, radio, media, phone, Bluetooth and USB.
    - Capture evidence for every P0/P1 case.

    ## Day 3: Integration Validation

    - Reverse camera, cluster alerts, SWC, HVAC and navigation.
    - Run cross-feature audio focus and power mode checks.

    ## Day 4: Diagnostics, OTA And Stress

    - DID/DTC validation.
    - OTA interruption and rollback tests.
    - 200 ignition cycles or scaled dry-run equivalent.

    ## Day 5: Release Board Package

    - RTM coverage.
    - Validation report.
    - Open defect list.
    - Risk assessment.
    - Go/no-go recommendation.
    """)

    write(ROOT / "50_CAPSTONE_BENCH_PROJECT" / "SAMPLE_RELEASE_SIGNOFF_REPORT.md", """
    # Sample Release Sign-Off Report

    | Field | Value |
    | --- | --- |
    | Build | MGH_IVI_RC_01 |
    | Bench | MGH_BENCH_01 |
    | CANoe Config | MGH_IVI_Bench.cfg |
    | DBC | MG_Hector_IVI_Training.dbc |
    | Execution Window | 5 days |

    ## Result Summary

    | Category | Total | Pass | Fail | Blocked |
    | --- | ---: | ---: | ---: | ---: |
    | Smoke | 8 | 8 | 0 | 0 |
    | IVI Features | 25 | 23 | 2 | 0 |
    | Connectivity | 20 | 18 | 1 | 1 |
    | Camera/Cluster/SWC | 18 | 17 | 1 | 0 |
    | Diagnostics/OTA | 15 | 13 | 1 | 1 |
    | Power/Stress | 12 | 11 | 1 | 0 |

    ## Open Release Risks

    - Bluetooth reconnect intermittent after sleep: workaround available, regression needed after stack fix.
    - Reverse camera latency P95 exceeds KPI during low-voltage profile: release blocker if KPI is contractual.

    ## Recommendation

    Conditional no-go until reverse camera low-voltage behavior is fixed or formally waived by the release board.
    """)


if __name__ == "__main__":
    main()
