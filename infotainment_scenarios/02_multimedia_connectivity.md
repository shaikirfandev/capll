# Scenarios 6–10 — Multimedia & Connectivity
## Infotainment Test Validation — Scenario-Based Interview Prep

---

## Scenario 6 — USB Music Playback Stops After 20 Minutes

> **Interviewer:** "A customer plugs in a USB drive with 500 songs. Music plays fine for ~20 minutes, then stops completely. Unplugging and re-plugging restarts it. What do you investigate?"

**Background:**
20-minute consistent cutoff points to a deterministic trigger — not random hardware. This could be a buffer overflow, thermal throttling, memory leak, or a file system traversal issue.

**Investigation Path:**

**Step 1 — Reproduce with time correlation:**
- Is it always exactly 20 minutes or approximately 20 minutes?
- If exactly 20 min: software timer-based trigger (periodic NVM save, memory cleanup, session timeout)
- If approximately 20 min: correlates with number of songs scanned (~500 songs × 2.4s each = 20 min)

**Step 2 — USB media scanner:**
When a USB is inserted, the IVI scans all files to build the media library.
If the library build takes 20 min (large USB, many files), it may restart the media service mid-playback.
Test: Insert a USB with only 10 songs → does it stop at 20 min still?

**Step 3 — Memory leak check:**
```bash
# ADB into IVI (Android-based)
adb shell dumpsys meminfo com.android.music
# Check memory usage trend — rising steadily = leak
# After 20 min if heap crosses threshold, OS kills the media process
```

**Step 4 — Thermal throttling:**
- IVI processor temperature after 20 min of data decoding + map rendering + audio output
- If SoC temperature > 95°C → thermal throttle → USB data rate drops → buffer underrun → audio stops
- Check: `adb shell cat /sys/class/thermal/thermal_zone*/temp`

**Step 5 — USB file system check:**
- Large USB drives (128GB+) with FAT32 sometimes cause IVI to re-enumerate after traversing more than 65,535 files
- Re-enumeration appears as USB disconnect/reconnect → media stops

**CAPL + ADB Test:**
```bash
# Monitor media service health every 60 seconds
while true; do
  echo "=== $(date) ==="
  adb shell dumpsys media.audio_flinger | grep -E "output|latency|underrun"
  adb shell ps | grep -E "media|music"
  sleep 60
done
```

**Test Cases:**
```
TC_USB_MUS_001: USB with 10 songs → play for 60 min → music continuous (no stop)
TC_USB_MUS_002: USB with 500 songs → play → note exact time of first stop
TC_USB_MUS_003: USB with 500 songs, disable media scanner in settings → play 60 min
TC_USB_MUS_004: Monitor IVI CPU/RAM usage during 30 min USB playback — no crash threshold crossed
TC_USB_MUS_005: USB re-insertion 20 times in 10 min → IVI handles gracefully, no crash
TC_USB_MUS_006: 128GB FAT32 USB with 60,000 files → IVI must not freeze or restart
```

**Root Cause Summary:**
If 20 min correlates with media library build completing: media service restarts after scan — SW architecture bug (scanner and player share same process context). If correlates with memory: heap leak in audio decoder. Fix: isolate media scanner to background thread, increase heap limit, or OTA firmware update.

---

## Scenario 7 — FM Radio Has Static Only in Specific Cities

> **Interviewer:** "An FM radio works perfectly in the factory, in the test lab, and in most cities — but customers in one specific region (e.g., Dubai, above 40°C ambient) report only static on all FM channels. What do you investigate?"

**Background:**
Location/temperature-specific FM failure points to environmental sensitivity — either the tuner hardware, antenna connector, or gain control algorithm behaving differently in hot conditions.

**Investigation Path:**

**Step 1 — Isolate environment:**
- Does it fail only at high temperature (>38°C) or only in that specific city regardless of temperature?
- If high temperature: thermal coefficient problem in RF components
- If city-specific: that city may have a different FM band plan (87.5–108 MHz in UAE vs different in some regions), or FM signal strength unusually high causing overload

**Step 2 — Antenna check:**
- High ambient temperature causes connector oxidation faster in humid coastal cities
- Test: replace antenna connector, apply dielectric grease → does static reduce?
- Check antenna impedance: should be 75Ω ± 5%

**Step 3 — AGC (Automatic Gain Control) overflow:**
In cities with very strong FM transmitters nearby (< 1km away), signal strength can be 80–90 dBuV.
The tuner AGC may not handle peak signals above its design range → overload → distortion → sounds like static
Test: add 20dB attenuator between antenna and tuner → does static disappear? → confirms overload

**Step 4 — Thermal derating:**
```
FM tuner chip datasheet: operating range 0°C to +70°C
In Dubai: interior dashboard temperature can reach 85–90°C
Chip enters thermal protection → reduces gain → signal below noise floor → static
```

**Step 5 — RDS signal check:**
- At 40°C+ the RDS decoder may malfunction → tuner loses station lock → manual frequency entry needed
- Test: disable RDS lock, manually tune to known strong station → does static persist?

