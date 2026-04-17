# Scenarios 26–30 — HMI, Voice, Boot & Performance
## Infotainment Test Validation — Scenario-Based Interview Prep

---

## Scenario 26 — IVI Takes 55 Seconds to Boot (Spec Is 30 Seconds)

> **Interviewer:** "A customer complains the infotainment screen takes nearly a minute to show anything after turning the ignition on. Your spec says the cluster should show within 5 seconds and full IVI within 30 seconds. How do you diagnose and fix this?"

**Background:**
IVI boot time regression after SW update is one of the most common infotainment defects. The customer perceives this as quality degradation.

**Investigation Path:**

**Step 1 — Measure per-phase boot time:**
```bash
# Connect via ADB over Ethernet before boot
adb logcat -v time > boot_log.txt &    # capture from boot start

# Key timestamps to find in logcat:
grep "kernel boot" boot_log.txt         # Linux kernel starts
grep "init: starting" boot_log.txt      # Android init starts
grep "ActivityManager: Start" boot_log.txt  # Android framework starts
grep "SystemServer: Entered" boot_log.txt   # System services start
grep "IVI_Launcher: onCreate" boot_log.txt  # IVI app starts
grep "Display: first frame" boot_log.txt    # First pixel on screen
```

**Step 2 — Compare against previous SW version:**
```
SW v2.8 (meeting spec):                   SW v3.0 (failing spec):
  Kernel boot:        3s                    Kernel boot:        3s   (same)
  Android init:       5s                    Android init:      12s   (+7s) ←
  System services:    8s                    System services:   18s  (+10s) ←
  IVI app start:      4s                    IVI app start:      5s   (+1s)
  First pixel:       20s                    First pixel:       40s  (+20s)
  Full interactive:  28s                    Full interactive:  58s  (+30s)
```

The delta is clearly in Android init and System services — something added in v3.0 is causing these delays.

**Step 3 — Identify v3.0 additions:**
Review SW changelog for v3.0:
- Added: New OTA manager service (starts at boot, scans server)
- Added: Enhanced map pre-loading (caches 10GB map tiles at boot)
- Added: Cloud sync service (uploads logs at every boot)

The OTA manager and cloud sync are making network calls during boot → waiting for TCP timeout if no connectivity → adds 15–20s each.

**Step 4 — Fix options:**
1. Lazy initialization: defer OTA check and cloud sync to 60s after full boot instead of during boot
2. Timeout reduction: reduce network call timeout from 10s to 2s
3. Async startup: run background services in parallel with UI boot (do not block UI thread)

**CAPL Equivalent (Python for boot time measurement):**
```python
import subprocess, time, re

def measure_boot_time(adb_log_file):
    timestamps = {}
    milestones = {
        'kernel_start': r'Linux version',
        'android_init': r'init: starting service',
        'framework':    r'SystemServer: Entered',
        'ivi_launcher': r'IVI_Launcher.*onCreate',
        'first_frame':  r'Choreographer.*frames'
    }

    with open(adb_log_file) as f:
        for line in f:
            for milestone, pattern in milestones.items():
                if re.search(pattern, line) and milestone not in timestamps:
                    time_match = re.match(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', line)
                    if time_match:
                        timestamps[milestone] = time_match.group(1)

    # Print phase durations
    keys = list(milestones.keys())
    for i in range(1, len(keys)):
        if keys[i-1] in timestamps and keys[i] in timestamps:
            print(f"{keys[i-1]} → {keys[i]}: " +
                  f"[calculate delta from timestamps]")
    return timestamps

results = measure_boot_time('boot_log.txt')
```

**Test Cases:**
```
TC_BOOT_001: Cold boot (first ignition after overnight) → cluster shows within 5 seconds
TC_BOOT_002: Cold boot → full IVI interactive (respond to touch) within 30 seconds
TC_BOOT_003: Warm restart (ignition cycle within 2 min) → IVI ready within 15 seconds
TC_BOOT_004: Boot time with no network connectivity → same as with network (no blocking call)
TC_BOOT_005: 100 consecutive cold boot cycles → mean boot time < 28s, max < 35s
TC_BOOT_006: Boot time regression test: run after every SW build → alert if > 5% slower than baseline
```

