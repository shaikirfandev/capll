# Module 13 — Automotive SOC & Incident Response

> Level: Advanced | Est. study time: 8 hours

---

## 13.1 Vehicle Security Operations Center (VSOC)

```
VSOC ARCHITECTURE:

  ┌─────────────────────────────────────────────────────────────────┐
  │                     VEHICLE FLEET (millions of vehicles)        │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
  │  │ Vehicle 1 │  │ Vehicle 2│  │ Vehicle 3│  │ Vehicle N│       │
  │  │  TCU/GW  │  │  TCU/GW │  │  TCU/GW  │  │  TCU/GW  │       │
  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
  └───────┼──────────────┼─────────────┼──────────────┼────────────┘
          │              │             │              │
          └──────────────┴─────────────┴──────────────┘
                                  │ TLS 1.3 (MQTT/HTTPS)
  ┌───────────────────────────────▼──────────────────────────────┐
  │                    CLOUD DATA INGESTION                      │
  │  ┌──────────────┐  ┌─────────────────┐  ┌────────────────┐  │
  │  │  Message     │  │  Data Pipeline  │  │  Data Lake     │  │
  │  │  Broker      │  │  (Kafka/Kinesis)│  │  (S3/Blob)     │  │
  │  │  (MQTT/AMQP) │  │                 │  │  Historical    │  │
  │  └──────────────┘  └─────────────────┘  └────────────────┘  │
  └───────────────────────────────────────────────────────────────┘
                                  │
  ┌───────────────────────────────▼──────────────────────────────┐
  │                    VSOC PLATFORM                             │
  │  ┌──────────────────┐  ┌─────────────────────────────────┐  │
  │  │  Vehicle IDS/IPS  │  │  SIEM (Splunk/Elastic/Sentinel) │  │
  │  │  Rule engine      │  │  Correlation rules              │  │
  │  │  ML anomaly det.  │  │  Alert management               │  │
  │  └──────────────────┘  └─────────────────────────────────┘  │
  │  ┌──────────────────┐  ┌─────────────────────────────────┐  │
  │  │  Threat Intel     │  │  Incident Ticketing             │  │
  │  │  CVE feeds        │  │  (ServiceNow / Jira)            │  │
  │  │  IOC sharing      │  │  Playbook automation            │  │
  │  └──────────────────┘  └─────────────────────────────────┘  │
  └───────────────────────────────────────────────────────────────┘
                                  │
  ┌───────────────────────────────▼──────────────────────────────┐
  │                    VSOC ANALYST TEAM                         │
  │  Tier 1: Alert triage (24/7)                                 │
  │  Tier 2: Incident analysis (business hours + on-call)        │
  │  Tier 3: Deep investigation + OEM engineering escalation     │
  └───────────────────────────────────────────────────────────────┘
```

---

## 13.2 In-Vehicle IDS (Intrusion Detection System)

```
TYPES OF AUTOMOTIVE IDS:

  Network IDS (NIDS):
    Placement: Gateway ECU (monitors all CAN buses, Ethernet)
    Detects: CAN injection, flooding, unexpected message IDs
    Challenge: High throughput (CAN FD at 8 Mbps), hard real-time constraints
    
  Host IDS (HIDS):
    Placement: On the ECU itself
    Detects: Flash modification, abnormal RAM usage, unexpected function calls
    Challenge: Limited ECU resources (no OS-level logging on MCUs)
    
  Behavioral IDS (BIDS):
    Placement: Cloud/Backend (analyzes vehicle telemetry)
    Detects: Statistical anomalies over time, fleet-level patterns
    Challenge: Privacy vs security (what telemetry is permissible?)

IDS RULE EXAMPLES:

  /* CAN Anomaly: Unexpected message ID */
  Rule_ID: CAN_001
  Trigger: CAN_ID NOT IN whitelist_for_bus_chassis
  Severity: HIGH
  Action: Alert VSOC + increment suspect_frame_counter
  
  /* CAN Anomaly: Message rate too high */
  Rule_ID: CAN_002
  Trigger: COUNT(CAN_ID_0x123) > 100 per 100ms
  Severity: CRITICAL  /* Normal cycle = 10ms, flood = DoS */
  Action: Alert + optional: enable bus-off protection
  
  /* UDS Anomaly: Programming session without prior extended session */
  Rule_ID: UDS_001
  Trigger: UDS_SERVICE_0x10_0x02 WITHOUT prior 0x10_0x03 in same session
  Severity: HIGH
  Action: Alert VSOC + log ECU ID, timestamp, session context
  
  /* OTA Anomaly: Unexpected firmware update attempt */
  Rule_ID: OTA_001
  Trigger: OTA_UPDATE for ECU_ID NOT IN scheduled_update_list
  Severity: CRITICAL
  Action: Block + Alert + Escalate to Tier 3
```

