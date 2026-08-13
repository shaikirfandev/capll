# Test Strategy

## Objectives
- validate functional correctness of ADAS algorithms
- verify failure handling and degradation behavior
- maintain CI-friendly, hardware-free regression execution

## Layers
1. **Unit**: controller logic, thresholds, state machines, Kalman math
2. **Component**: controller interaction with vehicle, CAN, and diagnostics mocks
3. **Integration**: multi-module behavior across sensing, control, and diagnostics
4. **System**: end-user feature workflows and end-to-end behavior
5. **Safety/Diagnostics**: fault injection, DTC lifecycle, UDS services
6. **Scenario**: YAML-driven regression from curated use cases

## Quality Gates
- strict pytest markers/config
- warnings treated as errors
- deterministic mocks only
- traceable test IDs and requirement references in docstrings