**Root Cause Summary:**
Boot-time regression caused by two new services (OTA manager, cloud sync) making blocking network calls during the Android system services startup phase. Each service waits for TCP timeout (default 10s) before giving up if no network. Fix: convert all network calls at boot to non-blocking async with 2s max timeout, defer to post-boot background thread.

---

## Scenario 27 — Voice Assistant Activates Accidentally While Playing Music

> **Interviewer:** "Voice assistant activates without the user pressing any button — specifically when a song with a phrase similar to the wake word plays through the speakers. How do you prevent false wake-word activations?"

**Background:**
Voice assistants use a keyword spotter running continuously on a DSP (Digital Signal Processor). If the spotter detects the wake word in music output from the speakers, it incorrectly activates.

**Technical Problem:**
- Wake word: "Hey [Name]"  (e.g., "Hey Sonia")
- Song playing: lyrics contain phonetically similar sounds
- Microphone picks up speaker output → keyword spotter triggers

**Investigation Path:**

**Step 1 — Reproduce with specific songs:**
Catalogue which songs or audio content triggers false activations.
Note: word timing, pitch, tempo — does slower/faster playback change the false activation rate?

**Step 2 — AEC reference signal quality:**
The keyword spotter should use the AEC (Acoustic Echo Canceller) reference signal to suppress the speaker output from the microphone input.
If AEC reference is misaligned by > 10ms → speaker audio leaks into mic feed → keyword spotter activates.
Test: turn music OFF → any false activations should stop → confirms speaker leakage cause.

**Step 3 — Wake word False Acceptance Rate:**
Measure FAR (False Acceptance Rate):
```
FAR = false_activations / total_time_active
Acceptable FAR: < 1 per hour of operation
Test measurement: 8 hours of Music playback → count false activations
```

**Step 4 — Speaker playback volume dependence:**
Does false activation only occur at volume > 70%?
At high volume, acoustic coupling from speaker to microphone overwhelms AEC capacity.
AEC is designed for expected room gain — vehicle cabin at full volume exceeds design range.

**Step 5 — DSP tuning fix:**
```python
# Conceptual: wake word spotter confidence threshold adjustment
# At high media volume → raise confidence threshold (require stronger keyword match)

def get_wakeword_threshold(media_volume_pct: float) -> float:
    """
    Dynamically adjust wake word confidence threshold based on media volume.
    Higher volume = require higher confidence to avoid false activations.
    """
    base_threshold = 0.65       # nominal sensitivity
    volume_factor  = media_volume_pct / 100.0
    adjusted = base_threshold + (volume_factor * 0.25)  # max +0.25 at full volume
    return min(adjusted, 0.92)   # cap at 0.92 to still allow legitimate activations

# At 0% volume:   threshold = 0.65
# At 50% volume:  threshold = 0.775
# At 100% volume: threshold = 0.90
```

**Test Cases:**
```
TC_VOICE_FA_001: Play 4 hours of top-40 music at 70% volume → ≤ 1 false activation
TC_VOICE_FA_002: Play specific songs known to contain phonetically similar phrases → 0 false activations
TC_VOICE_FA_003: Music at 100% volume → false activation rate ≤ 3 per hour (degraded but acceptable)
TC_VOICE_FA_004: User says actual wake word at 70% music volume → correct activation within 1.5s
TC_VOICE_FA_005: Wake word detection in 5 languages → FAR ≤ 1/hour for each language
TC_VOICE_FA_006: Passenger conversation → no false activation (voice gender/distance discrimination)
```

**Root Cause Summary:**
AEC reference signal delay in this vehicle model is 18ms (higher than the 8ms the keyword spotter was calibrated for), causing the AEC to fail to cancel speaker output from the microphone feed. At high volume, the uncancelled speaker signal matches the wake word phoneme pattern. Fix: recalibrate AEC reference delay for this specific speaker-microphone geometry, and increase confidence threshold at high volume.

---

## Scenario 28 — IVI Screen Freezes When Receiving an Incoming Call

> **Interviewer:** "When an incoming Bluetooth call arrives while the navigation screen is active, the IVI freezes for 3–4 seconds before the call UI appears. During the freeze, the touch screen is completely unresponsive. How do you investigate?"

**Investigation Path:**

**Step 1 — UI thread blocking:**
3–4 second freeze = main UI thread blocked.
Android has an ANR (Application Not Responding) timeout of 5 seconds — a 4s freeze is just under ANR threshold.
```bash
# Check for ANR logs
adb shell cat /data/anr/traces.txt | head -200
# Look for: "main" thread WAIT or BLOCK state, with navigation app holding a mutex
```

