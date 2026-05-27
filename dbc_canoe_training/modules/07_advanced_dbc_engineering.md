# Module 07 — Advanced DBC Engineering

> **Level**: Advanced  
> **Duration**: ~5 hours  
> **Goal**: Master advanced DBC techniques including extended multiplexing, CAN FD, SecOC, AUTOSAR mapping, signal packing optimization, and ADAS-specific frame design.

---

## 7.1 Extended Multiplexing — SG_MUL_VAL_

### Standard vs Extended Multiplexing

| Feature | Standard Mux (SG_) | Extended Mux (SG_MUL_VAL_) |
|---------|-----------|----------------|
| Mux selectors | 1 per message | Multiple per message |
| Mux range | 0–2^n-1 (single value) | Range-based (e.g., 0-3, 4-7) |
| Nesting | Not supported | Supported (mux of mux) |
| CANdb++ | "Multiplexer" checkbox | "Multiplex Indicator" tab |
| DBC keyword | `M` / `m<n>` in SG_ | `SG_MUL_VAL_` block |

### Extended Multiplexing Syntax

```
SG_MUL_VAL_ <signal_name> : <mux_signal_name> <range_start>-<range_end>[, <range_start>-<range_end>];

Example: ADAS Radar Object List
  Frame: Radar_Objects, DLC=64 (CAN FD)
  MuxID signal: Obj_ID (bits 0-5, 0-31 → up to 32 objects)

  SG_ Obj_ID     : 0|6@1+  (1,0) [0|31]   ""  AEB_ECU
  SG_ Obj_Type   : 6|3@1+  (1,0) [0|7]    ""  AEB_ECU
  SG_ Obj_Range  : 9|12@1+ (0.05,0) [0|204.75] "m" AEB_ECU
  SG_ Obj_Speed  : 21|11@1- (0.05,0) [-51.2|51.15] "m/s" AEB_ECU

  SG_MUL_VAL_ Obj_Type  : Obj_ID 0-31;
  SG_MUL_VAL_ Obj_Range : Obj_ID 0-31;
  SG_MUL_VAL_ Obj_Speed : Obj_ID 0-31;
```

### Why Extended Mux Is Used in ADAS

```
ADAS sensor fusion transmits multiple objects in one CAN FD frame:
  - Camera: up to 10 lane boundary points per frame
  - Radar: up to 32 detected objects per scan
  - LIDAR: up to 64 cluster points per frame
  
Single CAN 2.0 (8 bytes) is too small → use CAN FD (64 bytes)
SG_MUL_VAL_ allows dynamic object numbering within one frame
```

---

## 7.2 Dynamic DLC in CAN FD

### CAN FD DLC Table

| DLC value | Payload bytes |
|-----------|--------------|
| 0–8       | 0–8 (same as CAN 2.0) |
| 9         | 12 |
| 10        | 16 |
| 11        | 20 |
| 12        | 24 |
| 13        | 32 |
| 14        | 48 |
| 15        | 64 |

### CAN FD DBC Message Declaration

```
BO_ 1280 Camera_LaneData: 64 Camera_ECU
 SG_ Frame_Counter   : 0|8@1+   (1,0)   [0|255]   ""    AEB_ECU,IPC
 SG_ Lane_Count      : 8|4@1+   (1,0)   [0|4]     ""    AEB_ECU
 SG_ LaneCurv_L      : 12|16@1- (0.0001,0) [-3.2768|3.2767] "1/m" AEB_ECU
 SG_ LaneCurv_R      : 28|16@1- (0.0001,0) [-3.2768|3.2767] "1/m" AEB_ECU
 SG_ LaneWidth       : 44|8@1+  (0.04,0)  [0|10.2]   "m" AEB_ECU
 SG_ LDW_Warning_L   : 52|2@1+  (1,0)   [0|3]     ""    IPC
 SG_ LDW_Warning_R   : 54|2@1+  (1,0)   [0|3]     ""    IPC
 SG_ CRC_Camera      : 56|8@1+  (1,0)   [0|255]   ""    AEB_ECU
```

