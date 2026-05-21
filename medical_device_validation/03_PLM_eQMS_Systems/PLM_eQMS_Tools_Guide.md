# PLM Systems, eQMS, and Requirements Management Tools

## 1. PLM Systems Overview

### What is PLM?
Product Lifecycle Management (PLM) software manages all information about a product from inception through engineering, manufacturing, service, and disposal. In medical devices, the PLM system typically hosts:
- **Design documents** (drawings, specs, BOM)
- **Document control** (version control, approval workflows)
- **Change management** (ECO/ECR process)
- **DHF/DMR** content organisation
- **Configuration management**

---

## 2. Siemens Teamcenter

### Architecture
```
Teamcenter Architecture:
├── Teamcenter Rich Client (desktop application)
├── Teamcenter Active Workspace (web browser UI)
├── Teamcenter Server (FSC, GMS, volume)
├── Oracle / SQL Server database
└── Integration connectors (NX, Solid Edge, AutoCAD, etc.)
```

### Key Objects in Teamcenter
| Object Type | Used For |
|------------|---------|
| Item / Item Revision | Version-controlled document or part |
| Dataset | The actual file attached to an Item Revision |
| BOM / BOMView | Bill of Materials structure |
| Workflow / Process | Approval routing and sign-off |
| Change Request (CR) | Initiates a change |
| Engineering Change Order (ECO) | Approved change to be implemented |
| Form | Metadata / structured data entry |
| Folder | Organisation hierarchy |

### Document Control Workflow (Teamcenter)
```
Author creates Item Revision (status: "In Work")
    ↓
Author uploads dataset (Word, PDF, drawing)
    ↓
Author initiates Workflow (Submit for Review)
    ↓
Reviewer receives task → Reviews → Approves or Rejects
    ↓
Approver receives task → Signs → Releases
    ↓
Item Revision status → "Released"
    ↓
Previous revision status → "Superseded"
```

### Common Teamcenter Operations for V&V Engineers
1. **Search**: Find documents by part number, description, revision
2. **Check Out / Check In**: Lock document for editing, return with changes
3. **View Revision History**: See all revisions and who approved
4. **BOM Management**: Add/remove items, associate test results to parts
5. **Workflow Monitoring**: Track approval status
6. **Export for Audit**: Generate PDF with metadata for DHF

### Teamcenter Validation (IQ/OQ/PQ)
- **IQ**: Verify Teamcenter installed on correct server, version, OS, database
- **OQ**: Verify core functions work — create item, workflow, version control, access control
- **PQ**: Verify the system meets specific business process requirements in medical device context

---

## 3. PTC Windchill

### Windchill vs Teamcenter (Quick Comparison)
| Feature | Windchill | Teamcenter |
|---------|-----------|-----------|
| UI | Web-native | Rich client + Active Workspace |
| Deployment | On-premise / cloud (Atlas) | On-premise / Cloud (Xcelerator) |
| CAD Integration | PTC Creo native | NX native (others via connectors) |
| Medical use | Strong in medical/pharma | Strong in aerospace/automotive |
| DHF support | eQMS module available | Quality module available |

### Windchill Key Features for Medical
- **Windchill PDMLink**: Core PLM, document/part management
- **Windchill ProjectLink**: Project and program management
- **Windchill Quality Management**: CAPA, NCR, audit management
- **Windchill Regulatory Content Management**: Links to regulatory submissions

### Windchill Document Life Cycle (DLC)
```
States: [In Work] → [Under Review] → [Released] → [Obsolete]
                              ↑
                        [Rework] ←─ Rejected
```

### Object Types in Windchill
- **WTDocument**: Word/Excel/PDF documents with version control
- **WTPart**: Physical parts (hardware) with BOMs
- **EPMDocument**: CAD files (Creo, AutoCAD)
- **Change Notice (CN)**: Approved change
- **Change Request (CR)**: Proposed change
- **Promotion Request**: Move to next lifecycle state

---

