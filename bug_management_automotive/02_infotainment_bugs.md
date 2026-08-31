# Infotainment — Bug Reproduction, Reporting, Resolving & Diagnostics

> **Domain**: Head Unit (HU) — Android Automotive OS / QNX / Embedded Linux
> **Sub-systems**: Android Auto · Apple CarPlay · Bluetooth (A2DP, HFP, AVRCP) · Navigation · Media · Voice Assistant · Wi-Fi Hotspot · USB Audio
> **Tools**: ADB · Android Studio · Wireshark · CANoe · JIRA

---

## 1. Bug Categories in Infotainment

| Category | Description | Example |
|---------|-------------|---------|
| App Crash / ANR | Application freezes or is force-closed by Android | Navigation ANR after 45 min; media player crash on MP3 |
| Memory Leak | Memory grows continuously, never freed | Launcher heap grows 10 MB/hour → OOM after 3 hours |
| Display / HMI Bug | Screen freeze, blank, wrong content rendered | Screen goes black in reverse; wrong album art displayed |
| Audio Routing Bug | Wrong audio source plays through wrong output | Navigation voice played through rear speakers; phone call through media speaker |
| Connectivity Bug | Bluetooth, Wi-Fi, USB connect/disconnect issues | A2DP disconnects after 30 min; Android Auto drops every 15 min |
| Boot / Startup Bug | HU fails to boot correctly after update or power cycle | Black screen on boot; stuck at OEM splash screen |
| Performance Bug | Slow response, lag, jitter | Touch response > 1 s; animation stutters |
| CAN Integration Bug | HMI displays wrong CAN-sourced data | Wrong gear position on display; speed mismatch |
| OTA / Update Bug | Update fails or corrupts HU software | HU stuck on update screen after OTA push |
| Security Bug | Unauthorized access, privacy violation | USB device bypasses DRM; ADB enabled in production build |

---

## 2. Bug Scenario 1 — Navigation ANR After 45 Minutes of Continuous Use


### Bug Description
**Title:** Navigation app becomes unresponsive (ANR) after 40–50 min of active route guidance  
**Severity:** P1 — Customer-visible feature failure  
**Reported by:** 12 customer complaints, same app version (v4.2.1)  
**Frequency:** Reproducible consistently after ~45 min

### Reproduction Steps
```
Environment:
  HU OS: Android Automotive 12
  SW version: Navigation v4.2.1
  Hardware: Qualcomm SA8155P SoC
  Route: Long destination (> 50 km, continuous TBT active)

Steps:
  1. Set navigation to destination 80 km away (requires > 1 hour drive)
  2. Start driving; TBT (Turn-by-Turn) instructions active; screen on
  3. At ~43–47 min mark: touchscreen becomes unresponsive (frozen)
  4. System shows "Navigation not responding" dialog OR screen goes blank 8 s, then reboots
  5. Reproducible on bench with simulated GPS route playback
```

### Reproduction on Bench (No Vehicle Needed)
```bash
# On development HU (engineering build with ADB access):
# Step 1: Push a simulated NMEA GPS route file
adb push long_route_80km.nmea /data/local/tmp/

# Step 2: Start memory monitoring IN BACKGROUND before launching navigation
adb shell dumpsys meminfo com.oem.navigation > meminfo_T0.txt &

# Step 3: Launch navigation with GPS replay
adb shell am start -n com.oem.navigation/.MainActivity \
  --es "replay_nmea" "/data/local/tmp/long_route_80km.nmea"

# Step 4: Capture continuous logcat in background
adb logcat -b all -v threadtime > navlog_session.txt &

# Step 5: Every 10 min, snapshot memory
# T=10 min:
adb shell dumpsys meminfo com.oem.navigation > meminfo_T10.txt
# T=20:
adb shell dumpsys meminfo com.oem.navigation > meminfo_T20.txt
# T=40: (just before crash)
adb shell dumpsys meminfo com.oem.navigation > meminfo_T40.txt

# Step 6: Wait for ANR / crash
```