### DBC Attributes for CAN FD

```
BA_DEF_ BO_ "VFrameFormat" ENUM "StandardCAN", "ExtendedCAN", "StandardCAN_FD", "ExtendedCAN_FD";
BA_DEF_DEF_ "VFrameFormat" "StandardCAN";

/* Assign CAN FD to specific messages */
BA_ "VFrameFormat" BO_ 1280 "StandardCAN_FD";

/* Bit rate switch (BRS) — data phase uses faster bitrate */
BA_DEF_ BO_ "BusType" STRING;
BA_ "BusType" "CAN FD";
```

---

## 7.3 SecOC — Secure Onboard Communication in DBC

### What is SecOC?

SecOC (Secure Onboard Communication) is an AUTOSAR module that adds:
- **Freshness counter** — prevents replay attacks
- **Message Authentication Code (MAC)** — prevents spoofing

### SecOC Signal Naming Convention

```
For a protected message AEB_Req:
  Original:     SG_ AEB_Active       (application data)
  Freshness:    SG_ SecOC_Fresh_AEB  (freshness value, e.g., 8 bits)
  Truncated MAC: SG_ SecOC_MAC_AEB   (truncated MAC, e.g., 24 or 32 bits)

DBC example:
BO_ 580 AEB_Req_Sec: 8 AEB_ECU
 SG_ AEB_Active       : 0|1@1+  (1,0)  [0|1]   ""     CGW
 SG_ AEB_State        : 1|3@1+  (1,0)  [0|7]   ""     CGW
 SG_ AEB_Decel_Req    : 4|8@1+  (0.1,0) [0|25.5] "m/s2" CGW
 SG_ AEB_Obj_Distance : 12|16@1+ (0.01,0) [0|655.35] "m" CGW
 SG_ SecOC_Fresh_AEB  : 28|8@1+  (1,0)  [0|255] ""    CGW
 SG_ SecOC_MAC_AEB    : 36|24@1+ (1,0)  [0|16777215] "" CGW
```

### Custom BA_DEF_ for SecOC

```
BA_DEF_ BO_  "SecOC"               ENUM "None","Tx","Rx","TxRx";
BA_DEF_ BO_  "SecOCFreshnessValueId" INT 0 65535;
BA_DEF_ BO_  "SecOCAuthInfoTxLength" INT 0 64;
BA_DEF_ SG_  "SecOCDataID"          INT 0 65535;

BA_DEF_DEF_ "SecOC" "None";
BA_DEF_DEF_ "SecOCFreshnessValueId" 0;
BA_DEF_DEF_ "SecOCAuthInfoTxLength" 0;
BA_DEF_DEF_ "SecOCDataID" 0;

/* Assign to AEB_Req message */
BA_ "SecOC"                  BO_ 580 "Tx";
BA_ "SecOCFreshnessValueId"  BO_ 580 1;
BA_ "SecOCAuthInfoTxLength"  BO_ 580 24;
BA_ "SecOCDataID"            SG_ 580 SecOC_MAC_AEB 1;
```

### SecOC CAPL Validation

```capl
variables {
  byte lastFreshness = 0;
}

on message AEB_Req_Sec {
  byte currentFresh;
  currentFresh = this.byte(3);  // Byte containing freshness

  if(currentFresh == lastFreshness) {
    writeEx(0, 1, "SecOC REPLAY ATTACK detected! AEB_Req freshness 0x%02X", currentFresh);
  }
  else if((byte)(currentFresh - lastFreshness) > 10) {
    writeEx(0, 2, "SecOC JUMP in freshness: %d→%d", lastFreshness, currentFresh);
  }
  lastFreshness = currentFresh;
}
```

---

## 7.4 Gateway Communication in DBC

### Multi-Bus Gateway Architecture

