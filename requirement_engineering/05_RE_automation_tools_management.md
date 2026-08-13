# Automotive Requirements Engineering — Automation, Management, Change, Conflict, Metrics, and Quality Analysis

> **Scope**: Sections 23 through 28 of an advanced automotive requirements engineering reference.
> **Audience**: System engineers, software requirements engineers, safety engineers, validation engineers, test automation engineers, ECU architects, and supplier quality teams.
> **Context**: Automotive ECU, ADAS, body, powertrain, chassis, and safety-related development under ASPICE, ISO 26262, ISO/IEC/IEEE 29148, and common OEM-supplier delivery models.

---

## Table of Contents

- [Section 23: Requirements for Test Automation](#requirements-for-test-automation)
- [Section 24: Requirements Management Tools](#requirements-management-tools)
- [Section 25: Requirement Change Management](#requirement-change-management)
- [Section 26: Requirement Conflict Resolution](#requirement-conflict-resolution)
- [Section 27: Requirements Metrics](#requirements-metrics)
- [Section 28: Requirements Quality Analysis](#requirements-quality-analysis)

---

## Section 23: Requirements for Test Automation

Test automation in automotive engineering is only valuable when it is explicitly **requirements-driven**. A fast test that is not anchored to an approved requirement is operationally convenient but weak in audits, weak in safety arguments, and weak in release decisions. In contrast, a requirement-linked automated test supports traceability, regression control, evidence generation, and objective quality reporting.

In mature automotive programs, the automation chain is not merely “write pytest and run it.” The chain is a controlled engineering flow that starts with an approved requirement and ends with a report that proves the requirement was verified under known conditions.

### 23.1 Core Principle

A requirement must be verifiable by at least one method, and the selected verification method should be represented in a repeatable, reviewable, and tool-supported workflow.

```text
REQ -> TC -> pytest -> CANoe -> CAN FD -> ECU -> Expected Safety Reaction -> Test Report
```

This flow is especially powerful for body, powertrain, chassis, and ADAS ECUs where requirement verification involves bus stimulation, diagnostic triggers, timing measurements, and observation of safe-state behavior.

### 23.2 Why Requirements-Driven Automation Matters

- It ensures every automated test exists for a business, functional, safety, or regulatory reason.
- It allows traceability from requirement to test case, to script, to result, to release evidence.
- It helps review boards understand exactly which product behavior changed after a requirement update.
- It supports ASPICE SYS.4/SWE.4 evidence and ISO 26262 confirmation arguments.
- It reduces hidden orphan tests that consume test execution time but verify nothing formally approved.
- It enables gap analysis: requirements without tests, tests without requirements, and changed requirements without refreshed verification.

### 23.3 Artifact Chain

| Artifact | Purpose | Typical Owner | Example |
|---|---|---|---|
| Requirement (REQ) | Defines intended system behavior | Requirements engineer / system engineer | `REQ-BRK-217` |
| Test Case (TC) | Human-readable verification design | Test engineer | `TC-BRK-217-01` |
| Automated Test Script | Executable verification logic | Test automation engineer | `test_braking_safe_reaction.py` |
| Test Environment Configuration | Defines CANoe setup, channels, dbc/arxml, variants | Test environment owner | `canoe_cfg/BrakeSystem.cfg` |
| Stimulus and Observation Data | Input frames, diagnostic requests, measurements | Validation team | `can_inputs/*.json` |
| ECU Execution Evidence | Actual response from target ECU | ECU / HIL / bench | log frames, diagnostics, internal traces |
| Test Report | Formal evidence for review and release | QA / test lead | HTML, JUnit XML, PDF, dashboard entry |

### 23.4 Typical Requirement-to-Test Mapping Pattern

| Requirement ID | Requirement Statement | Verification Level | Test Case ID | Automation Target | Acceptance Criterion |
|---|---|---|---|---|---|
| `REQ-BRK-217` | When brake pressure sensor signal is lost for more than 100 ms, the brake control ECU shall set a fault state and request torque reduction within 50 ms. | Integration / HIL | `TC-BRK-217-01` | pytest + CANoe + CAN FD bench | Fault DTC set, torque reduction request transmitted, reaction time <= 50 ms |
| `REQ-ADAS-481` | If forward radar object confidence falls below threshold for 200 ms during active AEB monitoring, the ADAS ECU shall disable autonomous braking and notify the driver. | System / vehicle | `TC-ADAS-481-02` | pytest + CANoe restbus + camera/radar simulation | Driver warning shown, AEB output inhibited, event logged |
| `REQ-BCM-133` | When the door-open signal is present and vehicle speed exceeds 5 km/h, the BCM shall issue a warning chime within 300 ms. | SIL / HIL | `TC-BCM-133-03` | pytest + CANoe + audio event trace | Chime request message sent within 300 ms |

### 23.5 Verification Method Selection

| Requirement Characteristic | Suitable Automation Level | Notes |
|---|---|---|
| Pure logic / algorithmic boundary | Unit test with pytest only | Fastest feedback, highest isolation |
| Interface and bus contract | pytest + CAN replay/simulation | Best for message encoding, timing, invalid payload testing |
| ECU integration and safe reaction | pytest + CANoe + CAN FD + target ECU | Needed for observable reaction in realistic environment |
| Multi-ECU sequence | CANoe orchestration + pytest wrappers | Supports end-to-end stimulus and response collection |
| Driver HMI validation | Partial automation + image/log inspection | Often needs hybrid automation and manual judgment |

### 23.6 Recommended Traceability Fields for Automated Tests

| Field | Purpose |
|---|---|
| Requirement ID | Unique requirement reference such as `REQ-SAF-1021` |
| Requirement version | Baseline or revision used when test was authored or updated |
| Test case ID | Controlled ID for the human-readable test design |
| Pytest node ID | Executable identity such as `tests/test_safe_state.py::test_torque_reduction_on_sensor_loss` |
| Verification method | Analysis, inspection, unit test, integration test, HIL, vehicle test |
| Environment version | CANoe configuration version, DBC version, ECU build version |
| ASIL / criticality | Risk classification affecting rigor and independence |
| Expected result | Pass criteria with measurable thresholds |
| Report reference | Link to execution artifact or report entry |

### 23.7 End-to-End Flow Example

The following example shows the intended traceability logic for a safety-related brake ECU reaction.

```text
[Approved Requirement]
REQ-BRK-217
  "When brake pressure sensor signal is unavailable for >100 ms,
   the Brake ECU shall request torque reduction within 50 ms and
   store diagnostic event DTC_BPS_LOSS."
       |
       v
[Derived Test Case]
TC-BRK-217-01
  Preconditions: IGN ON, speed 40 km/h, normal communication present
  Stimulus: remove brake pressure signal for 120 ms
  Expected: fault latched, torque reduction request present <=50 ms, DTC stored
       |
       v
[pytest automation]
  - prepares bench
  - commands CANoe measurement start
  - injects CAN FD frames representing signal loss
  - observes ECU response
       |
       v
[CANoe execution layer]
  - applies restbus simulation
  - logs timestamps and messages
  - exposes COM automation interface to Python
       |
       v
[CAN FD network + ECU under test]
  - receives signal absence / invalid state
  - executes safety logic
  - transmits torque reduction request and fault status
       |
       v
[Expected Safety Reaction]
  - safe-state request issued
  - DTC stored
  - timing requirement met
       |
       v
[Test Report]
  - pass/fail
  - measured latency
  - captured messages
  - linked requirement and ECU build version
```

### 23.8 Production-Quality Test Architecture

A maintainable production test stack usually separates test intent from transport details. The requirement engineer cares that the requirement is verified; the automation engineer ensures the software architecture keeps that verification stable and reusable.

```text
tests/
  conftest.py
  markers.py
  data/
    requirements.csv
    variants.yaml
  integration/
    test_brake_safe_state.py
    test_door_warning.py
  unit/
    test_signal_timeout_logic.py
automation/
  canoe_adapter.py
  can_bus.py
  dbc_codec.py
  ecu_observer.py
  reporting.py
  requirements.py
  timing.py
```

### 23.9 Example Requirement and Test Case Definition

#### Requirement

```text
ID: REQ-SAF-BRK-217
Title: Safe reaction on brake pressure sensor loss
Statement: When the brake pressure sensor signal is unavailable for more than 100 ms,
the Brake Control ECU shall request powertrain torque reduction within 50 ms and
shall store DTC_BPS_LOSS.
Source: System safety requirement derived from FSC item BRK-12
ASIL: C
Verification method: Integration test on CAN FD bench
```

#### Test Case

```text
ID: TC-SAF-BRK-217-01
Purpose: Verify safe-state reaction and diagnostic storage after loss of brake pressure sensor input
Preconditions:
- ECU flashed with build BRK_ECU_5.8.12
- Ignition ON
- Vehicle speed simulated at 40 km/h
- No active brake-related DTCs
Stimulus:
- Stop valid signal transmission for 120 ms
Expected results:
- Torque reduction request appears on CAN FD within 50 ms from timeout detection
- DTC_BPS_LOSS is stored and readable via UDS
- Reaction remains active until valid signal is restored and fault clear conditions are met
```

### 23.10 Python Domain Model for Traceable Tests

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class Criticality(str, Enum):
    QM = "QM"
    ASIL_A = "ASIL-A"
    ASIL_B = "ASIL-B"
    ASIL_C = "ASIL-C"
    ASIL_D = "ASIL-D"


@dataclass(frozen=True, slots=True)
class RequirementRef:
    id: str
    version: str
    title: str
    criticality: Criticality


@dataclass(frozen=True, slots=True)
class TestCaseRef:
    id: str
    requirement: RequirementRef
    purpose: str
    verification_method: str


@dataclass(frozen=True, slots=True)
class TestEvidence:
    testcase: TestCaseRef
    ecu_build: str
    canoe_cfg: str
    report_dir: Path

    def as_metadata(self) -> dict[str, str]:
        return {
            "requirement_id": self.testcase.requirement.id,
            "requirement_version": self.testcase.requirement.version,
            "requirement_title": self.testcase.requirement.title,
            "criticality": self.testcase.requirement.criticality.value,
            "testcase_id": self.testcase.id,
            "verification_method": self.testcase.verification_method,
            "ecu_build": self.ecu_build,
            "canoe_cfg": self.canoe_cfg,
        }


def requirement_ids(items: Iterable[TestCaseRef]) -> list[str]:
    return [item.requirement.id for item in items]
```

This model gives structure to metadata that is frequently lost in ad hoc automation. In regulated environments, that metadata is not decoration; it is part of the evidence package.

### 23.11 Example CAN Message Abstraction

```python
from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True, slots=True)
class CanFrame:
    arbitration_id: int
    data: bytes
    timestamp: float
    channel: str = "CANFD1"


class BusTimeoutError(RuntimeError):
    pass


class AbstractCanBus:
    def send(self, frame: CanFrame) -> None:
        raise NotImplementedError

    def recv(self, arbitration_id: int, timeout_s: float) -> CanFrame:
        raise NotImplementedError


def wait_for_frame(bus: AbstractCanBus, arbitration_id: int, timeout_s: float) -> CanFrame:
    deadline = monotonic() + timeout_s
    while monotonic() < deadline:
        try:
            return bus.recv(arbitration_id=arbitration_id, timeout_s=0.010)
        except BusTimeoutError:
            continue
    raise BusTimeoutError(f"No frame 0x{arbitration_id:X} within {timeout_s:.3f}s")
```

### 23.12 CANoe Adapter Pattern

Many teams use Python as the orchestration layer and CANoe as the automotive network execution environment. The adapter pattern below keeps test logic independent from CANoe COM details.

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class MeasurementResult:
    started: bool
    log_file: Path


class CanoeAdapter:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self._measurement_running = False

    def open(self) -> None:
        # In production, wrap Vector CANoe COM API or a service bridge.
        # Validate config existence, version, and matching DBC set here.
        if not self.config_path.exists():
            raise FileNotFoundError(self.config_path)

    def start_measurement(self, log_file: Path) -> MeasurementResult:
        self._measurement_running = True
        return MeasurementResult(started=True, log_file=log_file)

    def stop_measurement(self) -> None:
        self._measurement_running = False

    def is_running(self) -> bool:
        return self._measurement_running

    def set_system_variable(self, namespace: str, variable: str, value: int | float | str) -> None:
        if not self._measurement_running:
            raise RuntimeError("Measurement must be running before writing system variables")
        # Write to CANoe system variable namespace or CAPL gateway.

    def call_capl_function(self, function_name: str, *args: object) -> None:
        if not self._measurement_running:
            raise RuntimeError("Measurement must be running before CAPL interaction")
        # Bridge into CAPL, .NET, or vTESTstudio function layer.
```

### 23.13 Pytest Fixtures for Bench Control

```python
from __future__ import annotations

from pathlib import Path

import pytest

from automation.canoe_adapter import CanoeAdapter
from automation.reporting import EvidenceCollector
from automation.requirements import RequirementRef, TestCaseRef, Criticality


@pytest.fixture(scope="session")
def canoe() -> CanoeAdapter:
    adapter = CanoeAdapter(config_path=Path("canoe_cfg/BrakeSystem.cfg"))
    adapter.open()
    return adapter


@pytest.fixture
def evidence() -> EvidenceCollector:
    report_dir = Path("reports/evidence")
    return EvidenceCollector(report_dir=report_dir)


@pytest.fixture
def brk217_refs() -> tuple[RequirementRef, TestCaseRef]:
    requirement = RequirementRef(
        id="REQ-SAF-BRK-217",
        version="B12",
        title="Safe reaction on brake pressure sensor loss",
        criticality=Criticality.ASIL_C,
    )
    testcase = TestCaseRef(
        id="TC-SAF-BRK-217-01",
        requirement=requirement,
        purpose="Verify torque reduction request and DTC storage on signal loss",
        verification_method="HIL integration test",
    )
    return requirement, testcase
```

> **Engineering note**: In an actual project, use a project-approved evidence directory, network storage, or CI artifact location that is versioned and retained according to the verification process.

### 23.14 Reporting Helper

```python
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EvidenceCollector:
    report_dir: Path
    entries: list[dict[str, Any]] = field(default_factory=list)

    def add_measurement(self, name: str, value: Any, unit: str | None = None) -> None:
        entry = {"name": name, "value": value}
        if unit is not None:
            entry["unit"] = unit
        self.entries.append(entry)

    def write_json(self, filename: str, metadata: dict[str, str]) -> Path:
        self.report_dir.mkdir(parents=True, exist_ok=True)
        target = self.report_dir / filename
        target.write_text(
            json.dumps({"metadata": metadata, "entries": self.entries}, indent=2),
            encoding="utf-8",
        )
        return target
```

### 23.15 Production-Quality pytest Example — Safety Reaction Test

The example below illustrates several best practices: clear linkage to the requirement, explicit timing measurement, diagnostic verification, readable assertions, and evidence generation.

```python
from __future__ import annotations

from time import monotonic

import pytest

from automation.can_bus import CanFrame, wait_for_frame
from automation.diagnostics import UdsClient
from automation.signal_injection import BrakePressureSensorStimulus


@pytest.mark.requirement("REQ-SAF-BRK-217")
@pytest.mark.testcase("TC-SAF-BRK-217-01")
@pytest.mark.asil("C")
@pytest.mark.integration
def test_torque_reduction_on_brake_pressure_signal_loss(
    canoe,
    can_bus,
    uds_client: UdsClient,
    evidence,
    brk217_refs,
) -> None:
    requirement, testcase = brk217_refs
    metadata = {
        "requirement_id": requirement.id,
        "requirement_version": requirement.version,
        "testcase_id": testcase.id,
        "criticality": requirement.criticality.value,
        "verification_method": testcase.verification_method,
    }

    canoe.start_measurement(log_file=evidence.report_dir / "brk217.asc")

    # Establish preconditions
    can_bus.send(CanFrame(0x101, bytes.fromhex("2800000000000000"), monotonic()))  # speed 40 km/h
    uds_client.clear_diagnostic_information()

    stimulus = BrakePressureSensorStimulus(can_bus)
    stimulus.transmit_valid_signal(duration_s=0.100)

    start = monotonic()
    stimulus.drop_signal_for(duration_s=0.120)

    torque_reduction_frame = wait_for_frame(can_bus, arbitration_id=0x321, timeout_s=0.050)
    reaction_latency_ms = round((torque_reduction_frame.timestamp - start) * 1000.0, 3)

    dtcs = uds_client.read_dtcs()

    evidence.add_measurement("reaction_latency", reaction_latency_ms, "ms")
    evidence.add_measurement("torque_reduction_frame", torque_reduction_frame.data.hex())
    evidence.add_measurement("dtcs", dtcs)

    assert reaction_latency_ms <= 50.0, (
        f"Expected torque reduction request within 50 ms, got {reaction_latency_ms} ms"
    )
    assert "DTC_BPS_LOSS" in dtcs, "Brake pressure sensor loss DTC was not stored"
    assert torque_reduction_frame.data[0] & 0x01 == 0x01, (
        "Torque reduction request bit not set in powertrain coordination message"
    )

    report = evidence.write_json("brk217_result.json", metadata=metadata)
    assert report.exists()

    canoe.stop_measurement()
```

### 23.16 Example Negative Test

Requirements-driven automation should also verify that a safety reaction does **not** occur outside its trigger condition.

```python
@pytest.mark.requirement("REQ-SAF-BRK-217")
@pytest.mark.testcase("TC-SAF-BRK-217-02")
@pytest.mark.integration
def test_no_torque_reduction_for_short_signal_dropout(canoe, can_bus, uds_client) -> None:
    canoe.start_measurement(log_file=Path("reports/brk217_short_dropout.asc"))
    stimulus = BrakePressureSensorStimulus(can_bus)

    stimulus.transmit_valid_signal(duration_s=0.100)
    stimulus.drop_signal_for(duration_s=0.050)  # less than timeout threshold

    with pytest.raises(BusTimeoutError):
        wait_for_frame(can_bus, arbitration_id=0x321, timeout_s=0.060)

    assert "DTC_BPS_LOSS" not in uds_client.read_dtcs()
    canoe.stop_measurement()
```

### 23.17 Parameterized Variant Test Example

Modern ECUs are variant-rich. Good automation reuses the same requirement with calibrated thresholds or different message layouts per vehicle line.

```python
import pytest


@pytest.mark.parametrize(
    "variant_name,speed_kph,timeout_ms",
    [
        pytest.param("base", 40, 100, id="base-40kph"),
        pytest.param("heavy_vehicle", 30, 120, id="heavy-30kph"),
        pytest.param("sport", 60, 80, id="sport-60kph"),
    ],
)
def test_fault_reaction_across_variants(variant_name, speed_kph, timeout_ms, setup_variant, can_bus):
    variant = setup_variant(variant_name)
    variant.set_vehicle_speed(speed_kph)
    variant.drop_brake_pressure_signal(timeout_ms / 1000.0 + 0.020)
    response = wait_for_frame(can_bus, arbitration_id=variant.torque_reduction_arbid, timeout_s=0.080)
    assert response.data[0] & 0x01 == 0x01
```

### 23.18 Requirement Coverage Matrix for Automation

| Requirement Status | Test Automation Expectation | Action |
|---|---|---|
| Approved and stable | Automated verification preferred | Implement or maintain regression test |
| Approved but complex HMI perception | Hybrid automation may be used | Define manual evidence supplement |
| Draft / volatile | Script spike acceptable, production automation deferred | Avoid locking unstable details prematurely |
| Safety-related and repetitive | Automation strongly recommended | Run on every relevant build baseline |
| Obsolete / replaced | Existing automated tests must be reviewed | Retire, replace, or re-link tests |

### 23.19 Test Design Rules for Requirements Engineers

| Rule | Explanation |
|---|---|
| One requirement, one primary verification intent | Avoid scripts that mix unrelated behaviors and produce unclear failures. |
| Observable pass criteria only | Expected results must be measurable: timing, signal state, DTC presence, mode change, or output value. |
| Explicit preconditions | Ignition state, vehicle speed, network health, and calibration must be part of the test case. |
| Stimulus realism | Fault injection must represent physically or logically plausible failure modes. |
| Negative coverage | Tests should prove both trigger and non-trigger boundaries. |
| Version pinning | Link the test result to requirement baseline, ECU build, and environment version. |
| Repeatability | Random waits, hard-coded magic delays, and hidden bench dependencies should be eliminated. |

### 23.20 Typical Failure Modes in Test Automation Traceability

- Requirement ID only appears in the test title but is not stored in report metadata.
- One script verifies five requirements, so a single failure gives no precise requirement verdict.
- CANoe configuration version is not captured, making re-execution impossible during root-cause analysis.
- Requirements changed but test names and acceptance criteria were not updated.
- Timeouts in scripts are wider than the requirement threshold, hiding timing non-compliance.
- Pass/fail relies on human inspection of raw logs rather than machine-checkable assertions.

### 23.21 Recommended pytest Markers

```python
def pytest_configure(config):
    config.addinivalue_line("markers", "requirement(id): link test to requirement")
    config.addinivalue_line("markers", "testcase(id): link test to formal test case")
    config.addinivalue_line("markers", "asil(level): declare safety integrity level")
    config.addinivalue_line("markers", "integration: integration bench test")
    config.addinivalue_line("markers", "hil: hardware-in-the-loop test")
    config.addinivalue_line("markers", "diagnostics: UDS diagnostic verification")
```

### 23.22 Example Custom pytest Report Enrichment

```python
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    report.requirement_ids = [mark.args[0] for mark in item.iter_markers(name="requirement")]
    report.testcase_ids = [mark.args[0] for mark in item.iter_markers(name="testcase")]
    report.asil = [mark.args[0] for mark in item.iter_markers(name="asil")]
```

This style supports export into JUnit XML post-processing, internal dashboards, or ALM import routines.

### 23.23 Mapping Automated Results Back to Requirements

| Report Field | Why It Matters for Requirements Management |
|---|---|
| Requirement ID | Supports direct traceability and coverage reporting |
| Requirement Version / Baseline | Prevents using outdated evidence after requirement change |
| Test Case ID | Connects executable result to approved verification design |
| ECU build hash/version | Supports reproducibility and release qualification |
| Environment version | Distinguishes product defects from environment defects |
| Verdict timestamp | Helps determine evidence freshness |
| Raw logs and summarized measurements | Enables debug without rerunning immediately |

### 23.24 CAN FD-Specific Considerations

- Signal packing and endian behavior must match the agreed DBC or AUTOSAR description.
- Payload length changes can influence test robustness when message definitions evolve.
- Timing checks should distinguish message timestamp, stimulus timestamp, and ECU internal timeout start point.
- Network load on CAN FD can affect measurement jitter; acceptance criteria should define whether jitter is included or excluded.
- Bus-off, error passive, and missing-ack conditions may be relevant for diagnostic and safety robustness tests.

### 23.25 Example Review Checklist for Automated Requirement Verification

- [ ] Is the requirement approved and uniquely identified?
- [ ] Does the automated test link to the current requirement version or baseline?
- [ ] Does the test case explicitly define preconditions, stimulus, expected result, and pass/fail logic?
- [ ] Are timing thresholds in the code equal to the requirement thresholds and not widened for convenience?
- [ ] Is the bench configuration version captured?
- [ ] Does the test report store objective evidence and not just console text?
- [ ] Are both positive and negative boundary conditions covered?
- [ ] Is there a clear strategy for regression execution frequency?

### 23.26 Example Requirement-to-pytest Traceability Table

| Requirement | Test Case | pytest Node | Level | Criticality | Status |
|---|---|---|---|---|---|
| REQ-SAF-BRK-217 | TC-SAF-BRK-217-01 | tests/integration/test_brake_safe_state.py::test_torque_reduction_on_brake_pressure_signal_loss | HIL | ASIL-C | Implemented |
| REQ-SAF-BRK-217 | TC-SAF-BRK-217-02 | tests/integration/test_brake_safe_state.py::test_no_torque_reduction_for_short_signal_dropout | HIL | ASIL-C | Implemented |
| REQ-BCM-133 | TC-BCM-133-03 | tests/integration/test_door_warning.py::test_chime_on_door_open_above_speed_threshold | SIL/HIL | QM | Implemented |
| REQ-ADAS-481 | TC-ADAS-481-02 | tests/system/test_aeb_disable_on_low_confidence.py::test_aeb_is_disabled_after_low_confidence_timeout | System bench | ASIL-B | Planned |

### 23.27 Integration with CI/CD

- Run fast unit-level requirement tests on every merge request or pull request.
- Run interface and diagnostics tests on nightly benches or when impacted modules change.
- Run safety-critical regression suites on approved ECU builds and record immutable artifacts.
- Block release candidates if requirement-linked critical tests fail or if impacted requirements have no fresh evidence.

### 23.28 When Requirements Engineers Should Reject an Automated Test

- The script verifies an implementation detail rather than the externally required behavior.
- The test passes because of hard-coded sleeps and not because the required event was objectively observed.
- The test uses stale acceptance thresholds after a requirement revision.
- The test cannot prove which requirement is affected when it fails.
- The test report is not reviewable by an independent engineer.

### 23.29 Mini Case Study: Fault-Tolerant Steering Assist

| Element | Example |
|---|---|
| Requirement | `REQ-EPAS-552`: If steering torque sensor channels differ by >10% for >30 ms, the EPAS ECU shall enter degraded assist mode and store a sensor plausibility DTC. |
| Test case | Inject mismatch between channel A and B while driving at 60 km/h equivalent. |
| Automation | pytest triggers mismatch via CANoe, monitors assist mode signal and DTC response. |
| Expected safety reaction | Assist torque limited to degraded level, DTC stored, driver warning issued. |
| Report content | mismatch duration, reaction latency, mode transition, DTC record, ECU build. |

### 23.30 Key Takeaways

- A requirement without an executable verification strategy is a future integration risk.
- Automated tests should be treated as controlled engineering artifacts, not convenience scripts.
- The strongest automation chain is traceable, measurable, versioned, and reviewable.
- Production-quality pytest for automotive verification must handle metadata, timing, evidence, and bench integration deliberately.

---

## Section 24: Requirements Management Tools

Requirements management tools differ in workflow style, governance depth, user experience, and integration model. However, automotive teams should evaluate every tool through the same practical questions:

- How do engineers create and structure requirements?
- How are requirements linked to architecture, code, tests, hazards, and defects?
- How are baselines and versions established?
- How are reviews and approvals executed and evidenced?
- How are changes controlled and propagated?
- How is traceability reported to OEMs, auditors, and release boards?

### 24.1 Tool Comparison Framework

| Capability | What Good Looks Like in Automotive |
|---|---|
| Requirement creation | Templates, attributes, variant support, rich text discipline, and unique IDs |
| Linking | End-to-end links from stakeholder and safety requirements to SW, HW, tests, defects, and release evidence |
| Baseline | Immutable snapshots for audits, deliveries, and change comparison |
| Review | Formal review workflows with comments, disposition, and signatures |
| Approval | Role-based approval with electronic evidence and status transitions |
| Change | Impact analysis, suspect links, revision history, and change workflows |
| Traceability | Matrix views, gap analysis, coverage dashboards, and exportable evidence |
| Reporting | Release-oriented, supplier-oriented, and audit-oriented reporting packages |

### 24.2 IBM DOORS

**Overview**: Classic object-based requirements database still common in long-running OEM and Tier-1 programs, especially where formal baselines and heavyweight traceability are central.

| Topic | Practical Use in Automotive Programs |
|---|---|
| Requirement creation | Create requirements in formal modules with object headings, text objects, attribute columns, and object numbering schemes. Teams often define dedicated modules for stakeholder, system, safety, software, and interface requirements. |
| Linking | Use link modules and formal link rules to connect requirements to hazards, architecture elements, source documents, and test specifications. Link direction must be standardized because inconsistent semantics create reporting confusion. |
| Baseline | Create formal baselines at requirement reviews, supplier handoff points, and release gates. Baselines are critical in classic DOORS because many contractual deliveries reference exact module baseline numbers. |
| Review | Reviews are often done by freezing candidate content, exporting views, or using companion review workflows. Good practice includes comment attributes, review status, and disposition objects rather than uncontrolled email edits. |
| Approval | Approval is typically represented through state attributes, e-signature workflow integration, and role-controlled write access. The approval logic must be agreed in the project process, not improvised per module. |
| Change | Changes are handled by modifying objects under change request context, comparing against baselines, flagging suspect links, and regenerating trace reports. DXL is often used to automate suspect detection and reports. |
| Traceability | Excellent for deep hierarchical trace matrices across large formal modules. Strong for compliance-heavy projects if naming rules, link policies, and views are disciplined. |
| Reporting | Generate baseline comparison reports, trace matrices, missing-link reports, attribute summaries, and customer delivery extracts. Many organizations use DXL scripts to standardize exports. |

**Strengths**
- Very strong baseline discipline
- Mature handling of formal modules
- Powerful traceability for large compliance programs

**Common governance risks**
- User experience can be difficult for new engineers
- Customization can become fragile
- Poorly governed DXL can create maintenance debt

**Practical advice for automotive teams**
- Define a requirement information model before scaling IBM DOORS.
- Standardize IDs, statuses, review states, and link semantics.
- Train engineers on what the tool means in the process, not only where to click.
- Periodically audit for orphan requirements, suspect links, duplicate artifacts, and stale baselines.

### 24.3 DOORS Next

**Overview**: Modern web-based lifecycle platform in the IBM Engineering family with richer collaboration, configuration management, and OSLC-style linking compared with classic DOORS.

| Topic | Practical Use in Automotive Programs |
|---|---|
| Requirement creation | Create requirements as artifacts with templates, artifact types, attributes, reusable collections, and module-like views. Text, diagrams, and review comments are more collaborative than in classic environments. |
| Linking | Links can connect requirements with architecture, models, test cases, work items, and defects across tools. Proper link type definition is essential so that “satisfies,” “verifies,” and “implements” are not mixed casually. |
| Baseline | Use configurations, streams, and baselines to manage evolving content. This is especially useful for variant-rich automotive platforms where one project reuses shared requirement sets. |
| Review | Formal reviews are built into the collaborative workflow. Stakeholders can comment, discuss, and approve specific artifacts or collections with review records preserved in the platform. |
| Approval | Approval is usually workflow-driven with state changes, reviewer lists, and e-signature-compatible governance depending on process configuration. |
| Change | Change sets, suspect links, and configuration comparison support impact analysis. Teams should define rules for when a change belongs in a stream, a baseline, or a controlled release branch. |
| Traceability | Strong cross-tool traceability when the surrounding engineering lifecycle suite is integrated consistently. Excellent for “show me upstream and downstream impact” use cases. |
| Reporting | Web dashboards, saved views, lifecycle queries, configuration-based status reports, and exportable collections support both internal and external reporting. |

**Strengths**
- Collaborative web access
- Good configuration model
- Strong lifecycle integration potential

**Common governance risks**
- Configuration concepts require training
- Trace quality depends heavily on process discipline
- Cross-tool performance must be monitored in large programs

**Practical advice for automotive teams**
- Define a requirement information model before scaling DOORS Next.
- Standardize IDs, statuses, review states, and link semantics.
- Train engineers on what the tool means in the process, not only where to click.
- Periodically audit for orphan requirements, suspect links, duplicate artifacts, and stale baselines.

### 24.4 Polarion

**Overview**: ALM platform widely used for automotive and medical development, appreciated for integrated requirements, tests, work items, and strong traceability reporting.

| Topic | Practical Use in Automotive Programs |
|---|---|
| Requirement creation | Requirements are created as work items or document-based artifacts with templates, rich text, custom fields, and workflow states. Teams often maintain separate live documents for system, safety, and software requirements. |
| Linking | Link requirements to derived requirements, tests, defects, risks, and change requests using defined relationship roles. Built-in bidirectional trace views make gaps visible early. |
| Baseline | Use baselines on documents or project states to preserve approved snapshots. Baseline comparison is practical for supplier deliveries and audit packages. |
| Review | Review and discussion are tightly integrated. Engineers can comment in-line, run review cycles, and dispose comments while keeping a visible audit trail. |
| Approval | Workflow states, approvals, and electronic signatures can be configured so that release or safety sign-off cannot progress without the required roles. |
| Change | Requirement changes propagate through suspect links, impacted test cases, and work-item relationships. Polarion is particularly strong when requirements and tests live in one ALM environment. |
| Traceability | Very strong traceability, especially when tests are managed in the same system. LiveDocs combined with linked work items are useful for ASPICE and ISO 26262 evidence generation. |
| Reporting | Excellent document-style reports, dashboards, widgets, and compliance evidence pages. Teams often produce customer-ready reports directly from the platform. |

**Strengths**
- Strong requirement-test integration
- Good audit trail
- Useful LiveDocs workflow for formal content

**Common governance risks**
- Customization requires governance
- Users can misuse work-item types if templates are weak
- Large projects need indexing and structure discipline

**Practical advice for automotive teams**
- Define a requirement information model before scaling Polarion.
- Standardize IDs, statuses, review states, and link semantics.
- Train engineers on what the tool means in the process, not only where to click.
- Periodically audit for orphan requirements, suspect links, duplicate artifacts, and stale baselines.

### 24.5 Jama

**Overview**: Collaboration-oriented requirements and systems engineering platform known for review workflows, relationship views, and broad stakeholder participation.

| Topic | Practical Use in Automotive Programs |
|---|---|
| Requirement creation | Requirements are created with item types, reusable templates, fields, and structured review packages. Jama is often favored when cross-functional review participation is a primary concern. |
| Linking | Relationship rules connect requirements, tests, risks, defects, and user needs. Good governance is needed to distinguish semantic intent among relationship types. |
| Baseline | Baselines and review snapshots preserve project state at milestone decisions. Automotive teams should name baselines by release, vehicle line, and variant context. |
| Review | One of Jama’s strongest areas. Formal reviews with comments, voting, decisions, and participation tracking support distributed OEM-supplier teams effectively. |
| Approval | Approvals can be part of workflow transitions and review completions. Clear reviewer responsibility matrices are important so approvals are meaningful, not ceremonial. |
| Change | When requirements change, downstream relationships and review packages help coordinate impact. Change history is visible and suitable for engineering discussion. |
| Traceability | Relationship views and trace explorers help identify coverage gaps and downstream test obligations. |
| Reporting | Good for stakeholder-facing reports, review participation metrics, trace reports, and project status dashboards. |

**Strengths**
- Strong structured reviews
- Good for distributed collaboration
- Clear relationship visualization

**Common governance risks**
- Trace quality still depends on disciplined link creation
- Variant-heavy programs need careful data model design
- Integration architecture must be planned early

**Practical advice for automotive teams**
- Define a requirement information model before scaling Jama.
- Standardize IDs, statuses, review states, and link semantics.
- Train engineers on what the tool means in the process, not only where to click.
- Periodically audit for orphan requirements, suspect links, duplicate artifacts, and stale baselines.

### 24.6 Codebeamer

**Overview**: Configurable ALM/PLM-style platform often used in regulated industries for integrating requirements, risk, tests, and software planning.

| Topic | Practical Use in Automotive Programs |
|---|---|
| Requirement creation | Requirements are created as tracker items or structured documents with templates and field schemas. Teams can tailor artifact models for system, safety, cybersecurity, and software layers. |
| Linking | Provides relationship modeling among requirements, change requests, tests, source artifacts, and risks. Effective use depends on a carefully designed tracker taxonomy. |
| Baseline | Baselines and release snapshots support formal milestones and customer deliveries. Product-line teams often use branch/variant strategies to manage reuse. |
| Review | Review workflows and comment threads support formal and informal analysis. Review packages should be standardized by project process to avoid inconsistent evidence quality. |
| Approval | Workflow controls and role-based transitions support approval sequences, especially where quality and safety roles must approve before release progression. |
| Change | Supports change impact analysis through linked trackers, histories, and suspect relationships. Particularly useful when requirements, risks, and tests are all treated as first-class managed items. |
| Traceability | Strong configurable traceability with dashboards and matrices. Useful where engineering wants a single digital thread across disciplines. |
| Reporting | Reports cover release status, coverage, workflow bottlenecks, test progress, and impact views. Custom dashboards are common in transformation programs. |

**Strengths**
- Flexible data model
- Good integrated lifecycle potential
- Strong regulated-development fit

**Common governance risks**
- Over-customization can harm usability
- Governance required for tracker model consistency
- Training needed for new users

**Practical advice for automotive teams**
- Define a requirement information model before scaling Codebeamer.
- Standardize IDs, statuses, review states, and link semantics.
- Train engineers on what the tool means in the process, not only where to click.
- Periodically audit for orphan requirements, suspect links, duplicate artifacts, and stale baselines.

### 24.7 Enterprise Architect

**Overview**: Model-based engineering tool frequently used for system architecture, interfaces, and requirement-model linking rather than as the only enterprise requirements repository.

| Topic | Practical Use in Automotive Programs |
|---|---|
| Requirement creation | Requirements can be created as model elements, structured packages, or imported artifacts. It is practical for associating requirements with architecture views, states, interfaces, and behaviors. |
| Linking | Trace, realize, verify, satisfy, and dependency relationships can connect requirements to components, state machines, sequence diagrams, and software structures. |
| Baseline | Package baselines and model versioning support controlled change review. Many teams combine EA baselines with an external master requirement repository. |
| Review | Reviews often occur through model walkthroughs, review packages, linked comments, or exported documentation. Review discipline is required because architecture-focused tools can encourage informal changes. |
| Approval | Approval is usually process-enforced through package status, model governance, and external release control rather than built-in heavy workflow alone. |
| Change | Excellent for visual impact analysis on architecture and interface models after requirement changes. Less ideal as the sole change-management engine for large distributed supplier chains. |
| Traceability | Strong architectural traceability, especially where requirements must be shown against blocks, interfaces, functions, and behavior models. |
| Reporting | Document generation, relationship matrices, model reports, and interface catalogs are common outputs. |

**Strengths**
- Excellent requirement-to-architecture linkage
- Strong MBSE support
- Good visualization of design impact

**Common governance risks**
- Can become model-heavy without process clarity
- Not always the best standalone enterprise review tool
- Template governance is essential

**Practical advice for automotive teams**
- Define a requirement information model before scaling Enterprise Architect.
- Standardize IDs, statuses, review states, and link semantics.
- Train engineers on what the tool means in the process, not only where to click.
- Periodically audit for orphan requirements, suspect links, duplicate artifacts, and stale baselines.

### 24.8 Jira

**Overview**: Primarily a work management tool, but often used in automotive software organizations to manage requirement-derived tasks, stories, defects, and changes, especially when combined with plugins or linked ALM tools.

| Topic | Practical Use in Automotive Programs |
|---|---|
| Requirement creation | Native Jira is better suited to epics, stories, and tasks than formal requirements. If used for requirements, teams should define strict issue types, templates, and field policies, or use dedicated plugins. |
| Linking | Can link issues, epics, bugs, change requests, and test cases. However, semantic rigor is weaker than dedicated requirements tools unless process rules are enforced. |
| Baseline | Baseline capability is limited compared with formal ALM tools. Teams typically use fix versions, snapshots, exports, or plugin-based version control rather than true requirements baselines. |
| Review | Reviews are practical for workflow comments and lightweight collaboration, but formal requirement reviews require disciplined states and possibly external review evidence. |
| Approval | Approvals can be mimicked through transitions, permissions, and automation, though this is not as naturally compliance-oriented as in dedicated RM platforms. |
| Change | Jira is very effective for managing change requests, implementation tasks, and defect workflow. It becomes stronger when requirement IDs from a master system are embedded and linked consistently. |
| Traceability | Good for operational traceability to implementation and defects; weaker for formal requirement hierarchy unless integrated with a dedicated requirements system. |
| Reporting | Dashboards, queries, and sprint/release views are strong for work progress and change flow, not always for formal audit packages. |

**Strengths**
- Excellent for execution management
- Strong automation and workflow flexibility
- Very familiar to software teams

**Common governance risks**
- Not a full requirements repository by itself in most safety-heavy programs
- Easy to create ambiguous artifact semantics
- Baseline discipline can be insufficient

**Practical advice for automotive teams**
- Define a requirement information model before scaling Jira.
- Standardize IDs, statuses, review states, and link semantics.
- Train engineers on what the tool means in the process, not only where to click.
- Periodically audit for orphan requirements, suspect links, duplicate artifacts, and stale baselines.

### 24.9 Git

**Overview**: Version control system, not a full requirements management tool, but increasingly used to manage requirement documents, test specifications, and change history in text-based engineering workflows.

| Topic | Practical Use in Automotive Programs |
|---|---|
| Requirement creation | Requirements can be authored as Markdown, reStructuredText, YAML, or plain text under repository control. Templates, pull-request checks, and linting can improve consistency. |
| Linking | Linking can be done through IDs, file references, issue links, commit references, and generated trace matrices. Semantic relationships are possible but not as naturally queryable as in dedicated RM tools without additional tooling. |
| Baseline | Tags, branches, and signed releases provide strong baseline capability. A tagged release can act as a requirement baseline if document discipline is strong. |
| Review | Pull requests enable line-by-line review, comments, and required reviewers. This is extremely effective for text-based requirement reviews when teams are comfortable with developer-style workflows. |
| Approval | Approval is represented by protected branches, required reviewers, status checks, and signed commits or tags. The policy must define what constitutes formal approval. |
| Change | Git gives excellent history, diffs, blame, and change lineage. Requirement changes can be discussed and merged with high transparency. |
| Traceability | Traceability depends on conventions and automation. IDs, scripts, and structured link syntax are needed to generate reliable coverage reports. |
| Reporting | Reporting usually requires additional scripts, static site generators, CI pipelines, or dashboards. Raw Git alone is not enough for executive or audit reporting. |

**Strengths**
- Excellent version history
- Strong peer review model
- Natural fit for docs-as-code engineering

**Common governance risks**
- Traceability is convention-driven
- Non-technical stakeholders may struggle
- Requires automation to reach enterprise-grade reporting

**Practical advice for automotive teams**
- Define a requirement information model before scaling Git.
- Standardize IDs, statuses, review states, and link semantics.
- Train engineers on what the tool means in the process, not only where to click.
- Periodically audit for orphan requirements, suspect links, duplicate artifacts, and stale baselines.

### 24.10 GitHub / GitLab

**Overview**: Platform layer around Git that adds pull requests or merge requests, issues, actions/pipelines, code review, approvals, and project-level visibility. Increasingly important in software-centric automotive programs.

| Topic | Practical Use in Automotive Programs |
|---|---|
| Requirement creation | Requirement files can be created and edited directly in repositories, often with templates, forms, markdown previews, and validation checks in CI. Issues can also capture change requests or stakeholder requests. |
| Linking | Links can connect requirement documents to issues, merge requests, commits, test pipelines, releases, and code. With discipline, this creates a powerful software-facing digital thread. |
| Baseline | Releases, tags, protected branches, and branch strategies support baseline control. Signed releases are useful for external delivery references. |
| Review | Pull request and merge request reviews are excellent for textual requirement changes, code-linked changes, and collaborative discussion. Required approvers and status checks add rigor. |
| Approval | Approvals are enforced through branch protection, review rules, status checks, CODEOWNERS, and compliance pipeline gates. |
| Change | Every change is visible as a diff, linked to issues, reviewers, CI results, and often test evidence. This makes software requirement evolution highly transparent. |
| Traceability | Powerful when coupled with naming conventions, issue templates, labels, test reports, and generated trace matrices. Still weaker than dedicated RM data models unless enhanced by automation. |
| Reporting | Excellent for development dashboards, pipeline evidence, release notes, and API-driven custom reports. Formal automotive evidence packages may require additional generation steps. |

**Strengths**
- Excellent review and automation ecosystem
- Strong connection between requirements, code, and tests
- Good developer adoption

**Common governance risks**
- Formal requirement semantics must be designed deliberately
- Audit-oriented traceability needs automation
- Non-software stakeholders may need onboarding

**Practical advice for automotive teams**
- Define a requirement information model before scaling GitHub / GitLab.
- Standardize IDs, statuses, review states, and link semantics.
- Train engineers on what the tool means in the process, not only where to click.
- Periodically audit for orphan requirements, suspect links, duplicate artifacts, and stale baselines.

### 24.11 Summary Comparison Table

| Tool | Best Fit | Baseline Strength | Review Strength | Traceability Strength | Typical Automotive Use |
|---|---|---|---|---|---|
| IBM DOORS | Formal compliance-heavy programs | Very High | Medium | Very High | OEM/Tier-1 classic requirement repositories |
| DOORS Next | Collaborative lifecycle management | High | High | High | Modern enterprise RM with integrated lifecycle |
| Polarion | Integrated requirement-test management | High | High | Very High | ALM-centric automotive programs |
| Jama | Stakeholder review-heavy development | High | Very High | High | Distributed review and systems engineering |
| Codebeamer | Configurable regulated lifecycle | High | High | High | Integrated requirement-risk-test workflows |
| Enterprise Architect | Requirement-to-architecture modeling | Medium | Medium | High | MBSE and design traceability |
| Jira | Execution and change tracking | Low-Medium | Medium | Medium | Software planning and change management |
| Git | Docs-as-code workflows | High | High | Convention-based | Text-based controlled requirements |
| GitHub/GitLab | Reviewed, automated software-centric workflows | High | High | Convention + automation | Requirement-code-test integration |

### 24.12 Tool Selection Guidance

- If contractual baselines and object-level trace matrices dominate, classic DOORS remains strong.
- If integrated requirements, tests, and reviews are central, Polarion, Jama, or Codebeamer are often attractive.
- If architecture-model linkage is the critical concern, Enterprise Architect adds high value.
- If the organization is software-heavy and comfortable with docs-as-code, Git plus GitHub/GitLab can be very powerful when disciplined properly.
- If Jira is used, avoid pretending it is automatically a complete requirements solution; define its role explicitly in the engineering toolchain.

---

## Section 25: Requirement Change Management

Requirement change management is the discipline of controlling how approved requirements are modified after they enter a governed baseline. In automotive programs, uncontrolled requirement change is one of the most common causes of schedule slip, test churn, safety argument instability, supplier conflict, and late rework.

### 25.1 Why Change Management Exists

- Vehicle programs evolve because regulations, customer expectations, hazards, hardware assumptions, and supplier constraints change.
- A requirement change can invalidate architecture, code, calibration, diagnostics, tests, and already-issued evidence packages.
- Change management provides a controlled way to decide whether a requested change should be accepted, rejected, deferred, or split.

### 25.2 Core Concepts

| Concept | Practical Meaning |
|---|---|
| Change request | Formal proposal to add, modify, delete, or clarify a requirement. |
| Change impact analysis | Systematic analysis of what artifacts, functions, hazards, and releases are affected. |
| Requirement baseline | Approved snapshot used as a contractual or engineering reference point. |
| Versioning | Controlled evolution of the requirement statement, attributes, rationale, and linked artifacts. |
| Approval | Decision by authorized roles such as system lead, safety engineer, software lead, and change control board. |
| Configuration management | Control of the combinations of requirements, design, code, calibration, and test evidence that define a release. |
| Change propagation | Deliberate update of downstream artifacts after a requirement change is approved. |
| Regression testing | Selective or full re-verification proving no unintended effects were introduced. |

### 25.3 Standard Change Flow

```text
Requirement Change Request
        -> Clarification / categorization
        -> Safety Impact Analysis
        -> Architecture Impact Analysis
        -> Software Impact Analysis
        -> Test Impact Analysis
        -> Validation / release impact analysis
        -> Approval decision
        -> Baseline update and configuration update
        -> Implementation and verification
        -> Regression testing
        -> Release decision
```

### 25.4 Minimum Data for a Good Change Request

- Change request ID
- Originator and organization
- Target requirement ID(s)
- Current baseline/version
- Proposed new wording
- Reason for change
- Urgency and release target
- Safety or cybersecurity relevance
- Affected variants / vehicle lines / markets
- Initial assumptions and supporting evidence

### 25.5 Change Classification

| Change Type | Example | Typical Governance Response |
|---|---|---|
| Clarification | Remove ambiguity without changing behavior | Fast review, limited downstream update if semantics unchanged |
| Functional enhancement | New feature or widened capability | Full impact analysis |
| Safety correction | Safe-state or fault response modification | Mandatory safety review and verification update |
| Interface change | Message, API, diagnostic, or hardware signal change | Architecture and integration review required |
| Variant-only change | Market or vehicle-line-specific change | Variant baseline and selective regression update |
| Deletion / de-scope | Remove feature or obligation | Validate downstream removal and contract implications |

### 25.6 Requirement Baselines

A requirement baseline is not simply a saved file version. It is the controlled product definition that downstream engineering is allowed to implement and verify against. Good baseline management answers three questions:

- What exact requirement content was approved?
- When did it become effective for implementation and testing?
- Which release, ECU build, and evidence package correspond to that baseline?

### 25.7 Versioning Practices

- Increment versions when meaning changes, not only formatting.
- Preserve rationale for each revision.
- Record whether linked tests were reviewed, updated, or confirmed unchanged.
- Do not overwrite historical approval evidence.
- Maintain comparison visibility between current and previous baseline statements.

### 25.8 Approval Workflow

| Role | Review Focus | Typical Approval Question |
|---|---|---|
| Requirements engineer | Quality and consistency | Is the new statement clear, atomic, and testable? |
| Safety engineer | Hazard and safe-state implications | Does the change alter ASIL assumptions, FTTI, or safety goals? |
| System architect | Functional allocation and interface impact | Does architecture still support the changed behavior? |
| Software lead | Implementation feasibility | What modules and resources are affected? |
| Test lead | Verification scope | Which tests must be added, updated, or re-run? |
| Release manager / CCB | Scope and schedule | Can this change be absorbed without destabilizing the release? |

### 25.9 Configuration Management Link

Requirement change management fails when it is disconnected from configuration management. A changed requirement must map to the correct combinations of:

- Requirement baseline
- Architecture baseline
- Software branch or build
- Calibration dataset
- Test specification version
- Bench or environment configuration
- Release package identifier

### 25.10 Change Propagation Checklist

- [ ] Update the requirement statement and rationale.
- [ ] Update derived lower-level requirements.
- [ ] Update linked hazards, safety requirements, or cybersecurity assumptions if relevant.
- [ ] Update architecture models and interface specifications.
- [ ] Update software requirements and design descriptions.
- [ ] Update test cases, automation, and expected-result thresholds.
- [ ] Update release notes and validation plans.

### 25.11 Regression Testing Strategy After Requirement Change

| Change Impact Level | Regression Strategy | Example |
|---|---|---|
| Localized logic change | Targeted unit + integration regression | Timeout threshold adjustment in one module |
| Interface change | Integration and network regression | CAN signal scaling or message period change |
| Safety response change | Safety-focused regression + affected feature set | Changed fallback strategy after sensor fault |
| Architecture-level change | Broad subsystem or system regression | Functional allocation moved across ECUs |
| Variant-wide common platform change | Full platform regression for impacted variants | Shared diagnostic service behavior changed |

### 25.12 Scenario 1: AEB warning threshold tightened for a new regulation

**Change trigger**: An OEM requests that Forward Collision Warning must activate earlier to satisfy a new market regulation. The system requirement changes from TTC < 2.0 s to TTC < 2.4 s under specified conditions.

| Flow Stage | Key Analysis |
|---|---|
| Requirement Change | System requirement threshold changes to earlier warning trigger. |
| Safety Impact | Safety engineer reviews whether earlier warning introduces nuisance alerts or affects safety goal assumptions. |
| Architecture Impact | Architect checks if sensor fusion confidence and timing budget still support the earlier decision point. |
| Software Impact | Algorithm thresholds, filtering logic, and HMI timing may need updates. |
| Test Impact | Existing boundary tests around TTC = 2.0 s must be updated; new nuisance alert tests added. |
| Validation Impact | Vehicle validation must confirm usability and avoid excessive false positives. |
| Release Impact | Release board decides whether change enters current SOP branch or a later market variant branch. |

**Lessons for the requirements engineer**
- A simple numeric threshold change can trigger significant validation effort.
- Earlier warnings may improve compliance but reduce customer acceptance if false positives rise.

### 25.13 Scenario 2: Brake sensor fault reaction changed from warning-only to torque reduction request

**Change trigger**: Field incidents show the previous warning-only strategy is insufficient. Safety analysis recommends an active torque reduction request on persistent brake pressure signal loss.

| Flow Stage | Key Analysis |
|---|---|
| Requirement Change | Safe-state behavior is strengthened from warning-only to active coordination with powertrain. |
| Safety Impact | Safety goals, HARA assumptions, and FSC/TSC entries are updated because the item behavior changes under fault. |
| Architecture Impact | Powertrain coordination interface and network timing path must be verified. |
| Software Impact | Brake ECU fault manager, coordination manager, diagnostics, and debouncing logic are updated. |
| Test Impact | New integration and HIL tests must prove torque reduction bit setting, timing, and reset behavior. |
| Validation Impact | Vehicle tests confirm drivability and that the mitigation does not create secondary hazards. |
| Release Impact | May require software release note highlighting changed safety behavior and service implications. |

**Lessons for the requirements engineer**
- Safety-triggered changes often affect multiple ECUs and test levels.
- The change should not be approved without complete downstream verification planning.

### 25.14 Scenario 3: CAN FD diagnostic response time relaxed due to bus-load constraints

**Change trigger**: Supplier bench data shows the current 20 ms diagnostic response requirement is unrealistic during peak network load; proposal is to relax it to 35 ms for non-safety services.

| Flow Stage | Key Analysis |
|---|---|
| Requirement Change | Performance requirement is relaxed for a subset of diagnostics. |
| Safety Impact | Safety engineer verifies the affected diagnostics are not part of fault tolerant time assumptions. |
| Architecture Impact | Network architect reviews bus load assumptions and arbitration strategy. |
| Software Impact | Diagnostic scheduler and queue management may remain unchanged or receive optimization. |
| Test Impact | Performance test limits and timing assertions must be updated carefully by service class. |
| Validation Impact | After-sales and manufacturing stakeholders verify no plant or service disruption. |
| Release Impact | Documentation and tester scripts in service environment may need update. |

**Lessons for the requirements engineer**
- Relaxing a requirement is still a change that needs disciplined reasoning.
- Separating safety and non-safety diagnostics prevents unnecessary over-design.

### 25.15 Scenario 4: New cyber requirement enforces authenticated flashing sequence

**Change trigger**: Cybersecurity assessment mandates authenticated flashing for OTA-capable ECUs, affecting diagnostic programming requirements.

| Flow Stage | Key Analysis |
|---|---|
| Requirement Change | Programming sequence and access-control requirements are expanded. |
| Safety Impact | Safety review confirms recovery and safe-update mechanisms remain valid after security control insertion. |
| Architecture Impact | Bootloader, certificate handling, backend trust chain, and manufacturing flow are affected. |
| Software Impact | Bootloader logic, key handling, timeout behavior, and diagnostics stack require changes. |
| Test Impact | Security, negative, and recovery-path tests must be added; existing flashing tests updated. |
| Validation Impact | Manufacturing, service, and field-update validation must re-run end-to-end scenarios. |
| Release Impact | Release cannot proceed until plant and after-sales tools support the new authentication flow. |

**Lessons for the requirements engineer**
- Cyber changes often ripple deeply into tools and operations.
- Safety and cybersecurity assurance cases must remain aligned.

### 25.16 Scenario 5: Variant-specific seatbelt warning requirement added for a regulation market

**Change trigger**: A market-specific regulation requires additional visual warning behavior when rear seat occupancy is detected and belts are unlatched.

| Flow Stage | Key Analysis |
|---|---|
| Requirement Change | New market-specific functional requirement is introduced. |
| Safety Impact | Usually limited safety impact, but HMI distraction and fail-safe assumptions should still be checked. |
| Architecture Impact | Occupancy and belt-state interfaces, cluster behavior, and gateway routing may be affected. |
| Software Impact | BCM or restraint controller logic, cluster presentation logic, and variant coding tables may change. |
| Test Impact | Variant matrix expands; existing base-market tests remain, plus new regulation-market coverage. |
| Validation Impact | Market-specific legal compliance and HMI validation required. |
| Release Impact | Feature must be isolated to variant coding so unaffected markets do not regress. |

**Lessons for the requirements engineer**
- Variant changes can look small but multiply verification combinations.
- Baseline identification by market and variant is essential.

### 25.17 Senior Requirements Engineer Practices for Change Management

- Separate wording clarification from behavioral change; they deserve different levels of governance.
- Never approve a requirement change without identifying the owner for each downstream impacted artifact.
- Demand explicit justification for “no test impact” claims.
- Ensure baseline references appear in meeting minutes, review decisions, and release evidence.
- Track open change propagation actions until closure; approval alone does not complete the change.

### 25.18 Common Failure Patterns

- Requirement text changed but linked test cases were not re-reviewed.
- Supplier implemented a changed requirement against a superseded baseline.
- Approval was given verbally or in email without a controlled artifact state change.
- A “small” timeout change caused broader system timing conflicts that were not assessed.
- Release notes did not disclose altered safety behavior, confusing integration and service teams.

### 25.19 Key Takeaways

- Requirement change management is a system discipline, not a text-editing activity.
- Every approved change must have a traceable impact story across safety, architecture, software, test, validation, and release.
- Strong baseline and configuration discipline is what turns change from chaos into controlled engineering.

---

## Section 26: Requirement Conflict Resolution

Requirement conflicts are normal in automotive engineering because vehicles are built at the intersection of customer expectation, safety, performance, timing, cost, hardware capability, software flexibility, cybersecurity, regulations, and supplier reality. A senior requirements engineer is not merely a recorder of conflicting wishes; that engineer is a structured resolver of engineering trade-offs.

### 26.1 What a Requirement Conflict Is

A requirement conflict exists when two or more approved or proposed requirements cannot all be satisfied simultaneously under the same assumptions, architecture, schedule, cost, or physical constraints.

### 26.2 Conflict Resolution Principles

- Make the conflict explicit and write it down in objective terms.
- Distinguish true conflict from incomplete understanding or ambiguous wording.
- Bring evidence: hazard analysis, measurements, timing budgets, cost data, diagnostics strategy, or regulation text.
- Escalate decisions to the right authority level if safety, legal compliance, or platform strategy is affected.
- Document resolution rationale so the next engineer does not reopen the same debate from zero.

### 26.3 Conflict Scenario: Customer vs safety

**Situation**: The customer wants lane centering to remain active with minimal driver torque input for comfort. Safety analysis states the feature must disengage if driver hands-off confidence persists beyond a defined interval.

| Stakeholder | Position |
|---|---|
| Customer / product | Longer continuous comfort and fewer disengagements. |
| Safety team | Hands-off misuse increases hazard exposure; disengagement and warning are required. |

**How the conflict is resolved**
1. Confirm the misuse scenario, hazard severity, and regulatory expectations.
2. Review whether a graded response is possible: warning first, then controlled disengagement.
3. Define measurable hand-detection thresholds and escalation timing.
4. Update requirement set so comfort logic cannot override safety escalation logic.

**Senior requirements engineer approach**: The senior requirements engineer frames the decision around hazard acceptance, not preference. Customer comfort may influence thresholds and HMI strategy, but cannot negate a safety requirement without a formal safety case change.

### 26.4 Conflict Scenario: Performance vs safety

**Situation**: A chassis feature team wants maximum steering assist responsiveness, but safety analysis requires additional plausibility checks that add latency.

| Stakeholder | Position |
|---|---|
| Performance team | Lower latency improves steering feel and customer perception. |
| Safety team | Plausibility checks reduce risk of unintended torque output. |

**How the conflict is resolved**
1. Quantify the real latency impact and determine the fault coverage improvement.
2. Check whether safety checks can be pipelined or implemented on a faster execution path.
3. Split nominal-path performance requirement from fault-monitoring requirement if needed.
4. Verify final design against both feel targets and safety timing constraints.

**Senior requirements engineer approach**: The senior engineer prevents the debate from becoming emotional by converting it into timing budgets, fault coverage, and driver-perceived performance data.

### 26.5 Conflict Scenario: Cost vs redundancy

**Situation**: Program cost pressure pushes for removal of a redundant sensor channel, while safety architecture assumes dual-channel sensing for ASIL decomposition.

| Stakeholder | Position |
|---|---|
| Program / purchasing | Remove hardware cost and complexity. |
| Safety / system architecture | Redundancy is part of the claimed safety mechanism. |

**How the conflict is resolved**
1. Check whether the redundancy is a safety requirement, design assumption, or merely a preferred implementation.
2. Re-run safety analysis if the architecture changes materially.
3. Evaluate alternative mechanisms such as analytical redundancy only if they deliver equivalent coverage and timing.
4. Reject cost-driven requirement change if no equivalent safety argument exists.

**Senior requirements engineer approach**: The senior requirements engineer anchors the discussion in the approved safety concept and prevents cost optimization from silently eroding the safety case.

### 26.6 Conflict Scenario: Software vs hardware

**Situation**: Software requests a higher-resolution steering angle signal to improve control smoothness, but hardware says the current sensor and network budget cannot support it in the target SOP timing window.

| Stakeholder | Position |
|---|---|
| Software team | Higher resolution or rate is needed for algorithm quality. |
| Hardware / EE architecture | Sensor change or bus redesign is too late or too expensive. |

**How the conflict is resolved**
1. Clarify whether the requirement is truly resolution-limited or estimation-quality-limited.
2. Investigate filtering, estimation, or interpolation alternatives within existing hardware bounds.
3. If hardware change is unavoidable, escalate as platform change with release impact visible.
4. Rewrite the requirement around functional need and measurable performance rather than implicit hardware assumptions.

**Senior requirements engineer approach**: The senior engineer translates software desire into measurable system-level need and avoids premature hardware mandates inside software requirement text.

### 26.7 Conflict Scenario: OEM vs supplier

**Situation**: The OEM requires a diagnostic response behavior that differs from the supplier platform standard. The supplier claims the OEM request breaks reuse and timing assumptions.

| Stakeholder | Position |
|---|---|
| OEM | Vehicle integration and after-sales process depend on the requested behavior. |
| Supplier | Platform deviation increases complexity, risk, and cost. |

**How the conflict is resolved**
1. Validate whether the OEM requirement is mandatory, negotiable, or historically inherited without current need.
2. Assess whether configurable behavior can satisfy both reuse and OEM integration expectations.
3. Capture the agreement in explicit requirement wording and interface specifications.
4. Baseline the resolution so later teams do not revert to conflicting assumptions.

**Senior requirements engineer approach**: The senior requirements engineer acts as translator between contractual expectation and technical feasibility, converting open disagreement into a documented decision with variant or configuration logic where possible.

### 26.8 Conflict Scenario: Functional vs diagnostic requirement

**Situation**: A functional requirement asks for immediate feature availability after ignition ON, while diagnostic self-tests require several hundred milliseconds before safe activation can be claimed.

| Stakeholder | Position |
|---|---|
| Functional team | Fast availability improves customer experience. |
| Diagnostics / safety team | Feature must not activate before self-test completion. |

**How the conflict is resolved**
1. Separate feature availability, degraded availability, and safe activation states.
2. Allow limited pre-availability indication only if hazardous behavior is impossible.
3. Add explicit requirement states for initialization, pending, active, and blocked.
4. Verify HMI messaging so the customer is not misled during self-test delay.

**Senior requirements engineer approach**: The senior engineer resolves the conflict by introducing state clarity rather than picking a simplistic winner.

### 26.9 Conflict Scenario: Safety vs cybersecurity

**Situation**: Cybersecurity requires authenticated access and rate-limited commands, but safety service operations demand fast emergency diagnostic access in workshop or recovery modes.

| Stakeholder | Position |
|---|---|
| Cybersecurity team | Strong authentication and anti-abuse controls are non-negotiable. |
| Safety / service team | Emergency recovery must remain achievable under controlled conditions. |

**How the conflict is resolved**
1. Define operating modes clearly: normal operation, plant mode, service mode, recovery mode.
2. Use role-based or condition-based access rather than a one-size-fits-all rule.
3. Validate fail-secure and fail-safe interactions for power loss, certificate failure, and incomplete flashing.
4. Document the agreed compromise in both safety and cybersecurity requirement sets.

**Senior requirements engineer approach**: The senior requirements engineer ensures neither discipline silently dominates; instead, the resolution must satisfy safety recovery needs without creating exploitable openings.

### 26.10 Conflict Scenario: Timing vs computational load

**Situation**: A perception feature requires a 20 ms cycle time, but processor analysis shows worst-case computational load exceeds safe margin when all diagnostics and monitoring are enabled.

| Stakeholder | Position |
|---|---|
| Feature team | Short cycle time is needed for object tracking quality. |
| Platform / software architecture | CPU overload threatens timing determinism and system stability. |

**How the conflict is resolved**
1. Perform real WCET and scheduling analysis instead of average-load arguments.
2. Look for algorithm partitioning, degraded modes, hardware acceleration, or monitoring rate redesign.
3. If no feasible solution exists, renegotiate the requirement with quantified performance impact.
4. Avoid hiding the issue through “best effort” wording for a hard real-time requirement.

**Senior requirements engineer approach**: The senior requirements engineer keeps the discussion evidence-based and prevents schedule pressure from accepting infeasible timing commitments.

### 26.11 Conflict Resolution Workflow Used by Senior Engineers

- Restate the conflicting requirements in plain, testable language.
- Identify whether the conflict is semantic, architectural, safety-related, timing-related, contractual, or organizational.
- Collect evidence from analysis, test data, standards, and stakeholder intent.
- Generate feasible resolution options, including split states, degraded modes, configuration options, or staged behaviors.
- Evaluate options against safety, compliance, cost, schedule, and customer impact.
- Document the decision and update requirement baselines and trace links.

### 26.12 Typical Mistakes in Conflict Resolution

- Resolving by authority alone without engineering rationale.
- Allowing implementation teams to “work it out later” without updated requirement text.
- Treating safety and cybersecurity as optional opinions rather than governed constraints.
- Accepting ambiguous compromise wording that cannot be verified objectively.
- Failing to update downstream tests after the conflict resolution changes the behavior.

### 26.13 Key Takeaways

- Conflicts are inevitable in complex automotive systems; unmanaged conflicts are what create instability.
- Senior requirements engineers resolve conflicts by clarifying intent, quantifying constraints, and documenting trade-offs.
- The best resolution is usually one that preserves safety and compliance while making customer, cost, and implementation trade-offs explicit rather than hidden.

---

## Section 27: Requirements Metrics

Requirements metrics convert the health of a requirements set from opinion into evidence. Good metrics do not exist to create dashboards for their own sake. They exist to help engineering leaders answer questions such as:

- Are requirements stabilizing or still churning?
- Do we have enough traceability to trust release decisions?
- Are reviews finding issues early enough?
- Are requirements written clearly enough to avoid test and implementation waste?

### 27.1 Metric Design Principles

- Every metric needs a precise definition, data source, calculation period, and owner.
- A metric should influence action; if nobody will act on it, it is decorative.
- Use metrics in context. A high change rate early in concept phase may be healthy; late in release phase it may be dangerous.
- Do not optimize teams into gaming the numbers; review the behaviors encouraged by each metric.

### 27.2 Requirement Volatility

**Definition**: The degree to which requirements are added, modified, or deleted over a defined period.

**Formula**: `Requirement Volatility (%) = ((Added + Modified + Deleted) / Total Baselined Requirements at Start of Period) x 100`

**Worked example**: If a project starts the month with 400 baselined requirements and during the month 12 are added, 20 modified, and 8 deleted, volatility = ((12 + 20 + 8) / 400) x 100 = 10.0%.

**Interpretation**: High volatility late in the lifecycle indicates instability and probable rework risk.

**Practical actions**
- Check which domains drive the changes.
- Separate expected variant growth from defect-driven churn.
- Increase change board scrutiny near release milestones.

### 27.3 Requirement Stability

**Definition**: The complement of volatility; indicates how much of the requirement set remains unchanged during a period.

**Formula**: `Requirement Stability (%) = 100 - Requirement Volatility (%)`

**Worked example**: If volatility is 10.0%, stability is 90.0%.

**Interpretation**: High stability near release is generally good, provided unresolved defects are not being ignored.

**Practical actions**
- Track stability trend across milestones.
- Compare stability between safety and non-safety domains.
- Use with review defect trends to avoid false confidence.

### 27.4 Requirement Coverage

**Definition**: The proportion of requirements that have at least one valid downstream implementation and/or verification link, depending on project definition.

**Formula**: `Requirement Coverage (%) = (Number of Requirements with Required Downstream Links / Total Applicable Requirements) x 100`

**Worked example**: If 360 out of 400 applicable requirements have required verification links, coverage = 90.0%.

**Interpretation**: A low value indicates unimplemented or unverifiable parts of the specification.

**Practical actions**
- Identify orphan requirements.
- Prioritize safety and release-critical gaps.
- Ensure N/A exclusions are justified, not convenient.

### 27.5 Traceability Coverage

**Definition**: The percentage of required trace links that actually exist across the chosen digital thread.

**Formula**: `Traceability Coverage (%) = (Established Required Links / Expected Required Links) x 100`

**Worked example**: If process rules expect 1,200 links and 1,080 exist, coverage = 90.0%.

**Interpretation**: This metric reveals how complete the trace network is, not whether every requirement is good.

**Practical actions**
- Audit by link type: derives, satisfies, verifies, mitigates.
- Flag broken or suspect links after changes.
- Use automated reports where possible.

### 27.6 Defect Density

**Definition**: The number of requirement defects identified relative to the size of the requirement set.

**Formula**: `Defect Density = Number of Requirement Defects / Number of Requirements`

**Worked example**: If 48 defects are logged against 320 reviewed requirements, defect density = 0.15 defects per requirement.

**Interpretation**: Useful for comparing quality across modules or releases, especially when normalized by size.

**Practical actions**
- Compare density by team and artifact type.
- Correlate with ambiguity rate and review maturity.
- Use trend, not isolated points only.

### 27.7 Ambiguity Rate

**Definition**: The proportion of requirements containing ambiguous wording, undefined terms, or unclear conditions identified during review.

**Formula**: `Ambiguity Rate (%) = (Requirements Flagged as Ambiguous / Requirements Reviewed) x 100`

**Worked example**: If 22 out of 200 reviewed requirements contain ambiguous terms such as “quickly,” “if necessary,” or “normally,” ambiguity rate = 11.0%.

**Interpretation**: A high ambiguity rate predicts implementation inconsistency and test disputes.

**Practical actions**
- Maintain a project banned-words list.
- Train authors on measurable wording.
- Use peer review checklists focused on clarity.

### 27.8 Review Defect Rate

**Definition**: The average number of defects found per requirement review or per reviewed requirement, depending on chosen normalization.

**Formula**: `Review Defect Rate = Number of Defects Found in Reviews / Number of Requirements Reviewed`

**Worked example**: If 75 defects are found while reviewing 250 requirements, rate = 0.30 defects per requirement.

**Interpretation**: High rate early is acceptable and even healthy; high rate late suggests weak upstream authoring or unstable input.

**Practical actions**
- Track by phase and authoring team.
- Distinguish major vs minor review defects.
- Feed lessons into templates and training.

### 27.9 Change Rate

**Definition**: The rate at which change requests are raised or approved over time for a requirement set.

**Formula**: `Change Rate = Number of Approved Requirement Changes / Time Period`

**Worked example**: If 18 requirement changes are approved during four weeks, the change rate is 4.5 approved changes per week.

**Interpretation**: Change rate helps understand workload and instability, especially when paired with impact severity.

**Practical actions**
- Categorize by origin: OEM, safety, defect, manufacturing, supplier.
- Track emergency vs planned changes.
- Use to forecast re-verification effort.

### 27.10 Test Coverage

**Definition**: The percentage of applicable requirements that are covered by at least one test case.

**Formula**: `Test Coverage (%) = (Requirements with At Least One Test Case / Total Testable Requirements) x 100`

**Worked example**: If 285 of 300 testable requirements have linked test cases, test coverage = 95.0%.

**Interpretation**: This measures planned verification completeness, not actual execution status.

**Practical actions**
- Focus first on safety and release-critical requirements.
- Split by unit, integration, system, and vehicle level.
- Review exclusions explicitly.

### 27.11 Verification Coverage

**Definition**: The percentage of applicable requirements for which verification has been executed and a verdict recorded.

**Formula**: `Verification Coverage (%) = (Requirements with Executed Verification Evidence / Total Applicable Requirements) x 100`

**Worked example**: If 240 of 300 applicable requirements have current executed evidence, verification coverage = 80.0%.

**Interpretation**: Important near release because a test case existing on paper is not the same as verified evidence.

**Practical actions**
- Separate passed, failed, blocked, and not-run evidence.
- Check evidence freshness after requirement changes.
- Prioritize missing evidence for critical requirements.

### 27.12 Validation Coverage

**Definition**: The percentage of stakeholder or system-level expectations that have been validated in representative operational conditions.

**Formula**: `Validation Coverage (%) = (Validated Stakeholder/System Requirements / Total Stakeholder/System Requirements Planned for Validation) x 100`

**Worked example**: If 68 of 80 stakeholder requirements planned for validation have field, vehicle, or user-representative evidence, validation coverage = 85.0%.

**Interpretation**: Validation focuses on “did we build the right thing?” rather than only “did we build it right?”

**Practical actions**
- Keep validation distinct from lower-level verification metrics.
- Ensure representative operational scenarios are defined.
- Highlight gaps before customer demonstrations or homologation gates.

### 27.13 Example Metrics Dashboard for an ADAS ECU Program

| Metric | Current Value | Target / Threshold | Interpretation |
|---|---|---|---|
| Requirement volatility | 7.5% | <= 5% after design freeze | Slightly high; review late OEM requests |
| Requirement stability | 92.5% | >= 95% after design freeze | Not yet fully stable |
| Requirement coverage | 96% | 100% for ASIL requirements | General coverage strong, safety gap remains |
| Traceability coverage | 93% | >= 98% | Missing links still present |
| Defect density | 0.12 | <= 0.08 at release review | Quality improving but still elevated |
| Ambiguity rate | 4% | <= 2% | Author training still needed |
| Review defect rate | 0.18 | Trend downward | Healthy if trending down |
| Change rate | 3.2/week | <= 1/week late phase | Late-phase churn warning |
| Test coverage | 97% | 100% safety, >=95% overall | Almost complete |
| Verification coverage | 84% | >= 95% before release candidate | Execution backlog exists |
| Validation coverage | 70% | >= 90% before customer gate | Vehicle validation lagging |

### 27.14 How Metrics Should Be Used by Role

| Role | Most Relevant Metrics | Why |
|---|---|---|
| Requirements engineer | Ambiguity rate, defect density, traceability coverage | Improves specification quality and linkage completeness |
| Safety engineer | Coverage, verification coverage, volatility | Tracks stability of safety-relevant requirement set |
| Test lead | Test coverage, verification coverage, change rate | Plans workload and evidence readiness |
| Project manager | Volatility, stability, change rate | Monitors schedule risk and churn |
| Release manager | Verification and validation coverage | Determines readiness for delivery |

### 27.15 Metric Pitfalls

- Counting links without checking link correctness.
- Declaring 100% test coverage when many requirements are linked to weak or irrelevant tests.
- Comparing defect density across teams without normalizing review depth or artifact complexity.
- Rewarding low review defect rate even when it may indicate superficial reviews.
- Treating late-stage low volatility as success when teams may simply be suppressing needed changes.

### 27.16 Key Takeaways

- Good metrics create visibility, prioritization, and accountability.
- The most valuable metrics combine completeness, quality, and change behavior.
- Metrics must be interpreted in lifecycle context and never replace engineering judgment.

---

## Section 28: Requirements Quality Analysis

Requirements quality analysis is the disciplined review of whether a requirement is clear, complete, consistent, feasible, testable, and expressed at the correct level of abstraction. Many automotive project problems can be traced back to poor requirement quality rather than weak implementation skill.

### 28.1 Quality Analysis Goals

- Prevent ambiguity before implementation and testing begin.
- Detect incomplete or contradictory intent early.
- Remove implementation bias where the requirement should state behavior only.
- Improve verifiability, traceability, and review efficiency.

### 28.2 Eight Frequent Quality Problems

### 28.3 Ambiguous requirement

**Problem example**

```text
The braking warning shall be issued quickly when the situation becomes critical.
```

**Problem**: Words like “quickly” and “critical” are subjective and undefined. Different engineers may interpret them differently.

**Detection**: Reviewers flag vague adjectives, undefined thresholds, and unclear trigger conditions. Test engineers cannot derive objective pass criteria.

**Correction**: When time-to-collision is less than 1.8 s and vehicle speed is greater than 20 km/h, the FCW function shall issue an audible warning within 150 ms.

**Review**: Confirm every timing, condition, and output is measurable and linked to defined signal terms.

### 28.4 Incomplete requirement

**Problem example**

```text
When communication is lost, the ECU shall enter fallback mode.
```

**Problem**: The requirement does not define which communication, for how long, which fallback mode, or how long the mode must persist.

**Detection**: Questions emerge immediately during review: bus? signal? timeout? recovery condition? output behavior?

**Correction**: If the Brake ECU does not receive message `WheelSpeed_Status` for more than 100 ms, it shall enter fallback mode `BRAKE_DEGRADED` and maintain that mode until three consecutive valid messages are received.

**Review**: Check that trigger, timing, mode name, and exit criteria are present.

### 28.5 Contradictory requirement

**Problem example**

```text
REQ-1: The diagnostic session shall time out after 5 s of inactivity. REQ-2: The programming session shall remain active indefinitely while ignition is ON.
```

**Problem**: If programming session is a diagnostic session, the two requirements conflict unless scoped or prioritized explicitly.

**Detection**: Traceability and review reveal that both apply in overlapping conditions without exception handling.

**Correction**: The programming session shall remain active while ignition is ON, except when no diagnostic request is received for 300 s, after which session timeout shall occur.

**Review**: Verify scope, exceptions, and precedence rules. Confirm downstream tests match the resolved logic.

### 28.6 Non-testable requirement

**Problem example**

```text
The infotainment startup shall feel responsive to the user.
```

**Problem**: “Feel responsive” cannot be verified objectively without measurable criteria or a defined validation method.

**Detection**: Test team cannot write unambiguous pass/fail criteria.

**Correction**: The infotainment HMI home screen shall be displayed within 2.0 s after ignition ON under nominal battery voltage and ambient temperature 20°C to 30°C.

**Review**: Confirm whether it is now a verification requirement or whether an additional subjective validation requirement is needed.

### 28.7 Over-constrained requirement

**Problem example**

```text
The body controller shall implement the warning chime using a 2 kHz square wave generated by Timer 3 interrupt every 5 ms.
```

**Problem**: The statement constrains implementation details that may not be necessary for the required behavior and may block better solutions.

**Detection**: Architecture and software reviews recognize unnecessary design prescription in a requirement that should describe external behavior.

**Correction**: The body controller shall generate a driver warning chime with acoustic profile `CHIME_DOOR_WARNING` within 200 ms after the trigger condition is met.

**Review**: Ensure the requirement states what must be achieved, not an arbitrary internal design unless mandated by interface or safety rationale.

### 28.8 Under-specified requirement

**Problem example**

```text
The ECU shall support over-the-air updates securely.
```

**Problem**: The requirement names a goal but omits authentication, integrity, rollback, recovery, key management, and failure behavior.

**Detection**: Cybersecurity and implementation teams cannot derive concrete design or tests.

**Correction**: The ECU shall accept over-the-air software packages only after successful signature verification using the approved OEM certificate chain and shall revert to the previous validated image if update installation is interrupted before completion.

**Review**: Check that threat-informed behaviors and failure responses are explicitly covered.

### 28.9 Implementation-specific requirement

**Problem example**

```text
The ADAS function shall use a Kalman filter with 64-bit floating-point operations for object tracking.
```

**Problem**: The requirement dictates a design approach rather than the externally required performance, unless a justified architectural standard mandates it.

**Detection**: Design review shows algorithm choice is prematurely fixed in requirements without need.

**Correction**: The ADAS function shall track up to 64 objects with lateral position error not exceeding 0.15 m at 100 km/h in the defined reference scenarios.

**Review**: Confirm that algorithm freedom remains while performance expectation is measurable.

### 28.10 Duplicate requirement

**Problem example**

```text
Two separate requirements in different modules both state the same door-open warning behavior with slightly different wording.
```

**Problem**: Duplicates create maintenance divergence and review confusion, especially when one copy changes and the other does not.

**Detection**: Tool queries, text similarity checks, and review walkthroughs reveal overlapping semantics.

**Correction**: Keep one master requirement for the behavior and derive or reference it from downstream modules as needed.

**Review**: Verify all trace links point to the retained master requirement and obsolete duplicates are retired formally.

### 28.11 Practical Quality Review Checklist

- [ ] Is the requirement atomic, or does it hide multiple behaviors in one sentence?
- [ ] Does it use defined terms and project vocabulary consistently?
- [ ] Is every trigger, state, threshold, and output measurable?
- [ ] Is the requirement complete enough for design and test to proceed?
- [ ] Does it avoid unnecessary implementation prescription?
- [ ] Does it conflict with any upstream, peer, or downstream requirement?
- [ ] Can a test engineer derive an objective test case from it?
- [ ] Is the requirement duplicated elsewhere?

### 28.12 Example Review Dialogue

| Reviewer Comment | Why It Matters | Better Direction |
|---|---|---|
| “What does quickly mean here?” | Ambiguous timing cannot be verified. | Replace with a measurable latency limit. |
| “Which signal loss are we talking about?” | Incomplete trigger definition leads to inconsistent implementation. | Name the signal and timeout condition explicitly. |
| “Why are we forcing this algorithm?” | May be over-constraining design without value. | State required accuracy or performance instead. |
| “This seems to repeat REQ-BCM-133.” | Duplicates create divergence risk. | Merge or reference the master requirement. |

### 28.13 Quality Analysis Workflow

- Screen new requirements with templates and linting rules.
- Perform peer review focused on clarity, completeness, and testability.
- Perform specialist review for safety, cybersecurity, diagnostics, and architecture topics.
- Resolve comments and update requirement wording and rationale.
- Re-check downstream trace links and verification strategy after major edits.
- Baseline only after quality criteria are satisfied.

### 28.14 Automated Support for Quality Analysis

- Ambiguity keyword scans can flag terms such as “quickly,” “normally,” “if necessary,” and “sufficient.”
- Traceability reports can identify unverified, orphan, or duplicate-looking requirements.
- Schema validation can ensure mandatory fields such as rationale, ASIL, and verification method are present.
- Diff reviews can highlight behavioral changes hidden inside “small wording updates.”

### 28.15 Example Before-and-After Set

| State | Requirement Text |
|---|---|
| Before | When temperature is high, the fan shall run fast. |
| After | When coolant temperature exceeds 110°C, the ECU shall command cooling fan duty cycle to 100% within 50 ms. |
| Before | The ECU shall securely store logs. |
| After | The ECU shall store security event logs in non-volatile memory protected against unauthorized modification and shall preserve the latest 500 events across ignition cycles. |
| Before | The vehicle shall warn the driver appropriately. |
| After | When rear cross-traffic is detected within the defined collision zone while reverse gear is engaged, the system shall issue one audible warning and one visual alert within 200 ms. |

### 28.16 Key Takeaways

- Most requirement quality problems are detectable long before implementation if reviews are disciplined.
- Clear, complete, and testable requirements reduce conflict, rework, and test ambiguity.
- A senior requirements engineer continuously improves the requirement set, not just individual sentences.

---

## Appendix A: Extended Example Trace Package

| Layer | Example Artifact | Example Identifier | Notes |
|---|---|---|---|
| Stakeholder requirement | Braking safety objective | SHR-BRK-12 | Customer and safety expectation |
| System requirement | Safe reaction on pressure sensor loss | REQ-SAF-BRK-217 | Allocated to Brake ECU and Powertrain coordination |
| Software requirement | Set torque reduction request bit after timeout debounce | SWR-BRK-902 | Implemented in fault manager |
| Test case | Loss of brake pressure signal triggers torque reduction | TC-SAF-BRK-217-01 | Integration/HIL level |
| pytest script | Automated verification node | test_torque_reduction_on_brake_pressure_signal_loss | Stores machine-readable evidence |
| Bench configuration | CANoe project configuration | BrakeSystem.cfg@v18 | Defines restbus and CAPL gateway |
| ECU build | Brake ECU firmware | BRK_ECU_5.8.12 | Exact SW baseline under test |
| Report | JSON + JUnit + ASC logs | REP-BRK-217-2026-08-13-01 | Formal evidence package |

## Appendix B: Example Requirement Quality Gate Questions

1. Does requirement item 1 contribute to clarity, completeness, traceability, or verification readiness?
2. Does requirement item 2 contribute to clarity, completeness, traceability, or verification readiness?
3. Does requirement item 3 contribute to clarity, completeness, traceability, or verification readiness?
4. Does requirement item 4 contribute to clarity, completeness, traceability, or verification readiness?
5. Does requirement item 5 contribute to clarity, completeness, traceability, or verification readiness?
6. Does requirement item 6 contribute to clarity, completeness, traceability, or verification readiness?
7. Does requirement item 7 contribute to clarity, completeness, traceability, or verification readiness?
8. Does requirement item 8 contribute to clarity, completeness, traceability, or verification readiness?
9. Does requirement item 9 contribute to clarity, completeness, traceability, or verification readiness?
10. Does requirement item 10 contribute to clarity, completeness, traceability, or verification readiness?
11. Does requirement item 11 contribute to clarity, completeness, traceability, or verification readiness?
12. Does requirement item 12 contribute to clarity, completeness, traceability, or verification readiness?
13. Does requirement item 13 contribute to clarity, completeness, traceability, or verification readiness?
14. Does requirement item 14 contribute to clarity, completeness, traceability, or verification readiness?
15. Does requirement item 15 contribute to clarity, completeness, traceability, or verification readiness?
16. Does requirement item 16 contribute to clarity, completeness, traceability, or verification readiness?
17. Does requirement item 17 contribute to clarity, completeness, traceability, or verification readiness?
18. Does requirement item 18 contribute to clarity, completeness, traceability, or verification readiness?
19. Does requirement item 19 contribute to clarity, completeness, traceability, or verification readiness?
20. Does requirement item 20 contribute to clarity, completeness, traceability, or verification readiness?
21. Does requirement item 21 contribute to clarity, completeness, traceability, or verification readiness?
22. Does requirement item 22 contribute to clarity, completeness, traceability, or verification readiness?
23. Does requirement item 23 contribute to clarity, completeness, traceability, or verification readiness?
24. Does requirement item 24 contribute to clarity, completeness, traceability, or verification readiness?
25. Does requirement item 25 contribute to clarity, completeness, traceability, or verification readiness?
26. Does requirement item 26 contribute to clarity, completeness, traceability, or verification readiness?
27. Does requirement item 27 contribute to clarity, completeness, traceability, or verification readiness?
28. Does requirement item 28 contribute to clarity, completeness, traceability, or verification readiness?
29. Does requirement item 29 contribute to clarity, completeness, traceability, or verification readiness?
30. Does requirement item 30 contribute to clarity, completeness, traceability, or verification readiness?
31. Does requirement item 31 contribute to clarity, completeness, traceability, or verification readiness?
32. Does requirement item 32 contribute to clarity, completeness, traceability, or verification readiness?
33. Does requirement item 33 contribute to clarity, completeness, traceability, or verification readiness?
34. Does requirement item 34 contribute to clarity, completeness, traceability, or verification readiness?
35. Does requirement item 35 contribute to clarity, completeness, traceability, or verification readiness?
36. Does requirement item 36 contribute to clarity, completeness, traceability, or verification readiness?
37. Does requirement item 37 contribute to clarity, completeness, traceability, or verification readiness?
38. Does requirement item 38 contribute to clarity, completeness, traceability, or verification readiness?
39. Does requirement item 39 contribute to clarity, completeness, traceability, or verification readiness?
40. Does requirement item 40 contribute to clarity, completeness, traceability, or verification readiness?

## Appendix C: Extended Tool Practice Prompts

### Practice prompts for IBM DOORS

- Create a new safety requirement with mandatory attributes and review state.
- Link the requirement to one hazard, one software requirement, and one verification artifact.
- Create a baseline and compare it against the previous approved version.
- Record a review comment that identifies ambiguity and resolve it with corrected wording.
- Generate a traceability report showing upstream and downstream links.
- Simulate a change request and document which dashboards or reports would be updated.

### Practice prompts for DOORS Next

- Create a new safety requirement with mandatory attributes and review state.
- Link the requirement to one hazard, one software requirement, and one verification artifact.
- Create a baseline and compare it against the previous approved version.
- Record a review comment that identifies ambiguity and resolve it with corrected wording.
- Generate a traceability report showing upstream and downstream links.
- Simulate a change request and document which dashboards or reports would be updated.

### Practice prompts for Polarion

- Create a new safety requirement with mandatory attributes and review state.
- Link the requirement to one hazard, one software requirement, and one verification artifact.
- Create a baseline and compare it against the previous approved version.
- Record a review comment that identifies ambiguity and resolve it with corrected wording.
- Generate a traceability report showing upstream and downstream links.
- Simulate a change request and document which dashboards or reports would be updated.

### Practice prompts for Jama

- Create a new safety requirement with mandatory attributes and review state.
- Link the requirement to one hazard, one software requirement, and one verification artifact.
- Create a baseline and compare it against the previous approved version.
- Record a review comment that identifies ambiguity and resolve it with corrected wording.
- Generate a traceability report showing upstream and downstream links.
- Simulate a change request and document which dashboards or reports would be updated.

### Practice prompts for Codebeamer

- Create a new safety requirement with mandatory attributes and review state.
- Link the requirement to one hazard, one software requirement, and one verification artifact.
- Create a baseline and compare it against the previous approved version.
- Record a review comment that identifies ambiguity and resolve it with corrected wording.
- Generate a traceability report showing upstream and downstream links.
- Simulate a change request and document which dashboards or reports would be updated.

### Practice prompts for Enterprise Architect

- Create a new safety requirement with mandatory attributes and review state.
- Link the requirement to one hazard, one software requirement, and one verification artifact.
- Create a baseline and compare it against the previous approved version.
- Record a review comment that identifies ambiguity and resolve it with corrected wording.
- Generate a traceability report showing upstream and downstream links.
- Simulate a change request and document which dashboards or reports would be updated.

### Practice prompts for Jira

- Create a new safety requirement with mandatory attributes and review state.
- Link the requirement to one hazard, one software requirement, and one verification artifact.
- Create a baseline and compare it against the previous approved version.
- Record a review comment that identifies ambiguity and resolve it with corrected wording.
- Generate a traceability report showing upstream and downstream links.
- Simulate a change request and document which dashboards or reports would be updated.

### Practice prompts for Git

- Create a new safety requirement with mandatory attributes and review state.
- Link the requirement to one hazard, one software requirement, and one verification artifact.
- Create a baseline and compare it against the previous approved version.
- Record a review comment that identifies ambiguity and resolve it with corrected wording.
- Generate a traceability report showing upstream and downstream links.
- Simulate a change request and document which dashboards or reports would be updated.

### Practice prompts for GitHub / GitLab

- Create a new safety requirement with mandatory attributes and review state.
- Link the requirement to one hazard, one software requirement, and one verification artifact.
- Create a baseline and compare it against the previous approved version.
- Record a review comment that identifies ambiguity and resolve it with corrected wording.
- Generate a traceability report showing upstream and downstream links.
- Simulate a change request and document which dashboards or reports would be updated.

## Appendix D: Extended Change Impact Questions

### Safety impact review questions

- Safety question 1: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 2: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 3: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 4: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 5: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 6: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 7: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 8: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 9: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 10: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 11: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 12: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 13: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 14: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?
- Safety question 15: What assumption, artifact, or decision in safety engineering changes if the requirement wording is modified?

### Architecture impact review questions

- Architecture question 1: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 2: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 3: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 4: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 5: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 6: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 7: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 8: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 9: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 10: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 11: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 12: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 13: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 14: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?
- Architecture question 15: What assumption, artifact, or decision in architecture engineering changes if the requirement wording is modified?

### Software impact review questions

- Software question 1: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 2: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 3: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 4: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 5: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 6: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 7: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 8: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 9: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 10: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 11: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 12: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 13: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 14: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?
- Software question 15: What assumption, artifact, or decision in software engineering changes if the requirement wording is modified?

### Calibration impact review questions

- Calibration question 1: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 2: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 3: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 4: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 5: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 6: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 7: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 8: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 9: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 10: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 11: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 12: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 13: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 14: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?
- Calibration question 15: What assumption, artifact, or decision in calibration engineering changes if the requirement wording is modified?

### Diagnostics impact review questions

- Diagnostics question 1: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 2: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 3: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 4: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 5: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 6: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 7: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 8: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 9: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 10: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 11: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 12: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 13: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 14: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?
- Diagnostics question 15: What assumption, artifact, or decision in diagnostics engineering changes if the requirement wording is modified?

### Test impact review questions

- Test question 1: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 2: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 3: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 4: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 5: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 6: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 7: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 8: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 9: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 10: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 11: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 12: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 13: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 14: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?
- Test question 15: What assumption, artifact, or decision in test engineering changes if the requirement wording is modified?

### Validation impact review questions

- Validation question 1: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 2: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 3: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 4: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 5: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 6: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 7: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 8: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 9: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 10: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 11: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 12: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 13: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 14: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?
- Validation question 15: What assumption, artifact, or decision in validation engineering changes if the requirement wording is modified?

### Release impact review questions

- Release question 1: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 2: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 3: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 4: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 5: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 6: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 7: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 8: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 9: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 10: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 11: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 12: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 13: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 14: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?
- Release question 15: What assumption, artifact, or decision in release engineering changes if the requirement wording is modified?

## Appendix E: Extended Conflict Facilitation Questions

### Facilitating a workshop for Customer vs safety

- Facilitation question 1: What evidence would reduce uncertainty in the customer vs safety conflict?
- Facilitation question 2: What evidence would reduce uncertainty in the customer vs safety conflict?
- Facilitation question 3: What evidence would reduce uncertainty in the customer vs safety conflict?
- Facilitation question 4: What evidence would reduce uncertainty in the customer vs safety conflict?
- Facilitation question 5: What evidence would reduce uncertainty in the customer vs safety conflict?
- Facilitation question 6: What evidence would reduce uncertainty in the customer vs safety conflict?
- Facilitation question 7: What evidence would reduce uncertainty in the customer vs safety conflict?
- Facilitation question 8: What evidence would reduce uncertainty in the customer vs safety conflict?
- Facilitation question 9: What evidence would reduce uncertainty in the customer vs safety conflict?
- Facilitation question 10: What evidence would reduce uncertainty in the customer vs safety conflict?
- Facilitation question 11: What evidence would reduce uncertainty in the customer vs safety conflict?
- Facilitation question 12: What evidence would reduce uncertainty in the customer vs safety conflict?

### Facilitating a workshop for Performance vs safety

- Facilitation question 1: What evidence would reduce uncertainty in the performance vs safety conflict?
- Facilitation question 2: What evidence would reduce uncertainty in the performance vs safety conflict?
- Facilitation question 3: What evidence would reduce uncertainty in the performance vs safety conflict?
- Facilitation question 4: What evidence would reduce uncertainty in the performance vs safety conflict?
- Facilitation question 5: What evidence would reduce uncertainty in the performance vs safety conflict?
- Facilitation question 6: What evidence would reduce uncertainty in the performance vs safety conflict?
- Facilitation question 7: What evidence would reduce uncertainty in the performance vs safety conflict?
- Facilitation question 8: What evidence would reduce uncertainty in the performance vs safety conflict?
- Facilitation question 9: What evidence would reduce uncertainty in the performance vs safety conflict?
- Facilitation question 10: What evidence would reduce uncertainty in the performance vs safety conflict?
- Facilitation question 11: What evidence would reduce uncertainty in the performance vs safety conflict?
- Facilitation question 12: What evidence would reduce uncertainty in the performance vs safety conflict?

### Facilitating a workshop for Cost vs redundancy

- Facilitation question 1: What evidence would reduce uncertainty in the cost vs redundancy conflict?
- Facilitation question 2: What evidence would reduce uncertainty in the cost vs redundancy conflict?
- Facilitation question 3: What evidence would reduce uncertainty in the cost vs redundancy conflict?
- Facilitation question 4: What evidence would reduce uncertainty in the cost vs redundancy conflict?
- Facilitation question 5: What evidence would reduce uncertainty in the cost vs redundancy conflict?
- Facilitation question 6: What evidence would reduce uncertainty in the cost vs redundancy conflict?
- Facilitation question 7: What evidence would reduce uncertainty in the cost vs redundancy conflict?
- Facilitation question 8: What evidence would reduce uncertainty in the cost vs redundancy conflict?
- Facilitation question 9: What evidence would reduce uncertainty in the cost vs redundancy conflict?
- Facilitation question 10: What evidence would reduce uncertainty in the cost vs redundancy conflict?
- Facilitation question 11: What evidence would reduce uncertainty in the cost vs redundancy conflict?
- Facilitation question 12: What evidence would reduce uncertainty in the cost vs redundancy conflict?

### Facilitating a workshop for Software vs hardware

- Facilitation question 1: What evidence would reduce uncertainty in the software vs hardware conflict?
- Facilitation question 2: What evidence would reduce uncertainty in the software vs hardware conflict?
- Facilitation question 3: What evidence would reduce uncertainty in the software vs hardware conflict?
- Facilitation question 4: What evidence would reduce uncertainty in the software vs hardware conflict?
- Facilitation question 5: What evidence would reduce uncertainty in the software vs hardware conflict?
- Facilitation question 6: What evidence would reduce uncertainty in the software vs hardware conflict?
- Facilitation question 7: What evidence would reduce uncertainty in the software vs hardware conflict?
- Facilitation question 8: What evidence would reduce uncertainty in the software vs hardware conflict?
- Facilitation question 9: What evidence would reduce uncertainty in the software vs hardware conflict?
- Facilitation question 10: What evidence would reduce uncertainty in the software vs hardware conflict?
- Facilitation question 11: What evidence would reduce uncertainty in the software vs hardware conflict?
- Facilitation question 12: What evidence would reduce uncertainty in the software vs hardware conflict?

### Facilitating a workshop for OEM vs supplier

- Facilitation question 1: What evidence would reduce uncertainty in the oem vs supplier conflict?
- Facilitation question 2: What evidence would reduce uncertainty in the oem vs supplier conflict?
- Facilitation question 3: What evidence would reduce uncertainty in the oem vs supplier conflict?
- Facilitation question 4: What evidence would reduce uncertainty in the oem vs supplier conflict?
- Facilitation question 5: What evidence would reduce uncertainty in the oem vs supplier conflict?
- Facilitation question 6: What evidence would reduce uncertainty in the oem vs supplier conflict?
- Facilitation question 7: What evidence would reduce uncertainty in the oem vs supplier conflict?
- Facilitation question 8: What evidence would reduce uncertainty in the oem vs supplier conflict?
- Facilitation question 9: What evidence would reduce uncertainty in the oem vs supplier conflict?
- Facilitation question 10: What evidence would reduce uncertainty in the oem vs supplier conflict?
- Facilitation question 11: What evidence would reduce uncertainty in the oem vs supplier conflict?
- Facilitation question 12: What evidence would reduce uncertainty in the oem vs supplier conflict?

### Facilitating a workshop for Functional vs diagnostic requirement

- Facilitation question 1: What evidence would reduce uncertainty in the functional vs diagnostic requirement conflict?
- Facilitation question 2: What evidence would reduce uncertainty in the functional vs diagnostic requirement conflict?
- Facilitation question 3: What evidence would reduce uncertainty in the functional vs diagnostic requirement conflict?
- Facilitation question 4: What evidence would reduce uncertainty in the functional vs diagnostic requirement conflict?
- Facilitation question 5: What evidence would reduce uncertainty in the functional vs diagnostic requirement conflict?
- Facilitation question 6: What evidence would reduce uncertainty in the functional vs diagnostic requirement conflict?
- Facilitation question 7: What evidence would reduce uncertainty in the functional vs diagnostic requirement conflict?
- Facilitation question 8: What evidence would reduce uncertainty in the functional vs diagnostic requirement conflict?
- Facilitation question 9: What evidence would reduce uncertainty in the functional vs diagnostic requirement conflict?
- Facilitation question 10: What evidence would reduce uncertainty in the functional vs diagnostic requirement conflict?
- Facilitation question 11: What evidence would reduce uncertainty in the functional vs diagnostic requirement conflict?
- Facilitation question 12: What evidence would reduce uncertainty in the functional vs diagnostic requirement conflict?

### Facilitating a workshop for Safety vs cybersecurity

- Facilitation question 1: What evidence would reduce uncertainty in the safety vs cybersecurity conflict?
- Facilitation question 2: What evidence would reduce uncertainty in the safety vs cybersecurity conflict?
- Facilitation question 3: What evidence would reduce uncertainty in the safety vs cybersecurity conflict?
- Facilitation question 4: What evidence would reduce uncertainty in the safety vs cybersecurity conflict?
- Facilitation question 5: What evidence would reduce uncertainty in the safety vs cybersecurity conflict?
- Facilitation question 6: What evidence would reduce uncertainty in the safety vs cybersecurity conflict?
- Facilitation question 7: What evidence would reduce uncertainty in the safety vs cybersecurity conflict?
- Facilitation question 8: What evidence would reduce uncertainty in the safety vs cybersecurity conflict?
- Facilitation question 9: What evidence would reduce uncertainty in the safety vs cybersecurity conflict?
- Facilitation question 10: What evidence would reduce uncertainty in the safety vs cybersecurity conflict?
- Facilitation question 11: What evidence would reduce uncertainty in the safety vs cybersecurity conflict?
- Facilitation question 12: What evidence would reduce uncertainty in the safety vs cybersecurity conflict?

### Facilitating a workshop for Timing vs computational load

- Facilitation question 1: What evidence would reduce uncertainty in the timing vs computational load conflict?
- Facilitation question 2: What evidence would reduce uncertainty in the timing vs computational load conflict?
- Facilitation question 3: What evidence would reduce uncertainty in the timing vs computational load conflict?
- Facilitation question 4: What evidence would reduce uncertainty in the timing vs computational load conflict?
- Facilitation question 5: What evidence would reduce uncertainty in the timing vs computational load conflict?
- Facilitation question 6: What evidence would reduce uncertainty in the timing vs computational load conflict?
- Facilitation question 7: What evidence would reduce uncertainty in the timing vs computational load conflict?
- Facilitation question 8: What evidence would reduce uncertainty in the timing vs computational load conflict?
- Facilitation question 9: What evidence would reduce uncertainty in the timing vs computational load conflict?
- Facilitation question 10: What evidence would reduce uncertainty in the timing vs computational load conflict?
- Facilitation question 11: What evidence would reduce uncertainty in the timing vs computational load conflict?
- Facilitation question 12: What evidence would reduce uncertainty in the timing vs computational load conflict?

## Appendix F: Extended Metric Examples

### Metric drill-down: Requirement volatility

- Definition recap: The degree to which requirements are added, modified, or deleted over a defined period.
- Formula recap: Requirement Volatility (%) = ((Added + Modified + Deleted) / Total Baselined Requirements at Start of Period) x 100
- Example 1: Explain how requirement volatility would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 2: Explain how requirement volatility would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 3: Explain how requirement volatility would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 4: Explain how requirement volatility would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 5: Explain how requirement volatility would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 6: Explain how requirement volatility would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 7: Explain how requirement volatility would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 8: Explain how requirement volatility would change if one subsystem adds late regulatory changes while another subsystem remains stable.

### Metric drill-down: Requirement stability

- Definition recap: The complement of volatility; indicates how much of the requirement set remains unchanged during a period.
- Formula recap: Requirement Stability (%) = 100 - Requirement Volatility (%)
- Example 1: Explain how requirement stability would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 2: Explain how requirement stability would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 3: Explain how requirement stability would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 4: Explain how requirement stability would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 5: Explain how requirement stability would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 6: Explain how requirement stability would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 7: Explain how requirement stability would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 8: Explain how requirement stability would change if one subsystem adds late regulatory changes while another subsystem remains stable.

### Metric drill-down: Requirement coverage

- Definition recap: The proportion of requirements that have at least one valid downstream implementation and/or verification link, depending on project definition.
- Formula recap: Requirement Coverage (%) = (Number of Requirements with Required Downstream Links / Total Applicable Requirements) x 100
- Example 1: Explain how requirement coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 2: Explain how requirement coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 3: Explain how requirement coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 4: Explain how requirement coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 5: Explain how requirement coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 6: Explain how requirement coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 7: Explain how requirement coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 8: Explain how requirement coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.

### Metric drill-down: Traceability coverage

- Definition recap: The percentage of required trace links that actually exist across the chosen digital thread.
- Formula recap: Traceability Coverage (%) = (Established Required Links / Expected Required Links) x 100
- Example 1: Explain how traceability coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 2: Explain how traceability coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 3: Explain how traceability coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 4: Explain how traceability coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 5: Explain how traceability coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 6: Explain how traceability coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 7: Explain how traceability coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 8: Explain how traceability coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.

### Metric drill-down: Defect density

- Definition recap: The number of requirement defects identified relative to the size of the requirement set.
- Formula recap: Defect Density = Number of Requirement Defects / Number of Requirements
- Example 1: Explain how defect density would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 2: Explain how defect density would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 3: Explain how defect density would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 4: Explain how defect density would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 5: Explain how defect density would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 6: Explain how defect density would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 7: Explain how defect density would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 8: Explain how defect density would change if one subsystem adds late regulatory changes while another subsystem remains stable.

### Metric drill-down: Ambiguity rate

- Definition recap: The proportion of requirements containing ambiguous wording, undefined terms, or unclear conditions identified during review.
- Formula recap: Ambiguity Rate (%) = (Requirements Flagged as Ambiguous / Requirements Reviewed) x 100
- Example 1: Explain how ambiguity rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 2: Explain how ambiguity rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 3: Explain how ambiguity rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 4: Explain how ambiguity rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 5: Explain how ambiguity rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 6: Explain how ambiguity rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 7: Explain how ambiguity rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 8: Explain how ambiguity rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.

### Metric drill-down: Review defect rate

- Definition recap: The average number of defects found per requirement review or per reviewed requirement, depending on chosen normalization.
- Formula recap: Review Defect Rate = Number of Defects Found in Reviews / Number of Requirements Reviewed
- Example 1: Explain how review defect rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 2: Explain how review defect rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 3: Explain how review defect rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 4: Explain how review defect rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 5: Explain how review defect rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 6: Explain how review defect rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 7: Explain how review defect rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 8: Explain how review defect rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.

### Metric drill-down: Change rate

- Definition recap: The rate at which change requests are raised or approved over time for a requirement set.
- Formula recap: Change Rate = Number of Approved Requirement Changes / Time Period
- Example 1: Explain how change rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 2: Explain how change rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 3: Explain how change rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 4: Explain how change rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 5: Explain how change rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 6: Explain how change rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 7: Explain how change rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 8: Explain how change rate would change if one subsystem adds late regulatory changes while another subsystem remains stable.

### Metric drill-down: Test coverage

- Definition recap: The percentage of applicable requirements that are covered by at least one test case.
- Formula recap: Test Coverage (%) = (Requirements with At Least One Test Case / Total Testable Requirements) x 100
- Example 1: Explain how test coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 2: Explain how test coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 3: Explain how test coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 4: Explain how test coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 5: Explain how test coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 6: Explain how test coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 7: Explain how test coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 8: Explain how test coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.

### Metric drill-down: Verification coverage

- Definition recap: The percentage of applicable requirements for which verification has been executed and a verdict recorded.
- Formula recap: Verification Coverage (%) = (Requirements with Executed Verification Evidence / Total Applicable Requirements) x 100
- Example 1: Explain how verification coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 2: Explain how verification coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 3: Explain how verification coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 4: Explain how verification coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 5: Explain how verification coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 6: Explain how verification coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 7: Explain how verification coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 8: Explain how verification coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.

### Metric drill-down: Validation coverage

- Definition recap: The percentage of stakeholder or system-level expectations that have been validated in representative operational conditions.
- Formula recap: Validation Coverage (%) = (Validated Stakeholder/System Requirements / Total Stakeholder/System Requirements Planned for Validation) x 100
- Example 1: Explain how validation coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 2: Explain how validation coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 3: Explain how validation coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 4: Explain how validation coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 5: Explain how validation coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 6: Explain how validation coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 7: Explain how validation coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.
- Example 8: Explain how validation coverage would change if one subsystem adds late regulatory changes while another subsystem remains stable.

## Appendix G: Extended Requirement Quality Exercises

### Exercise set: Ambiguous requirement

- Exercise 1: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.
- Exercise 2: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.
- Exercise 3: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.
- Exercise 4: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.
- Exercise 5: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.
- Exercise 6: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.
- Exercise 7: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.
- Exercise 8: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.
- Exercise 9: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.
- Exercise 10: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.
- Exercise 11: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.
- Exercise 12: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.
- Exercise 13: Rewrite a poor automotive requirement so that the ambiguous requirement issue is removed, and define how you would review the correction.

### Exercise set: Incomplete requirement

- Exercise 1: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.
- Exercise 2: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.
- Exercise 3: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.
- Exercise 4: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.
- Exercise 5: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.
- Exercise 6: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.
- Exercise 7: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.
- Exercise 8: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.
- Exercise 9: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.
- Exercise 10: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.
- Exercise 11: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.
- Exercise 12: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.
- Exercise 13: Rewrite a poor automotive requirement so that the incomplete requirement issue is removed, and define how you would review the correction.

### Exercise set: Contradictory requirement

- Exercise 1: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.
- Exercise 2: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.
- Exercise 3: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.
- Exercise 4: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.
- Exercise 5: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.
- Exercise 6: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.
- Exercise 7: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.
- Exercise 8: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.
- Exercise 9: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.
- Exercise 10: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.
- Exercise 11: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.
- Exercise 12: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.
- Exercise 13: Rewrite a poor automotive requirement so that the contradictory requirement issue is removed, and define how you would review the correction.

### Exercise set: Non-testable requirement

- Exercise 1: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.
- Exercise 2: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.
- Exercise 3: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.
- Exercise 4: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.
- Exercise 5: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.
- Exercise 6: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.
- Exercise 7: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.
- Exercise 8: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.
- Exercise 9: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.
- Exercise 10: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.
- Exercise 11: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.
- Exercise 12: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.
- Exercise 13: Rewrite a poor automotive requirement so that the non-testable requirement issue is removed, and define how you would review the correction.

### Exercise set: Over-constrained requirement

- Exercise 1: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.
- Exercise 2: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.
- Exercise 3: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.
- Exercise 4: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.
- Exercise 5: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.
- Exercise 6: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.
- Exercise 7: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.
- Exercise 8: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.
- Exercise 9: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.
- Exercise 10: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.
- Exercise 11: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.
- Exercise 12: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.
- Exercise 13: Rewrite a poor automotive requirement so that the over-constrained requirement issue is removed, and define how you would review the correction.

### Exercise set: Under-specified requirement

- Exercise 1: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.
- Exercise 2: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.
- Exercise 3: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.
- Exercise 4: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.
- Exercise 5: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.
- Exercise 6: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.
- Exercise 7: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.
- Exercise 8: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.
- Exercise 9: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.
- Exercise 10: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.
- Exercise 11: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.
- Exercise 12: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.
- Exercise 13: Rewrite a poor automotive requirement so that the under-specified requirement issue is removed, and define how you would review the correction.

### Exercise set: Implementation-specific requirement

- Exercise 1: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.
- Exercise 2: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.
- Exercise 3: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.
- Exercise 4: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.
- Exercise 5: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.
- Exercise 6: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.
- Exercise 7: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.
- Exercise 8: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.
- Exercise 9: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.
- Exercise 10: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.
- Exercise 11: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.
- Exercise 12: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.
- Exercise 13: Rewrite a poor automotive requirement so that the implementation-specific requirement issue is removed, and define how you would review the correction.

### Exercise set: Duplicate requirement

- Exercise 1: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
- Exercise 2: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
- Exercise 3: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
- Exercise 4: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
- Exercise 5: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
- Exercise 6: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
- Exercise 7: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
- Exercise 8: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
- Exercise 9: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
- Exercise 10: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
- Exercise 11: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
- Exercise 12: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
- Exercise 13: Rewrite a poor automotive requirement so that the duplicate requirement issue is removed, and define how you would review the correction.
