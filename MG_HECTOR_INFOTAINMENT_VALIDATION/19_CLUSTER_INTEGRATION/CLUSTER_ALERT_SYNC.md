# Cluster Alert Synchronization

Validate that IVI and cluster present warnings consistently. Typical checks include warning text, icon/tell-tale state, priority, chime policy, acknowledgement behavior and timeout.

## Example Alert Flow

1. CANoe injects `DoorAjar = 1` while ignition is ON.
2. Cluster warning appears.
3. IVI vehicle status page shows door open.
4. Chime routing follows audio focus policy.
5. Clearing the signal removes both warnings within KPI.