```
         CAN-HS1 (ADAS)                   CAN-HS2 (Comfort)
         ─────────────                    ───────────────────
         AEB_ECU ──────> WheelSpeed ──> CGW ──> IPC (simplified)
         ABS_ECU ──────> AEB_Req    ──> CGW ──> BCM_Display
         
         CGW routes selected signals between buses
         Different CAN ID on each bus for same physical signal!
```

### Gateway DBC Pattern

```
DBC for CAN-HS1 (ABS_ECU transmits WheelSpeed):
  BO_ 512 WheelSpeed: 8 ABS_ECU
    SG_ WheelSpeed_FL : 0|16@1+ (0.01,0) [0|655.35] "km/h" AEB_ECU,CGW

DBC for CAN-HS2 (CGW re-transmits with different ID):
  BO_ 1024 WheelSpeed_GW: 8 CGW
    SG_ WheelSpeed_FL : 0|16@1+ (0.01,0) [0|655.35] "km/h" IPC,BCM

IMPORTANT: Same raw encoding on both buses
  → Gateway passes raw bytes through (no re-encoding)
  → If encoding is different, use CAPL or IL to translate

Custom attribute for gateway origin:
  BA_DEF_ BO_ "GatewaySourceId"  INT 0 65535;
  BA_ "GatewaySourceId" BO_ 1024 512;  ← CAN-HS2 msg 1024 sourced from HS1 msg 512
```

---

## 7.5 AUTOSAR COM Stack Mapping to DBC

### AUTOSAR Communication Abstraction Layers

```
Application Layer
      │
      ▼
  Com Module (I-Signal with encoding)
      │  
      ▼
  PDU Router (I-PDU routing between busses)
      │
      ▼  
  CanIf / FrIf / EthIf
      │
      ▼
  CAN/FlexRay/Ethernet Hardware
```

### Mapping AUTOSAR I-Signal to DBC Signal

| AUTOSAR | DBC | Notes |
|---------|-----|-------|
| ComSignalId | — (DBC uses name) | |
| ComSignalLength | SG_ length | |
| ComBitPosition | SG_ start_bit | AUTOSAR: bit0 at MSB of byte0 |
| ComSignalEndianness | @1 (Intel) / @0 (Motorola) | |
| ComSignalType | UNS/SIGNED type | |
| ComFactor | SG_ factor | |
| ComOffset | SG_ offset | |
| InitValue | BA_ GenSigStartValue | |
| I-PDU name | BO_ name | |
| I-PDU ID | BO_ ID (in hex) | |
| I-PDU length | BO_ DLC | |

### ARXML to DBC Conversion

```
Tool: CANdb++ imports .arxml directly:
  File → Import → AUTOSAR Network Communication (.arxml)

For manual conversion:
  python-can / cantools can parse both:
  
  import cantools
  # Load ARXML (partial support)
  db = cantools.database.load_file('network.arxml')
  # Export to DBC
  cantools.database.dump_file(db, 'output.dbc')
```

---

## 7.6 Signal Packing Optimization

### Bus Load Formula

```
Bus Load (%) = (Σ Frame_bits × Frame_rate) / Bitrate × 100

Where:
  Frame_bits = 44 + 8 × DLC + round_up(interframe_bits)
             = 44 + 8×DLC (approximate for standard CAN)
  Frame_rate = 1000 / CycleTime_ms (frames per second)
  Bitrate = 500000 bps

Example: AEB_Req (DLC=8, 20ms cycle)
  Frame_bits = 44 + 8×8 = 108 bits
  Frame_rate = 1000/20 = 50 frames/s
  Contribution = 108 × 50 = 5400 bits/s
  Bus load = 5400 / 500000 × 100 = 1.08%
```

### Full Bus Load Calculation (All 6 Messages)

