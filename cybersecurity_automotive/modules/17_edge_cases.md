# Module 17 — Edge Cases & Failure Modes

> Level: Advanced | Est. study time: 6 hours

---

## 17.1 SecOC Edge Cases

### FC-001: Freshness Counter Rollover

```
SCENARIO: SecOC freshness counter reaches maximum value (2^24 - 1 = 16,777,215)
          and rolls over back to 0.

ROOT CAUSE:
  Counter stored as 24-bit value. After 16 million increments, rolls to 0.
  At 100 messages/second: rollover in ~46 hours of continuous operation.
  
IMPACT:
  After rollover: receiver sees counter(0) < last_accepted_counter(16777215)
  → All messages rejected as replays
  → Safety-critical messages (AEB, EPS) no longer authenticated
  → System either crashes or degrades to unsafe mode
  
DETECTION:
  Monitor freshness counter value in production
  Alert when approaching 80% of max value
  
MITIGATION:
  Option A: Use 64-bit counters (AUTOSAR FVM supports this)
  Option B: Scheduled counter resync procedure (UDS routine control)
  Option C: NvM-backed counter with resync on boot
  
RESYNC PROCEDURE:
  Both ECUs enter Programming Session → 
  OTA command resets counters atomically →
  Both resume with counter = 0 at same time
  
VALIDATION STRATEGY:
  Test: Run sender at 1000 Hz (100x normal) → verify rollover handling
  SWR test: Manually inject counter = 0xFFFFFE → verify rollover transition
```

### FC-002: NvM Write Failure for Counter Persistence

```
SCENARIO: Flash memory write fails during freshness counter persistence to NvM.

ROOT CAUSE:
  Flash wears out (rated for ~100K writes on typical ECU flash)
  Write interrupted by sudden power loss (e.g., crash, ECU reset)
  
IMPACT:
  After ECU reset: counter reads last valid NvM value (potentially old)
  ECU accepts messages from lower counter values → window for replay attacks
  
DETECTION:
  NvM write error callback → log security event
  Compare NvM counter to in-RAM counter on startup
  
MITIGATION:
  Wear-leveling: rotate write address across multiple NvM blocks
  Redundant storage: write counter to two independent NvM blocks
  Signed counter: MAC over counter value prevents tampering with NvM
  
  /* On startup: verify NvM counter integrity */
  void FvM_Init(void) {
      uint32_t nvm_counter_a = NvM_ReadBlock(NVM_FV_BLOCK_A);
      uint32_t nvm_counter_b = NvM_ReadBlock(NVM_FV_BLOCK_B);
      
      if (nvm_counter_a != nvm_counter_b) {
          /* Discrepancy: take higher value + log event */
          g_freshnessCounter = MAX(nvm_counter_a, nvm_counter_b);
          log_security_event(SEC_EVENT_FV_DISCREPANCY, 0);
      } else {
          g_freshnessCounter = nvm_counter_a;
      }
  }
```

---

## 17.2 Secure Boot Edge Cases

### FC-003: Clock/Time Dependency in Certificate Validation

```
SCENARIO: ECU uses X.509 certificate for Secure Boot, but RTC is reset.

ROOT CAUSE:
  X.509 certificates have validity period (NotBefore / NotAfter).
  After battery disconnect or ECU power loss: RTC may reset to epoch (Jan 1, 1970).
  Certificate validator sees: "current time = 1970" → certificate not yet valid → rejected.
  
IMPACT:
  ECU refuses to boot (cert rejected) → vehicle immobilized
  
DETECTION:
  RTC validation at boot: if RTC < minimum_plausible_time → RTC reset detected
  
MITIGATION:
  Option A: Use monotonic counter-based validity (not calendar time)
  Option B: Trust-anchor chain: only check signature, not time validity
  Option C: Store last-known-good time in NvM; if RTC < NvM time → use NvM time
  Option D: OCSP (Online Certificate Status Protocol) with time from server
  
  /* RTC sanity check in bootloader */
  #define MIN_PLAUSIBLE_TIME 1640000000UL  /* Jan 1, 2022 - compile-time lower bound */
  
  if (get_rtc_unix_time() < MIN_PLAUSIBLE_TIME) {
      rtc_is_valid = FALSE;
      /* Use certificate without time validation until RTC synced via OTA */
  }
```

