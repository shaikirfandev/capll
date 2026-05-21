from __future__ import annotations

import time


def test_reverse_camera_trigger_latency_dry_run(canoe, bench_config):
    start = time.perf_counter()
    canoe.set_signal("PowerMode", 2)
    canoe.set_signal("GearPosition", 1)
    canoe.wait(0.1)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < bench_config["kpis"]["reverse_camera_latency_ms"]

