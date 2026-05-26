# Test Manager Complete Playbook

## Purpose

This document defines the responsibilities, daily operating rhythm, monthly handling, governance model and execution checklist for a Test Manager leading an Automotive Infotainment Validation program such as an MG Hector-style IVI validation project.

The Test Manager is accountable for converting requirements, builds, benches, tools, people and defects into a controlled validation release decision. The role is not only tracking test cases. It is ownership of validation readiness, execution quality, defect truth, risk visibility, evidence completeness and release confidence.

## Role Summary

The Test Manager owns the validation program across planning, execution, reporting and release support.

Primary mission:

- Ensure the infotainment system is validated against requirements, customer use cases and OEM release gates.
- Ensure the team has clear priorities every day.
- Ensure defects are real, reproducible, well-triaged and visible to the right owners.
- Ensure test evidence is complete enough for OEM, Tier1, engineering and management decisions.
- Ensure validation coverage improves release by release.

## Core Responsibilities

### Test Planning

- Understand OEM requirements, system specifications, diagnostic specifications, DBC/ARXML updates and feature change requests.
- Convert requirements into validation scope, test cases, traceability matrix and execution plan.
- Define test levels: bench, SIL, HIL, vehicle, regression, sanity, smoke, endurance and release validation.
- Identify required benches, devices, phones, cables, cameras, CANoe configurations, software builds and diagnostic access.
- Define entry and exit criteria for every test cycle.
- Create feature-wise validation ownership for IVI, Bluetooth, WiFi, USB, projection, audio, navigation, camera, cluster, steering switch, HVAC, OTA, diagnostics and power modes.

### Execution Management

- Assign daily tasks to validation engineers.
- Track execution status by feature, build, bench and priority.
- Remove blockers such as bench unavailability, missing builds, DBC mismatch, phone/device shortage or unclear requirements.
- Ensure all failures have logs, traces, screenshots, videos, DTC readouts and reproduction steps.
- Ensure sanity, smoke and regression are executed in the correct order.
- Prevent random testing by enforcing planned execution and evidence discipline.

### Defect Governance

- Review every major defect before it is escalated.
- Ensure defect quality: title, environment, steps, expected result, actual result, reproduction rate, logs and suspected layer.
- Run defect triage with development, systems, diagnostics, Android, connectivity, audio, camera and vehicle network owners.
- Track defect aging, severity, priority, fix version and retest status.
- Separate real product defects from bench issues, setup mistakes, requirement gaps and duplicate reports.
- Maintain open defect risk summary for management and release boards.

### People Management

- Allocate engineers based on skill: CANoe, CAPL, Android, diagnostics, Bluetooth, camera, automation, vehicle integration.
- Mentor junior engineers on evidence collection, RCA and OEM communication.
- Review test cases and defect reports written by team members.
- Build backup ownership so one person’s absence does not block a feature.
- Track workload, weekend support, night test requirements and bench rotation fairly.

### Stakeholder Management

- Communicate status clearly to OEM, Tier1, software teams, program managers and leadership.
- Highlight risk early, not at release deadline.
- Translate technical issues into business/release impact.
- Defend validation results with evidence.
- Escalate blockers with exact ask, owner and deadline.

### Release Governance

- Define release readiness based on test coverage, pass rate, open defects, critical risks and regression status.
- Approve or reject build promotion from sanity to full validation.
- Prepare validation summary for release board.
- Maintain go/no-go recommendation with evidence.
- Ensure known issues, deviations and waivers are documented.

## Day-To-Day Responsibilities

## Daily Start Of Day

The Test Manager should begin every day with a structured validation control check.

### 1. Build And Bench Readiness

Check:

- Which software build is under test today?
- Is the build flashed on all required benches?
- Are CANoe configuration, DBC, diagnostic files and test scripts aligned with the build?
- Are all benches powered, connected and usable?
- Are phones, USB devices, cameras, Ethernet tools and diagnostic tools available?
- Are any benches blocked by hardware failure, harness issue or license problem?

Output:

- Daily bench availability list.
- Build readiness confirmation.
- Immediate blocker list.

### 2. Review Previous Day Status

