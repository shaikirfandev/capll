from __future__ import annotations

from pathlib import Path
import csv
import json
import textwrap


ROOT = Path("MG_HECTOR_INFOTAINMENT_VALIDATION")
INDEX = ROOT / "MODULE_INDEX.csv"


REQUIRED_RELATIVE_FILES = [
    "README.md",
    "00_MODULE_OVERVIEW.md",
    "01_theory_notes.md",
    "02_bench_setup_diagrams.md",
    "03_canoe_configuration_examples.md",
    "04_OEM_VALIDATION_LAB_MANUAL.md",
    "05_REQUIREMENT_SPECIFICATION.md",
    "06_FAILURE_INJECTION_MATRIX.csv",
    "07_EVIDENCE_COLLECTION_CHECKLIST.md",
    "08_RELEASE_READINESS_GATE.md",
    "09_INTERVIEW_STAR_SCENARIOS.md",
    "10_DAILY_PRACTICE_TASKS.md",
    "PERFORMANCE_OPTIMIZATION.md",
    "production_issue_examples.md",
    "capl/{slug}_simulation.can",
    "python/{slug}_automation.py",
    "logs/{slug}_sample_can.asc",
    "uds/{slug}_uds_examples.md",
    "test_cases/{slug}_test_cases.csv",
    "workflows/oem_validation_workflow.md",
    "debugging/debugging_scenarios.md",
    "debugging/root_cause_analysis.md",
    "interview/interview_questions.md",
    "reports/validation_report_template.md",
    "traceability/requirements_traceability.csv",
    "signals/vehicle_signal_examples.csv",
    "requirements/{slug}_requirements.csv",
    "labs/{slug}_bench_lab.md",
    "evidence/{slug}_evidence_manifest.md",
    "automation/{slug}_automation_plan.md",
    "release/{slug}_release_signoff.md",
]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def load_modules() -> list[dict[str, str]]:
    with INDEX.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def slug(folder: str) -> str:
    return folder.lower()


def overview(folder: str, title: str, focus: str) -> str:
    return f"""
    # Module Overview: {title}

    ## Purpose

    This module turns `{title}` into a production validation work package. The focus is {focus}. The expected learner output is not only theoretical understanding, but the ability to run a bench-level validation activity, collect evidence, explain failures, and defend the result in an OEM release review.

    ## Definition Of Complete

    - You can explain the feature or domain architecture in IVI terms.
    - You can identify the vehicle signals, diagnostics, Android/Linux services and user-facing outputs involved.
    - You can configure CANoe monitoring or rest bus simulation for the relevant state.
    - You can execute nominal, negative, boundary, recovery and stress tests.
    - You can collect synchronized CANoe, diagnostic, Android/Linux and visual evidence.
    - You can produce a release-quality defect report and RCA.
    - You can answer senior interview questions using this module as a real project example.

    ## MG Hector-Style Context

    Use this as a representative MG Hector connected-SUV infotainment bench. Replace the training DBC, DIDs, timing and topology with released program data on a real project. The workflow remains the same: requirement review, bench setup, CANoe/CAPL simulation, execution, evidence, RCA, regression and sign-off.

    ## Interfaces To Check

    | Layer | What To Verify |
    | --- | --- |
    | Power | KL30, KL15, ACC, crank, sleep and wake behavior |
    | CAN | cyclic message presence, signal scaling, timeout, alive counter |
    | Diagnostics | software DID, DTC status, session behavior, negative response |
    | Android/Linux | service state, logcat, kernel, process health, memory |
    | User Output | UI, audio, video, warnings, responsiveness and persistence |
    | Automation | repeatability, evidence naming, verdict traceability |
    """


