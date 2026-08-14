# Part 11 — OTA (Over-The-Air) Integration

---

## 11.1 What is OTA?

OTA (Over-The-Air) allows updating vehicle software remotely via the cellular network — without the vehicle needing to visit a dealership.

**Types:**
- **SOTA (Software OTA)** — application-level updates (IVI apps, maps, calibration)
- **FOTA (Firmware OTA)** — firmware updates (ECU firmware, bootloader)

---

## 11.2 Full OTA Architecture

```
+-------------------+       +-------------------+
|   OEM Cloud       |       |   OTA Backend      |
|   OTA Server      |       |   Campaign Manager |
|   Package Server  |       |   Device Registry  |
+-------------------+       +-------------------+
         |                             |
         | HTTPS / MQTT (TLS)          |
         ↓                             ↓
+----------------------------------------------+
|               TCU (Vehicle Gateway)           |
|  OTA Manager | Download Agent | Verification  |
|  Cellular Modem (LTE/5G)                     |
+----------------------------------------------+
         |
         | CAN / DoIP / Ethernet
         ↓
+------------------+  +------------------+  +------------------+
|    ECU 1         |  |    ECU 2         |  |   Cluster ECU    |
|  Bootloader      |  |  Bootloader      |  |  Bootloader      |
|  Application A   |  |  Application B   |  |  Application C   |
+------------------+  +------------------+  +------------------+
```

---

## 11.3 OTA Campaign Flow

```
1. OEM creates software update (new firmware binary)
2. OEM signs package (RSA-2048 or ECDSA-P256 with OEM private key)
3. OEM uploads to OTA server
4. Campaign manager defines: target vehicles (by VIN or model), rollout percentage
5. TCU connects to server (polling or push notification)
6. TCU checks for pending campaigns
7. TCU downloads firmware package (HTTPS with TLS 1.3)
8. TCU verifies: signature, CRC, version compatibility
9. TCU pre-conditions check: ignition off, battery voltage OK, cellular signal OK
10. TCU initiates ECU update via DoIP/CAN:
    a. UDS programming session
    b. Security access
    c. Erase flash
    d. Transfer firmware blocks
    e. Verify CRC
    f. ECU reset
11. ECU reboots, validates new firmware, reports success
12. TCU reports campaign result to OTA server
13. OTA server updates device registry: "VIN123 updated to SW v2.5.1"
```

---

## 11.4 A/B Partition Update

A/B partition (also called dual-bank update) prevents bricking the ECU if an update fails:

```
Flash Layout:
+------------------+
|   Bootloader     |
+------------------+
|   Partition A    |  ← currently running firmware
+------------------+
|   Partition B    |  ← new firmware written here
+------------------+
|   NvM / Config   |
+------------------+

OTA writes new firmware to Partition B (while A is running)
After write + verification:
  Bootloader switches boot to Partition B
  ECU reboots into B
  If B fails validation: bootloader falls back to A (rollback)
  If B runs OK: A is now the fallback partition for next update
```

---

## 11.5 Delta Updates

Delta updates contain only the changed bytes between old and new firmware, reducing download size:

```
Old firmware:   v2.4.0 (512 KB)
New firmware:   v2.5.0 (518 KB)
Delta package:  v2.4.0→v2.5.0 (e.g., 42 KB)

TCU applies delta:
  Reads current firmware from ECU
  Applies patch algorithm (bsdiff, Xdelta, or EB CARIAD specific)
  Produces new firmware in memory
  Flashes new firmware to ECU
```

---

## 11.6 OTA Security

| Security Requirement | Implementation |
|---|---|
| Package integrity | SHA-256 checksum of firmware package |
| Package authenticity | ECDSA or RSA signature by OEM |
| Transport security | TLS 1.2/1.3 for HTTPS download |
| Server authentication | Server certificate pinned in TCU |
| Client authentication | Mutual TLS (TCU has client certificate in HSM) |
| Anti-replay | Campaign ID + nonce prevents re-sending old packages |
| Anti-rollback | Version counter in OTP; refuse downgrades |
| Secure boot | ECU verifies signature before running new firmware |

---

## 11.7 Campaign Management

OTA campaigns allow controlled rollouts:

```
Stage 1: 1% of vehicles (beta fleet)
  → Monitor: success rate, DTCs, crash reports
Stage 2: 10% of vehicles
  → Monitor same metrics
Stage 3: 100% rollout (if Stage 2 success rate > 98%)

Campaign pause: if success rate drops below threshold → auto-pause, alert OEM
Campaign abort: if critical failure detected → rollback all vehicles
```

---

## 11.8 OTA Failure Handling

| Failure | Cause | Response |
|---|---|---|
| Download failure | Cellular loss | Resume download (chunked transfer) |
| Signature verification failure | Corrupted package | Discard, retry download |
| Flash write failure | Flash wear/error | Set DTC, report to server |
| ECU validation failure after flash | Firmware fault | Rollback to partition A |
| Precondition failure | Low battery | Wait and retry |
| Campaign mismatch | Wrong SW version | Abort, report to server |

---

## 11.9 AUTOSAR UCM (Update and Configuration Management)

AUTOSAR Adaptive includes **UCM (Update and Configuration Management)** as a functional cluster for OTA:
- Receives software packages from OTA backend
- Manages installation, activation, and rollback
- Uses ara::exec to start/stop applications
- Reports status via ara::diag

---

## 11.10 OTA Integration Example

**Scenario:** Update ADAS ECU from SW v1.2.0 to v1.3.0 in field vehicle

```
Step 1: Create update package
  - Build v1.3.0 binary
  - Sign with OEM ADAS signing key
  - Create campaign on OTA server: target ADAS HW variant 1A

Step 2: Vehicle receives campaign
  - TCU polls OTA server: receives campaign notification
  - TCU downloads package (45 MB) over LTE, stores to TCU flash

Step 3: Precondition checks
  - Vehicle parked (vehicle speed = 0)
  - Battery voltage > 12.5V
  - No active DTC blocking update

Step 4: ADAS ECU flashing via DoIP
  - TCU → DoIP → ADAS ECU
  - Programming session → Security access → Erase → Transfer → Verify

Step 5: Validation
  - ADAS ECU reboots into new firmware
  - Self-test: sensor initialization, communication check
  - Reports: SW version = v1.3.0, DTCs clear

Step 6: Reporting
  - TCU sends result: {vin, ecu_id, from_version, to_version, status=SUCCESS, timestamp}
  - OTA server logs success
```

---

## Summary

| Topic | Key Points |
|---|---|
| FOTA vs SOTA | FOTA = firmware, SOTA = application/data |
| A/B partitions | Safe update with rollback capability |
| Delta updates | Reduce download size |
| Security | TLS, signatures, anti-replay, secure boot |
| Campaign management | Staged rollout, monitoring, auto-pause |
| Failure handling | Resume, rollback, report |
| AUTOSAR UCM | Adaptive AUTOSAR OTA management cluster |

---

*Next: [Part 12 — Build & CI/CD Integration](part-12-build-cicd.md)*
