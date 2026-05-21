from __future__ import annotations

from pathlib import Path

from adapters.can_log import AscLog


def test_can_log_counts_reverse_signal():
    log = AscLog(Path(__file__).resolve().parents[1] / "testdata" / "reverse_camera_nominal.asc")
    assert log.count_can_id("130") == 1
    assert log.count_can_id("301") == 1
    assert log.first_timestamp_for_id("130") == 1.0