### ADB Log Analysis
```bash
grep -E "ANR|ActivityManager.*navigation|OutOfMemory|navigation.*died|GC_FOR_ALLOC" navlog_session.txt

# Findings:
04-17 14:43:11 E ActivityManager: ANR in com.oem.navigation
04-17 14:43:11 E ActivityManager: PID: 4321 | CPU usage: 99% for 60+ s
04-17 14:43:11 W art: Throwing OutOfMemoryError "Failed to allocate 4194304-byte array"
04-17 14:43:11 I GC: Alloc concurrent mark sweep GC freed 12KB, 2% free 480MB/486MB, paused 250ms total 1500ms
```

### Memory Growth Analysis
```
meminfo comparison:
  T=0  min: Heap Alloc = 48,200 KB
  T=10 min: Heap Alloc = 72,400 KB  (+24 MB)
  T=20 min: Heap Alloc = 96,100 KB  (+48 MB)
  T=40 min: Heap Alloc = 178,000 KB (+130 MB) → near heap limit (192 MB for this process)
  T=45 min: OOM → ANR → crash
  
Pattern: Linear heap growth = memory leak (not a one-time burst)
Growth rate: ~3 MB/min
```

### Root Cause Investigation — MAT (Memory Analyzer Tool)
```bash
# Dump heap just before expected crash (T=42 min):
adb shell am dumpheap com.oem.navigation /data/local/tmp/nav_heap.hprof
adb pull /data/local/tmp/nav_heap.hprof .

# Open in Eclipse MAT → Leak Suspects → Dominator Tree
```

**MAT Finding:**
```
Leak: Class = com.oem.navigation.render.MapTileCache
  Instance count: 3,840 (expected: ≤ 100)
  Retained heap: 128 MB
  GC Root path:
    static TileManager.sTileCache (ArrayList)
      → MapTile[3840]
        → Each MapTile holds: Bitmap (256×256 px; ARGB_8888 = 256 KB)
        
Root Cause: MapTileCache.evict() is never called when tiles scroll off screen.
  sTileCache is a static ArrayList → tiles never garbage collected.
  Each new tile loaded adds to list; nothing removes old tiles.
```

### Fix
```java
// Before fix: no eviction
public void addTile(MapTile tile) {
    sTileCache.add(tile);
}

// After fix: LRU cache with max size
private static final int MAX_TILES = 100;
public void addTile(MapTile tile) {
    if (sTileCache.size() >= MAX_TILES) {
        MapTile oldest = sTileCache.remove(0);  // FIFO eviction
        oldest.bitmap.recycle();                // free bitmap memory
    }
    sTileCache.add(tile);
}
```

### Verification After Fix
```bash
# Repeat 60-min GPS replay with memory monitoring
adb shell dumpsys meminfo com.oem.navigation

# T=0:  Heap Alloc = 48,000 KB
# T=30: Heap Alloc = 51,200 KB  (stable)
# T=60: Heap Alloc = 50,800 KB  (stable — eviction working)
# Result: No ANR, no OOM over 60 min → PASS
```

### Bug Report Template (JIRA)
```
Summary: [Infotainment][Navigation] ANR after 45 min of continuous route guidance

Severity: P1
Component: Navigation App
SW Version: v4.2.1
HW: SA8155P Development Board

Preconditions:
  - Engineering build with ADB access
  - Long-route GPS NMEA file ready

Steps to Reproduce:
  1. Push 80 km NMEA route file to /data/local/tmp/
  2. Launch navigation with GPS replay enabled
  3. Monitor meminfo every 10 min
  4. Observe ANR/crash at ~43–47 min mark

Actual: Navigation ANRS; screen frozen; "not responding" dialog
Expected: Navigation runs stably for full journey duration (≥ 2 hours)

Root Cause: MapTileCache static ArrayList — no eviction; heap fills within 45 min
Attachments: navlog_session.txt, nav_heap.hprof, meminfo_T0_T40.zip

Regression: New issue in v4.2.1 — was not present in v4.1.0
```

