# PLM Tool Validation — IQ/OQ/PQ Complete Guide

## 1. What is Computer System Validation (CSV)?

In FDA-regulated environments, **any computer system used to create, modify, maintain, archive, retrieve, or transmit data** that is part of regulatory records must be **validated** before it is used in production.

This applies to:
- PLM systems (Teamcenter, Windchill) used for DHF/DMR
- eQMS platforms (ETQ, TrackWise) for QMS records
- Test management tools (RQM, Jama) for V&V records
- ERP systems (SAP) used for batch records / DHR
- LIMS (lab information management)

**Regulatory Basis:**
- 21 CFR Part 11 §11.10(a): "Validation of systems to ensure accuracy, reliability, consistent intended performance, and the ability to discern invalid or altered records"
- 21 CFR Part 820.70(i): "Validate computer software for its intended use according to an established protocol"
- EU Annex 11 (pharma) / ISO 13485 §7.5.6 (process validation)

---

## 2. GAMP 5 Framework (FDA Accepted Guidance)

GAMP 5 (Good Automated Manufacturing Practice 5) provides the framework for CSV. Key principle: **risk-based approach** — validation effort proportional to risk and complexity.

### V-Model for CSV
```
User Requirements Spec (URS)
        ↕ traces
Functional Spec (FS)  ←──────────────────→ Acceptance Testing (UAT/PQ)
        ↕ traces
Design Spec (DS)  ←──────────────────────→ System Testing (OQ)
        ↕ traces
Module/Unit Spec  ←──────────────────────→ Unit Testing (IQ)
```

---

## 3. IQ — Installation Qualification

### Purpose
Verify that the system (hardware, software, network) is **installed correctly** and matches the approved specification.

### IQ Scope for a PLM System (e.g., Windchill 12.1)
```
IQ Checklist:
□ Server hardware specifications match approved spec
  (CPU, RAM, disk, OS version, network configuration)
□ Windchill software version and patch level documented
□ Oracle / SQL Server version documented
□ Installation performed per vendor procedure
□ Network connectivity verified (server ↔ client)
□ Environment variables and configuration files documented
□ System backup configured and tested
□ Antivirus / security software does not interfere
□ Vendor certificates / licences installed
□ Administrator accounts created and secured
□ Date/time configuration: synchronised to NTP server
□ Installation qualified in: DEV → QA → PROD environments
```

### IQ Test Case Example
```
Test ID:     IQ-TC-001
Title:       Verify Windchill Server Version
Requirement: SRS-IQ-001 — System shall be installed with Windchill 12.1.2
Procedure:
  Step 1: Log in to Windchill server via admin console
  Step 2: Navigate to Help → About Windchill
  Step 3: Record the version number displayed
Acceptance Criteria: Version displayed = "12.1.2" (PTC Windchill PDMLink)
Actual Result:    _______________
Pass / Fail:      □
Executed by:      _______________ Date: ___________
```

---

## 4. OQ — Operational Qualification

### Purpose
Verify that the system **functions as intended** across its operating range — confirms the system meets its functional specification under normal and boundary conditions.

### OQ Scope for PLM System
Covers all configured **functions and workflows**:

```
OQ Test Areas:
1. User Authentication and Access Control
   ├─ Valid user can log in
   ├─ Invalid credentials rejected
   ├─ Account locked after N failed attempts
   ├─ Role-based access enforced (read-only user cannot approve)
   └─ Session timeout enforced

2. Document Lifecycle Management
   ├─ Document creation (all object types)
   ├─ Check-out / Check-in workflow
   ├─ Version increment on new revision
   ├─ Previous revision becomes superseded on release
   └─ Document cannot be edited without check-out

3. Workflow / Approval Process
   ├─ Correct approvers receive tasks per workflow template
   ├─ Rejection routes document back to author
   ├─ Approval completes workflow, releases document
   ├─ Workflow cannot be bypassed
   └─ Notifications sent at each workflow step

4. Electronic Signatures (21 CFR Part 11)
   ├─ Signature requires username + password
   ├─ Signature meaning captured (approved, reviewed, etc.)
   ├─ Signature linked to document — cannot be transferred
   └─ Signature timestamp = system time (not user-modifiable)

5. Audit Trail
   ├─ Audit trail created on every record change
   ├─ Audit trail captures: user, action, old value, new value, timestamp
   ├─ Audit trail cannot be deleted or modified by any user
   └─ Audit trail viewable by authorised users

6. Search and Retrieval
   ├─ Search by part number returns correct results
   ├─ Search by description returns correct results
   ├─ Retrieved document matches stored document
   └─ Search performance within acceptable limits

7. BOM Management (if applicable)
   ├─ BOM hierarchy created correctly
   ├─ BOM effectivity dates enforced
   ├─ Component addition/removal tracked
   └─ BOM comparison between revisions works

8. Integration Tests
   ├─ CAD-PLM integration: NX part checked into Teamcenter
   ├─ ERP integration: BOM exported to SAP
   └─ eQMS integration: change notice triggers NCR in TrackWise
```

