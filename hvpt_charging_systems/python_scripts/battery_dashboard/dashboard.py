"""
battery_dashboard/dashboard.py
Live BMS Battery Dashboard — Tkinter GUI with real-time CAN data.

Features:
    - Dark theme full-screen or windowed dashboard
    - Signal cards: SoC, Pack Voltage, Pack Current, Temperatures (max/min)
    - Color-coded warning thresholds (yellow = warn, red = fault)
    - Real-time scrolling SoC chart (matplotlib in tkinter)
    - Contactor state indicator
    - BMS fault code display
    - CAN connection status indicator

Usage:
    python dashboard.py --dbc EV_BMS.dbc --channel PCAN_USBBUS1
    python dashboard.py --dbc EV_BMS.dbc --channel test --interface virtual
"""
import tkinter as tk
from tkinter import ttk
import argparse
import threading
import time
import can
import cantools
from collections import deque
from typing import Optional


# ─── Color palette ────────────────────────────────────────────────────────────
BG_DARK      = "#0d1117"
BG_CARD      = "#161b22"
ACCENT_BLUE  = "#58a6ff"
ACCENT_GREEN = "#3fb950"
ACCENT_WARN  = "#e3b341"
ACCENT_FAULT = "#f85149"
TEXT_PRI     = "#e6edf3"
TEXT_SEC     = "#8b949e"
CARD_BORDER  = "#30363d"

# ─── Signal definitions ───────────────────────────────────────────────────────
SIGNAL_MAP = {
    'BMS_SoC':          {'label': 'State of Charge', 'unit': '%',   'warn_low': 10, 'warn_high': 95,  'fault_low': 5,  'fault_high': 100},
    'BMS_PackVoltage':  {'label': 'Pack Voltage',    'unit': 'V',   'warn_low': 360,'warn_high': 400, 'fault_low': 340,'fault_high': 415},
    'BMS_PackCurrent':  {'label': 'Pack Current',    'unit': 'A',   'warn_low': -5, 'warn_high': 200, 'fault_low': -10,'fault_high': 250},
    'BMS_MaxCellTemp':  {'label': 'Max Cell Temp',   'unit': '°C',  'warn_low': -10,'warn_high': 45,  'fault_low': -20,'fault_high': 60},
    'BMS_MinCellTemp':  {'label': 'Min Cell Temp',   'unit': '°C',  'warn_low': -15,'warn_high': 50,  'fault_low': -30,'fault_high': 55},
    'BMS_MaxCellVolt':  {'label': 'Max Cell Volt',   'unit': 'V',   'warn_low': 3.0,'warn_high': 4.1, 'fault_low': 2.8,'fault_high': 4.25},
    'BMS_MinCellVolt':  {'label': 'Min Cell Volt',   'unit': 'V',   'warn_low': 3.0,'warn_high': 4.1, 'fault_low': 2.8,'fault_high': 4.25},
    'BMS_IsolationRes': {'label': 'Isolation',       'unit': 'kΩ',  'warn_low': 200,'warn_high': None,'fault_low': 100,'fault_high': None},
    'BMS_FaultCode':    {'label': 'Fault Code',      'unit': '',    'warn_low': None,'warn_high': 0,  'fault_low': None,'fault_high': 0},
}

SOC_HISTORY_LEN = 300  # ~5 minutes at 1Hz


class SignalCard(tk.Frame):
    """Single metric display card."""

    def __init__(self, parent, label: str, unit: str, warn_config: dict):
        super().__init__(parent, bg=BG_CARD,
                         highlightbackground=CARD_BORDER,
                         highlightthickness=1,
                         padx=15, pady=12)
        self._unit = unit
        self._warn = warn_config

        self._label_widget = tk.Label(
            self, text=label, font=('Segoe UI', 9),
            bg=BG_CARD, fg=TEXT_SEC
        )
        self._label_widget.pack(anchor='w')

        self._value_widget = tk.Label(
            self, text="---", font=('Segoe UI', 28, 'bold'),
            bg=BG_CARD, fg=TEXT_PRI
        )
        self._value_widget.pack(anchor='w')

        self._unit_widget = tk.Label(
            self, text=unit, font=('Segoe UI', 10),
            bg=BG_CARD, fg=TEXT_SEC
        )
        self._unit_widget.pack(anchor='w')

    def update_value(self, value: Optional[float]):
        if value is None:
            self._value_widget.config(text="---", fg=TEXT_SEC)
            return

        text = f"{value:.1f}"
        color = ACCENT_GREEN

        w = self._warn
        if w.get('fault_high') is not None and value >= w['fault_high']:
            color = ACCENT_FAULT
        elif w.get('fault_low') is not None and value <= w['fault_low']:
            color = ACCENT_FAULT
        elif w.get('warn_high') is not None and value >= w['warn_high']:
            color = ACCENT_WARN
        elif w.get('warn_low') is not None and value <= w['warn_low']:
            color = ACCENT_WARN

        self._value_widget.config(text=text, fg=color)


