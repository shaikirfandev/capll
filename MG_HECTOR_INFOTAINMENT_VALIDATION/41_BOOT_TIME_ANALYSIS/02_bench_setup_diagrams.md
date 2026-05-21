# Bench Setup Diagrams: Boot Time Analysis

## Infotainment Validation Bench

```mermaid
flowchart LR
    PSU[Programmable DC Power Supply\n12 V nominal, current limit] --> Harness[Bench Harness\nKL30 KL15 ACC GND]
    Harness --> IVI[MG Hector-style IVI Head Unit]
    CANoe[Vector CANoe + VN Interface] <-->|CAN HS / CAN FD| Harness
    ETH[Ethernet TAP / Switch] <-->|100/1000BASE-T1 via media converter| IVI
    Phone[Reference Phones\niOS and Android] <-->|BT/WiFi/USB| IVI
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
