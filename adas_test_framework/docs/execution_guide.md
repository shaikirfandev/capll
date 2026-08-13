# Execution Guide

## Local execution
```bash
cd adas_test_framework
pytest tests/unit/ -v
pytest tests/component/ tests/integration/ -v
pytest tests/system/ tests/diagnostics/ tests/safety/ tests/scenarios/ -v
```

## Marker-based execution
```bash
pytest -m smoke -v
pytest -m "acc or aeb or lka" -v
pytest -m diagnostics -v
pytest -m fault_injection -v
```

## CI recommendations
- run unit tests on every commit
- run component/integration on pull requests
- run full regression nightly with HTML and coverage reports
- archive scenario YAML and diagnostics artifacts with the build