def lab_manual(folder: str, title: str, focus: str) -> str:
    return f"""
    # OEM Validation Lab Manual: {title}

    ## Lab Objective

    Validate {title.lower()} on an MG Hector-style IVI bench using CANoe, CAPL, Python, adb/logcat and UDS diagnostics.

    ## Equipment

    - IVI head unit or software bench equivalent.
    - Programmable 12 V DC supply with current limit.
    - Vector VN interface and CANoe.
    - Bench harness with KL30, KL15, ACC, GND, CAN-H, CAN-L and required peripherals.
    - Android reference phone, iPhone reference device, USB media, camera simulator or media converter when relevant.
    - Automation PC with Python, pytest and adb.

    ## Pre-Execution Checklist

    1. Confirm bench ID, harness revision and power supply current limit.
    2. Start CANoe and load the representative or project DBC.
    3. Verify no critical DTC is present before stimulus.
    4. Capture software version DID and build fingerprint.
    5. Start synchronized CANoe logging and Android/Linux logging.

    ## Execution Flow

    1. Set bench to a known state: KL30 on, KL15 off, CANoe measurement stopped.
    2. Start CANoe measurement and rest bus simulation.
    3. Apply KL15/IGN and wait for IVI ready.
    4. Execute the nominal test path for {title.lower()}.
    5. Execute at least three fault injections from `06_FAILURE_INJECTION_MATRIX.csv`.
    6. Execute one recovery path: sleep/wakeup, reconnect, reset or ignition cycle.
    7. Read DTCs and capture post-test software/service state.
    8. Fill report and traceability artifacts.

    ## Pass Criteria

    - Functional result matches requirement.
    - No critical crash, boot loop, stale state, blocked UI or unexpected DTC.
    - Performance KPI is measured or explicitly marked not applicable.
    - Evidence is sufficient for a third-party reviewer to reproduce and understand the result.

    ## Common Bench Mistakes

    - Running a feature test before IVI boot readiness is stable.
    - Trusting CANoe physical output without checking channel mapping.
    - Filing a software defect before proving the simulated ECU signal is correct.
    - Missing pre-fault and post-fault DTC snapshots.
    - Capturing logs without build ID, bench ID or timestamp.
    """


def requirements_md(folder: str, title: str, focus: str) -> str:
    prefix = folder[:2]
    return f"""
    # Requirement Specification: {title}

    ## Functional Requirements

    | Req ID | Requirement | Verification Method | Priority |
    | --- | --- | --- | --- |
    | MGH-{prefix}-FUNC-001 | The IVI shall support the defined {title.lower()} behavior in IGN mode. | Bench functional test | P0 |
    | MGH-{prefix}-FUNC-002 | The IVI shall preserve a valid user-visible state after sleep/wakeup where applicable. | Recovery test | P1 |
    | MGH-{prefix}-FUNC-003 | The IVI shall handle unavailable dependency inputs without crash or undefined UI. | Fault injection | P0 |

    ## Diagnostic Requirements

    | Req ID | Requirement | Verification Method | Priority |
    | --- | --- | --- | --- |
    | MGH-{prefix}-DIAG-001 | The IVI shall expose software identification through approved DIDs. | UDS DID read | P0 |
    | MGH-{prefix}-DIAG-002 | The IVI shall set or suppress DTCs according to the diagnostic specification during {title.lower()} faults. | DTC test | P1 |

    ## Performance Requirements

    | Req ID | Requirement | Verification Method | Priority |
    | --- | --- | --- | --- |
    | MGH-{prefix}-PERF-001 | User-visible response latency shall meet the feature KPI or documented target. | Timed measurement | P1 |
    | MGH-{prefix}-PERF-002 | The feature shall not cause memory, CPU, thread or file descriptor growth during stress execution. | Stress monitoring | P1 |

    ## Evidence Requirements

    Every passed or failed result must include CAN trace, test report, relevant IVI logs and diagnostic snapshot unless marked not applicable with reviewer approval.
    """


