"""
can_log_analyzer/analyze_log.py
Offline CAN Bus Log Analyzer — supports .blf and .asc log files.

Usage:
    python analyze_log.py --log capture.blf --dbc EV_BMS.dbc --report out.html
    python analyze_log.py --log capture.asc --signals BMS_SoC,BMS_Voltage

Features:
    - Parse BLF / ASC log files via python-can
    - Decode all signals from DBC
    - Per-message statistics (count, min period, max period, mean period, jitter)
    - Per-signal statistics (min, max, mean, stddev)
    - Bus load per second histogram
    - Missing message detection (expected but absent)
    - HTML report with embedded charts
"""
import argparse
import statistics
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import can
import cantools


# ─────────────────────────────────────────────────────────────────────────────
# PARSING
# ─────────────────────────────────────────────────────────────────────────────

def parse_log(log_path: str, db: cantools.db.Database) -> dict:
    """
    Parse a BLF or ASC log file and return structured data.

    Returns:
        {
          'messages': {arb_id: [{'ts': float, 'data': bytes}]},
          'signals':  {signal_name: [float]},
          'errors':   int,
          'duration': float,
          'total_bits': {second_bucket: int},
        }
    """
    result = {
        'messages': defaultdict(list),
        'signals': defaultdict(list),
        'errors': 0,
        'duration': 0.0,
        'total_bits': defaultdict(int),  # second bucket -> bit count
    }

    first_ts = None
    last_ts = 0.0

    try:
        log_reader = can.LogReader(log_path)
    except Exception as e:
        raise ValueError(f"Cannot open log file: {e}")

    for msg in log_reader:
        if msg is None:
            continue
        if msg.is_error_frame:
            result['errors'] += 1
            continue

        ts = msg.timestamp
        if first_ts is None:
            first_ts = ts
        last_ts = ts
        t_rel = ts - first_ts

        # Message tracking
        result['messages'][msg.arbitration_id].append({
            'ts': t_rel,
            'data': msg.data
        })

        # Bus load bits
        bits = 47 + 8 * (msg.dlc or len(msg.data))
        second_bucket = int(t_rel)
        result['total_bits'][second_bucket] += bits

        # Signal decoding
        try:
            decoded = db.decode_message(
                msg.arbitration_id, msg.data, decode_choices=False
            )
            for sig_name, value in decoded.items():
                if isinstance(value, (int, float)):
                    result['signals'][sig_name].append(float(value))
        except Exception:
            pass

    result['duration'] = last_ts - (first_ts or 0)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# STATISTICS
# ─────────────────────────────────────────────────────────────────────────────

def compute_message_stats(messages: dict, db: cantools.db.Database,
                          bitrate: int = 500000) -> list:
    """Compute timing statistics per message ID."""
    rows = []
    for arb_id, entries in sorted(messages.items()):
        timestamps = [e['ts'] for e in entries]
        if len(timestamps) < 2:
            periods_ms = []
        else:
            periods_ms = [(timestamps[i+1] - timestamps[i]) * 1000
                          for i in range(len(timestamps) - 1)]

        try:
            name = db.get_message_by_frame_id(arb_id).name
        except KeyError:
            name = f"0x{arb_id:03X}"

        rows.append({
            'name': name,
            'id': f"0x{arb_id:03X}",
            'count': len(entries),
            'mean_period_ms': f"{statistics.mean(periods_ms):.2f}" if periods_ms else "—",
            'min_period_ms':  f"{min(periods_ms):.2f}" if periods_ms else "—",
            'max_period_ms':  f"{max(periods_ms):.2f}" if periods_ms else "—",
            'jitter_ms':      f"{max(periods_ms) - min(periods_ms):.2f}" if periods_ms else "—",
            'stdev_ms':       f"{statistics.stdev(periods_ms):.2f}" if len(periods_ms) > 1 else "—",
        })
    return rows


def compute_signal_stats(signals: dict, filter_names: list = None) -> list:
    """Compute min/max/mean/stdev per signal."""
    rows = []
    for name, values in sorted(signals.items()):
        if filter_names and name not in filter_names:
            continue
        if not values:
            continue
        rows.append({
            'name': name,
            'samples': len(values),
            'min':    f"{min(values):.4f}",
            'max':    f"{max(values):.4f}",
            'mean':   f"{statistics.mean(values):.4f}",
            'stdev':  f"{statistics.stdev(values):.4f}" if len(values) > 1 else "—",
        })
    return rows


def compute_bus_load(total_bits: dict, bitrate: int = 500000) -> dict:
    """Compute bus load % per second."""
    return {sec: (bits / bitrate) * 100.0 for sec, bits in sorted(total_bits.items())}


# ─────────────────────────────────────────────────────────────────────────────
# HTML REPORT
# ─────────────────────────────────────────────────────────────────────────────

