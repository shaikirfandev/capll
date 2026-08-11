# Architecture

The framework uses a layered architecture centered on deterministic software models so tests run without real hardware.

- **Communication layer**: mock CAN, CAN-FD, and UDS transport abstractions.
- **Sensor layer**: camera, radar, lidar detections and Kalman-based fusion.
- **Vehicle layer**: reusable vehicle state and YAML scenario loading.
- **ADAS layer**: ACC, AEB, LKA, FCW, and BSD feature controllers.
- **Diagnostics layer**: DTC management and UDS service handling.
- **Safety layer**: fault injection and degradation verification.
- **Utility layer**: assertions and timing helpers.

Test suites mirror the V-cycle with unit, component, integration, system, diagnostics, safety, and scenario coverage.
