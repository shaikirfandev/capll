# Android Memory Analysis Workflow

1. Capture baseline: `adb shell dumpsys meminfo`.
2. Start feature stress case and collect memory every minute.
3. Capture heap dump for suspected process.
4. Compare Java heap, native heap, graphics, ashmem, binder and thread count.
5. Correlate memory growth with user actions and logs.
6. Confirm leak by repeated cycles and recovery after process restart.