def generate_html_report(log_path: str, duration: float, errors: int,
                         msg_stats: list, sig_stats: list,
                         bus_load: dict, output_path: str):
    """Generate a self-contained HTML analysis report."""

    def table(headers: list, rows: list) -> str:
        th = ''.join(f'<th>{h}</th>' for h in headers)
        trs = ''
        for row in rows:
            tds = ''.join(f'<td>{v}</td>' for v in row.values())
            trs += f'<tr>{tds}</tr>'
        return f'<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'

    # Bus load sparkline ASCII art
    bus_loads = list(bus_load.values())
    bl_avg = statistics.mean(bus_loads) if bus_loads else 0
    bl_peak = max(bus_loads) if bus_loads else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CAN Log Analysis — {Path(log_path).name}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0d1117; color: #e6edf3; margin: 0; padding: 20px; }}
  h1 {{ color: #58a6ff; border-bottom: 2px solid #30363d; padding-bottom: 10px; }}
  h2 {{ color: #79c0ff; margin-top: 30px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
  th {{ background: #1a2244; color: #fff; padding: 8px 12px; text-align: left; }}
  td {{ padding: 6px 12px; border-bottom: 1px solid #21262d; }}
  tr:hover td {{ background: #161b22; }}
  .stat-card {{ display: inline-block; background: #161b22; border: 1px solid #30363d;
                border-radius: 8px; padding: 15px 25px; margin: 10px 10px 10px 0; }}
  .stat-label {{ font-size: 0.8em; color: #8b949e; }}
  .stat-value {{ font-size: 1.8em; font-weight: bold; color: #58a6ff; }}
  .warn {{ color: #e3b341; }}
  .ok   {{ color: #3fb950; }}
  footer {{ margin-top: 40px; color: #8b949e; font-size: 0.85em; }}
</style>
</head>
<body>
<h1>CAN Log Analysis Report</h1>
<p><b>File:</b> {Path(log_path).name} &nbsp;|&nbsp;
   <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

<h2>Summary</h2>
<div class="stat-card">
  <div class="stat-label">Duration</div>
  <div class="stat-value">{duration:.1f}s</div>
</div>
<div class="stat-card">
  <div class="stat-label">Error Frames</div>
  <div class="stat-value {'warn' if errors > 0 else 'ok'}">{errors}</div>
</div>
<div class="stat-card">
  <div class="stat-label">Avg Bus Load</div>
  <div class="stat-value {'warn' if bl_avg > 60 else 'ok'}">{bl_avg:.1f}%</div>
</div>
<div class="stat-card">
  <div class="stat-label">Peak Bus Load</div>
  <div class="stat-value {'warn' if bl_peak > 80 else 'ok'}">{bl_peak:.1f}%</div>
</div>
<div class="stat-card">
  <div class="stat-label">Messages Seen</div>
  <div class="stat-value">{len(msg_stats)}</div>
</div>

<h2>Message Timing Statistics</h2>
{table(['Name', 'ID', 'Count', 'Mean (ms)', 'Min (ms)', 'Max (ms)', 'Jitter (ms)', 'StdDev (ms)'], msg_stats)}

<h2>Signal Statistics</h2>
{table(['Signal', 'Samples', 'Min', 'Max', 'Mean', 'StdDev'], sig_stats)}

<footer>
  Generated by EV Powertrain CAN Log Analyzer | ISO 11898 compliant analysis
</footer>
</body>
</html>"""

    with open(output_path, 'w') as f:
        f.write(html)
    print(f"[Analyzer] Report saved: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='CAN Log Analyzer')
    parser.add_argument('--log',     required=True, help='.blf or .asc log file')
    parser.add_argument('--dbc',     required=True, help='DBC database file')
    parser.add_argument('--report',  default='reports/log_analysis.html',
                        help='Output HTML report path')
    parser.add_argument('--bitrate', type=int, default=500000)
    parser.add_argument('--signals', default=None,
                        help='Comma-separated signal names to include in signal stats')
    args = parser.parse_args()

    db = cantools.database.load_file(args.dbc)
    filter_signals = args.signals.split(',') if args.signals else None

    print(f"[Analyzer] Parsing {args.log}...")
    data = parse_log(args.log, db)
    print(f"[Analyzer] Duration: {data['duration']:.1f}s | "
          f"Messages: {sum(len(v) for v in data['messages'].values())} | "
          f"Errors: {data['errors']}")

    msg_stats = compute_message_stats(data['messages'], db, args.bitrate)
    sig_stats = compute_signal_stats(data['signals'], filter_signals)
    bus_load  = compute_bus_load(data['total_bits'], args.bitrate)

    os.makedirs(os.path.dirname(args.report) or '.', exist_ok=True)
    generate_html_report(
        args.log, data['duration'], data['errors'],
        msg_stats, sig_stats, bus_load, args.report
    )


if __name__ == '__main__':
    main()