class SoCChart(tk.Frame):
    """Scrolling SoC history chart drawn on tkinter Canvas."""

    def __init__(self, parent, width=600, height=120):
        super().__init__(parent, bg=BG_CARD,
                         highlightbackground=CARD_BORDER,
                         highlightthickness=1)
        self._history: deque = deque(maxlen=SOC_HISTORY_LEN)
        self._w = width
        self._h = height

        tk.Label(self, text="SoC History", font=('Segoe UI', 9),
                 bg=BG_CARD, fg=TEXT_SEC).pack(anchor='w', padx=10, pady=(8, 0))

        self._canvas = tk.Canvas(self, width=width, height=height,
                                 bg=BG_DARK, highlightthickness=0)
        self._canvas.pack(padx=10, pady=(4, 10))

    def push(self, soc: float):
        self._history.append(soc)
        self._redraw()

    def _redraw(self):
        c = self._canvas
        c.delete('all')

        if len(self._history) < 2:
            return

        # Grid lines at 25%, 50%, 75%
        for pct in (25, 50, 75):
            y = self._h - (pct / 100.0) * self._h
            c.create_line(0, y, self._w, y, fill=CARD_BORDER, dash=(4, 4))
            c.create_text(5, y - 2, text=f"{pct}%", fill=TEXT_SEC,
                          font=('Segoe UI', 7), anchor='w')

        pts = list(self._history)
        n = len(pts)
        xs = [i * self._w / (SOC_HISTORY_LEN - 1) for i in range(n)]
        ys = [self._h - (v / 100.0) * self._h for v in pts]

        # Draw line
        coords = []
        for x, y in zip(xs, ys):
            coords.extend([x, y])
        if len(coords) >= 4:
            c.create_line(*coords, fill=ACCENT_BLUE, width=2, smooth=True)

        # Current value dot
        c.create_oval(xs[-1]-4, ys[-1]-4, xs[-1]+4, ys[-1]+4,
                      fill=ACCENT_BLUE, outline='')