def failure_matrix(title: str) -> str:
    return """FaultID,Fault_Type,Injection_Method,Expected_IVI_Behavior,Expected_Diagnostic_Behavior,Evidence
FI-001,Missing cyclic CAN input,Stop related rest bus message in CANoe,Graceful timeout handling no crash,DTC set if specified,CANoe trace plus DTC read
FI-002,Invalid signal range,Transmit out-of-range or invalid enum value,Ignore or fallback to safe default,NRC/DTC per spec,CAN trace logcat
FI-003,Power interruption,Toggle KL15 or apply low-voltage profile,No corruption defined recovery,No unexpected permanent DTC,Power log CAN trace
FI-004,Peripheral disconnect,Disconnect USB phone camera audio or network dependency,User-visible recovery message,DTC only if specified,Kernel log logcat screen
FI-005,High load condition,Run bus load or app stress while feature active,No ANR boot loop or permanent degradation,No critical DTC,Performance logs
FI-006,Sleep/wakeup transition,Enter sleep during active feature then wake,State restored or reset as requirement defines,DTC behavior per spec,CAN wake trace logcat
"""


def evidence_checklist(title: str) -> str:
    return f"""
    # Evidence Collection Checklist: {title}

    ## Mandatory Evidence

    - CANoe BLF or ASC with 10 seconds before and after stimulus.
    - CANoe XML/PDF test report or pytest report.
    - Software version DID and build fingerprint.
    - Pre-test and post-test DTC snapshot.
    - Android logcat for the complete test window.
    - Kernel/system logs if USB, camera, audio, Ethernet, boot or power behavior is involved.
    - Screenshot or video for user-visible IVI behavior.
    - Bench metadata: bench ID, tester, build, DBC, harness revision and date.

    ## Evidence Naming

    `MGH_BENCH_01_<BuildID>_{title.replace(" ", "_")}_<TestID>_<YYYYMMDD_HHMMSS>`

    ## Reviewer Questions The Evidence Must Answer

    1. What exact stimulus was applied?
    2. What did the IVI receive on the vehicle network?
    3. What did the IVI show, play, publish or diagnose?
    4. Was the failure reproducible?
    5. Which layer is most likely responsible?
    """


def release_gate(title: str) -> str:
    return f"""
    # Release Readiness Gate: {title}

    ## Entry Gate

    - Requirements reviewed and baselined.
    - CANoe configuration and DBC version recorded.
    - Bench health check passed.
    - Known issues reviewed.
    - Test data and reference devices available.

    ## Exit Gate

    | Gate | Required State |
    | --- | --- |
    | P0 tests | 100% pass or formal deviation |
    | P1 tests | pass or approved risk |
    | Critical defects | zero open |
    | DTC baseline | no unexpected active DTC |
    | Regression | executed after every fix |
    | Evidence | complete and traceable |

    ## Go/No-Go Questions

    - Can this feature fail in a way visible to the customer?
    - Does the failure affect legal, safety, camera, call, navigation or warning behavior?
    - Is there a known workaround?
    - Can the defect escape to vehicle integration or production?
    """


def star_scenarios(title: str) -> str:
    return f"""
    # Interview STAR Scenarios: {title}

    ## Scenario 1: Bench Issue Isolated From Software Issue

    Situation: {title} failed during bench execution.
    Task: Prove whether the issue was IVI software, bench simulation or peripheral setup.
    Action: Compared CANoe trace, DBC scaling, diagnostic state and Android/Linux logs against a known-good run.
    Result: Identified the failing layer and prevented an incorrect defect assignment.

    ## Scenario 2: Production Defect RCA

    Situation: A customer-visible failure appeared intermittently.
    Task: Reproduce and provide release-board-quality RCA.
    Action: Built a repeatable CANoe/CAPL stimulus, collected synchronized evidence and quantified reproduction rate.
    Result: Delivered actionable defect report with suspected module and regression test.

    ## Scenario 3: Automation Improvement

    Situation: Manual validation consumed too much bench time.
    Task: Automate repeatable checks for {title.lower()}.
    Action: Added pytest/CANoe/adb orchestration with evidence manifest and clear pass/fail thresholds.
    Result: Reduced execution time and improved regression reliability.
    """