### FC-004: Hash Algorithm Mismatch After Partial OTA

```
SCENARIO: OTA update upgrades hash algorithm from SHA-256 to SHA-384 in bootloader,
          but application still uses SHA-256 headers.

ROOT CAUSE:
  Multi-stage OTA: bootloader upgraded in Stage 1, application not yet upgraded.
  Bootloader now expects SHA-384 headers.
  Application image still has SHA-256 headers.
  
IMPACT:
  Vehicle cannot complete boot → permanent brick until recovery flash
  
MITIGATION:
  Atomic OTA: bootloader and application upgraded in single atomic transaction
  Compatibility flag: bootloader supports both SHA-256 and SHA-384 during migration
  Rollback: if new bootloader cannot verify application → auto-rollback to old bootloader
  
  /* Bootloader: support multiple algorithms during migration */
  Std_ReturnType VerifyFirmwareHash(const FwHeader_t *header) {
      if (header->hash_algo == HASH_SHA384) {
          return Verify_SHA384(header);
      } else if (header->hash_algo == HASH_SHA256) {
          /* Legacy support during migration period */
          return Verify_SHA256(header);
      }
      return E_NOT_OK;  /* Unknown algorithm → reject */
  }
```

---

## 17.3 TLS / Certificate Edge Cases

### FC-005: Certificate Expiry in Production Fleet

```
SCENARIO: OTA backend TLS certificate expires → all vehicles lose OTA connectivity.

ROOT CAUSE:
  Certificate valid for 2 years. Operations team misses renewal.
  All vehicles simultaneously lose OTA connection.
  
IMPACT:
  Mass-scale OTA failure → no security patches deployable
  Last patch potentially deployed months ago → growing vulnerability window
  
REAL OCCURRENCE: Multiple automotive OEMs experienced this 2020–2022

MITIGATION:
  Monitoring: alert at 90 days before expiry (>90 day renewal lead time)
  Automated renewal: Let's Encrypt / ACME protocol for backend certs
  Certificate pinning: update pin in vehicle before cert change
  Grace period: accept old cert for 30 days after expiry (transition window)
  
RECOVERY FROM EXPIRED CERT:
  Option A: If OTA still works (somehow) → push cert update
  Option B: Dealer update via USB/OBD → emergency channel
  Option C: Phased renewal: update DNS → new cert → phased vehicle cert-pin update
```

### FC-006: Certificate Pinning vs CDN Change

```
SCENARIO: Vehicle pins specific TLS certificate. OEM migrates to new CDN.
          New CDN uses different certificate → all vehicles reject OTA connection.

ROOT CAUSE:
  Certificate pinning (leaf cert pinning) is too specific.
  CDN migration changes certificate.
  
MITIGATION:
  Pin CA certificate (not leaf cert) — more stable
  Or: pin public key hash (SPKI pinning) — survives cert renewal with same key
  Implement cert transparency monitoring
  
  /* Pin CA cert hash, not leaf cert hash */
  #define PINNED_CA_SPKI_HASH \
      "\xDE\xAD\xBE\xEF..."  /* SHA-256 of CA SubjectPublicKeyInfo */
      
  bool verify_pin(X509 *cert) {
      /* Check if any cert in chain matches our pinned CA */
      /* More flexible than pinning the specific leaf cert */
  }
```

---

## 17.4 CAN Bus Edge Cases

### FC-007: Bus-Off Storm (Multiple ECUs Simultaneously)