### Recurring Bug Pattern (Intermittent Reoccurrence)
```
IF this bug reappears after the fix is deployed:
  Step 1: Verify fix commit is in the current build:
      adb shell pm dump com.oem.navigation | grep versionName
      → Confirm version > 4.2.1 (fixed)
      
  Step 2: Check if tile eviction is actually running:
      adb logcat | grep "MapTileCache.evict"
      → If no eviction log lines → eviction code path not reached
      
  Step 3: Check for a NEW leak source (different class):
      Repeat MAT analysis — Dominator Tree may show different class at top
      
  Step 4: Check if route distance changed (longer than 80 km):
      Longer route = more tiles loaded = eviction buffer still too large
      → Reduce MAX_TILES from 100 to 60 if issue recurs on 120+ km routes
      
  Step 5: Run with LeakCanary enabled (debug build):
      → LeakCanary will auto-detect new leak source and report exact GC root path
```

---

## 3. Bug Scenario 2 — Android Auto Disconnects Every 30 Minutes

### Bug Description
**Title:** Android Auto (USB) drops connection repeatedly after ~30 min of use  
**Severity:** P2 — Major feature broken, workaround: reconnect USB  
**Frequency:** Reproducible with 3 phone models (Samsung S23, Pixel 7, OnePlus 11)

### Reproduction Steps
```
Environment:
  HU OS: Android Automotive 12
  Phone: Samsung Galaxy S23 (Android 14, AA v10.3)
  Cable: OEM-supplied USB-C to USB-A (AOA 2.0 capable)
  
Steps:
  1. Connect phone via USB to HU; Android Auto launches
  2. Start navigation + media playback (both projections active)
  3. Drive or simulate continuous use
  4. At ~28–32 min: Android Auto drops → phone shows "Disconnected from Android Auto"
  5. Reconnect USB → AA re-launches within 15 s
  6. Drop occurs again at ~30 min mark → consistent 30-min interval
```

### ADB Log Capture
```bash
# Capture from HU:
adb logcat -b all > aa_disconnect_log.txt

# Filter for AA events:
grep -E "AndroidAuto|AOA|USBDisconnect|HeartbeatTimeout|HUConnection" aa_disconnect_log.txt

# Finding:
04-17 11:30:01 W AndroidAuto: Heartbeat timeout: no ping received for 30000 ms
04-17 11:30:01 I AndroidAuto: Connection closed: reason=WATCHDOG_TIMEOUT
04-17 11:30:01 E USBHost: USB device disconnected: vendor=0x04E8 (Samsung)
04-17 11:30:02 I AndroidAuto: Session terminated; AA UI teardown
```

### Root Cause Analysis
```
Android Auto uses a heartbeat (keep-alive) ping every 5 s over the AOA USB protocol.
If no ping received for 30,000 ms (30 s) → AA watchdog kills connection.

Finding:
  At the 30 min mark, HU CPU load spikes to 95% (caused by:
    media decoder processing high-bitrate video ad in Google Maps turn-by-turn preview)
  → Android Auto heartbeat send() scheduled but delayed by CPU backpressure
  → Phone does not receive ping for 30+ s → phone-side watchdog closes connection
  
This explains the 30-min interval: it takes exactly 30 min of combined navigation + 
media for the map preloading and media decode queue to saturate CPU.
```

### Diagnostics — CPU Profile
```bash
# Capture CPU sample during the crash window (T=28–32 min):
adb shell top -d 1 -n 60 > cpu_T28_T32.txt | grep -E "omnav|media|AndroidAuto"

# Output at T=29 min:
PID   USER   CPU%   NAME
4321  system  48%   com.google.android.projection.gearhead  (AA)
4322  system  31%   com.oem.navigationservice
5102  media   19%   mediacodec
# Total: 98% → system cannot schedule AA heartbeat thread in time
```

### Fix
1. **Priority boost**: Assign AA heartbeat thread `THREAD_PRIORITY_AUDIO` (-16 nice value) to guarantee scheduling even under load.
2. **Media decoder throttle**: When AA is active, limit media decode bitrate to ≤ 8 Mbps (was unlimited).
3. **Watchdog extension**: Increase phone-side heartbeat timeout from 30 s to 60 s (Google AA API configuration).

