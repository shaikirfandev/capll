# Debugging Scenarios: Video Validation

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