def practice_tasks(title: str) -> str:
    return f"""
    # Daily Practice Tasks: {title}

    1. Draw the signal and service path for {title.lower()} from vehicle input to IVI output.
    2. Decode five CAN trace lines relevant to this module.
    3. Write one CAPL function that stimulates the main dependency.
    4. Write one Python check that parses evidence and returns pass/fail.
    5. Read one DID and explain why it matters.
    6. Inject one fault and document expected DTC behavior.
    7. Create one defect report from a simulated failure.
    8. Answer one interview question using STAR format.
    """


def req_csv(folder: str, title: str) -> str:
    prefix = folder[:2]
    return f"""RequirementID,ASIL_or_QM,Requirement,Priority,Verification,LinkedTest
MGH-{prefix}-FUNC-001,QM,{title} nominal behavior shall work in IGN mode,P0,Bench functional test,TC_FUNC_001
MGH-{prefix}-NEG-001,QM,{title} shall handle invalid or missing dependency input gracefully,P0,Fault injection,TC_NEG_001
MGH-{prefix}-REC-001,QM,{title} shall recover after sleep wake or reconnect where applicable,P1,Recovery test,TC_REC_001
MGH-{prefix}-DIAG-001,QM,{title} diagnostic identification and DTC behavior shall match diagnostic spec,P1,UDS test,TC_DIAG_001
MGH-{prefix}-PERF-001,QM,{title} user-visible latency shall meet KPI,P1,Performance test,TC_PERF_001
"""


def bench_lab(folder: str, title: str) -> str:
    return f"""
    # Bench Lab: {title}

    ## Lab Steps

    1. Load `CANoe_Project/Databases/MG_Hector_IVI_Training.dbc`.
    2. Start rest bus simulation.
    3. Set power mode to IGN.
    4. Verify IVI heartbeat and boot state.
    5. Execute the module-specific nominal stimulus.
    6. Execute one negative stimulus and one recovery stimulus.
    7. Capture evidence and update traceability.

    ## Expected Artifacts

    - Completed test case CSV row.
    - CAN trace.
    - Logcat/kernel evidence if applicable.
    - UDS DID/DTC snapshot.
    - RCA note for any failure.
    - Release gate decision.
    """


def evidence_manifest(title: str) -> str:
    return f"""
    # Evidence Manifest: {title}

    | Artifact | Required | Example Path |
    | --- | --- | --- |
    | CAN trace | Yes | `evidence/can/<test_id>.blf` |
    | CANoe report | Yes | `evidence/reports/<test_id>.xml` |
    | adb logcat | Conditional | `evidence/android/<test_id>_logcat.txt` |
    | Kernel log | Conditional | `evidence/linux/<test_id>_dmesg.txt` |
    | UDS readout | Yes | `evidence/diagnostics/<test_id>_uds.txt` |
    | Screen/video | Conditional | `evidence/video/<test_id>.mp4` |
    | RCA | On failure | `debugging/root_cause_analysis.md` |
    """


def automation_plan(title: str) -> str:
    return f"""
    # Automation Plan: {title}

    ## Automatable Checks

    - Start/stop CANoe measurement.
    - Set power mode, gear, speed and feature-specific system variables.
    - Collect CAN traces and adb logs.
    - Read software DID and DTC status.
    - Parse result evidence and generate markdown/JUnit reports.

    ## Suggested pytest Names

    - `test_{title.lower().replace(" ", "_")}_smoke`
    - `test_{title.lower().replace(" ", "_")}_negative_missing_signal`
    - `test_{title.lower().replace(" ", "_")}_sleep_wakeup_recovery`
    - `test_{title.lower().replace(" ", "_")}_stress_cycles`

    ## Manual Review Remains Needed For

    - Visual UI correctness.
    - Audio quality.
    - Camera image quality.
    - User experience wording.
    - Any safety or legal warning behavior.
    """


