from __future__ import annotations


def test_ivi_boot_smoke(canoe, adb, uds, evidence_dir):
    canoe.set_signal("PowerMode", 2)
    canoe.wait(0.2)

    response = uds.send("10 03")
    assert response.positive, response

    sw = uds.send("22 F1 80")
    assert sw.positive, sw

    log_path = adb.collect_logcat(evidence_dir / "boot_smoke_logcat.txt")
    assert log_path.exists()


def test_no_critical_dtc_in_baseline(uds):
    response = uds.send("19 02 FF")
    assert response.positive
    assert response.response.startswith("59 02")