Review:

- Test cases executed.
- Passed, failed, blocked and not run count.
- New defects raised.
- Defects rejected or reopened.
- Logs missing from failed cases.
- Retests pending after new fixes.

Output:

- Yesterday’s execution closure.
- Carry-forward items for today.

### 3. Conduct Daily Stand-Up

Keep the stand-up short and execution-focused.

Each engineer reports:

- What was completed yesterday?
- What will be tested today?
- What is blocked?
- Which defects need triage?
- Which logs or evidence are pending?

The Test Manager confirms:

- Today’s top priorities.
- Bench assignments.
- Feature owners.
- Expected end-of-day deliverables.

### 4. Prioritize Daily Execution

Recommended priority order:

1. Build sanity and smoke validation.
2. Critical retests for release-blocking defects.
3. P0/P1 functional validation.
4. Regression around recent fixes.
5. Diagnostics and DTC verification.
6. Stress, endurance and long-duration tests.
7. Exploratory validation for high-risk areas.

### 5. Monitor Execution During The Day

The Test Manager should not wait until evening for status.

Check every few hours:

- Are engineers executing planned cases?
- Are failures being captured correctly?
- Are benches idle while people wait for decisions?
- Are repeated failures pointing to a common build issue?
- Is any test invalid due to wrong setup or wrong DBC?
- Are critical issues communicated immediately?

### 6. Review New Defects

Every new serious defect should be reviewed before escalation.

Defect quality checklist:

- Clear title.
- Correct feature/component.
- Correct build and bench details.
- Exact steps to reproduce.
- Expected and actual result.
- Reproduction rate.
- CANoe trace attached.
- Android logcat attached if applicable.
- Screenshot/video attached for UI/camera issues.
- UDS DTC snapshot attached if relevant.
- First-level RCA included.

### 7. Run Defect Triage

Daily triage should cover:

- New critical defects.
- Blocker defects.
- Defects awaiting owner assignment.
- Defects needing more logs.
- Retest-ready defects.
- Reopened defects.
- Duplicate or invalid defects.

Triage output:

- Owner.
- Next action.
- Target fix build.
- Retest owner.
- Risk category.

### 8. Update Dashboards

Daily dashboard should show:

- Total planned test cases.
- Executed test cases.
- Pass/fail/blocked/not run.
- Feature-wise progress.
- Build-wise defect trend.
- Open critical defects.
- Retest pending.
- Bench availability.
- Automation execution status.
- Release risk summary.

### 9. End Of Day Closure

Before finishing the day:

- Confirm all executed test results are updated.
- Confirm all failed cases have evidence.
- Confirm all defects are raised or linked.
- Confirm blocked cases have blocker reason and owner.
- Confirm long-duration tests are running correctly.
- Send daily status report.

## Daily Status Report Format

```text
Subject: Daily IVI Validation Status - Build <Build ID> - <Date>

1. Build Under Test:
2. Benches Used:
3. Execution Summary:
   Planned:
   Executed:
   Passed:
   Failed:
   Blocked:

4. Feature Status:
   IVI Features:
   Bluetooth:
   USB:
   Projection:
   Reverse Camera:
   Cluster:
   Diagnostics:
   OTA:
   Power Modes:

5. New Defects:
6. Critical/Open Blockers:
7. Retest Completed:
8. Risks:
9. Support Required:
10. Plan For Tomorrow:
```

## Weekly Responsibilities

### Weekly Planning

- Review upcoming build plan.
- Confirm validation scope for the week.
- Freeze weekly test priorities.
- Allocate benches and engineers.
- Confirm phones, devices, cables and lab equipment.
- Review pending requirement clarifications.

### Weekly Review

Review with stakeholders:

- Execution progress.
- Open defects by severity.
- Defect aging.
- Feature readiness.
- Automation coverage.
- Bench utilization.
- Requirement coverage.
- Release risks.

### Weekly Test Case Review

Check:

- Are new requirements covered?
- Are negative and boundary cases included?
- Are regression cases updated after defects?
- Are automation candidates identified?
- Are obsolete cases removed or marked inactive?

