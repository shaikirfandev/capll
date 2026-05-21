from __future__ import annotations


def test_safe_mode_blocks_destructive_write(uds):
    response = uds.send("2E F1 90 31 32 33")
    assert not response.positive
    assert "blocked" in response.notes


def test_read_software_did_positive(uds):
    response = uds.send("22 F1 80")
    assert response.positive
    assert response.response.startswith("62 F1 80")
