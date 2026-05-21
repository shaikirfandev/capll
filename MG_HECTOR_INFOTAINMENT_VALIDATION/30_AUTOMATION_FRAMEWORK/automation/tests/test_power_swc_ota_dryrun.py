from __future__ import annotations


def test_power_mode_cycle_dry_run(canoe):
    for state in [0, 1, 2, 3, 2, 0]:
        canoe.set_signal("PowerMode", state)
        canoe.wait(0.02)
    assert canoe.measurement_running


def test_steering_voice_long_press_dry_run(canoe):
    canoe.set_signal("SWC_KeyCode", 0x40)
    canoe.wait(0.05)
    canoe.set_signal("SWC_KeyCode", 0)
    assert canoe.measurement_running


def test_ota_dry_run_rejects_bad_package(uds):
    response = uds.send("31 01 FF 00")
    assert not response.positive