### Weekly Defect Aging Review

Track:

- Defects open more than 7 days.
- Critical defects without owner.
- Defects fixed but not retested.
- Reopened defects.
- Defects blocked due to missing logs.
- Requirement clarification defects.

### Weekly Automation Review

Review:

- Automated tests executed.
- Automation failures.
- False failures.
- New automation candidates.
- CANoe/CAPL script stability.
- Python/pytest framework stability.
- CI integration status.

## Month-By-Month Handling

## Month 1: Program Understanding And Setup

Focus:

- Understand product scope, architecture, features and release plan.
- Establish validation process and team structure.
- Prepare benches, tools and test assets.

Key responsibilities:

- Collect all requirements, specifications, DBC files, diagnostic specs and feature documents.
- Identify stakeholders and feature owners.
- Define validation scope by feature.
- Build master test plan.
- Build requirement traceability matrix.
- Review existing test cases.
- Identify missing test areas.
- Confirm bench architecture and lab readiness.
- Define defect workflow and severity rules.
- Define reporting templates.

Deliverables:

- Master validation plan.
- Feature-wise test strategy.
- Bench readiness checklist.
- Requirement traceability matrix baseline.
- Defect management process.
- Daily and weekly reporting format.

## Month 2: Test Design And Bench Stabilization

Focus:

- Complete test case design.
- Stabilize bench setup.
- Create CANoe/CAPL simulation baseline.

Key responsibilities:

- Review test cases for all major features.
- Add negative, boundary, recovery and stress cases.
- Validate CANoe configuration.
- Validate rest bus simulation.
- Confirm diagnostic DID and DTC access.
- Prepare reference phone/device matrix.
- Finalize automation candidates.
- Run dry execution on sample builds.

Deliverables:

- Reviewed test case repository.
- Stable CANoe bench configuration.
- CAPL simulation baseline.
- Diagnostic smoke procedure.
- Device compatibility matrix.
- Automation backlog.

## Month 3: First Full Validation Cycle

Focus:

- Execute first full validation cycle on integrated build.
- Establish defect baseline.

Key responsibilities:

- Run smoke and sanity validation.
- Execute P0/P1 functional test cases.
- Track all failures with complete evidence.
- Conduct daily defect triage.
- Separate setup issues from product defects.
- Identify unstable features.
- Report feature readiness weekly.

Deliverables:

- Full cycle execution report.
- Open defect list.
- Feature readiness dashboard.
- Risk register.
- Updated RTM.

## Month 4: Regression And Deeper Integration

Focus:

- Validate fixes.
- Expand integration testing across features.

Key responsibilities:

- Execute retests on fixed defects.
- Run regression around changed modules.
- Validate cross-feature behavior such as audio focus, camera priority, projection interruption and power transitions.
- Track reopened defects.
- Update test cases based on defects found.
- Improve automation for stable regression cases.

Deliverables:

- Regression report.
- Retest closure report.
- Cross-feature integration report.
- Updated automation suite.
- Defect trend analysis.

## Month 5: Stress, Performance And Reliability

Focus:

- Validate long-duration stability and performance KPIs.

Key responsibilities:

- Plan endurance tests.
- Run boot cycle tests.
- Run Bluetooth reconnect stress.
- Run USB/projection connect-disconnect stress.
- Run reverse camera repeated activation.
- Monitor CPU, memory, boot time and UI latency.
- Track memory leak and stability defects.
- Validate sleep current and wakeup behavior.

Deliverables:

- Stress test report.
- Performance KPI report.
- Memory and stability analysis.
- Power mode validation report.
- Reliability defect list.

## Month 6: Release Candidate Validation

Focus:

- Validate release candidate and prepare go/no-go recommendation.

Key responsibilities:

- Freeze validation scope.
- Execute release regression.
- Verify all critical fixes.
- Confirm no unexpected active DTCs.
- Review known issues and waivers.
- Confirm evidence completeness.
- Prepare release sign-off report.
- Present risk to release board.

Deliverables:

- Release validation report.
- Go/no-go recommendation.
- Known issue list.
- Waiver/deviation list.
- Final defect summary.
- Release board presentation.