class Dashboard:
    """Main BMS Dashboard application."""

    def __init__(self, root: tk.Tk, bus: can.Bus, db: cantools.db.Database):
        self._root = root
        self._bus = bus
        self._db = db
        self._signals: dict = {}
        self._cards: dict = {}
        self._running = True
        self._connected = False

        root.title("EV Battery Dashboard")
        root.configure(bg=BG_DARK)
        root.resizable(True, True)

        self._build_ui()
        self._start_rx_thread()
        self._schedule_ui_update()

    def _build_ui(self):
        root = self._root

        # ── Title bar ──
        title_frame = tk.Frame(root, bg=BG_DARK)
        title_frame.pack(fill='x', padx=20, pady=(15, 0))

        tk.Label(title_frame, text="EV Battery Management System",
                 font=('Segoe UI', 16, 'bold'),
                 bg=BG_DARK, fg=ACCENT_BLUE).pack(side='left')

        self._status_dot = tk.Label(title_frame, text="● DISCONNECTED",
                                    font=('Segoe UI', 10),
                                    bg=BG_DARK, fg=ACCENT_FAULT)
        self._status_dot.pack(side='right')

        # ── Signal cards grid ──
        cards_frame = tk.Frame(root, bg=BG_DARK)
        cards_frame.pack(fill='x', padx=20, pady=15)

        card_signals = [
            ('BMS_SoC', 0, 0), ('BMS_PackVoltage', 0, 1), ('BMS_PackCurrent', 0, 2),
            ('BMS_MaxCellTemp', 1, 0), ('BMS_MinCellTemp', 1, 1),
            ('BMS_MaxCellVolt', 1, 2), ('BMS_MinCellVolt', 2, 0),
            ('BMS_IsolationRes', 2, 1), ('BMS_FaultCode', 2, 2),
        ]

        for (sig_name, row, col) in card_signals:
            cfg = SIGNAL_MAP[sig_name]
            card = SignalCard(cards_frame, cfg['label'], cfg['unit'], cfg)
            card.grid(row=row, column=col, padx=6, pady=6, sticky='nsew')
            cards_frame.grid_columnconfigure(col, weight=1)
            self._cards[sig_name] = card

        # ── SoC Chart ──
        self._soc_chart = SoCChart(root, width=680, height=120)
        self._soc_chart.pack(padx=20, pady=(0, 15), fill='x')

        # ── Contactor state bar ──
        status_frame = tk.Frame(root, bg=BG_CARD,
                                highlightbackground=CARD_BORDER,
                                highlightthickness=1)
        status_frame.pack(fill='x', padx=20, pady=(0, 15))

        tk.Label(status_frame, text="Contactor State:", font=('Segoe UI', 9),
                 bg=BG_CARD, fg=TEXT_SEC, padx=10, pady=8).pack(side='left')
        self._contactor_label = tk.Label(status_frame, text="UNKNOWN",
                                         font=('Segoe UI', 10, 'bold'),
                                         bg=BG_CARD, fg=TEXT_SEC, padx=10)
        self._contactor_label.pack(side='left')

    def _start_rx_thread(self):
        """Start background thread for CAN reception."""
        t = threading.Thread(target=self._rx_loop, daemon=True)
        t.start()

    def _rx_loop(self):
        while self._running:
            try:
                msg = self._bus.recv(timeout=0.1)
                if msg and not msg.is_error_frame:
                    decoded = self._db.decode_message(
                        msg.arbitration_id, msg.data, decode_choices=False
                    )
                    self._signals.update(decoded)
                    self._connected = True
            except can.CanError:
                self._connected = False
            except Exception:
                pass

    def _schedule_ui_update(self):
        """Schedule periodic UI refresh at ~10Hz."""
        self._update_ui()
        self._root.after(100, self._schedule_ui_update)

    def _update_ui(self):
        # Update connection status
        if self._connected:
            self._status_dot.config(text="● LIVE", fg=ACCENT_GREEN)
        else:
            self._status_dot.config(text="● DISCONNECTED", fg=ACCENT_FAULT)

        # Update signal cards
        for sig_name, card in self._cards.items():
            val = self._signals.get(sig_name)
            if val is not None:
                card.update_value(float(val))

        # Update SoC chart
        soc = self._signals.get('BMS_SoC')
        if soc is not None:
            self._soc_chart.push(float(soc))

        # Update contactor state
        contactor = self._signals.get('BMS_ContactorState', -1)
        contactor_labels = {0: ('OPEN', ACCENT_WARN), 1: ('CLOSED', ACCENT_GREEN),
                            2: ('PRECHARGE', ACCENT_BLUE), 3: ('FAULT', ACCENT_FAULT)}
        lbl, color = contactor_labels.get(int(contactor) if contactor is not None else -1,
                                          ('UNKNOWN', TEXT_SEC))
        self._contactor_label.config(text=lbl, fg=color)

    def stop(self):
        self._running = False


def main():
    parser = argparse.ArgumentParser(description='EV Battery Dashboard')
    parser.add_argument('--dbc',       required=True, help='DBC database file')
    parser.add_argument('--channel',   default='PCAN_USBBUS1')
    parser.add_argument('--interface', default='pcan')
    parser.add_argument('--bitrate',   type=int, default=500000)
    args = parser.parse_args()

    db = cantools.database.load_file(args.dbc)
    bus = can.interface.Bus(channel=args.channel, bustype=args.interface,
                            bitrate=args.bitrate)

    root = tk.Tk()
    dash = Dashboard(root, bus, db)

    def on_close():
        dash.stop()
        bus.shutdown()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == '__main__':
    main()
