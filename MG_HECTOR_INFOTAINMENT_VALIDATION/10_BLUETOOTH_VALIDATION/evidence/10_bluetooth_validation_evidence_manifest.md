# Evidence Manifest: Bluetooth Validation

| Artifact | Required | Example Path |
| --- | --- | --- |
| CAN trace | Yes | `evidence/can/<test_id>.blf` |
| CANoe report | Yes | `evidence/reports/<test_id>.xml` |
| adb logcat | Conditional | `evidence/android/<test_id>_logcat.txt` |
| Kernel log | Conditional | `evidence/linux/<test_id>_dmesg.txt` |
| UDS readout | Yes | `evidence/diagnostics/<test_id>_uds.txt` |
| Screen/video | Conditional | `evidence/video/<test_id>.mp4` |
| RCA | On failure | `debugging/root_cause_analysis.md` |