```
SCENARIO: ECU goes bus-off → automatically recovers after 128 * 11 bit errors.
          Recovery attempt → more errors → bus-off again → storm.

ROOT CAUSE:
  Persistent hardware fault (damaged CAN transceiver, short to ground)
  Multiple ECUs affected → simultaneous bus-off storms
  Bus utilization reaches 100% → all ECUs queuing frames → escalating errors
  
IMPACT:
  Complete CAN bus failure → vehicle loses all communication
  Safety systems (ABS, ESC, AEB) non-operational
  
DETECTION:
  CAN error counter monitoring: TEC > 200 → alert
  Bus-off recovery count: >3 recoveries in 1 minute → hardware fault
  
MITIGATION:
  Auto-recovery with backoff: 1st recovery immediate, 2nd after 100ms, 3rd after 1s
  Gateway: detect bus-off storm → isolate affected bus from rest of network
  
  /* ECU bus-off handler */
  void CAN_BusOff_Handler(void) {
      static uint8_t recovery_count = 0;
      recovery_count++;
      
      if (recovery_count > 3) {
          /* Hardware fault — do not attempt further recovery */
          set_safe_state(SAFE_STATE_CAN_FAULT);
          log_dtc(DTC_CAN_HARDWARE_FAULT);
          return;
      }
      
      /* Exponential backoff before recovery */
      uint32_t delay_ms = (1u << recovery_count) * 10u;  /* 20ms, 40ms, 80ms */
      start_timer(delay_ms, CAN_Recovery_Callback);
  }
```

### FC-008: DLC Spoofing Attack

```
SCENARIO: Attacker sends valid CAN ID but with wrong DLC (data length code).

ROOT CAUSE:
  CAN allows any DLC 0–8. ECU receiver expects fixed DLC.
  If receiver reads beyond actual data (trusting DLC in message) → buffer over-read.
  Or: if receiver ignores message but IDS whitelisted by ID only → injection bypass.
  
ATTACK EXAMPLE:
  Legitimate: 0x244 DLC=8 (AEB message, normally 8 bytes)
  Attacker:   0x244 DLC=0 (empty frame) → passes ID-based IDS but disrupts receiver
  Or:         0x244 DLC=8, only 4 valid bytes → receiver reads garbage bytes 4-7
  
MITIGATION:
  IDS rules: whitelist BOTH message ID AND expected DLC
  ECU receiver: validate DLC before accessing data bytes (Module 12 pattern)
  
  Rule_ID: CAN_DLC_001
  Trigger: CAN_ID == 0x244 AND DLC != 8
  Action: DROP + ALERT
```

---

## 17.5 UDS Edge Cases

### FC-009: Security Access State Lost on ECU Reset

```
SCENARIO: UDS session with Security Access granted. ECU receives reset command
          mid-operation (or power cycle). Security state lost.
          Tester assumes it's still authenticated.

ROOT CAUSE:
  Security access state is in RAM → cleared on reset.
  UDS standard: ECU returns to Default Session on reset.
  Some testers don't re-authenticate after unexpected reset.
  
IMPACT:
  Tester sends programming commands → NRC 0x22 (conditionsNotCorrect)
  Could be interpreted as vulnerability by automated test
  
MITIGATION:
  Tester must detect unexpected NRC and re-execute session/auth sequence
  ECU must always start in Default Session after reset (not retain security state)
  
  /* Tester state machine */
  Std_ReturnType execute_flash_sequence(void) {
      Std_ReturnType ret = E_OK;
      
      /* Retry loop for unexpected ECU resets */
      for (int attempt = 0; attempt < 3; attempt++) {
          ret = enter_programming_session();
          if (ret != E_OK) continue;
          
          ret = authenticate_security_access_level_2();
          if (ret != E_OK) continue;
          
          ret = download_firmware();
          if (ret == E_OK) return E_OK;  /* Success */
          
          /* Reset or error — retry from beginning */
          wait_ms(500);
      }
      return E_NOT_OK;
  }
```

### FC-010: DIDS with Dynamic Length Responses

```
SCENARIO: DID (e.g., 0xF1A0 — system information) returns variable length response.
          Tester expects fixed 20 bytes, ECU sends 25 bytes after SW update.

ROOT CAUSE:
  DID response format changed between SW versions.
  No backward compatibility in DID definition.
  
IMPACT:
  Automated test fails (length mismatch)
  Parsing code reads beyond expected boundary → buffer over-read in tester tool
  
MITIGATION:
  DID responses should include length field
  Tester: validate length against known version, not hardcoded value
  DID change management: version-bump required for any response format change
```

---

## 17.6 OTA Edge Cases

### FC-011: OTA Update During Driving

