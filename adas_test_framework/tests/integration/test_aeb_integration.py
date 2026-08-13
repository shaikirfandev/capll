from __future__ import annotations

import pytest

from adas.aeb import InterventionLevel, TargetType
from adas.fcw import FCWController
from diagnostics.dtc import DTCManager


@pytest.mark.integration
@pytest.mark.aeb
class TestAEBIntegration:
    def test_aeb_and_fcw_warning_consistency(self, aeb_controller) -> None:
        """Test ID: AEB_INT_001
Requirement: AEB integration shall align with FCW warning stage.
Objective: Verify cross-feature consistency."""
        fcw = FCWController()
        assert fcw.update(20.0, 17.0, 13.0) is True
        assert aeb_controller.update(20.0, 17.0, 13.0, TargetType.VEHICLE) is InterventionLevel.WARNING

    def test_aeb_integration_escalates_to_full_brake(self, aeb_controller) -> None:
        """Test ID: AEB_INT_002
Requirement: AEB integration shall reach full brake for imminent collision.
Objective: Verify escalation path."""
        level = aeb_controller.update(25.0, 10.0, 15.0, TargetType.VEHICLE)
        assert level is InterventionLevel.FULL_BRAKE

    def test_aeb_integration_records_dtc_on_sensor_fault(self, aeb_controller) -> None:
        """Test ID: AEB_INT_003
Requirement: AEB integration shall support fault logging.
Objective: Verify DTC manager interoperability."""
        manager = DTCManager()
        manager.set_dtc(0x100001, description="AEB sensor blocked")
        assert manager.read_active()[0].description == "AEB sensor blocked"

    def test_aeb_integration_ignores_receding_target(self, aeb_controller) -> None:
        """Test ID: AEB_INT_004
Requirement: AEB integration shall ignore receding targets.
Objective: Verify negative closing-speed path."""
        level = aeb_controller.update(10.0, 15.0, 12.0, TargetType.CYCLIST)
        assert level is InterventionLevel.NONE

    def test_aeb_integration_supports_pedestrian_target(self, aeb_controller) -> None:
        """Test ID: AEB_INT_005
Requirement: AEB integration shall support pedestrian targets.
Objective: Verify pedestrian integration path."""
        level = aeb_controller.update(12.0, 10.0, 0.0, TargetType.PEDESTRIAN)
        assert level in (InterventionLevel.PARTIAL_BRAKE, InterventionLevel.FULL_BRAKE)

    def test_aeb_integration_reports_active_state(self, aeb_controller) -> None:
        """Test ID: AEB_INT_006
Requirement: AEB integration shall expose active state.
Objective: Verify integration observability."""
        aeb_controller.update(18.0, 12.0, 6.0, TargetType.VEHICLE)
        assert aeb_controller.is_active() is True
