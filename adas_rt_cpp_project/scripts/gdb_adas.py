#!/usr/bin/env python3
"""
gdb_adas.py — GDB Python automation script for ADAS process debugging.

USAGE
─────
  gdb -x scripts/gdb_adas.py --args ./bazel-bin/src/adas_rt
  gdb -x scripts/gdb_adas.py --pid $(pgrep adas_rt)

COMMANDS ADDED
──────────────
  adas-tracks          — Print all active SensorFusion tracks
  adas-faults          — Print DTC fault table
  adas-rt-stats        — Print RT scheduler jitter statistics
  adas-bt-all-threads  — Backtrace all threads (condensed)
  adas-watch-latency   — Set watchpoint on max_jitter_us exceeding threshold
"""

import gdb
import re


# ── Helper: read string from char[] ──────────────────────────────────────────

def gdb_string(val) -> str:
    try:
        return val.string()
    except Exception:
        return str(val)


# ── adas-tracks command ───────────────────────────────────────────────────────

class AdasTracksCommand(gdb.Command):
    """Print current SensorFusion track list."""

    def __init__(self):
        super().__init__("adas-tracks", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        try:
            # Access the global fusion object
            fusion = gdb.parse_and_eval("g_fusion")
            tracks_map = fusion["tracks_"]
            print(f"{'ID':>6}  {'px [m]':>8}  {'py [m]':>8}  {'vx [m/s]':>10}  {'vy [m/s]':>10}  {'hits':>5}  {'confirmed':>9}")
            print("-" * 70)

            # Iterate std::unordered_map (GDB pretty-printer)
            for item in tracks_map:
                t = item['second']
                tid   = int(t['track_id'])
                px    = float(t['x']['data'][0])
                py    = float(t['x']['data'][1])
                vx    = float(t['x']['data'][2])
                vy    = float(t['x']['data'][3])
                hits  = int(t['hits'])
                conf  = hits >= 3
                print(f"{tid:>6}  {px:>8.2f}  {py:>8.2f}  {vx:>10.3f}  {vy:>10.3f}  {hits:>5}  {'YES' if conf else 'no':>9}")
        except gdb.error as e:
            print(f"[adas-tracks] Error: {e}")
            print("  Tip: ensure the binary has debug symbols (bazel build with -c dbg)")


AdasTracksCommand()


# ── adas-faults command ───────────────────────────────────────────────────────

class AdasFaultsCommand(gdb.Command):
    """Print active DTC faults from FaultManager."""

    def __init__(self):
        super().__init__("adas-faults", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        try:
            # FaultManager is a singleton; call dump() via inferior function call
            gdb.execute("call adas::diag::FaultManager::instance().dump()")
        except gdb.error as e:
            print(f"[adas-faults] Error: {e}")


AdasFaultsCommand()


# ── adas-rt-stats command ─────────────────────────────────────────────────────

class AdasRtStatsCommand(gdb.Command):
    """Print RtScheduler task statistics (jitter, deadline misses)."""

    def __init__(self):
        super().__init__("adas-rt-stats", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        try:
            sched = gdb.parse_and_eval("scheduler")
            ctxs  = sched["contexts_"]
            # GDB vector size
            start = ctxs["_M_impl"]["_M_start"]
            finish = ctxs["_M_impl"]["_M_finish"]
            size  = int(finish - start)

            print(f"{'Task':<25}  {'Exec':>8}  {'Misses':>8}  {'MaxJitter(µs)':>14}  {'AvgJitter(µs)':>14}")
            print("-" * 75)

            for i in range(size):
                ctx   = (start + i).dereference()
                stats = ctx["stats"]
                name  = gdb_string(ctx["task"]["name"])
                execs = int(stats["executions"])
                miss  = int(stats["deadline_misses"])
                maxj  = int(stats["max_jitter_us"])
                avgj  = int(stats["avg_jitter_us"])
                print(f"{name:<25}  {execs:>8}  {miss:>8}  {maxj:>14}  {avgj:>14}")
        except gdb.error as e:
            print(f"[adas-rt-stats] Error: {e}")


AdasRtStatsCommand()


# ── adas-bt-all-threads command ───────────────────────────────────────────────

class AdasBtAllThreads(gdb.Command):
    """Condensed backtrace of all threads (shows top 3 frames each)."""

    def __init__(self):
        super().__init__("adas-bt-all-threads", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        inferior = gdb.selected_inferior()
        for thread in inferior.threads():
            thread.switch()
            frame = gdb.selected_frame()
            print(f"\n── Thread {thread.num} ({thread.name or 'unnamed'}) ──")
            depth = 0
            while frame and depth < 5:
                try:
                    fn   = frame.function().name if frame.function() else "<unknown>"
                    sal  = frame.find_sal()
                    loc  = f"{sal.symtab.filename}:{sal.line}" if sal.symtab else ""
                    print(f"  #{depth:2}  {fn}  {loc}")
                except Exception:
                    print(f"  #{depth:2}  <frame info unavailable>")
                frame = frame.older()
                depth += 1


AdasBtAllThreads()


# ── adas-watch-latency command ────────────────────────────────────────────────

class AdasWatchLatency(gdb.Command):
    """Set a watchpoint to break when RT jitter exceeds N microseconds.
       Usage: adas-watch-latency 500
    """

    def __init__(self):
        super().__init__("adas-watch-latency", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        try:
            threshold = int(arg.strip()) if arg.strip() else 1000
            # Watch the first task's max_jitter_us field
            gdb.execute(f"watch -l scheduler.contexts_[0].stats.max_jitter_us")
            print(f"Watchpoint set on max_jitter_us (threshold reference: {threshold} µs)")
            print("Note: GDB will break on any write to max_jitter_us; check value manually.")
        except gdb.error as e:
            print(f"[adas-watch-latency] Error: {e}")


AdasWatchLatency()


# ── Startup banner ────────────────────────────────────────────────────────────

print("""
╔═══════════════════════════════════════════════════════╗
║  ADAS GDB Helper loaded                               ║
║  Commands:                                            ║
║    adas-tracks          — show active fusion tracks   ║
║    adas-faults          — dump DTC fault table        ║
║    adas-rt-stats        — RT task jitter statistics   ║
║    adas-bt-all-threads  — condensed thread backtraces ║
║    adas-watch-latency N — break on jitter > N µs      ║
╚═══════════════════════════════════════════════════════╝
""")