| Message | DLC | Cycle | Bits | Rate | bits/s | Load % |
|---------|-----|-------|------|------|--------|--------|
| WheelSpeed | 8 | 10ms | 108 | 100 | 10800 | 2.16% |
| AEB_Req | 8 | 20ms | 108 | 50 | 5400 | 1.08% |
| VehicleStatus | 8 | 10ms | 108 | 100 | 10800 | 2.16% |
| EPS_Status | 4 | 20ms | 76 | 50 | 3800 | 0.76% |
| IPC_Display | 8 | 100ms | 108 | 10 | 1080 | 0.22% |
| BCM_Status | 6 | 100ms | 92 | 10 | 920 | 0.18% |
| **Total** | | | | | **32800** | **6.56%** |

```
6.56% is well under the 30% safe operating limit ✅
Typical rule of thumb: < 30% = comfortable, < 50% = acceptable, > 70% = congested
```

### Signal Alignment Best Practices

```
For maximum efficiency, pack signals to byte boundaries where possible:

✅ GOOD (byte-aligned):
  SG_ Signal1 : 0|8@1+   → occupies exactly byte 0
  SG_ Signal2 : 8|8@1+   → occupies exactly byte 1
  SG_ Signal3 : 16|16@1+ → occupies exactly bytes 2-3

❌ INEFFICIENT (bit scatter):
  SG_ SignalA : 0|5@1+   → 3 bits of byte 0 unused
  SG_ SignalB : 8|5@1+   → bits 13-15 unused
  SG_ SignalC : 16|5@1+  → bits 21-23 unused
  
  → These three signals could fit in 2 bytes but use 3 bytes

✅ BETTER: Pack signals together
  SG_ SignalA : 0|5@1+   (bits 0-4)
  SG_ SignalB : 5|5@1+   (bits 5-9)
  SG_ SignalC : 10|5@1+  (bits 10-14)
  SG_ SignalD : 15|1@1+  (bit 15 — flag or padding)
  → All fit in 2 bytes (DLC=2)!
```

---

## 7.7 ADAS Camera Frame Design — CAN FD Example

### Camera Perception Output Frame

ADAS Camera ECU outputs per-frame lane and object data at 30Hz (≈33ms cycle):

```
BO_ 1600 Camera_PerceptionData: 48 Camera_ECU
 SG_ Frm_Seq          : 0|8@1+   (1,0)     [0|255]    ""     AEB_ECU,EPS_ECU
 SG_ Timestamp_ms     : 8|32@1+  (0.001,0) [0|4294967.295] "ms" AEB_ECU
 
 /* Lane detection */
 SG_ Lane_Valid       : 40|2@1+  (1,0)  [0|3]  ""   AEB_ECU,EPS_ECU
 SG_ Lane_LDW_L       : 42|2@1+  (1,0)  [0|3]  ""   IPC
 SG_ Lane_LDW_R       : 44|2@1+  (1,0)  [0|3]  ""   IPC
 SG_ Lane_Curvature   : 46|18@1- (0.00001,0) [-1.31072|1.31071] "1/m" AEB_ECU,EPS_ECU
 SG_ Lane_Heading     : 64|16@1- (0.0001,0)  [-3.2768|3.2767]  "rad" AEB_ECU,EPS_ECU
 SG_ Lane_Width       : 80|10@1+ (0.02,0)    [0|20.46]          "m"  AEB_ECU
 
 /* Object detection — up to 4 objects */
 SG_ Obj_Mux         M : 96|4@1+  (1,0) [0|3]  ""   AEB_ECU
 SG_ Obj_Class      m0 : 100|4@1+ (1,0) [0|7]  ""   AEB_ECU
 SG_ Obj_Dist_Lat   m0 : 104|12@1- (0.05,0) [-102.4|102.35] "m" AEB_ECU
 SG_ Obj_Dist_Long  m0 : 116|12@1+ (0.05,0)   [0|204.75]   "m"  AEB_ECU
 SG_ Obj_RelSpeed   m0 : 128|11@1- (0.1,0)    [-102.4|102.3] "m/s" AEB_ECU
 
 SG_ CRC_Cam        : 376|8@1+  (1,0) [0|255] "" AEB_ECU

VA_DEF_ VFrameFormat "StandardCAN_FD";
BA_ "VFrameFormat" BO_ 1600 "StandardCAN_FD";
BA_ "GenMsgCycleTime" BO_ 1600 33;
```

