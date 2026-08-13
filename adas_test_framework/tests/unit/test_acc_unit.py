from __future__ import annotations

import pytest

from adas.acc import ACCController, ACCState


@pytest.mark.unit
@pytest.mark.acc
class TestACCUnit:
    def test_initial_state_is_off(self, acc_controller: ACCController) -> None:
        """Test ID: ACC_UNIT_001
Requirement: ACC shall initialize in OFF.
Objective: Verify default state before activation."""
        # ARRANGE
        controller = ACCController()

        # ACT / ASSERT
        assert controller.get_state() is ACCState.OFF

    def test_activate_moves_to_standby(self, acc_controller: ACCController) -> None:
        """Test ID: ACC_UNIT_002
Requirement: ACC shall enter STANDBY after activation.
Objective: Verify OFF to STANDBY transition."""
        # ACT
        state = acc_controller.activate()

        # ASSERT
        assert state is ACCState.STANDBY
        assert acc_controller.get_state() is ACCState.STANDBY

    def test_standby_to_active_without_target(self, acc_controller: ACCController) -> None:
        """Test ID: ACC_UNIT_003
Requirement: ACC shall become ACTIVE when cruising.
Objective: Verify STANDBY to ACTIVE transition without target."""
        # ARRANGE
        acc_controller.activate()

        # ACT
        acceleration = acc_controller.update(vehicle_speed=26.0, lead_vehicle_distance=None, lead_vehicle_speed=None)

        # ASSERT
        assert acc_controller.get_state() is ACCState.ACTIVE
        assert acceleration >= -0.1

    def test_active_to_braking_when_gap_is_small(self, acc_controller: ACCController) -> None:
        """Test ID: ACC_UNIT_004
Requirement: ACC shall brake to preserve headway.
Objective: Verify ACTIVE to BRAKING transition."""
        # ARRANGE
        acc_controller.activate()

        # ACT
        acceleration = acc_controller.update(vehicle_speed=30.0, lead_vehicle_distance=15.0, lead_vehicle_speed=20.0)

        # ASSERT
        assert acc_controller.get_state() is ACCState.BRAKING
        assert acceleration < 0.0

    def test_braking_to_override_on_driver_brake(self, acc_controller: ACCController) -> None:
        """Test ID: ACC_UNIT_005
Requirement: Driver brake shall override ACC.
Objective: Verify BRAKING to OVERRIDE transition."""
        # ARRANGE
        acc_controller.activate()
        acc_controller.update(vehicle_speed=30.0, lead_vehicle_distance=15.0, lead_vehicle_speed=20.0)

        # ACT
        acceleration = acc_controller.update(vehicle_speed=30.0, lead_vehicle_distance=15.0, lead_vehicle_speed=20.0, brake_pressed=True)

        # ASSERT
        assert acc_controller.get_state() is ACCState.OVERRIDE
        assert acceleration == 0.0
        assert acc_controller.driver_override_detected is True

    def test_deactivate_returns_to_off(self, acc_controller: ACCController) -> None:
        """Test ID: ACC_UNIT_006
Requirement: ACC shall deactivate to OFF.
Objective: Verify graceful shutdown from active path."""
        # ARRANGE
        acc_controller.activate()
        acc_controller.update(vehicle_speed=28.0, lead_vehicle_distance=None, lead_vehicle_speed=None)

        # ACT
        state = acc_controller.deactivate()

        # ASSERT
        assert state is ACCState.OFF
        assert acc_controller.compute_acceleration() == 0.0

    @pytest.mark.parametrize("set_speed", [30.0, 60.0, 120.0, 180.0])
    def test_set_speed_accepts_boundaries(self, set_speed: float) -> None:
        """Test ID: ACC_UNIT_007
Requirement: ACC shall support 30-180 kph set speeds.
Objective: Verify valid boundary and nominal setpoints."""
        # ARRANGE
        controller = ACCController()

        # ACT
        controller.set_speed(set_speed)

        # ASSERT
        assert controller.get_set_speed() == pytest.approx(set_speed)

    @pytest.mark.parametrize("set_speed", [29.9, 181.0])
    @pytest.mark.boundary
    def test_set_speed_rejects_invalid_boundaries(self, set_speed: float) -> None:
        """Test ID: ACC_UNIT_008
Requirement: ACC shall reject unsupported set speeds.
Objective: Verify invalid boundary handling."""
        # ARRANGE
        controller = ACCController()

        # ACT / ASSERT
        with pytest.raises(ValueError):
            controller.set_speed(set_speed)

    @pytest.mark.parametrize("gap", [1.0, 1.3, 1.6, 2.0])
    def test_time_gap_settings_are_supported(self, gap: float) -> None:
        """Test ID: ACC_UNIT_009
Requirement: ACC shall support calibrated headway settings.
Objective: Verify all configured time gaps can be selected."""
        # ARRANGE
        controller = ACCController()

        # ACT
        selected = controller.set_time_gap(gap)

        # ASSERT
        assert selected == gap
        assert controller.selected_time_gap == gap

    def test_target_loss_returns_to_active(self, acc_controller: ACCController) -> None:
        """Test ID: ACC_UNIT_010
Requirement: ACC shall resume cruise after target loss.
Objective: Verify BRAKING to ACTIVE transition on target disappearance."""
        # ARRANGE
        acc_controller.activate()
        acc_controller.update(vehicle_speed=30.0, lead_vehicle_distance=15.0, lead_vehicle_speed=20.0)

        # ACT
        acceleration = acc_controller.update(vehicle_speed=26.0, lead_vehicle_distance=None, lead_vehicle_speed=None)

        # ASSERT
        assert acc_controller.get_state() is ACCState.ACTIVE
        assert acceleration >= 0.0

    def test_compute_acceleration_positive_when_below_set_speed(self, acc_controller: ACCController) -> None:
        """Test ID: ACC_UNIT_011
Requirement: ACC shall accelerate below set speed.
Objective: Verify positive control effort during catch-up."""
        # ARRANGE
        acc_controller.activate()

        # ACT
        acc_controller.update(vehicle_speed=20.0, lead_vehicle_distance=None, lead_vehicle_speed=None)

        # ASSERT
        assert acc_controller.compute_acceleration() > 0.0

    def test_compute_acceleration_negative_when_above_target(self, acc_controller: ACCController) -> None:
        """Test ID: ACC_UNIT_012
Requirement: ACC shall decelerate above allowed target.
Objective: Verify negative control effort for overspeed."""
        # ARRANGE
        acc_controller.activate()

        # ACT
        acc_controller.update(vehicle_speed=35.0, lead_vehicle_distance=None, lead_vehicle_speed=None)

        # ASSERT
        assert acc_controller.compute_acceleration() < 0.0

    def test_throttle_override_sets_override_state(self, acc_controller: ACCController) -> None:
        """Test ID: ACC_UNIT_013
Requirement: Driver throttle override shall suspend ACC actuation.
Objective: Verify throttle override detection."""
        # ARRANGE
        acc_controller.activate()

        # ACT
        acc_controller.update(vehicle_speed=28.0, lead_vehicle_distance=None, lead_vehicle_speed=None, throttle_override=True)

        # ASSERT
        assert acc_controller.get_state() is ACCState.OVERRIDE
        assert acc_controller.driver_override_detected is True

    def test_below_min_vehicle_speed_returns_to_standby(self, acc_controller: ACCController) -> None:
        """Test ID: ACC_UNIT_014
Requirement: ACC shall not control below minimum vehicle speed.
Objective: Verify vehicle-speed boundary logic."""
        # ARRANGE
        acc_controller.activate()

        # ACT
        acceleration = acc_controller.update(vehicle_speed=5.0, lead_vehicle_distance=None, lead_vehicle_speed=None)

        # ASSERT
        assert acc_controller.get_state() is ACCState.STANDBY
        assert acceleration == 0.0

    def test_target_acquisition_limits_speed_to_lead_vehicle(self, acc_controller: ACCController) -> None:
        """Test ID: ACC_UNIT_015
Requirement: ACC shall regulate to lead vehicle speed.
Objective: Verify target acquisition caps commanded acceleration."""
        # ARRANGE
        acc_controller.activate()

        # ACT
        acceleration = acc_controller.update(vehicle_speed=25.0, lead_vehicle_distance=40.0, lead_vehicle_speed=23.0)

        # ASSERT
        assert acc_controller.get_state() in (ACCState.ACTIVE, ACCState.BRAKING)
        assert acceleration <= 2.0