## 4. eQMS Platforms

### ETQ Reliance
A cloud-based eQMS used heavily in FDA-regulated industries.

**Key Modules:**
```
ETQ Modules:
├── Document Control       → SOPs, work instructions, templates
├── Change Management      → ECR/ECO, impact assessments
├── CAPA Management        → Root cause analysis, action tracking
├── Nonconformance (NCR)   → Deviation, OOS, complaints
├── Audit Management       → Audit schedule, findings, CAPAs
├── Training Management    → Training matrix, records, reminders
├── Supplier Management    → Supplier qualification, audits
├── Risk Management        → FMEA, risk register
└── Complaint Handling     → MDR/vigilance linkage
```

**ETQ Validation Requirements (21 CFR Part 11):**
- ETQ itself is a validated system by ETQ (vendor IQ/OQ)
- Customer must perform **PQ** for their specific configuration/workflows
- All custom workflows, forms, and business rules require validation evidence

### TrackWise Digital (Sparta Systems / Honeywell)
TrackWise is widely used by large pharma and medical device companies for QMS.

**Key Features:**
- Industry-specific workflows pre-built (CAPA, NCR, complaint, change)
- Full Part 11 compliance (audit trail, e-signatures)
- Strong reporting and analytics
- Integration with ERP systems (SAP)
- **TrackWise Digital**: Cloud SaaS version with modern UI

**Validation Approach:**
- Vendor provides IQ documentation
- Customer executes OQ (verify standard workflows)
- Customer executes PQ (verify custom workflows in production-like environment)

### Veeva Vault QMS
Growing in medical device market (from pharma):
- Content management + QMS combined
- Strong for global/multi-site organisations
- Document control integrated with training
- Direct integration with Veeva RIM for regulatory submissions

---

## 5. Requirements Management Tools

### Jama Connect
Purpose-built requirements and test management for complex products.

**Key Capabilities:**
```
Jama Connect Features:
├── Requirements authoring (structured, hierarchical)
├── Traceability (forward/backward, visual diagram)
├── Review Center (structured review with comments, approvals)
├── Test Management (test cases, test runs, results)
├── Defect tracking (integration with Jira, Azure DevOps)
├── Reuse libraries (requirement sets reused across projects)
└── Risk management (risk items linked to requirements)
```

**Jama Item Types (customisable):**
- Stakeholder Need → User Requirement → System Requirement → Software Requirement → Test Case

**Traceability in Jama:**
```
Jama Traceability View:
User Need [UN-001] ──→ Sys Req [SR-012] ──→ SW Req [SWR-034] ──→ Test [TC-056]
                                        └──→ Design Spec [DS-007]
```

**Jama Review Centre:**
- Author publishes review request
- Reviewers comment line-by-line with timestamps
- Comments are dispositioned (accepted/rejected/deferred)
- Full audit trail of review comments and responses

### IBM DOORS / DNG (DOORS Next Generation)

**IBM DOORS Classic** (legacy):
- Module-based requirements database
- Uses ReqIF for import/export
- Strong for large complex systems (aerospace, medical)
- Traceability via DXL links

**IBM DOORS Next Generation (DNG)**:
- Web-based (part of IBM ELM / Engineering Lifecycle Management)
- Integrates with RQM (test), EWM (work items/defects)
- OSLC-based linking between tools
- Better UI than classic DOORS

```
IBM ELM Suite (formerly CLM):
├── DNG (DOORS Next) → Requirements
├── RQM (Quality Manager) → Test cases, test execution
├── EWM (Engineering Workflow Mgmt) → Defects, work items
└── LQE (Lifecycle Query Engine) → Cross-tool reporting
```

### IBM RQM (Rational Quality Manager) / IBM EWM
**Test Case Structure in RQM:**
- **Test Plan**: Scope, strategy, resources
- **Test Case**: Step-by-step procedure with expected results
- **Test Suite**: Collection of test cases
- **Test Execution Record**: Actual execution results
- **Test Script**: Automated script linked to manual test case