---

## 7.8 Radar Object List — Extended Mux Example

```
BO_ 1700 Radar_ObjectList: 64 Radar_ECU
 /* Header */
 SG_ Radar_Status       : 0|4@1+   (1,0) [0|7]  ""   AEB_ECU
 SG_ Radar_NumObjects   : 4|5@1+   (1,0) [0|31] ""   AEB_ECU
 SG_ Radar_Timestamp    : 9|16@1+  (0.001,0) [0|65.535] "s" AEB_ECU
 SG_ Radar_HostSpeed    : 25|12@1+ (0.05,0) [0|204.75] "m/s" AEB_ECU
 
 /* Object Multiplexer selector */
 SG_ Radar_ObjID    M   : 37|5@1+  (1,0) [0|31] ""   AEB_ECU

 /* Per-object data (one set per frame, selected by ObjID) */
 SG_ Obj_Dist      m0   : 42|12@1+ (0.05,0) [0|204.75] "m"    AEB_ECU
 SG_ Obj_Angle     m0   : 54|10@1- (0.1,0)  [-51.2|51.1] "deg" AEB_ECU
 SG_ Obj_VRel      m0   : 64|12@1- (0.05,-102.4) [-102.4|102.35] "m/s" AEB_ECU
 SG_ Obj_RCS       m0   : 76|8@1-  (0.5,0)  [-64|63.5] "dBm2" AEB_ECU
 SG_ Obj_Type      m0   : 84|3@1+  (1,0)   [0|7] ""    AEB_ECU
 SG_ Obj_Valid     m0   : 87|1@1+  (1,0)   [0|1] ""    AEB_ECU

/* Same signals for objects 1-31: use SG_MUL_VAL_ for IDs 1-31 */
SG_MUL_VAL_ Obj_Dist  : Radar_ObjID 0-31;
SG_MUL_VAL_ Obj_Angle : Radar_ObjID 0-31;
SG_MUL_VAL_ Obj_VRel  : Radar_ObjID 0-31;
SG_MUL_VAL_ Obj_RCS   : Radar_ObjID 0-31;
SG_MUL_VAL_ Obj_Type  : Radar_ObjID 0-31;
SG_MUL_VAL_ Obj_Valid : Radar_ObjID 0-31;

BA_ "VFrameFormat"   BO_ 1700 "StandardCAN_FD";
BA_ "GenMsgCycleTime" BO_ 1700 50;
```

---

## 7.9 E2E (End-to-End) Protection in DBC

AUTOSAR E2E profiles are referenced via DBC attributes:

```
BA_DEF_ SG_ "E2EProfile"        ENUM "None","P01","P02","P04","P06";
BA_DEF_ SG_ "E2EDataId"         INT 0 65535;
BA_DEF_ SG_ "E2ECounterOffset"  INT 0 511;
BA_DEF_ SG_ "E2ECRCOffset"      INT 0 511;

BA_DEF_DEF_ "E2EProfile"       "None";
BA_DEF_DEF_ "E2EDataId"        0;
BA_DEF_DEF_ "E2ECounterOffset" 0;
BA_DEF_DEF_ "E2ECRCOffset"     0;

/* AEB_Req protected by E2E Profile 01 */
BA_ "E2EProfile"       SG_ 580 CRC_AEB         "P01";
BA_ "E2EDataId"        SG_ 580 CRC_AEB         580;
BA_ "E2ECounterOffset" SG_ 580 Alive_Ctr_AEB   36;
BA_ "E2ECRCOffset"     SG_ 580 CRC_AEB         40;
```

---

## 7.10 DBC Versioning and Change Management

### DBC Version Attribute Pattern

