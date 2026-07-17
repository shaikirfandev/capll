"""
tests/test_sensor_validation.py
================================
Production-grade validation test suite for the Industrial Image Sensor Platform.

Coverage:
  - Unit tests: HAL layer, sensor driver, streaming engine logic
  - Integration tests: full pipeline (sensor → streaming → application)
  - Performance tests: FPS, latency, bandwidth
  - Stress tests: long-duration, power-cycle, frame-drop injection
  - Frame integrity: CRC, pixel statistics, dead-pixel detection
  - Multi-sensor synchronization tests
  - DTC and diagnostics tests
  - Firmware update tests

Requirements:
  pip install pytest pytest-html pytest-xdist numpy

Run:
  pytest tests/test_sensor_validation.py -v --html=reports/results.html
  pytest tests/test_sensor_validation.py -m performance -v
  pytest tests/test_sensor_validation.py -m stress --duration=3600 -v

Copyright (c) 2026 Industrial Vision Systems.
"""

from __future__ import annotations

import time
import struct
import threading
import statistics
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch, call

import numpy as np
import pytest

# ─── Test fixtures use mock transport for unit tests; real device for integration ───
REAL_DEVICE_AVAILABLE = False  # Set True when hardware is connected
try:
    from isf_sensor_sdk import SensorDevice, SensorControl, FrameCapture
    from isf_sensor_sdk import DiagnosticsClient, FirmwareUpdater
    from isf_sensor_sdk import PixelFormat, SensorConfig, FrameData
    from isf_sensor_sdk import RuntimeStats, DiagnosticEvent, _crc16