def release_signoff(title: str) -> str:
    return f"""
    # Release Sign-Off: {title}

    | Field | Value |
    | --- | --- |
    | Feature/Module | {title} |
    | Build | TBD |
    | Bench | TBD |
    | DBC | TBD |
    | CANoe Config | TBD |
    | Tester | TBD |

    ## Results

    | Category | Pass | Fail | Blocked | Notes |
    | --- | ---: | ---: | ---: | --- |
    | Smoke |  |  |  |  |
    | Functional |  |  |  |  |
    | Negative |  |  |  |  |
    | Recovery |  |  |  |  |
    | Stress |  |  |  |  |
    | Diagnostics |  |  |  |  |

    ## Decision

    - Go:
    - No-Go:
    - Conditional Go:

    ## Reviewer Notes

    Attach links to evidence and defects before release review.
    """


def update_root_manifest(modules: list[dict[str, str]], audit: dict[str, object]) -> None:
    lines = [
        "# Completion Audit",
        "",
        "This audit defines the completion contract for every numbered module.",
        "",
        f"- Numbered modules checked: {len(modules)}",
        f"- Required artifacts per module: {len(REQUIRED_RELATIVE_FILES)}",
        f"- Modules passing artifact contract: {audit['modules_passed']}",
        f"- Missing artifacts: {audit['missing_count']}",
        "",
        "## Required Artifact Contract",
        "",
    ]
    for item in REQUIRED_RELATIVE_FILES:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Module Results", ""])
    for module in audit["modules"]:
        status = "PASS" if not module["missing"] else "FAIL"
        lines.append(f"- `{module['folder']}`: {status}, files={module['file_count']}, missing={len(module['missing'])}")
    write(ROOT / "COMPLETION_AUDIT.md", "\n".join(lines) + "\n")


def main() -> None:
    modules = load_modules()
    audit_modules = []
    for module in modules:
        folder = module["Folder"]
        title = module["Title"]
        focus = module["Focus"]
        s = slug(folder)
        base = ROOT / folder

        write(base / "00_MODULE_OVERVIEW.md", overview(folder, title, focus))
        write(base / "04_OEM_VALIDATION_LAB_MANUAL.md", lab_manual(folder, title, focus))
        write(base / "05_REQUIREMENT_SPECIFICATION.md", requirements_md(folder, title, focus))
        write(base / "06_FAILURE_INJECTION_MATRIX.csv", failure_matrix(title))
        write(base / "07_EVIDENCE_COLLECTION_CHECKLIST.md", evidence_checklist(title))
        write(base / "08_RELEASE_READINESS_GATE.md", release_gate(title))
        write(base / "09_INTERVIEW_STAR_SCENARIOS.md", star_scenarios(title))
        write(base / "10_DAILY_PRACTICE_TASKS.md", practice_tasks(title))
        write(base / "requirements" / f"{s}_requirements.csv", req_csv(folder, title))
        write(base / "labs" / f"{s}_bench_lab.md", bench_lab(folder, title))
        write(base / "evidence" / f"{s}_evidence_manifest.md", evidence_manifest(title))
        write(base / "automation" / f"{s}_automation_plan.md", automation_plan(title))
        write(base / "release" / f"{s}_release_signoff.md", release_signoff(title))

        missing = []
        for rel in REQUIRED_RELATIVE_FILES:
            rel_path = rel.format(slug=s)
            if not (base / rel_path).exists():
                missing.append(rel_path)
        audit_modules.append(
            {
                "folder": folder,
                "file_count": sum(1 for p in base.rglob("*") if p.is_file()),
                "missing": missing,
            }
        )

    audit = {
        "modules_checked": len(modules),
        "required_artifacts_per_module": len(REQUIRED_RELATIVE_FILES),
        "modules_passed": sum(1 for m in audit_modules if not m["missing"]),
        "missing_count": sum(len(m["missing"]) for m in audit_modules),
        "modules": audit_modules,
    }
    write(ROOT / "COMPLETION_AUDIT.json", json.dumps(audit, indent=2))
    update_root_manifest(modules, audit)


if __name__ == "__main__":
    main()