```
BA_DEF_  "DatabaseVersion"  STRING;
BA_DEF_  "AuthorName"       STRING;
BA_DEF_  "ReviewedBy"       STRING;
BA_DEF_  "ApprovalStatus"   ENUM "DRAFT","IN_REVIEW","APPROVED","RELEASED","OBSOLETE";
BA_DEF_  "ChangeDescription" STRING;
BA_DEF_  "ReleaseDate"      STRING;

BA_DEF_DEF_ "DatabaseVersion"   "";
BA_DEF_DEF_ "ApprovalStatus"    "DRAFT";

BA_ "DatabaseVersion"   "2.3.1";
BA_ "AuthorName"        "Shaik Irfan";
BA_ "ApprovalStatus"    "RELEASED";
BA_ "ReleaseDate"       "2026-05-27";
BA_ "ChangeDescription" "ECR-1234: Added AEB_Decel_Req signal per safety review";
```

### Git Workflow for DBC Files

```bash
# DBC in Git — recommended practices:
# 1. One DBC per bus per repository
# 2. Tag releases: git tag v2.3.1-ADAS-HS1
# 3. Never force-push to main branch (DBC history is audit trail)
# 4. Use .gitattributes to ensure CRLF line endings on Windows

# .gitattributes:
*.dbc text eol=crlf
*.arxml text eol=lf

# Diff a DBC change:
git diff HEAD~1 -- ADAS_HS1.dbc | grep "^[+-]BO_\|^[+-] SG_"
```

---

## 7.11 Advanced Bit Timing and CAN FD Tolerance

### Bit Timing Register Settings

```
500 Kbps CAN 2.0 (typical 80 MHz clock):
  Prescaler:   8
  Time Quanta: 10 TQ per bit
  Seg1:        7 TQ
  Seg2:        2 TQ
  SJW:         1 TQ
  
2 Mbps CAN FD data phase (80 MHz clock):
  Prescaler:   2
  Time Quanta: 20 TQ per bit
  Seg1:        15 TQ
  Seg2:        4 TQ
  SJW:         2 TQ
  
Sample point: Should be 70-80% of bit time
  500K: (1+7)/10 = 80% ✅
  2M:   (1+15)/20 = 80% ✅
```

---

## 7.12 Common Advanced DBC Errors

| Error | Root Cause | Fix |
|-------|-----------|-----|
| `SG_MUL_VAL_` signal not decoded in CANoe | SG_MUL_VAL_ not placed after corresponding BO_ in file | Place SG_MUL_VAL_ at end of file (before BA_ section) |
| CAN FD message not transmitted | Missing VFrameFormat attribute set to "StandardCAN_FD" | Add BA_ "VFrameFormat" for each FD message |
| SecOC freshness counter not incrementing | IL not driving freshness — needs custom CAPL | Add CAPL handler to increment and embed freshness |
| E2E check fail in ECU but CRC value looks correct | Wrong DataId configured | Verify BA_ E2EDataId matches AUTOSAR SWC configuration |
| Gateway signals wrong value after routing | Encoding difference between two buses | Verify Factor/Offset identical in both bus DBC files |

---

## Module 07 — Knowledge Check

1. What DBC keyword is used for extended (multi-range) multiplexing?
2. How many bytes can a DLC=15 CAN FD frame carry?
3. What are the two SecOC fields added to a protected message in the DBC?
4. Write the bus load formula for a DLC=8, 20ms cycle message on a 500 Kbps bus.
5. What BA_DEF_ attribute tells CANoe that a message is CAN FD?
6. In a gateway system, why must the Factor and Offset be identical in both bus DBCs?

**Answers:**
1. `SG_MUL_VAL_`
2. 64 bytes (DLC=15 in CAN FD = 64 bytes payload)
3. Freshness counter signal (SecOC_Fresh_*) and truncated MAC signal (SecOC_MAC_*)
4. Load = ((44 + 8×8) × (1000/20)) / 500000 × 100 = (108 × 50) / 500000 × 100 = 1.08%
5. `VFrameFormat` with value `"StandardCAN_FD"` or `"ExtendedCAN_FD"`
6. The gateway passes raw bytes through without re-encoding; if Factor/Offset differs, the decoded physical value will be wrong on the receiving bus
