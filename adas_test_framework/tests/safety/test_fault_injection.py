from __future__ import annotations

import pytest


@pytest.mark.safety
@pytest.mark.fault_injection
class TestFaultInjection:
    def test_sensor_timeout_injection(self, fault_injector) -> None:
        """Test ID: SAFE_001
Requirement: Safety utilities shall support sensor timeout injection.
Objective: Verify timeout fault activation."""
        fault_injector.inject_sensor_timeout("camera")
        assert fault_injector.is_sensor_timed_out("camera") is True

    def test_signal_corruption_injection(self, fault_injector) -> None:
        """Test ID: SAFE_002
Requirement: Safety utilities shall support signal corruption.
Objective: Verify value mutation path."""
        fault_injector.inject_signal_corruption("distance", lambda value: value * 10)
        assert fault_injector.apply_faults({"distance": 5})["distance"] == 50

    def test_stuck_at_injection(self, fault_injector) -> None:
        """Test ID: SAFE_003
Requirement: Safety utilities shall support stuck-at faults.
Objective: Verify deterministic override."""
        fault_injector.inject_stuck_at("lane_quality", 0)
        assert fault_injector.apply_faults({"lane_quality": 100})["lane_quality"] == 0

    def test_can_suppression_injection(self, fault_injector, can_interface) -> None:
        """Test ID: SAFE_004
Requirement: Safety utilities shall support CAN suppression.
Objective: Verify frame blocking behavior."""
        fault_injector.suppress_can_id(0x321)
        can_interface.send(0x321, [1, 2, 3])
        assert can_interface.recv(0x321) is None

    def test_context_manager_clears_timeout(self, fault_injector) -> None:
        """Test ID: SAFE_005
Requirement: Safety utilities shall clean up injected faults.
Objective: Verify context manager lifecycle."""
        with fault_injector.sensor_timeout("radar"):
            assert fault_injector.is_sensor_timed_out("radar") is True
        assert fault_injector.is_sensor_timed_out("radar") is False
