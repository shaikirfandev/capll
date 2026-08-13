# ADAS Test Framework

Production-grade pytest-based ADAS validation framework built for hardware-free CI execution.

## Highlights
- Layered validation: unit, component, integration, system, diagnostics, safety, scenarios
- Mock CAN, CAN-FD, UDS, sensor fusion, and fault injection support
- Deterministic ADAS feature models for ACC, AEB, LKA, FCW, and BSD
- YAML-driven scenario execution and requirement traceability documents

## Quick Start
```bash
cd adas_test_framework
pytest tests/unit/ -v
```

## Project Layout
- `src/`: feature, vehicle, sensor, communication, diagnostics, safety utilities
- `tests/`: layered pytest suites with markers and fixtures
- `config/`: reusable framework, vehicle, sensor, and CAN configuration
- `test_data/`: scenario YAML inputs
- `docs/`: architecture, strategy, analysis, RTM, and execution guidance

## Useful Commands
```bash
pytest tests/unit/ -v
pytest -m "smoke and (acc or aeb or lka)" -v
pytest --cov=src --cov-report=term-missing
pytest -n auto tests/system/ -v
```