## Repeating Monthly Cycle After SOP Or Continuous Releases

For every monthly or sprint-based release:

1. Review change list.
2. Perform impact analysis.
3. Update regression scope.
4. Confirm test environment.
5. Execute sanity.
6. Execute impacted feature validation.
7. Execute regression.
8. Validate fixes.
9. Update metrics.
10. Publish release recommendation.

## Feature Ownership Matrix

| Feature Area | Test Manager Responsibility |
| --- | --- |
| IVI UI | Ensure functional, usability, language, responsiveness and persistence coverage |
| Bluetooth | Ensure phone matrix, reconnect, call, A2DP, PBAP and stress coverage |
| WiFi | Ensure hotspot, client mode, throughput and recovery validation |
| USB | Ensure media, projection, enumeration, corrupt media and reconnect validation |
| CarPlay/Android Auto | Ensure projection launch, recovery, audio focus and phone compatibility |
| Audio | Ensure routing, ducking, prompts, call audio, media and latency coverage |
| Navigation | Ensure route, GNSS loss, guidance, voice prompt and map behavior |
| Reverse Camera | Ensure trigger, latency, guidelines, no stale frame and fault handling |
| 360 Camera | Ensure camera switching, stitching, calibration and fault display |
| Cluster | Ensure warning sync, tell-tale behavior and chime policy |
| Steering Switch | Ensure short press, long press, stuck button and priority behavior |
| HVAC | Ensure display/control sync and stale state handling |
| UDS Diagnostics | Ensure DIDs, DTCs, sessions, resets and negative responses |
| OTA | Ensure download, install, rollback, interruption and post-update regression |
| Power Modes | Ensure KL15/KL30, sleep/wakeup, crank and low voltage behavior |

## Metrics Owned By Test Manager

### Execution Metrics

- Planned vs executed test cases.
- Pass/fail/blocked/not run count.
- Feature-wise completion percentage.
- Regression completion percentage.
- Automation execution percentage.

### Quality Metrics

- Defect count by severity.
- Defect count by feature.
- Defect discovery trend.
- Defect closure trend.
- Defect reopen rate.
- Defect leakage from bench to vehicle.
- Average defect age.

### Readiness Metrics

- Requirement coverage.
- P0/P1 pass rate.
- Open critical defects.
- Retest pending count.
- Evidence completeness.
- Bench availability.
- Build stability.

### Productivity Metrics

- Test cases executed per engineer.
- Automation savings.
- Bench utilization.
- Blocked time.
- Rework due to invalid defects or missing logs.

## Defect Severity Guidelines

| Severity | Meaning | Example |
| --- | --- | --- |
| S1 Critical | Safety/legal/release blocking, no workaround | Reverse camera black screen, boot loop, emergency call audio failure |
| S2 Major | Major customer feature broken, workaround difficult | Bluetooth call audio missing, Android Auto fails, OTA rollback failure |
| S3 Medium | Feature degraded but workaround exists | UI lag, wrong metadata, intermittent reconnect delay |
| S4 Minor | Cosmetic or low impact | Text truncation, minor alignment issue |

## Risk Management

The Test Manager must maintain a live risk register.

Risk fields:

- Risk ID.
- Feature.
- Description.
- Impact.
- Probability.
- Owner.
- Mitigation.
- Target closure date.
- Current status.

Common risks:

- Late software build.
- Wrong DBC version.
- Bench instability.
- Missing test devices.
- Diagnostic access blocked.
- Unclear requirement.
- High defect reopen rate.
- Automation false failures.
- Critical defect close to release.

## Meeting Cadence

| Meeting | Frequency | Owner | Purpose |
| --- | --- | --- | --- |
| Daily stand-up | Daily | Test Manager | Align execution and blockers |
| Defect triage | Daily or alternate days | Test Manager | Assign owners and actions |
| Bench readiness review | 2-3 times/week | Bench lead | Resolve lab blockers |
| Automation review | Weekly | Automation lead | Track regression automation |
| Feature readiness review | Weekly | Test Manager | Review feature status |
| Release risk review | Weekly, daily near release | Program/Test Manager | Decide release risk |
| Retrospective | Monthly | Test Manager | Improve process and quality |

