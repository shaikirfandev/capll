# Evidence Collection Checklist: Android Automotive

## Mandatory Evidence

- CANoe BLF or ASC with 10 seconds before and after stimulus.
- CANoe XML/PDF test report or pytest report.
- Software version DID and build fingerprint.
- Pre-test and post-test DTC snapshot.
- Android logcat for the complete test window.
- Kernel/system logs if USB, camera, audio, Ethernet, boot or power behavior is involved.
- Screenshot or video for user-visible IVI behavior.
- Bench metadata: bench ID, tester, build, DBC, harness revision and date.

## Evidence Naming

`MGH_BENCH_01_<BuildID>_Android_Automotive_<TestID>_<YYYYMMDD_HHMMSS>`

## Reviewer Questions The Evidence Must Answer

1. What exact stimulus was applied?
2. What did the IVI receive on the vehicle network?
3. What did the IVI show, play, publish or diagnose?
4. Was the failure reproducible?
5. Which layer is most likely responsible?
