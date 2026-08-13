from __future__ import annotations

import pytest

from diagnostics.dtc import DTCManager


@pytest.mark.diagnostics
class TestDTCLifecycle:
    def test_set_and_read_dtc(self) -> None:
        """Test ID: DTC_001
Requirement: DTC manager shall store active DTCs.
Objective: Verify set/read lifecycle."""
        manager = DTCManager()
        manager.set_dtc(0x100001, description="camera timeout")
        assert manager.read_active()[0].description == "camera timeout"

    def test_clear_specific_dtc(self) -> None:
        """Test ID: DTC_002
Requirement: DTC manager shall clear individual DTCs.
Objective: Verify targeted clear behavior."""
        manager = DTCManager()
        manager.set_dtc(0x100001)
        manager.clear(0x100001)
        assert manager.read_all() == []

    def test_clear_all_dtcs(self) -> None:
        """Test ID: DTC_003
Requirement: DTC manager shall clear all DTCs.
Objective: Verify global clear behavior."""
        manager = DTCManager()
        manager.set_dtc(0x100001)
        manager.set_dtc(0x100002)
        manager.clear()
        assert manager.read_all() == []

    def test_freeze_frame_is_retained(self) -> None:
        """Test ID: DTC_004
Requirement: DTC manager shall retain freeze-frame data.
Objective: Verify freeze-frame storage."""
        manager = DTCManager()
        manager.set_dtc(0x100010, freeze_frame={"speed_kph": 88, "distance_m": 12})
        assert manager.get_freeze_frame(0x100010)["speed_kph"] == 88

    def test_occurrence_count_increments(self) -> None:
        """Test ID: DTC_005
Requirement: DTC manager shall track occurrences.
Objective: Verify repeated fault counting."""
        manager = DTCManager()
        manager.set_dtc(0x100020)
        manager.set_dtc(0x100020)
        assert manager.read_all()[0].occurrence_count == 2