## Test Manager Daily Checklist

```text
[ ] Build under test confirmed
[ ] Bench availability confirmed
[ ] CANoe/DBC version confirmed
[ ] Daily priorities assigned
[ ] Stand-up completed
[ ] Critical defects reviewed
[ ] Retest queue updated
[ ] Blockers escalated
[ ] Dashboard updated
[ ] Evidence completeness checked
[ ] End-of-day report sent
```

## Test Manager Monthly Checklist

```text
[ ] Monthly validation scope reviewed
[ ] Requirement changes analyzed
[ ] RTM updated
[ ] Test cases updated
[ ] Automation backlog reviewed
[ ] Bench health reviewed
[ ] Device matrix updated
[ ] Defect trend analyzed
[ ] Quality risks updated
[ ] Release readiness reviewed
[ ] Team performance and training needs reviewed
[ ] Monthly report published
```

## Team Handling

### Junior Engineers

Responsibilities to assign:

- Execute defined test cases.
- Capture logs and screenshots.
- Raise defects using templates.
- Learn CANoe trace analysis.
- Run smoke and sanity tests.

Manager focus:

- Review their evidence.
- Teach defect quality.
- Give repeatable modules first.

### Mid-Level Engineers

Responsibilities to assign:

- Own feature modules.
- Create and review test cases.
- Perform first-level RCA.
- Support defect triage.
- Maintain feature dashboards.

Manager focus:

- Push ownership.
- Improve debugging depth.
- Assign cross-feature issues.

### Senior Engineers

Responsibilities to assign:

- Lead complex features.
- Own automation architecture.
- Resolve bench and CANoe issues.
- Mentor others.
- Represent validation in technical reviews.

Manager focus:

- Use them for high-risk topics.
- Involve them in release decisions.
- Ask them to improve process and tools.

## Communication Rules

Good communication from a Test Manager is specific, evidence-based and action-oriented.

Avoid:

- “Testing is going on.”
- “Many bugs are there.”
- “Build is not good.”
- “Team is checking.”

Use:

- “Build MGH_RC_05 has 82% P0/P1 execution completed. Two S1 defects remain: reverse camera black screen and OTA rollback failure. Reverse camera is reproducible 4/5 times on Bench 02 with CAN trace and video attached. OTA issue is awaiting update service owner analysis.”

## Release Board Readiness Questions

Before attending release board, the Test Manager must be ready to answer:

1. What was tested?
2. What was not tested?
3. Why was it not tested?
4. What are the top open risks?
5. Which defects are release blockers?
6. What is the customer impact?
7. Are all critical fixes retested?
8. Is regression complete?
9. Are there any active unexpected DTCs?
10. What is the final go/no-go recommendation?

## Escalation Rules

Escalate immediately when:

- S1 defect is found.
- Build cannot boot.
- Reverse camera, cluster warning, call audio or OTA recovery fails.
- Benches are blocked for more than half a day.
- Required logs or tools are unavailable.
- Requirement ambiguity blocks testing.
- Defect owner is not assigned within agreed SLA.
- Release date is at risk.

Escalation must include:

- Problem.
- Impact.
- Evidence.
- Owner needed.
- Decision needed.
- Deadline.

## Final Test Manager Output For Every Release

At the end of a release cycle, the Test Manager must provide:

- Master validation report.
- Feature-wise execution report.
- Requirement traceability matrix.
- Open defect summary.
- Closed defect summary.
- Retest report.
- Regression report.
- Known issue and waiver list.
- Risk register.
- Evidence archive.
- Go/no-go recommendation.

## Strong Test Manager Mindset

A strong Test Manager does not only ask “how many test cases passed?”

They ask:

- Do we trust this build?
- Have we tested the right risks?
- Can the customer still hit a serious issue?
- Are our defects actionable?
- Is our evidence strong enough?
- Are we finding issues early enough?
- Are we improving release by release?

The best Test Manager creates a validation system where engineers know what to test, developers know what to fix, management knows the risk and the release decision is based on evidence rather than optimism.