**Step 2 — Resource contention at call start:**
When a Bluetooth call arrives, multiple things happen simultaneously:
1. Bluetooth HFP connection setup (CPU intensive)
2. Audio routing change: music output → HFP output (involves AudioFlinger lock)
3. Navigation app saves state for suspend
4. In-call UI launches

If the navigation app is holding the AudioFlinger lock (for its own audio guidance) when the call system requests it → deadlock for 3–4s until navigation's audio lock times out.

**Step 3 — CPU usage spike:**
```bash
adb shell top -d 0.5 -n 10 > cpu_log.txt &
# Then trigger incoming call
# Check: does any process spike to 100% during the 3-4s freeze?
```

**Step 4 — Log timing analysis:**
```bash
adb logcat -v threadtime | grep -E "Call|Phone|HFP|AudioFocus|Navigation" > call_log.txt
# Find key events:
#   T+0.0s: Incoming call detected (HFP RING)
#   T+0.1s: AudioFocus request (Phone)
#   T+0.1s: AudioFocus response delayed... ← look here
#   T+3.8s: AudioFocus granted ← NavigationApp releases lock
#   T+3.8s: Call UI appears
```

**Step 5 — Fix:**
Navigation audio guidance should acquire `AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK`, not `AUDIOFOCUS_GAIN`.
With GAIN (exclusive): Navigation holds audio exclusively → phone must wait.
With GAIN_TRANSIENT_MAY_DUCK: Navigation is pre-emptible → phone can interrupt immediately.

**CAPL for Timing Test (system-level):**
```capl
// Measure time from call arrival CAN signal to IVI call UI display signal
variables {
  dword tCallArrived_ms = 0;
  dword tCallUIShown_ms = 0;
}

on signal Bluetooth::IncomingCall_Active {
  if (this.value == 1) {
    tCallArrived_ms = timeNow() / 10;
    write("Incoming call detected at %d ms", tCallArrived_ms);
  }
}

on signal IVI_ECU::CallUI_Displayed {
  if (this.value == 1) {
    tCallUIShown_ms = timeNow() / 10;
    dword delay = tCallUIShown_ms - tCallArrived_ms;
    if (delay <= 1500) {
      write("PASS — Call UI appeared in %d ms", delay);
    } else {
      write("FAIL — Call UI delay = %d ms (spec ≤1500ms)", delay);
    }
  }
}
```

**Test Cases:**
```
TC_CALL_001: Incoming call while navigation active → call UI appears within 1.5 seconds
TC_CALL_002: Touch screen responsive within 500ms of call arrival (no full freeze)
TC_CALL_003: Incoming call during: music + navigation simultaneously → call still within 1.5s
TC_CALL_004: Accept call → navigation voice resumes when call ends with correct ducking
TC_CALL_005: Decline call → navigation continues without having to manually restart
TC_CALL_006: 20 consecutive calls during navigation → no ANR, no cumulative delay increase
```

**Root Cause Summary:**
Navigation audio service holds `AUDIOFOCUS_GAIN` (exclusive ownership), blocking the telephony stack from acquiring audio focus for the call. The NavigationApp was implemented to hold exclusive audio for the full active navigation session. Fix: change to `AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK` so the telephony system can immediately pre-empt navigation audio on incoming calls.

---

## Scenario 29 — IVI Memory Usage Increases Continuously Over Long Drive

> **Interviewer:** "On a 6-hour drive, the IVI starts normally but after 4+ hours begins showing sluggish response. By hour 6, apps crash and the UI barely responds. Vehicle restart fixes it. What is the problem?"

**Background:**
Symptoms that worsen over time and are fixed by restart = memory leak. This is one of the most common long-term quality issues in automotive IVI systems.

**Investigation Path:**

**Step 1 — Confirm memory leak:**
```bash
# Monitor memory every 30 minutes during drive
adb shell free -m >> memory_log.txt && date >> memory_log.txt
# Or more detailed:
adb shell dumpsys meminfo > meminfo_$(date +%H%M).txt
# Repeat every 30 min → compare heap sizes per app
```

