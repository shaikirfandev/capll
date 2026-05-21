# Bluetooth Stress Scenarios

1. Pair phone, power cycle IVI, verify auto reconnect within KPI.
2. Pair five devices, switch priority, verify last connected behavior.
3. Start A2DP playback, inject CAN sleep request, wake and verify playback state.
4. Run active call, switch to reverse camera and verify audio focus policy.
5. Sync 5000 contacts and verify no UI freeze or ANR.
6. Move phone out of range for 60 seconds, return and verify recovery.
7. Toggle phone Bluetooth 100 times and collect HCI snoop/logcat evidence.