### OQ Test Case Example
```
Test ID:     OQ-TC-015
Title:       Verify Audit Trail Captures Document Modification
Requirement: SRS-OQ-015 — System shall capture all document changes in audit trail
Procedure:
  Step 1: Log in as user 'testuser1'
  Step 2: Search for and open document DOC-TEST-001 (Rev A)
  Step 3: Check out the document
  Step 4: Modify the description field from "Original" to "Modified"
  Step 5: Check in the document with comment "OQ Test"
  Step 6: Navigate to document audit trail
  Step 7: Verify audit trail entry for the description change

Acceptance Criteria:
  - Audit trail shows entry with:
    □ User: 'testuser1'
    □ Action: 'Check In' / 'Attribute Modified'
    □ Object: DOC-TEST-001
    □ Old Value: "Original"
    □ New Value: "Modified"
    □ Timestamp: within 2 minutes of test execution time
    □ Entry cannot be deleted or modified

Actual Result:    _______________
Pass / Fail:      □
```

---

## 5. PQ — Performance Qualification

### Purpose
Verify that the system **performs correctly in the actual business context** — end-to-end business process validation using representative data and scenarios.

### PQ Scope
PQ tests **business processes** rather than individual functions:

```
PQ Test Scenarios:
1. New Document Creation End-to-End
   Create SOP → Draft → Review → Approve → Release → Verify in DMR

2. Engineering Change Process
   Change Request → Impact Assessment → ECO → Update Documents → Release

3. DHF Package Compilation
   Create DHF folder → Link all required documents → Generate DHF report

4. Supplier Document Receipt
   Supplier uploads certificate → V&V engineer reviews → Approve → File in DHF

5. CAPA Process (if eQMS integrated)
   NCR raised → CAPA opened → Root cause documented → Action completed → Effectiveness verified

6. Regulatory Submission Package
   Compile documents for 510(k) → Export PDF with metadata → Verify completeness

7. Data Migration Verification (if applicable)
   Migrated document accessible → Matches original → Audit trail intact
```

### PQ Test Case Example
```
Test ID:     PQ-TC-003
Title:       New Product DHF End-to-End
Business Process: Complete design history file creation and release for NPI

Objective:
  Verify that the PLM system supports the complete NPI DHF process from
  design planning through design transfer.

Test Data:
  - Test project: "PROD-TEST-PQ" (non-production)
  - Documents: representative set of 10 DHF documents

Procedure:
  Step 1:  Create DHF folder structure in Teamcenter for PROD-TEST-PQ
  Step 2:  Upload Design Plan document (Rev 00, status: Draft)
  Step 3:  Route for review using "Document Review" workflow
  Step 4:  Reviewer reviews and approves
  Step 5:  Document status changes to "Released" — verify
  Step 6:  Repeat Steps 2-5 for: Design Inputs, Risk File, V&V Plan
  Step 7:  Upload Verification Test Report (Rev 00)
  Step 8:  Create traceability link: Verification Report → Design Input document
  Step 9:  Generate DHF completeness report
  Step 10: Verify all documents appear in report at correct revision

Acceptance Criteria:
  □ All documents released at correct revision
  □ Approval signatures captured for all documents
  □ Traceability links visible between documents
  □ DHF report shows all documents with correct metadata
  □ Audit trail shows complete history for each document

Actual Result:    _______________
Pass / Fail:      □
```

---

## 6. Validation Summary Report

After IQ + OQ + PQ execution, produce a Validation Summary Report:

```
VALIDATION SUMMARY REPORT

1. System Identification
   - System name and version
   - Validation environment

2. Validation Scope
   - What was validated
   - What was excluded and why

3. Results Summary
   - IQ: X tests, Y pass, Z fail
   - OQ: X tests, Y pass, Z fail
   - PQ: X tests, Y pass, Z fail

4. Deviations
   - List all deviations, risk assessment, disposition

5. Conclusion
   - System meets requirements for intended use
   - Ready for production use

6. Limitations and Exclusions

7. Recommendations (re-validation triggers)
   - Major version upgrade
   - Change to validation-critical functions
   - New regulatory requirement
   - Infrastructure change

8. Signatures
   - Validation Engineer
   - QA Manager
   - IT System Owner
```

---

## 7. Re-Validation Triggers

| Change Type | Re-Validation Required |
|-------------|----------------------|
| Major software version upgrade | Full OQ + affected PQ |
| Minor patch / hotfix | Risk assessment → targeted OQ |
| New workflow added | OQ for new workflow + affected PQ |
| Infrastructure change (server, OS) | IQ + representative OQ |
| New user role / access level | OQ for access control |
| Interface change (new integration) | OQ for integration |
| Security patch | Risk assessment → representative testing |

---

## 8. Validation Maintenance

### Periodic Review
- Conduct **annual review** of validated state
- Check: system still in validated state, no unauthorised changes
- Review audit logs for anomalies
- Update validation documentation if findings

### Change Control for Validated Systems
```
Change Request →
  Impact Assessment (does this affect validated functions?) →
    If YES: Validation Change Protocol →
              Test the affected functions →
              Update Validation Summary Report →
                Change Approved →
                  Implement in Production
    If NO: Document in change record, update risk assessment →
             Implement in Production
```

### Validation Metrics to Track
- Number of open deviations
- Time to close deviations
- Re-validation frequency
- Training completion rate
- Audit trail review completion
