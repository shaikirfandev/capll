# Start Here

This repository is meant to behave like a compact OEM infotainment validation workspace, not only a note dump.

## Recommended First Run

1. Read `LAB_SAFETY_AND_ASSUMPTIONS.md`.
2. Open `CANoe_Project/README.md` and inspect the representative DBC.
3. Review `03_BENCH_SETUP/MG_HECTOR_BENCH_ARCHITECTURE.md`.
4. Run the dry automation suite:

```bash
cd MG_HECTOR_INFOTAINMENT_VALIDATION/30_AUTOMATION_FRAMEWORK
python3 -m pytest automation/tests -q
```

5. Execute the capstone using `50_CAPSTONE_BENCH_PROJECT/CAPSTONE_RELEASE_EXECUTION_PLAN.md`.

## What Is Real vs Representative

The validation process, folder layout, evidence discipline, automation interfaces, RCA workflow and release gates match real OEM/Tier1 work. CAN IDs, DIDs, DBC contents, traces and topology are representative training data and must be replaced with released MG program artifacts on a real project.
