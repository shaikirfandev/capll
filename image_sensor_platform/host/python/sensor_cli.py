#!/usr/bin/env python3
"""
sensor_cli.py — Industrial Image Sensor Command-Line Interface

Usage:
    sensor-cli --help
    sensor-cli info
    sensor-cli capture --frames 10 --output /tmp/capture
    sensor-cli stream --fps 30 --show
    sensor-cli reg-read 0x0204
    sensor-cli reg-write 0x0204 0x01A0
    sensor-cli dtc list
    sensor-cli dtc clear
    sensor-cli fw-update firmware.bin
    sensor-cli perf --duration 30
    sensor-cli calibrate --type blemish

Copyright (c) 2026 Industrial Vision Systems.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('sensor-cli')


def _make_device(args):
    """Build a SensorDevice from CLI transport arguments."""
    # Import here so the CLI works even if partial dependencies missing
    try:
        from isf_sensor_sdk import SensorDevice
    except ImportError:
        print("ERROR: isf_sensor_sdk not found. Run: pip install -e host/python/", file=sys.stderr)
        sys.exit(1)

    if hasattr(args, 'uart') and args.uart:
        return SensorDevice.open_uart(args.uart, baudrate=getattr(args, 'baud', 921600))
    elif hasattr(args, 'tcp') and args.tcp:
        host, port = args.tcp.split(':')
        return SensorDevice.open_tcp(host, int(port))
    else:
        return SensorDevice.open_usb(vid=0x1234, pid=0x0001)


def cmd_info(args):
    """Print sensor information and capabilities."""
    from isf_sensor_sdk import SensorControl
    with _make_device(args) as dev:
        ctrl = SensorControl(dev)
        caps = ctrl.get_capabilities()
        stats = ctrl.get_stats()

    print("=" * 60)
    print("  Industrial Image Sensor — Device Information")
    print("=" * 60)
    print(f"  Available modes ({len(caps.modes)}):")
    for i, m in enumerate(caps.modes):
        print(f"    [{i}] {m['width']}×{m['height']} @ up to {m['fps_max']} fps  "
              f"({m['format'].name}, {m['lanes']}-lane MIPI)")
    print(f"\n  Gain range   : {caps.min_gain_x100/100:.1f}× – {caps.max_gain_x100/100:.1f}×")
    print(f"  Exposure range: {caps.min_exposure_us} µs – {caps.max_exposure_us/1000:.0f} ms")
    print(f"  Features     : HDR={caps.has_hdr}  HW-trigger={caps.has_trigger}  "
          f"Temperature={caps.has_temperature}")
    print(f"\n  Current state:")
    print(f"    FPS        : {stats.fps:.1f}")
    print(f"    Gain       : {stats.current_gain_x100/100:.2f}×")
    print(f"    Exposure   : {stats.current_exposure_us} µs")
    print(f"    Temperature: {stats.temperature_c:.1f} °C")
    print(f"    Frames     : {stats.frames_captured:,} captured, "
          f"{stats.frames_dropped:,} dropped ({stats.drop_rate*100:.2f}%)")


def cmd_capture(args):
    """Capture N frames and save to disk."""
    from isf_sensor_sdk import SensorControl, SensorConfig, FrameCapture
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    with _make_device(args) as dev:
        ctrl = SensorControl(dev)
        ctrl.configure(
            width=args.width, height=args.height,
            fps=args.fps, gain_x100=int(args.gain * 100),
            exposure_us=args.exposure
        )
        ctrl.start()
        print(f"Capturing {args.frames} frame(s) to {output_dir}/")

        with FrameCapture(dev) as cap:
            for i, frame in enumerate(cap.stream(count=args.frames)):
                path = output_dir / f"frame_{frame.sequence:06d}"
                cap.save_raw(frame, path)
                print(f"  [{i+1}/{args.frames}] seq={frame.sequence}  "
                      f"ts={frame.timestamp_us/1e6:.3f}s  "
                      f"temp={frame.temperature_c:.1f}°C  "
                      f"ecc={frame.ecc_errors} crc={frame.crc_errors}")

        ctrl.stop()
    print(f"Done. {args.frames} frames saved to {output_dir}/")


def cmd_stream(args):
    """Stream live frames and print statistics."""
    from isf_sensor_sdk import SensorControl, FrameCapture
    print(f"Streaming at {args.fps} fps. Press Ctrl+C to stop.")

    with _make_device(args) as dev:
        ctrl = SensorControl(dev)
        ctrl.configure(width=args.width, height=args.height, fps=args.fps)
        ctrl.start()

        frame_count = 0
        start = time.monotonic()
        try:
            with FrameCapture(dev) as cap:
                for frame in cap.stream():
                    frame_count += 1
                    elapsed = time.monotonic() - start
                    if frame_count % 30 == 0:
                        fps = frame_count / elapsed
                        stats = ctrl.get_stats()
                        print(f"\r  Frames: {frame_count:6d}  FPS: {fps:5.1f}  "
                              f"Dropped: {stats.frames_dropped:4d}  "
                              f"Temp: {stats.temperature_c:.1f}°C  ", end='', flush=True)
        except KeyboardInterrupt:
            print()
        finally:
            ctrl.stop()
    print(f"\nStreamed {frame_count} frames in {time.monotonic()-start:.1f}s")


def cmd_reg_read(args):
    """Read a sensor register."""
    from isf_sensor_sdk import SensorControl
    with _make_device(args) as dev:
        ctrl = SensorControl(dev)
        val = ctrl.read_register(args.reg)
    print(f"Reg 0x{args.reg:04X} = 0x{val:04X} ({val})")


def cmd_reg_write(args):
    """Write a sensor register."""
    from isf_sensor_sdk import SensorControl
    with _make_device(args) as dev:
        ctrl = SensorControl(dev)
        ctrl.write_register(args.reg, args.value)
    print(f"Written 0x{args.value:04X} to reg 0x{args.reg:04X}")


def cmd_dtc(args):
    """DTC management commands."""
    from isf_sensor_sdk import DiagnosticsClient
    with _make_device(args) as dev:
        diag = DiagnosticsClient(dev)
        if args.dtc_cmd == 'list':
            diag.print_dtc_report()
        elif args.dtc_cmd == 'clear':
            diag.clear_dtcs()
            print("DTCs cleared.")


def cmd_fw_update(args):
    """Update sensor firmware."""
    from isf_sensor_sdk import FirmwareUpdater
    fw_path = Path(args.firmware)
    if not fw_path.exists():
        print(f"ERROR: Firmware file not found: {fw_path}", file=sys.stderr)
        sys.exit(1)

    def progress(done, total):
        pct = done * 100 // total
        bar = '█' * (pct // 2) + '░' * (50 - pct // 2)
        print(f"\r  [{bar}] {pct:3d}%  {done//1024} kB / {total//1024} kB", end='', flush=True)

    with _make_device(args) as dev:
        updater = FirmwareUpdater(dev)
        updater.update(fw_path, progress_cb=progress)
    print("\nFirmware update complete.")


def cmd_perf(args):
    """Performance test — measure throughput and latency."""
    from isf_sensor_sdk import SensorControl, FrameCapture
    from collections import deque

    print(f"Performance test: {args.duration}s at {args.fps} fps, {args.width}×{args.height}")
    latencies = deque(maxlen=10000)

    with _make_device(args) as dev:
        ctrl = SensorControl(dev)
        ctrl.configure(width=args.width, height=args.height, fps=args.fps)
        ctrl.start()

        deadline = time.monotonic() + args.duration
        frame_count = 0

        with FrameCapture(dev) as cap:
            for frame in cap.stream():
                now_us = int(time.monotonic() * 1e6)
                latency = now_us - frame.timestamp_us
                latencies.append(latency)
                frame_count += 1
                if time.monotonic() >= deadline:
                    break

        ctrl.stop()

    stats = ctrl.get_stats()
    elapsed = args.duration
    fps_avg = frame_count / elapsed

    import statistics
    lat_ms = [l / 1000.0 for l in latencies]
    print("\n=== Performance Results ===")
    print(f"  Frames captured  : {frame_count:,}")
    print(f"  Average FPS      : {fps_avg:.2f}")
    print(f"  Frames dropped   : {stats.frames_dropped:,} ({stats.drop_rate*100:.3f}%)")
    print(f"  Latency (ms):")
    print(f"    Mean  : {statistics.mean(lat_ms):.2f}")
    print(f"    P50   : {statistics.median(lat_ms):.2f}")
    print(f"    P99   : {sorted(lat_ms)[int(len(lat_ms)*0.99)]:.2f}")
    print(f"    Max   : {max(lat_ms):.2f}")
    bw_mbps = (frame_count * args.width * args.height * 2) / (elapsed * 1e6)
    print(f"  Bandwidth        : {bw_mbps:.1f} MB/s")


# ─────────────────────────────────────────────────────────────────────────────
# Argument parser
# ─────────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='sensor-cli',
        description='Industrial Image Sensor CLI'
    )
    # Transport options (global)
    trans = parser.add_mutually_exclusive_group()
    trans.add_argument('--uart', metavar='PORT', help='UART transport (e.g. /dev/ttyUSB0)')
    trans.add_argument('--tcp',  metavar='HOST:PORT', help='TCP transport (e.g. 192.168.1.100:5000)')
    parser.add_argument('--baud', type=int, default=921600, help='UART baudrate')
    parser.add_argument('-v', '--verbose', action='store_true')

    sub = parser.add_subparsers(dest='command', required=True)

    # info
    sub.add_parser('info', help='Show sensor information and capabilities')

    # capture
    cap = sub.add_parser('capture', help='Capture frames to disk')
    cap.add_argument('--frames', type=int, default=1)
    cap.add_argument('--output', default='/tmp/isf_capture')
    cap.add_argument('--width', type=int, default=1920)
    cap.add_argument('--height', type=int, default=1080)
    cap.add_argument('--fps', type=int, default=30)
    cap.add_argument('--gain', type=float, default=1.0)
    cap.add_argument('--exposure', type=int, default=10000, metavar='US')

    # stream
    stm = sub.add_parser('stream', help='Stream live frames')
    stm.add_argument('--width', type=int, default=1920)
    stm.add_argument('--height', type=int, default=1080)
    stm.add_argument('--fps', type=int, default=30)

    # reg-read
    rr = sub.add_parser('reg-read', help='Read register')
    rr.add_argument('reg', type=lambda x: int(x, 0), metavar='REG')

    # reg-write
    rw = sub.add_parser('reg-write', help='Write register')
    rw.add_argument('reg',   type=lambda x: int(x, 0), metavar='REG')
    rw.add_argument('value', type=lambda x: int(x, 0), metavar='VALUE')

    # dtc
    dtc = sub.add_parser('dtc', help='DTC management')
    dtc.add_argument('dtc_cmd', choices=['list', 'clear'])

    # fw-update
    fw = sub.add_parser('fw-update', help='Update firmware')
    fw.add_argument('firmware', metavar='FILE')

    # perf
    perf = sub.add_parser('perf', help='Performance test')
    perf.add_argument('--duration', type=float, default=10.0, metavar='SECONDS')
    perf.add_argument('--width', type=int, default=1920)
    perf.add_argument('--height', type=int, default=1080)
    perf.add_argument('--fps', type=int, default=30)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    dispatch = {
        'info':      cmd_info,
        'capture':   cmd_capture,
        'stream':    cmd_stream,
        'reg-read':  cmd_reg_read,
        'reg-write': cmd_reg_write,
        'dtc':       cmd_dtc,
        'fw-update': cmd_fw_update,
        'perf':      cmd_perf,
    }

    try:
        dispatch[args.command](args)
    except ConnectionError as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(2)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