**Test Cases:**
```
TC_FM_001: FM reception in -10°C environment (cold chamber) → signal strength normal
TC_FM_002: FM reception in +70°C environment (hot soak) → signal strength must not degrade >6dB vs +25°C
TC_FM_003: Strong signal injection (85 dBuV) at antenna port → tuner must not distort
TC_FM_004: Antenna open circuit → IVI shows 'No Signal' (not static, not crash)
TC_FM_005: FM scan in all regions: EU (87.5–108MHz), US (87.9–107.9MHz), JP (76–95MHz)
TC_FM_006: Rapid channel scan 50 channels in 30s → no freeze, all channels evaluated
```

**Root Cause Summary:**
Most likely: AGC overload from proximity to a high-power transmitter, exacerbated by high temperature reducing the tuner chip's headroom. Solution: add external 10dB attenuator pad in antenna signal path for markets near strong transmitters, or OTA update AGC algorithm to handle higher input levels.

---

## Scenario 8 — Microphone Echo and Feedback During Calls

> **Interviewer:** "During hands-free calls, the person on the other end hears an echo of their own voice. The customer (driver) hears the call clearly. What causes this and how do you test it?"

**Background:**
The driver hears the far-end speaker through the car speakers. The microphone picks up this speaker output and sends it back to the far-end — this is acoustic echo. The IVI should have an AEC (Acoustic Echo Canceller) to remove this.

**Investigation Path:**

**Step 1 — Confirm it's AEC failure, not sidetone:**
- Sidetone: driver hears their own voice slightly delayed → different symptom
- Far-end echo: caller hears themselves delayed → AEC is not working

**Step 2 — AEC status check:**
```bash
adb shell dumpsys audio | grep -i "echo\|AEC\|acoustic"
# Check if AEC is enabled and what algorithm is running
```

**Step 3 — Microphone placement:**
- Microphone too close to speaker or in direct line of speaker output → AEC reference path insufficient
- Test: temporarily cover one speaker → does echo reduce? → confirms acoustic path issue

**Step 4 — AEC reference signal:**
AEC requires a "reference signal" = the exact electrical audio being sent to the speaker.
If the reference signal has processing delay vs the microphone signal → AEC correlation fails → echo not cancelled.

**Step 5 — Volume-dependence test:**
- At low volume (20%) → no echo
- At high volume (80%) → echo present
- This confirms the AEC tail length is insufficient for high SPL (sound pressure level) room reverb

**Step 6 — Bluetooth codec delay:**
- If Bluetooth HFP uses mSBC codec: 7.5ms encoding delay + 7.5ms decoding = 15ms total
- AEC model trained for wSBC (60ms delay) will fail to cancel echo from mSBC path
- Check: force HFP to wSBC → does echo disappear?

**Test Cases:**
```
TC_MIC_001: Hands-free call at 40% volume → far-end reports no echo
TC_MIC_002: Hands-free call at 100% volume → far-end reports no echo
TC_MIC_003: AEC disabled in config → echo should be audible (confirms test setup detects echo)
TC_MIC_004: Call quality MOS (Mean Opinion Score) ≥ 3.5 per ETSI TS 126 131
TC_MIC_005: Echo Return Loss Enhancement (ERLE) ≥ 30dB per ITU-T G.168
TC_MIC_006: Call with passenger speaking simultaneously → call party can still hear driver clearly
```

**Root Cause Summary:**
AEC algorithm not tuned for the specific speaker-microphone geometry of the vehicle. Every new vehicle model requires AEC tuning in an anechoic chamber. If the AEC tuning data was not updated for a new headliner (different acoustic absorption), the model is wrong and echo breaks through at high volume.

---

## Scenario 9 — Spotify App Crashes When Navigation Active

> **Interviewer:** "The Spotify app on the IVI crashes specifically when the navigation app is simultaneously giving turn-by-turn directions — not at any other time. How do you debug this?"

**Background:**
Navigation audio and Spotify audio share the same audio output pipeline. When navigation generates a voice prompt, it "ducks" (lowers) the music and mixes its audio. If this audio focus arbitration is broken, it can crash the audio client (Spotify).

**Investigation Path:**

**Step 1 — Audio focus check:**
Android AudioFocus system:
- Spotify requests: `AudioManager.AUDIOFOCUS_GAIN`
- Navigation requests: `AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK`
- When navigation gets focus, Spotify should duck (reduce volume) and resume
- If navigation's focus request is malformed → AudioManager throws exception → Spotify crashes

**Step 2 — Logcat at the moment of crash:**
```bash
adb logcat -v time | grep -E "Spotify|AudioFocus|AudioFlinger|FATAL|crash|ANR" > crash_log.txt
# Trigger navigation voice prompt → capture crash
# Look for: java.lang.RuntimeException, NullPointerException in AudioFocusListener
```

**Step 3 — Memory pressure:**
- Navigation map rendering + Spotify streaming simultaneously = high RAM usage
- If RAM < threshold → Android kills lowest-priority process (Spotify) → appears as crash
- Test: `adb shell free -m` during simultaneous use → if < 200MB free, memory kill likely

