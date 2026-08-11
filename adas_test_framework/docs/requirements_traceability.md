# Requirements Traceability

| Feature | Representative Requirements | Test Coverage |
| --- | --- | --- |
| ACC | speed range, state machine, headway control, override | `tests/unit/test_acc_unit.py`, `tests/component/test_acc_component.py`, `tests/system/test_acc_system.py` |
| AEB | TTC thresholds, object classification, false positives | `tests/unit/test_aeb_unit.py`, `tests/integration/test_aeb_integration.py`, `tests/system/test_aeb_system.py` |
| LKA | departure detection, torque response, warning escalation | `tests/unit/test_lka_unit.py`, `tests/component/test_lka_component.py`, `tests/system/test_lka_system.py` |
| Sensor Fusion | track lifecycle, fusion math, timeouts | `tests/unit/test_sensor_fusion_unit.py`, `tests/integration/test_sensor_fusion_integration.py` |
| Diagnostics | UDS services, DTC lifecycle | `tests/diagnostics/*.py`, `tests/system/test_end_to_end.py` |
| Safety | timeouts, corruption, degradation | `tests/safety/*.py`, `tests/system/test_end_to_end.py` |