**Traceability in RQM:**
- Test case → Requirement (DNG)
- Test execution → Defect (EWM/Jazz)
- Test plan → Feature/Story (EWM)

### ALM Tools Comparison

| Feature | Jama | IBM DNG/RQM | PolarionALM | Azure DevOps |
|---------|------|------------|-------------|-------------|
| Requirements | ★★★★★ | ★★★★★ | ★★★★☆ | ★★★☆☆ |
| Traceability | ★★★★★ | ★★★★☆ | ★★★★★ | ★★★☆☆ |
| Test Management | ★★★★☆ | ★★★★★ | ★★★★☆ | ★★★★☆ |
| Regulated use | ★★★★★ | ★★★★★ | ★★★★☆ | ★★★☆☆ |
| Integration | ★★★★☆ | ★★★★☆ | ★★★★★ | ★★★★★ |
| Learning curve | Medium | High | Medium | Low |

---

## 6. PLM Data Migration

### Common Migration Scenarios
1. **PLM to PLM**: Agile/Arena → Windchill, or legacy → Teamcenter
2. **Paper to PLM**: Scanned docs → electronic with metadata
3. **PLM version upgrade**: Teamcenter 11 → Teamcenter 13
4. **eQMS migration**: Paper SOPs → ETQ or TrackWise
5. **ERP integration**: PLM BOM → SAP Material Master

### PLM Migration Process
```
Phase 1: ASSESSMENT & PLANNING
├── Inventory source system objects (types, counts, relationships)
├── Map source objects to target objects (data mapping spec)
├── Identify data quality issues in source
├── Define migration rules (what to migrate, what to archive)
└── Migration strategy: big-bang vs phased vs parallel run

Phase 2: DATA CLEANSING
├── Identify duplicate records
├── Resolve missing metadata
├── Verify document completeness
└── Update to latest revision if needed

Phase 3: MIGRATION DEVELOPMENT
├── Write migration scripts (ETL: Extract, Transform, Load)
├── Test on development environment (sample data)
└── Validate migrated data against source

Phase 4: VALIDATION (if FDA-regulated)
├── IQ: Target system installed correctly
├── OQ: Migration scripts function correctly
├── PQ: Migrated data is accurate, complete, and accessible

Phase 5: CUTOVER
├── Freeze source system
├── Final migration run
├── Verification of migrated records
└── Switch users to target system

Phase 6: POST-MIGRATION
├── Decommission or archive source system
├── Update SOPs and training
└── Monitor for issues
```

### Migration Validation Requirements (21 CFR Part 11 / GAMP 5)
- Original records must be preserved (data integrity)
- Migrated records must be equivalent to originals
- Audit trail of migration must be maintained
- Electronic signatures must remain valid (or re-signed)
- System validation documentation updated

### GAMP 5 Categories (for system validation complexity)
| Category | Description | Validation Effort |
|----------|------------|-----------------|
| 1 | Infrastructure software (OS, network) | Low |
| 3 | Non-configured software (no customisation) | Medium |
| 4 | Configured software (ETQ, TrackWise default) | Medium-High |
| 5 | Custom software / bespoke | High |

---

## 7. Integration Patterns Between Tools

### Common Medical Device Tool Stack
```
Requirements:    Jama / DNG
     ↓ (traced)
Design:          Teamcenter / Windchill (CAD, BOM)
     ↓ (traced)
Test Cases:      RQM / Jama
     ↓ (results)
Defects:         Jira / EWM
     ↓ (CAPA)
Quality:         ETQ / TrackWise
     ↓ (document)
Regulatory:      Veeva Vault / DocuBridge
```

### Integration Best Practices
- Use **OSLC** (Open Services for Lifecycle Collaboration) for IBM tools
- Use **REST APIs** for Jama ↔ Jira integration
- **ReqIF** format for requirements exchange between tools
- Avoid manual copy-paste — automate links to preserve traceability integrity