### Recurring Bug Pattern (After Initial Fix)
```
If Android Auto disconnects recur after fix:

Scenario A — Same 30-min pattern → CPU loading still too high
  Check: new app installed on HU consuming background CPU?
  adb shell top -d 1 -n 10 > new_cpu_check.txt
  Action: Identify new CPU consumer; apply throttle or priority rules

Scenario B — Disconnects now random (not exactly 30 min) → different root cause
  Check: USB cable quality degradation
    Measure: USB voltage at HU port under load: should be ≥ 4.75 V
    Low voltage (<4.5V) → USB suspend event → AA teardown
  Check: BT coexistence (if AA Wireless enabled):
    Disable 2.4G Wi-Fi → if disconnects stop: Wi-Fi/BT coexistence issue
    Fix: Coexistence firmware update or channel separation

Scenario C — Only on new phone model (e.g., Galaxy S24 Ultra)
  Check: AOA protocol version compatibility
    Older HU may not support AOA 2.0 accessory mode for new phone firmware
  Action: Request AOA compatibility update from HU SW team
```

---

## 4. Bug Scenario 3 — Bluetooth A2DP Audio Stutters

### Bug Description
**Title:** Music audio via Bluetooth A2DP stutters every 5–10 seconds  
**Severity:** P2 — Audible quality defect  
**Frequency:** Consistent when Wi-Fi hotspot is active simultaneously

### Reproduction Steps
```
Steps:
  1. Connect phone via BT A2DP (codec: AAC)
  2. Enable HU Wi-Fi hotspot (2.4 GHz, channel 6)
  3. Play music from phone
  4. Observe: stutters every 5–10 s, lasting ~300 ms each
  5. Disable Wi-Fi hotspot → stutters stop immediately
  → Confirms Wi-Fi / Bluetooth coexistence as root cause
```

### Diagnostics — BT Protocol Logs
```bash
# Capture BT HCI snoop log:
adb shell svc bluetooth enable
adb shell am broadcast -a android.intent.action.MAIN -n com.android.bluetooth/.hfpclient.HeadsetClientStateMachine
adb pull /data/misc/bluetooth/logs/btsnoop_hci* .

# Analyse in Wireshark:
# Filter: bthci_acl || bthfp
# Look for: ACL retransmissions during Wi-Fi active periods
```

**Finding:** ACL packet retransmit count spikes from 0 to 8–12 retransmits per second during Wi-Fi TX bursts.

### Fix
- Enable BT/Wi-Fi coexistence arbitration in modem firmware:
  - Configure `COEX_BT_WIFI_PRIORITY = BT_PRIORITY_WHEN_SCO_OR_A2DP`
  - This pauses Wi-Fi TX for 2 ms during BT A2DP audio transmission slots

### Bug Report Summary

| Field | Value |
|-------|-------|
| Title | A2DP stutter when Wi-Fi hotspot active |
| Severity | P2 |
| Root Cause | BT/Wi-Fi 2.4 GHz coexistence – Wi-Fi TX interrupts BT A2DP ACL |
| Fix | Modem coexistence firmware: BT A2DP priority during audio slots |
| Retest | Play 30 min A2DP + Wi-Fi hotspot active → 0 stutters |
| Regression Risk | Any modem firmware update may reset coexistence config – retest after every modem update |

---

## 5. Bug Scenario 4 — HU Boot Failure After OTA Update (Black Screen)

### Bug Description
**Title:** Head Unit shows permanent black screen after OTA push to v4.3.0  
**Severity:** P1 — Total HU failure, vehicle not drivable (no reverse camera, no cluster display)  
**Affected:** 18 vehicles in field

### Reproduction Steps
```
Steps:
  1. HU running v4.2.1
  2. Push OTA package (v4.3.0) via telematics; HU downloads and applies
  3. HU reboots (post-update reboot)
  4. Screen remains black; no OEM splash logo visible
  5. HU does not respond to touch
  6. CAN trace: HU NM (Network Management) CAN message is ABSENT (ECU not waking up)
```

### ADB Diagnosis (via recovery mode)
```bash
# Enter recovery mode: hold POWER + VOL-DOWN during boot
# Or programmatic: adb reboot recovery (if adb still responds)

# In recovery, mount /system and check dmesg:
adb shell "cat /proc/last_kmsg" > last_kmsg.txt

# Finding in last_kmsg:
[    2.341] init: Unable to open '/dev/block/by-name/system': No such file or directory
[    2.342] init: Failed to mount /system
[    2.343] PANIC: Could not mount system partition
→ System partition mount failed → init panic → black screen

# Check partition table:
adb shell ls -la /dev/block/by-name/
# Missing: 'system' symlink → OTA partition update corrupted the partition table symlinks
```