Expected pattern with leak:
```
Hour 0:  Navigation=180MB  MediaPlayer=90MB   System=400MB   Free=1200MB
Hour 2:  Navigation=210MB  MediaPlayer=95MB   System=430MB   Free=1050MB
Hour 4:  Navigation=280MB  MediaPlayer=110MB  System=520MB   Free=820MB
Hour 6:  Navigation=410MB  MediaPlayer=180MB  System=700MB   Free=100MB
```

**Step 2 — Identify the leaking process:**
```bash
adb shell dumpsys meminfo | grep -E "Total RAM|Free RAM|Used RAM|HeapAlloc"
# Identify which app's HeapAlloc increases most per hour
```

**Step 3 — Map tile cache leak:**
Navigation apps are notorious for map tile memory leaks:
- As vehicle drives, new map tiles are loaded into memory
- Old tiles should be evicted from cache when no longer needed
- If eviction logic is broken: cache grows indefinitely
- Test: stop navigation → does memory reduce? If yes → map tile leak.

**Step 4 — Media metadata accumulation:**
On a 6-hour drive with streaming radio, the media player processes thousands of track metadata records.
If old metadata is not garbage collected → MediaPlayer heap grows continuously.

**Step 5 — Bitmap/texture leak in UI:**
Each screen transition (map zoom, menu open) may allocate GPU textures without freeing old ones.
Check with GPU profiling:
```bash
adb shell dumpsys gfxinfo com.ivi.navigation > gfx_log.txt
# Check "Total frames rendered" vs "Jank frames" over time
```

**CAPL / Python Long-Run Monitor:**
```python
import subprocess, time, datetime

def get_memory_info():
    result = subprocess.run(['adb', 'shell', 'cat', '/proc/meminfo'],
                            capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    mem = {}
    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            mem[parts[0].rstrip(':')] = int(parts[1])
    return mem

print("Starting 6-hour memory monitor...")
for _ in range(720):   # Every 30 seconds for 6 hours
    mem = get_memory_info()
    free_mb = mem.get('MemFree', 0) // 1024
    avail_mb = mem.get('MemAvailable', 0) // 1024
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"{timestamp} — Free: {free_mb}MB  Available: {avail_mb}MB")
    if avail_mb < 300:
        print(f"WARNING — Available memory critically low: {avail_mb}MB")
    time.sleep(30)
```

**Test Cases:**
```
TC_MEM_001: 6-hour drive → available RAM must not drop below 400MB at any point
TC_MEM_002: Navigation running 6 hours → NavigationApp heap growth ≤ 50MB total
TC_MEM_003: Media streaming 6 hours → MediaPlayer heap growth ≤ 30MB total
TC_MEM_004: Map zoom in/out 500 times → GPU texture memory stable (±10% of initial value)
TC_MEM_005: Stop navigation after 4 hours → navigation process memory reduces within 30s
TC_MEM_006: 24-hour soak test (vehicle parked, IVI left on) → no OOM crash
```

**Root Cause Summary:**
Navigation tile cache eviction policy is set to evict only when cache > 1GB. On a 6-hour motorway drive covering 600km, approximately 2GB of unique map tiles are loaded but not evicted. Combined with media metadata accumulation, total heap exceeds available RAM, triggering Android low-memory killer starting from lowest priority processes. Fix: reduce tile cache eviction threshold to 300MB and implement LRU (Least Recently Used) tile eviction every 5 minutes.

---

## Scenario 30 — Multiple Concurrent CAN Faults After IVI SW Downgrade

> **Interviewer:** "A customer visited a dealership who downgraded the IVI SW from v3.0 to v2.8 (rolling back due to a reported bug). After the downgrade, 12 new DTCs appeared across BCM, ADAS, and Cluster — all U-type (communication DTCs). The car previously had 0 DTCs. What happened and how do you fix it?"

**Background:**
This is a version compatibility problem. A downgrade is riskier than an upgrade because v2.8 IVI may not be compatible with the CAN message format changes made in other ECUs that were updated to work with v3.0.

**Investigation Path:**

**Step 1 — Identify all 12 DTCs:**
```
Run 0x19 02 FF on all ECUs:
  BCM:   U0100 (Lost comm with IVI)
         U0101 (Lost comm with TCM — IVI is gateway for TCM messages to cluster)
  ADAS:  U0155 (Lost comm with Cluster — IVI changed as gateway)
         U0184 (Lost comm with Navigation module — now inside IVI, different address)
  Cluster: U0100, U3001 (IVI protocol version mismatch)
  Total: 12 DTCs across 3 ECUs
```

