# Bench Lab: Vector Tools

## Lab Steps

1. Load `CANoe_Project/Databases/MG_Hector_IVI_Training.dbc`.
2. Start rest bus simulation.
3. Set power mode to IGN.
4. Verify IVI heartbeat and boot state.
5. Execute the module-specific nominal stimulus.
6. Execute one negative stimulus and one recovery stimulus.
7. Capture evidence and update traceability.

## Expected Artifacts

- Completed test case CSV row.
- CAN trace.
- Logcat/kernel evidence if applicable.
- UDS DID/DTC snapshot.
- RCA note for any failure.
- Release gate decision.
