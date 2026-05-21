# adb logcat Cheatsheet

```bash
adb devices
adb shell getprop ro.build.fingerprint
adb logcat -c
adb logcat -v threadtime > evidence/logcat.txt
adb shell dumpsys activity processes
adb shell dumpsys meminfo
adb shell dumpsys cpuinfo
adb bugreport evidence/bugreport.zip
```

For crash/ANR: capture `logcat`, `dropbox`, `tombstones`, `anr` traces if access is available and build policy permits.
