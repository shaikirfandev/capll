# Interview STAR Scenarios: Steering Switch Controls

## Scenario 1: Bench Issue Isolated From Software Issue

Situation: Steering Switch Controls failed during bench execution.
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
Task: Automate repeatable checks for steering switch controls.
Action: Added pytest/CANoe/adb orchestration with evidence manifest and clear pass/fail thresholds.
Result: Reduced execution time and improved regression reliability.