---

## 13.3 SIEM Integration — Automotive Log Sources

```
AUTOMOTIVE LOG TAXONOMY:

  Log Source          │ Format          │ Key Fields                  │ Retention
  ────────────────────┼─────────────────┼─────────────────────────────┼──────────
  IDS Gateway Alerts  │ CEF/JSON        │ ECU_ID, CAN_ID, timestamp   │ 90 days
  UDS Diagnostic Logs │ Custom/JSON     │ Service, NRC, session, ECU  │ 12 months
  OTA Update Events   │ JSON            │ VIN, ECU, version, result   │ Forever
  Security Access     │ JSON            │ Level, attempts, result     │ 12 months
  ECU Boot Events     │ Syslog-like     │ ECU_ID, boot_hash, result   │ 12 months
  Certificate Events  │ X.509 audit     │ Subject, expiry, status     │ Forever
  V2G/Charging Events │ OCPP JSON       │ VIN, EVSE, session, energy  │ 7 years

SPLUNK SPL CORRELATION EXAMPLE:

  /* Detect Security Access brute force across fleet */
  index=vsoc_uds 
  service="SecurityAccess" result="NRC_InvalidKey"
  | stats count by VIN, ECU_ID
  | where count > 3
  | eval severity=if(count > 10, "CRITICAL", "HIGH")
  | table VIN, ECU_ID, count, severity

  /* Detect fleet-wide pattern suggesting coordinated attack */
  index=vsoc_ids 
  alert_type="UnexpectedCAN_ID"
  | stats dc(VIN) as unique_vehicles count by CAN_ID
  | where unique_vehicles > 100
  | eval message="Fleet-wide CAN anomaly: " . CAN_ID
```

---

## 13.4 Incident Response Playbooks

### IRP-001: CAN Injection Attack

```
TRIGGER: IDS detects injection pattern (ID outside whitelist, high rate)

SEVERITY ASSESSMENT:
  ├─ Safety-critical ECU targeted (AEB, EPS, brakes)? → CRITICAL (P1)
  ├─ Non-safety ECU (body control, lighting)?         → HIGH (P2)  
  └─ Infotainment only?                              → MEDIUM (P3)

IMMEDIATE (0–1 hour):
  1. Determine if attack is active or historical
  2. Identify affected VINs from VSOC telemetry
  3. Brief safety team: vehicle safe to drive?
  4. [P1 only] Consider remote immobilization (if feature available)
  5. [P1 only] Contact national regulator (R155 mandates 72h notification)

INVESTIGATION (1–24 hours):
  6. Pull full CAN logs from affected vehicle(s) via OTA
  7. Identify attack source: physical (OBD) or remote (via gateway)?
  8. Reverse engineer injected message: what command was sent?
  9. Determine impact: did any ECU respond to injected message?
  10. Correlate: check if pattern seen in other vehicles

CONTAINMENT (parallel with investigation):
  11. Push IDS rule update to fleet: block the identified attack pattern
  12. If OBD-based: customer notification to visit dealer
  13. If remote: block at cloud gateway (if applicable)

ERADICATION:
  14. Root cause: which security control failed?
      - Missing whitelist rule?
      - SecOC not deployed on this bus?
  15. Develop patch: add SecOC / tighten whitelist
  16. Deploy via OTA to affected vehicles

POST-INCIDENT:
  17. Write incident report (ISO 21434 §14 format)
  18. Update TARA: add this attack to threat register
  19. Notify regulators (UNECE R155 requires tracking all incidents)
  20. Lessons learned meeting: prevent recurrence
```

### IRP-002: OTA Backend Compromise

```
TRIGGER: OTA package signed with valid cert but with unexpected content hash

IMMEDIATE (0–30 minutes):
  1. [CRITICAL] Pause ALL pending OTA deployments immediately
  2. Rotate affected signing certificate (revoke + reissue)
  3. Assess scope: how many packages were signed by compromised cert?
  4. Activate incident response team + CISO notification

INVESTIGATION:
  5. Forensic image of backend signing server
  6. Review HSM audit logs: who accessed signing key?
  7. Review deployment logs: which VINs received suspect packages?
  8. Verify installed firmware hashes vs known-good build artifacts

CONTAINMENT:
  9. Push firmware hash blocklist via emergency OTA channel
  10. ECUs reject any package with listed hashes
  11. Notify affected customers

ERADICATION:
  12. Rebuild signing infrastructure from scratch
  13. Rekey all HSMs
  14. Deploy known-good firmware to affected vehicles
  15. Update certificate pinning list

REGULATORY:
  16. 72-hour notification to national authority (UNECE R155)
  17. Provide impact assessment: number of affected vehicles
  18. Remediation timeline commitment
```

