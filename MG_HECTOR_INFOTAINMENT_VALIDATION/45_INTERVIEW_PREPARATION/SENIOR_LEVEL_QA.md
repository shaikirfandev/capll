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