```
SCENARIO: OTA update for ECU starts while vehicle is moving at 60 km/h.
          OTA abruptly interrupts ECU operation during download.

ROOT CAUSE:
  UNECE R156 requires SUMS to check pre-conditions before starting update.
  Some implementations check vehicle speed at start but not throughout.
  
IMPACT:
  ECU enters programming mode mid-drive → communication loss →
  If safety-critical ECU: immediate safety hazard
  
MITIGATION:
  R156 mandates: OTA must not apply safety-critical updates while vehicle is moving
  Pre-condition checks: speed = 0, engine off, parking brake set
  Continuous monitoring: abort update if vehicle starts moving
  Separate update of safety vs non-safety ECUs
```

### FC-012: Corrupted OTA Package

```
SCENARIO: OTA package download interrupted (cellular signal lost). 
          Vehicle retries with partial package.

ROOT CAUSE:
  No resume capability in OTA client.
  Partial package stored in download buffer.
  Hash verification of partial data fails.
  
IMPACT:
  OTA install loop: download → verify fails → download again → repeat
  If persistent: permanent loop consuming cellular bandwidth, battery
  
MITIGATION:
  Chunked download with chunk-level verification
  Resume capability: track last successfully received chunk
  Max retry limit with exponential backoff
  After N failures: mark update as failed, notify VSOC
```

---

## 17.7 SOME/IP Edge Cases

### FC-013: Service Offer Flooding (SOME/IP-SD Amplification)

```
SCENARIO: Rogue device on automotive Ethernet sends SOME/IP OfferService
          messages at high rate, flooding the SD multicast group.

ROOT CAUSE:
  No authentication on SOME/IP-SD messages (design limitation)
  Any device on the Ethernet segment can claim to offer any service
  
IMPACT:
  Legitimate clients pick up rogue service offer → connect to attacker
  Service table overflow in clients → legitimate services lost
  DoS: UDP multicast flooding → all ECUs processing irrelevant traffic
  
MITIGATION:
  TLS/DTLS on SOME/IP communications (authenticated services)
  Service instance tracking: if same service offered from new MAC → alert
  Firewall: whitelist known service provider MAC/IP pairs
  SOME/IP rate limiting: maximum N SD messages per second per source
```

---

## 17.8 Edge Case Summary Table

| ID | Category | Failure Mode | Detection | Mitigation Priority |
|----|----------|-------------|-----------|---------------------|
| FC-001 | SecOC | Counter rollover | Monitor NvM counter | HIGH |
| FC-002 | SecOC | NvM write failure | NvM write error callback | HIGH |
| FC-003 | Secure Boot | RTC reset breaks cert | RTC sanity check | MEDIUM |
| FC-004 | OTA | Hash algo mismatch | Boot compatibility test | HIGH |
| FC-005 | TLS | Cert expiry | 90-day monitoring | CRITICAL |
| FC-006 | TLS | Cert pin vs CDN change | SPKI pinning | HIGH |
| FC-007 | CAN | Bus-off storm | Error counter monitoring | HIGH |
| FC-008 | CAN | DLC spoofing | IDS DLC whitelist | MEDIUM |
| FC-009 | UDS | Auth state on reset | Tester retry logic | LOW |
| FC-010 | UDS | Dynamic DID length | Length validation | MEDIUM |
| FC-011 | OTA | Update during driving | Speed pre-condition | CRITICAL |
| FC-012 | OTA | Corrupted package | Chunked verify | MEDIUM |
| FC-013 | SOME/IP | SD flooding | SD rate limiting | MEDIUM |

---

## 17.9 Summary — Module 17

```
KEY TAKEAWAYS:

✓ Counter rollover is a real threat: plan for it with 64-bit counters or resync
✓ Certificate expiry is #1 operational cybersecurity failure in automotive fleets
✓ RTC reset breaks time-based certificate validation → need fallback strategy
✓ Bus-off storms can cascade: multiple simultaneous ECU failures
✓ DLC validation is as important as ID-based whitelisting
✓ OTA during driving violates R156 and creates safety risk
✓ SOME/IP-SD has no native authentication: compensate with network controls
✓ Each edge case requires: root cause, detection method, mitigation, validation test
```

**Next Module**: [18 — Interview Preparation](18_interview_prep.md)
