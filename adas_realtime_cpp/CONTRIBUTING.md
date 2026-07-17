# Contributing

- Keep control-core code allocation-free and free from blocking I/O.
- Add a test for every behavior change, including failed or degraded behavior.
- Preserve SI units and signal conventions from [Control and estimation design](docs/CONTROL_DESIGN.md).
- Treat limits, thresholds, and network data definitions as controlled calibration/configuration items.
- Do not merge a hardware adapter without its interface control document, timing analysis, E2E protection approach, and integration test evidence.