**Step 2 — Version compatibility matrix:**
```
v3.0 introduced:
  - New CAN message: IVI_Heartbeat_V2 (0x6B0) — replaced by IVI_Heartbeat_V1 (0x5B0)
  - New message for navigation status (now inside IVI, address changed)
  - New IVI gateway function forwarding TCM messages to cluster

v2.8 sends:
  - IVI_Heartbeat_V1 (0x5B0) — BCM expects V2 (0x6B0) → BCM logs U0100
  - No navigation status message — ADAS expects it → logs U0155
  - No TCM gateway function → Cluster loses TCM-originated messages → logs U0101
```

**Step 3 — CAN trace to confirm:**
```capl
// Run after downgrade — check which expected messages are missing
on start {
  write("Monitoring for missing messages (30 second scan)...");
}

variables {
  int gHeartbeatV1 = 0;
  int gHeartbeatV2 = 0;
  int gNavStatus   = 0;
  msTimer tmrReport;
}

on start { setTimer(tmrReport, 30000); }

on message 0x5B0 { gHeartbeatV1 = 1; write("IVI Heartbeat V1 detected (0x5B0)"); }
on message 0x6B0 { gHeartbeatV2 = 1; write("IVI Heartbeat V2 detected (0x6B0)"); }
on message 0x7C0 { gNavStatus   = 1; write("Nav Status message detected (0x7C0)"); }

on timer tmrReport {
  write("=== After SW Downgrade — Message Presence ===");
  write("IVI Heartbeat V1 (0x5B0): %s", gHeartbeatV1 ? "PRESENT" : "MISSING");
  write("IVI Heartbeat V2 (0x6B0): %s", gHeartbeatV2 ? "PRESENT" : "MISSING");
  write("Nav Status (0x7C0):        %s", gNavStatus   ? "PRESENT" : "MISSING");
}
```

**Step 4 — Fix options:**
1. **Re-upgrade to v3.0** (preferred) — if the original bug is not safety-critical
2. **Downgrade other ECUs too** — BCM/ADAS/Cluster back to versions compatible with IVI v2.8 (complex, risky)
3. **Apply compatibility patch** — IVI v2.8 patch that adds the V2 heartbeat message alongside V1 (backward compatible bridge)

**Step 5 — Process improvement:**
The root cause is a missing compatibility matrix in the release process.

```
Required: ECU Software Compatibility Matrix
┌─────────────┬──────┬──────┬──────┬──────┐
│ ECU         │ v2.6 │ v2.7 │ v2.8 │ v3.0 │
├─────────────┼──────┼──────┼──────┼──────┤
│ IVI         │  ✓   │  ✓   │  ✓   │  ✓   │
│ BCM         │  ✓   │  ✓   │  ✗   │  ✓   │ ← BCM v3.0 not compatible with IVI v2.8
│ ADAS        │  ✓   │  ✓   │  ✗   │  ✓   │
│ Cluster     │  ✓   │  ✓   │  ✗   │  ✓   │
└─────────────┴──────┴──────┴──────┴──────┘
```

**Test Cases:**
```
TC_COMPAT_001: IVI v2.8 + BCM v2.8 → 0 communication DTCs
TC_COMPAT_002: IVI v3.0 + BCM v3.0 → 0 communication DTCs
TC_COMPAT_003: IVI v2.8 + BCM v3.0 → system must warn technician of incompatibility before allowing
TC_COMPAT_004: IVI downgrade → all ECU SW versions checked for compatibility before flash
TC_COMPAT_005: Compatibility matrix validated at every joint release gate
TC_COMPAT_006: Dealer diagnostic tool shows compatibility warning if mismatched SW is detected
```

**Root Cause Summary:**
The v3.0 IVI SW changed CAN message IDs and added gateway functions that other ECUs in the same SW generation depend on. The downgrade procedure did not check the compatibility matrix — confirmed: no compatibility matrix existed. The 12 DTCs are all legitimate communication failures caused by the v2.8 IVI being incompatible with v3.0 BCM/ADAS/Cluster. Fix: create and enforce an ECU SW compatibility matrix gate in the service release process.

---
*File: 06_hmi_voice_performance.md | Scenarios 26–30 | April 2026*