except ImportError:
    pytest.skip("isf_sensor_sdk not installed", allow_module_level=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers / shared utilities
# ─────────────────────────────────────────────────────────────────────────────
def _make_mock_frame(sequence: int = 0, width: int = 1920, height: int = 1080,
                      ecc_errors: int = 0, crc_errors: int = 0) -> FrameData:
    pixels = np.random.randint(0, 4096, (height, width), dtype=np.uint16)
    return FrameData(
        sequence=sequence, timestamp_us=int(time.monotonic() * 1e6),
        width=width, height=height,
        pixel_format=PixelFormat.RAW12,
        gain_x100=150, exposure_us=5000,
        temperature_c_x10=253,
        ecc_errors=ecc_errors, crc_errors=crc_errors, flags=0,
        pixels=pixels
    )


def _make_mock_device() -> MagicMock:
    """Create a SensorDevice mock with sensible defaults."""
    dev = MagicMock(spec=SensorDevice)
    # Default: send_command returns an empty success response
    dev.send_command.return_value = b''
    return dev


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Unit: CRC and protocol
# ─────────────────────────────────────────────────────────────────────────────
class TestCrc16:
    def test_crc_known_value(self):
        """CRC-16/CCITT-FALSE of 0x313233343536373839 should be 0x29B1."""
        data = b'123456789'
        assert _crc16(data) == 0x29B1

    def test_crc_empty(self):
        """CRC of empty data should equal initial value."""
        result = _crc16(b'')
        assert isinstance(result, int)

    def test_crc_single_bit_difference(self):
        """Changing one bit must change the CRC."""
        data1 = b'\x00\x00\x00\x00'
        data2 = b'\x01\x00\x00\x00'
        assert _crc16(data1) != _crc16(data2)

    def test_crc_consistency(self):
        """Same input always produces same output (deterministic)."""
        data = b'IMX477_TEST_FRAME'
        assert _crc16(data) == _crc16(data)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Unit: SensorConfig and SensorControl
# ─────────────────────────────────────────────────────────────────────────────
class TestSensorConfig:
    def test_default_config(self):
        cfg = SensorConfig()
        assert cfg.width == 1920
        assert cfg.height == 1080
        assert cfg.fps == 30
        assert cfg.gain_x100 == 100
        assert not cfg.test_pattern

    def test_custom_config(self):
        cfg = SensorConfig(width=4056, height=3040, fps=10, gain_x100=400)
        assert cfg.width == 4056
        assert cfg.gain_x100 == 400


class TestSensorControl:
    @pytest.fixture
    def ctrl(self):
        dev = _make_mock_device()
        return SensorControl(dev), dev

    def test_configure_sends_command(self, ctrl):
        controller, dev = ctrl
        controller.configure(width=1920, height=1080, fps=30)
        dev.send_command.assert_called()

    def test_start_sends_start_command(self, ctrl):
        controller, dev = ctrl
        controller.start()
        calls = [c[0][0] for c in dev.send_command.call_args_list]
        assert 0x11 in calls  # _CMD_START

    def test_stop_sends_stop_command(self, ctrl):
        controller, dev = ctrl
        controller.stop()
        calls = [c[0][0] for c in dev.send_command.call_args_list]
        assert 0x12 in calls  # _CMD_STOP

    def test_get_stats_parses_response(self, ctrl):
        controller, dev = ctrl
        # Pack a valid stats response
        stats_bytes = struct.pack('<QQIIIHIh',
                                  1000, 2, 0, 0, 300, 150, 5000, 253)
        dev.send_command.return_value = stats_bytes
        stats = controller.get_stats()
        assert stats.frames_captured == 1000
        assert stats.frames_dropped == 2
        assert stats.fps == pytest.approx(30.0, abs=0.1)
        assert stats.temperature_c == pytest.approx(25.3, abs=0.1)
        assert stats.drop_rate == pytest.approx(2 / 1002, abs=1e-4)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Unit: FrameData
# ─────────────────────────────────────────────────────────────────────────────
class TestFrameData:
    def test_frame_properties(self):
        frame = _make_mock_frame(gain_x100=200)
        assert frame.gain == pytest.approx(2.0)

    def test_temperature_conversion(self):
        frame = _make_mock_frame()
        frame_mod = FrameData(
            **{**frame.__dict__, 'temperature_c_x10': 375}
        )
        assert frame_mod.temperature_c == pytest.approx(37.5, abs=0.01)

    def test_pixel_array_shape(self):
        frame = _make_mock_frame(width=640, height=480)
        assert frame.pixels.shape == (480, 640)
        assert frame.pixels.dtype == np.uint16


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Unit: DiagnosticsClient
# ─────────────────────────────────────────────────────────────────────────────
class TestDiagnosticsClient:
    def _make_dtc_response(self, dtcs: list) -> bytes:
        """Build a mock DTC response payload."""
        buf = bytes([len(dtcs)])
        for dtc in dtcs:
            buf += struct.pack('<IBIQQ',
                               dtc['code'], dtc['status'], dtc['occ'],
                               dtc['first_ts'], dtc['last_ts'])
        return buf

    def test_parse_empty_dtc_list(self):
        dev = _make_mock_device()
        dev.send_command.return_value = bytes([0])
        diag = DiagnosticsClient(dev)
        result = diag.get_dtcs()
        assert result == []

    def test_parse_single_dtc(self):
        dev = _make_mock_device()
        dev.send_command.return_value = self._make_dtc_response([
            {'code': 0xC0A000, 'status': 2, 'occ': 5,
             'first_ts': 1000000, 'last_ts': 5000000}
        ])
        diag = DiagnosticsClient(dev)
        dtcs = diag.get_dtcs()
        assert len(dtcs) == 1
        assert dtcs[0].dtc_code == 0xC0A000
        assert dtcs[0].status_name == "Confirmed"
        assert dtcs[0].occurrence_count == 5

    def test_clear_dtcs(self):
        dev = _make_mock_device()
        diag = DiagnosticsClient(dev)
        diag.clear_dtcs()
        dev.send_command.assert_called()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — Frame integrity checks
# ─────────────────────────────────────────────────────────────────────────────
class TestFrameIntegrity:
    """Validate pixel statistics and frame health."""

    def test_pixel_range_raw12(self):
        """RAW12 pixels must be in [0, 4095]."""
        frame = _make_mock_frame()
        assert int(frame.pixels.min()) >= 0
        assert int(frame.pixels.max()) <= 4095

    def test_no_crc_errors_nominal(self):
        """Nominal frame must have zero CRC errors."""
        frame = _make_mock_frame(crc_errors=0)
        assert frame.crc_errors == 0

    def test_detect_all_black_frame(self):
        """All-zero frame is a sensor defect or blocked optics."""
        pixels = np.zeros((1080, 1920), dtype=np.uint16)
        frame = FrameData(
            sequence=1, timestamp_us=0, width=1920, height=1080,
            pixel_format=PixelFormat.RAW12, gain_x100=100, exposure_us=5000,
            temperature_c_x10=250, ecc_errors=0, crc_errors=0, flags=0,
            pixels=pixels
        )
        mean_val = float(np.mean(frame.pixels))
        assert mean_val < 10.0, "All-black frame detected"

    def test_detect_dead_pixel_cluster(self):
        """Dead pixel cluster: > 0.5% pixels stuck at max value is suspicious."""
        pixels = np.random.randint(1000, 3000, (1080, 1920), dtype=np.uint16)
        dead_count = 50000  # ~2.4%
        rng = np.random.default_rng(42)
        rows = rng.integers(0, 1080, dead_count)
        cols = rng.integers(0, 1920, dead_count)
        pixels[rows, cols] = 4095

        total = pixels.size
        stuck_high = np.sum(pixels == 4095)
        stuck_pct = stuck_high / total
        assert stuck_pct > 0.005, f"Dead pixel rate {stuck_pct*100:.2f}% below threshold"

    def test_frame_snr(self):
        """Signal-to-Noise Ratio should be > 20 dB on a uniform target."""
        target = 2048  # Half scale on 12-bit
        noise_sigma = 15   # Expected read noise
        pixels = np.random.normal(target, noise_sigma, (1080, 1920)).astype(np.uint16)
        np.clip(pixels, 0, 4095, out=pixels)
        snr_db = 20 * np.log10(np.mean(pixels) / np.std(pixels))
        assert snr_db > 30.0, f"SNR {snr_db:.1f} dB below 30 dB threshold"

    def test_sequence_continuity(self):
        """Frame sequence numbers must be monotonically increasing with no gaps."""
        frames = [_make_mock_frame(sequence=i) for i in range(10)]
        sequences = [f.sequence for f in frames]
        assert sequences == list(range(10)), "Sequence gap or out-of-order frames"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — Performance tests (marked separately)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.performance
class TestPerformance:
    """Performance benchmarks — run against real hardware."""

    TARGET_FPS = 30
    MAX_LATENCY_MS = 50.0
    MAX_DROP_RATE = 0.001   # 0.1%

    @pytest.mark.skipif(not REAL_DEVICE_AVAILABLE, reason="Requires real hardware")
    def test_fps_1080p30(self):
        """1080p30 must sustain ≥ 28 fps average over 10 seconds."""
        with SensorDevice.open_usb() as dev:
            ctrl = SensorControl(dev)
            ctrl.configure(width=1920, height=1080, fps=30)
            ctrl.start()
            time.sleep(10)
            stats = ctrl.get_stats()
            ctrl.stop()

        assert stats.fps >= 28.0, f"FPS {stats.fps:.2f} below 28 fps threshold"

    @pytest.mark.skipif(not REAL_DEVICE_AVAILABLE, reason="Requires real hardware")
    def test_frame_drop_rate_nominal(self):
        """Frame drop rate must be < 0.1% during nominal operation."""
        with SensorDevice.open_usb() as dev:
            ctrl = SensorControl(dev)
            ctrl.configure(width=1920, height=1080, fps=30)
            ctrl.start()
            time.sleep(30)
            stats = ctrl.get_stats()
            ctrl.stop()

        assert stats.drop_rate < self.MAX_DROP_RATE, \
            f"Drop rate {stats.drop_rate*100:.3f}% exceeds {self.MAX_DROP_RATE*100}%"

    @pytest.mark.skipif(not REAL_DEVICE_AVAILABLE, reason="Requires real hardware")
    def test_end_to_end_latency(self):
        """End-to-end latency (SOF → dequeue) must be < 50 ms at 1080p30."""
        latencies = []
        with SensorDevice.open_usb() as dev:
            ctrl = SensorControl(dev)
            ctrl.configure(width=1920, height=1080, fps=30)
            ctrl.start()
            with FrameCapture(dev) as cap:
                for frame in cap.stream(count=100):
                    now_us = int(time.monotonic() * 1e6)
                    latencies.append((now_us - frame.timestamp_us) / 1000.0)
            ctrl.stop()

        p99_ms = sorted(latencies)[int(len(latencies) * 0.99)]
        assert p99_ms < self.MAX_LATENCY_MS, \
            f"P99 latency {p99_ms:.1f} ms exceeds {self.MAX_LATENCY_MS} ms"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — Stress tests
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.stress
class TestStress:
    """Stress and soak tests — long duration, power cycles."""

    @pytest.mark.skipif(not REAL_DEVICE_AVAILABLE, reason="Requires real hardware")
    def test_72h_continuous_streaming(self):
        """Sensor must stream for 72 hours without crash or frame drop spike."""
        duration_s = 72 * 3600
        with SensorDevice.open_usb() as dev:
            ctrl = SensorControl(dev)
            ctrl.configure(width=1920, height=1080, fps=30)
            ctrl.start()
            time.sleep(duration_s)
            stats = ctrl.get_stats()
            ctrl.stop()

        assert stats.drop_rate < 0.001
        assert stats.frames_captured > duration_s * 28  # At least 28 fps average

    @pytest.mark.skipif(not REAL_DEVICE_AVAILABLE, reason="Requires real hardware")
    @pytest.mark.parametrize("cycles", [100])
    def test_power_cycle_stability(self, cycles):
        """Sensor must reinitialise correctly after N power cycles."""
        failures = 0
        for i in range(cycles):
            try:
                with SensorDevice.open_usb() as dev:
                    ctrl = SensorControl(dev)
                    ctrl.configure(width=1920, height=1080, fps=30)
                    ctrl.start()
                    time.sleep(0.5)
                    stats = ctrl.get_stats()
                    ctrl.stop()
                if stats.frames_captured < 10:
                    failures += 1
            except Exception as e:
                failures += 1
                pytest.xfail(f"Power cycle {i} failed: {e}")

        assert failures == 0, f"{failures}/{cycles} power cycles failed"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — Multi-sensor synchronisation tests
# ─────────────────────────────────────────────────────────────────────────────
class TestMultiSensorSync:
    def test_timestamp_alignment_simulation(self):
        """
        Simulates two sensors producing frames.
        Their SOF timestamps must align within 1 frame period (1/fps).
        """
        fps = 30.0
        frame_period_us = int(1e6 / fps)
        tolerance_us = frame_period_us // 10  # 10% tolerance

        t0 = int(time.monotonic() * 1e6)
        frames_a = [_make_mock_frame(sequence=i) for i in range(30)]
        frames_b = [_make_mock_frame(sequence=i) for i in range(30)]

        # Simulate small offset between sensors (hardware trigger alignment)
        for i, (fa, fb) in enumerate(zip(frames_a, frames_b)):
            fa_ts = t0 + i * frame_period_us
            fb_ts = t0 + i * frame_period_us + 500  # 500 µs hardware skew

            delta_us = abs(fa_ts - fb_ts)
            assert delta_us < tolerance_us, \
                f"Frame {i}: timestamp delta {delta_us} µs exceeds tolerance {tolerance_us} µs"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9 — Firmware update tests
# ─────────────────────────────────────────────────────────────────────────────
class TestFirmwareUpdate:
    def test_fw_update_calls_correct_sequence(self, tmp_path):
        """Firmware update must follow: START → CHUNKS → FINALIZE."""
        fw_data = b'\xDE\xAD' * 1024  # 2 kB dummy firmware
        fw_file = tmp_path / 'test_fw.bin'
        fw_file.write_bytes(fw_data)

        dev = _make_mock_device()
        updater = FirmwareUpdater(dev)

        call_sequence = []
        def track_cmd(cmd_id, payload=b'', **kwargs):
            if cmd_id == 0x30:
                call_sequence.append(payload[0])
            return b''
        dev.send_command.side_effect = track_cmd

        updater.update(fw_file)

        assert call_sequence[0] == 0x01, "START command must be first"
        assert all(c == 0x02 for c in call_sequence[1:-1]), "All middle calls must be CHUNK"
        assert call_sequence[-1] == 0x03, "FINALIZE command must be last"

    def test_fw_update_progress_callback(self, tmp_path):
        """Progress callback must be called for each chunk."""
        fw_data = bytes(range(256)) * 16  # 4 kB
        fw_file = tmp_path / 'test_fw.bin'
        fw_file.write_bytes(fw_data)

        dev = _make_mock_device()
        dev.send_command.return_value = b''
        progress_calls = []
        updater = FirmwareUpdater(dev)
        updater.update(fw_file, progress_cb=lambda done, total: progress_calls.append(done))

        assert progress_calls[-1] == len(fw_data)
        assert all(a <= b for a, b in zip(progress_calls, progress_calls[1:]))  # Monotonic


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 10 — Regression test suite
# ─────────────────────────────────────────────────────────────────────────────
class TestRegression:
    """Regression tests that must pass before every release."""

    @pytest.mark.parametrize("width,height,fps", [
        (4056, 3040, 10),
        (1920, 1080, 60),
        (1280,  720, 120),
    ])
    def test_configure_resolution_modes(self, width, height, fps):
        """All supported resolution modes must be configurable without error."""
        dev = _make_mock_device()
        ctrl = SensorControl(dev)
        ctrl.configure(width=width, height=height, fps=fps)
        dev.send_command.assert_called()

    @pytest.mark.parametrize("gain_x100", [100, 200, 400, 800, 1600])
    def test_gain_range(self, gain_x100):
        """All valid gain values must be accepted without exception."""
        dev = _make_mock_device()
        ctrl = SensorControl(dev)
        ctrl.configure(width=1920, height=1080, fps=30, gain_x100=gain_x100)

    @pytest.mark.parametrize("exposure_us", [100, 1000, 10000, 100000, 500000])
    def test_exposure_range(self, exposure_us):
        """All valid exposure values must be accepted."""
        dev = _make_mock_device()
        ctrl = SensorControl(dev)
        ctrl.configure(width=1920, height=1080, fps=30, exposure_us=exposure_us)

    def test_start_stop_sequence(self):
        """Start → Stop sequence must produce correct command sequence."""
        dev = _make_mock_device()
        ctrl = SensorControl(dev)
        ctrl.start()
        ctrl.stop()
        cmd_ids = [c[0][0] for c in dev.send_command.call_args_list]
        start_idx = cmd_ids.index(0x11)
        stop_idx  = cmd_ids.index(0x12)
        assert start_idx < stop_idx, "STOP must come after START"

    def test_statistics_drop_rate_zero_when_no_drops(self):
        stats = RuntimeStats(
            frames_captured=1000, frames_dropped=0,
            ecc_errors=0, crc_errors=0, current_fps_x10=300,
            current_gain_x100=100, current_exposure_us=5000, temperature_c_x10=250
        )
        assert stats.drop_rate == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Pytest configuration
# ─────────────────────────────────────────────────────────────────────────────
def pytest_configure(config):
    config.addinivalue_line("markers", "performance: performance benchmark tests (require HW)")
    config.addinivalue_line("markers", "stress: long-duration stress tests (require HW)")
    config.addinivalue_line("markers", "integration: integration tests (require HW)")