### Root Cause
OTA package v4.3.0 contained a `dynamic_partitions_info.txt` update that changed super partition layout. The OTA pre-install script failed to re-create `/dev/block/by-name/system` symlink after repartitioning. Result: init cannot find the system partition at boot.

### Recovery Procedure
```bash
# Option A: Force-flash via fastboot (requires USB access):
adb reboot bootloader
fastboot flash super super_v430_fixed.img
fastboot reboot
# Result: HU boots normally

# Option B: Remote recovery OTA (if TCU still alive):
# Push recovery image via telematics (TCU is on separate power domain)
# TCU downloads recovery OTA package → flashes via recovery mode → reboots
```

### Recurring Bug Watchdog Protocol
```
If any future OTA causes black screen (regardless of version):

Phase 1 — Immediate (first 30 min):
  □ Check: does TCU respond to diagnostic? (TCU is separate ECU, not affected by HU crash)
    YES → TCU can push recovery OTA remotely
    NO  → physical USB fastboot required
  □ Deploy OTA campaign HOLD immediately (protect remaining fleet)
  □ Alert: all affected VINs flagged in OEM fleet portal

Phase 2 — Root cause (within 2 hours):
  □ Pull /proc/last_kmsg from affected vehicle
  □ Identify exact init/mount failure
  □ Compare OTA diff: what changed in v4.3.0 that touches partition table?
  □ Reproduce on bench: apply same OTA → confirm failure

Phase 3 — Fix + re-release:
  □ Fix OTA script: add partition symlink re-creation post-repartition
  □ Test fix on 5 bench units + 2 field units
  □ Canary: push to 10 vehicles; wait 1 hour; verify boot OK before full fleet push
  □ Add pre-flight check to OTA pipeline: validate symlinks exist after dry-run repartition
```

---

## 6. Common Infotainment Diagnostic Commands Reference

### ADB Diagnostics Quick Reference

| Goal | Command |
|------|---------|
| Capture full logcat | `adb logcat -b all -v threadtime > log.txt` |
| Memory of one app | `adb shell dumpsys meminfo com.oem.navigation` |
| All running processes memory | `adb shell dumpsys meminfo` |
| CPU usage (live) | `adb shell top -d 1` |
| GPU rendering stats | `adb shell dumpsys gfxinfo com.oem.launcher` |
| Capture heap dump | `adb shell am dumpheap com.pkg /data/local/tmp/heap.hprof` |
| Pull crash tombstone | `adb pull /data/tombstones/ ./tombstones/` |
| ANR traces | `adb pull /data/anr/traces.txt` |
| BT HCI snoop log | `adb pull /data/misc/bluetooth/logs/btsnoop_hci.log` |
| Input event test | `adb shell getevent -l` |
| Screen capture | `adb shell screencap -p /sdcard/screen.png && adb pull /sdcard/screen.png` |
| Screen record | `adb shell screenrecord /sdcard/record.mp4 --time-limit 60` |
| Force stop app | `adb shell am force-stop com.oem.navigation` |
| Clear app data | `adb shell pm clear com.oem.navigation` |
| Simulate low memory | `adb shell am send-trim-memory com.oem.navigation CRITICAL` |

### Performance Threshold Reference

| Metric | Target | Critical |
|--------|--------|---------|
| Touch response latency | ≤ 100 ms | > 300 ms |
| App launch time (cold) | ≤ 2 s | > 5 s |
| Navigation route calc | ≤ 3 s | > 8 s |
| BT connection time | ≤ 5 s | > 15 s |
| Android Auto connect | ≤ 10 s | > 30 s |
| HU boot (cold) | ≤ 20 s | > 45 s |
| Audio routing switch (media↔call) | ≤ 200 ms | > 1 s |
| OTA download 100 MB (LTE) | ≤ 3 min | > 15 min |
