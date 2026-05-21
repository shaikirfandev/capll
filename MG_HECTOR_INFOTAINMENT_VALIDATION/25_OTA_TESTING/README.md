# OTA Testing

This module is part of the MG Hector-style infotainment validation lab pack. It is written for bench validation engineers who need to connect CANoe, CAPL, Python, adb, diagnostic services and OEM release evidence into one working process.

Scope: download, install, rollback, interruption and post-update validation.

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