**Step 4 — Audio routing conflict:**
- Navigation uses a dedicated audio channel (Navigation stream)
- If both navigation and Spotify request the same audio stream channel simultaneously → conflict

**Step 5 — Reproduce in isolation:**
```python
# ADB automation to reproduce the bug
import subprocess, time

def run_adb(cmd):
    return subprocess.run(['adb', 'shell'] + cmd.split(), capture_output=True, text=True)

# Launch Spotify
run_adb('am start -n com.spotify.music/.MainActivity')
time.sleep(5)

# Simulate navigation voice prompt (broadcast intent)
run_adb('am broadcast -a android.navigation.VOICE_PROMPT_START')
time.sleep(2)

# Check if Spotify still running
result = run_adb('ps | grep spotify')
if 'spotify' in result.stdout:
    print("PASS — Spotify still running after nav prompt")
else:
    print("FAIL — Spotify process killed")
```

**Test Cases:**
```
TC_AUDIO_001: Play Spotify → trigger navigation voice → Spotify ducks → voice plays → Spotify resumes at full volume
TC_AUDIO_002: 50 consecutive navigation voice prompts during Spotify playback → no crash
TC_AUDIO_003: Navigation + Spotify + phone call → all three audio sources handle focus correctly
TC_AUDIO_004: Kill navigation mid-voice prompt → Spotify unmutes within 2 seconds
TC_AUDIO_005: Simultaneous audio focus request storms (10 requests/second) → no ANR, no crash
```

**Root Cause Summary:**
Audio focus callback in Spotify's vehicle-optimised build missing a null check — when navigation sends a rapid series of DUCK/UNDUCK events (e.g., at a complex junction with 3 voice prompts in 5 seconds), a null dereference occurs in the callback. Fix: defensive null check in audio focus listener, or rate-limit navigation audio events.

---

## Scenario 10 — Wi-Fi Hotspot Disconnects When Car is in Parking Mode

> **Interviewer:** "The in-car Wi-Fi hotspot (from the embedded TCU) drops all connected devices whenever the car enters parking mode — even if the car is configured to keep hotspot active in park. How do you investigate?"

**Background:**
The TCU manages cellular connectivity and Wi-Fi hotspot. Parking mode has specific power management policies. If the hotspot drops despite the user configuring it to stay on, the power management policy is overriding user settings.

**Investigation Path:**

**Step 1 — Define parking mode power policy:**
```
Parking mode events:
  - KL15 OFF (ignition key out)
  - Vehicle speed = 0 for > 30 seconds
  - Park brake engaged
Each may trigger a different power management state
```

**Step 2 — TCU power state machine:**
```
ACTIVE   → gear in Drive/Reverse, KL15 ON
STANDBY  → parked, KL15 OFF, timer running
SLEEP    → parked > 15 min, minimal power
DEEP SLEEP → overnight, only CAN wakeup possible
```
Check: does hotspot drop at STANDBY entry or SLEEP entry?
UDS 0x22 on TCU: read power state DID when hotspot drops.

**Step 3 — User setting persistence:**
```bash
adb shell settings get global wifi_hotspot_parking_keep_on
# Should return 1 if user enabled it
# If returns 0 → setting not being saved to NVM correctly
```

**Step 4 — Power management override:**
The vehicle OEM may have a hard-coded rule: hotspot off if battery SOC < 30% in park.
Even if user sets "keep hotspot on", this safety rule may take priority.
Test: park with battery fully charged → does hotspot stay on? → confirms SOC-gated rule.

**Step 5 — CAN wakeup vs TCU state:**
```capl
// Monitor TCU state transitions
on message TCU::PowerState_BC {
  write("TCU Power State: %d (1=Active 2=Standby 3=Sleep)  Hotspot=%d",
        this.TCU_PowerState,
        this.TCU_WiFiHotspot_Active);
}

on signal VehicleSpeed::Speed_kmh {
  if (this.value == 0) {
    write("Vehicle stopped — monitoring TCU for hotspot policy enforcement");
  }
}
```

**Test Cases:**
```
TC_WIFI_001: KL15 ON, hotspot ON → KL15 OFF → hotspot stays on for configured duration
TC_WIFI_002: Park > 15 min with hotspot keep-alive enabled → hotspot still active at 16 min
TC_WIFI_003: Battery SOC = 15% → hotspot disabled even if keep-alive enabled (safety policy)
TC_WIFI_004: Connected device streams video for 2 hours in park → TCU temperature < 75°C
TC_WIFI_005: Hotspot setting = ON, vehicle OTA update in progress → hotspot remains stable
TC_WIFI_006: 5 client devices connected → all maintain connection after 30 min park
```

**Root Cause Summary:**
TCU power management state machine ignores user hotspot preference flag when entering STANDBY state. The STANDBY entry function resets hotspot to default OFF without checking user preference NVM. Fix: add preference check at every power state transition before applying default policies.

---
*File: 02_multimedia_connectivity.md | Scenarios 6–10 | April 2026*