---

## 13.5 Threat Intelligence for Automotive

```python
"""
Automotive Threat Intelligence Feed Processor
Integrates CVE feeds, automotive-specific IOC lists
"""
import requests
import json
from typing import List, Dict
from datetime import datetime

class AutomotiveThreatIntel:
    NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    def __init__(self, api_key: str):
        self._api_key = api_key  # From environment variable
        self._headers = {"apiKey": self._api_key}
    
    def get_automotive_cves(self, days_back: int = 30) -> List[Dict]:
        """Fetch recent CVEs relevant to automotive components"""
        # Search for automotive keywords in NVD
        automotive_keywords = [
            "automotive", "ECU", "CAN bus", "AUTOSAR", 
            "telematics", "V2X", "ISO 15118", "UDS",
            "Infineon AURIX", "NXP S32K", "Renesas RH850"
        ]
        
        results = []
        for keyword in automotive_keywords:
            params = {
                "keywordSearch": keyword,
                "pubStartDate": self._days_ago(days_back),
                "pubEndDate": self._now()
            }
            resp = requests.get(self.NVD_API, headers=self._headers,
                                params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                results.extend(data.get("vulnerabilities", []))
        
        return self._deduplicate(results)
    
    def assess_vehicle_impact(self, cve: Dict, vehicle_sw_components: List[str]) -> Dict:
        """Determine if a CVE affects vehicles in fleet"""
        cve_id = cve.get("cve", {}).get("id", "")
        description = cve.get("cve", {}).get("descriptions", [{}])[0].get("value", "")
        cvss_score = self._extract_cvss(cve)
        
        affected = any(comp.lower() in description.lower() 
                       for comp in vehicle_sw_components)
        
        return {
            "cve_id": cve_id,
            "cvss_score": cvss_score,
            "affected": affected,
            "priority": "P1" if (affected and cvss_score >= 9.0) else
                        "P2" if (affected and cvss_score >= 7.0) else
                        "P3" if affected else "N/A",
            "description": description[:200]
        }
    
    def _extract_cvss(self, cve: Dict) -> float:
        try:
            metrics = cve["cve"]["metrics"]
            if "cvssMetricV31" in metrics:
                return metrics["cvssMetricV31"][0]["cvssData"]["baseScore"]
        except (KeyError, IndexError):
            return 0.0
    
    def _days_ago(self, days: int) -> str:
        from datetime import timedelta
        return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00.000")
    
    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%dT23:59:59.999")
    
    def _deduplicate(self, items: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for item in items:
            cve_id = item.get("cve", {}).get("id", "")
            if cve_id not in seen:
                seen.add(cve_id)
                unique.append(item)
        return unique
```

---

## 13.6 UNECE R155 Incident Reporting Requirements

```
UNECE R155 CYBERSECURITY MANAGEMENT SYSTEM (CSMS) — INCIDENT HANDLING:

  Reporting Obligations:
  ├── ANY detected cybersecurity incident must be tracked
  ├── Incidents with potential safety impact: notify type approval authority
  ├── Notification timeline: 72 hours for acute incidents (similar to GDPR)
  └── Annual reporting: incident statistics to regulatory authority
  
  Incident Categories (R155):
  ├── Category A: Attack realized → safety impact on vehicle
  ├── Category B: Attack realized → no safety impact (but unauthorized access)
  ├── Category C: Attack attempted → detected and prevented
  └── Category D: Vulnerability discovered → not yet exploited
  
  Required CSMS Documentation per Incident:
  1. Incident ID and date detected
  2. Affected vehicle type (not individual VINs for fleet privacy)
  3. Attack vector and method
  4. Cybersecurity goal affected
  5. Risk level (pre and post mitigation)
  6. Remediation actions taken
  7. Root cause analysis
  8. Prevention measures to avoid recurrence
  
  CSMS Audit:
  - OEM must undergo CSMS audit by UN-recognized technical service
  - Audit validates: process maturity, incident tracking, update management
  - Certificate valid for 3 years, renewable
```

---

## 13.7 Summary — Module 13

```
KEY TAKEAWAYS:

✓ VSOC = centralized security monitoring for entire vehicle fleet
✓ IDS placement: gateway (network), ECU (host), cloud (behavioral)
✓ SIEM correlation rules: brute force detection, fleet-wide pattern analysis
✓ Incident playbooks must address both technical and regulatory requirements
✓ UNECE R155: incidents must be tracked; acute safety incidents = 72h notification
✓ OTA compromise = most severe scenario: pause all deployments immediately
✓ CAN injection IR: determine if safety-critical ECU affected → determines priority
✓ Threat intel: automate CVE feed processing for fleet component matching
```

**Next Module**: [14 — Compliance & Standards](14_compliance_standards.md)
