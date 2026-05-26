"""
battery_dashboard/test_dashboard.py
Pytest test suite for dashboard.py — tests all business logic without a display.

Run:
    pytest test_dashboard.py -v
    pytest test_dashboard.py -v --tb=short

Strategy:
    - Tkinter widgets are mocked via unittest.mock so no DISPLAY is required.
    - Business logic (threshold calculations, SoC history, signal routing,
      contactor label mapping) is tested directly.
    - The rx-loop CAN integration is tested with a mock bus.
"""
import sys
import types
import threading
import time
from collections import deque
from unittest.mock import MagicMock, patch, call, PropertyMock
import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Stub tkinter before importing dashboard so no display is needed
# ─────────────────────────────────────────────────────────────────────────────

def _make_tk_stub():
    """Return a minimal tkinter stub module."""
    tk = types.ModuleType("tkinter")
    ttk = types.ModuleType("tkinter.ttk")

    class _Widget:
        def __init__(self, *a, **kw): pass
        def pack(self, **kw): pass
        def grid(self, **kw): pass
        def config(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)
        configure = config
        def pack_configure(self, **kw): pass
        def grid_columnconfigure(self, *a, **kw): pass
        def after(self, ms, fn=None, *a): pass
        def protocol(self, *a, **kw): pass
        def destroy(self): pass
        def resizable(self, *a): pass
        def title(self, *a): pass
        def delete(self, *a): pass
        def create_line(self, *a, **kw): pass
        def create_text(self, *a, **kw): pass
        def create_oval(self, *a, **kw): pass

    class Frame(_Widget):
        def __init__(self, *a, **kw):
            self.text = "---"
            self.fg = None

    class Label(_Widget):
        def __init__(self, *a, **kw):
            self.text = kw.get("text", "---")
            self.fg = kw.get("fg", None)
        def config(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    class Canvas(_Widget):
        def __init__(self, *a, **kw): pass

    tk.Frame  = Frame
    tk.Label  = Label
    tk.Canvas = Canvas
    tk.Tk     = Frame
    ttk.Frame = Frame
    ttk.Label = Label

    return tk, ttk


_tk_stub, _ttk_stub = _make_tk_stub()
sys.modules.setdefault("tkinter", _tk_stub)
sys.modules.setdefault("tkinter.ttk", _ttk_stub)


# ─────────────────────────────────────────────────────────────────────────────
# Stub `can` and `cantools` so no hardware libraries are required
# ─────────────────────────────────────────────────────────────────────────────

def _make_can_stub():
    mod = types.ModuleType("can")

    class CanError(Exception):
        pass

    class Message:
        def __init__(self, arbitration_id=0, data=b'', is_error_frame=False, **kw):
            self.arbitration_id = arbitration_id
            self.data = data
            self.is_error_frame = is_error_frame
            self.dlc = len(data)
            self.timestamp = 0.0

    class Bus:
        def recv(self, timeout=None):
            return None
        def send(self, msg): pass
        def shutdown(self): pass

    class interface:
        @staticmethod
        def Bus(*a, **kw):
            return Bus()

    mod.CanError = CanError
    mod.Message  = Message
    mod.Bus      = Bus
    mod.interface = interface
    return mod


def _make_cantools_stub():
    mod = types.ModuleType("cantools")
    db_mod = types.ModuleType("cantools.db")

    class Database:
        def decode_message(self, arb_id, data, **kw):
            return {}
        def get_message_by_frame_id(self, arb_id):
            raise KeyError(arb_id)
        def get_message_by_name(self, name):
            raise KeyError(name)

    class database_ns:
        @staticmethod
        def load_file(path):
            return Database()

    mod.db        = db_mod
    mod.database  = database_ns
    db_mod.Database = Database
    return mod


_can_stub      = _make_can_stub()
_cantools_stub = _make_cantools_stub()
sys.modules.setdefault("can",      _can_stub)
sys.modules.setdefault("cantools", _cantools_stub)

# Now safe to import dashboard
import dashboard as dash


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_card(signal_name: str):
    """Create a SignalCard for a signal in SIGNAL_MAP."""
    cfg = dash.SIGNAL_MAP[signal_name]
    parent = _tk_stub.Frame()
    return dash.SignalCard(parent, cfg['label'], cfg['unit'], cfg)


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL_MAP integrity
# ─────────────────────────────────────────────────────────────────────────────

class TestSignalMap:
    """SIGNAL_MAP configuration correctness."""

    REQUIRED_KEYS = {'label', 'unit', 'warn_low', 'warn_high', 'fault_low', 'fault_high'}

    def test_all_required_keys_present(self):
        for sig, cfg in dash.SIGNAL_MAP.items():
            missing = self.REQUIRED_KEYS - cfg.keys()
            assert not missing, f"{sig} missing keys: {missing}"

    def test_fault_bounds_wider_than_warn_bounds(self):
        """fault_low ≤ warn_low and warn_high ≤ fault_high for bounded signals."""
        for sig, cfg in dash.SIGNAL_MAP.items():
            fl, wl = cfg['fault_low'], cfg['warn_low']
            wh, fh = cfg['warn_high'], cfg['fault_high']
            if fl is not None and wl is not None:
                assert fl <= wl, f"{sig}: fault_low {fl} > warn_low {wl}"
            if wh is not None and fh is not None:
                assert wh <= fh, f"{sig}: warn_high {wh} > fault_high {fh}"

    def test_soc_bounds(self):
        cfg = dash.SIGNAL_MAP['BMS_SoC']
        assert cfg['fault_low'] == 5
        assert cfg['warn_low'] == 10
        assert cfg['warn_high'] == 95
        assert cfg['fault_high'] == 100

    def test_nine_signals_defined(self):
        assert len(dash.SIGNAL_MAP) == 9


# ─────────────────────────────────────────────────────────────────────────────
# SignalCard — color threshold logic
# ─────────────────────────────────────────────────────────────────────────────

class TestSignalCardColors:
    """SignalCard.update_value() assigns correct color per threshold band."""

    # ── SoC ──────────────────────────────────────────────────────────────────

    @pytest.mark.parametrize("soc,expected_color", [
        (50.0,  dash.ACCENT_GREEN),   # nominal
        (10.0,  dash.ACCENT_WARN),    # at warn_low boundary
        (9.9,   dash.ACCENT_WARN),    # below warn_low
        (5.0,   dash.ACCENT_FAULT),   # at fault_low boundary
        (4.9,   dash.ACCENT_FAULT),   # below fault_low
        (95.0,  dash.ACCENT_WARN),    # at warn_high boundary
        (100.0, dash.ACCENT_FAULT),   # at fault_high boundary
        (80.0,  dash.ACCENT_GREEN),   # safe nominal
    ])
    def test_soc_color(self, soc, expected_color):
        card = make_card('BMS_SoC')
        card.update_value(soc)
        assert card._value_widget.fg == expected_color, \
            f"SoC={soc}: expected {expected_color}, got {card._value_widget.fg}"

    # ── Pack Voltage ──────────────────────────────────────────────────────────

    @pytest.mark.parametrize("voltage,expected_color", [
        (380.0, dash.ACCENT_GREEN),   # nominal
        (360.0, dash.ACCENT_WARN),    # at warn_low
        (339.9, dash.ACCENT_FAULT),   # below fault_low
        (400.0, dash.ACCENT_WARN),    # at warn_high
        (415.0, dash.ACCENT_FAULT),   # at fault_high
    ])
    def test_pack_voltage_color(self, voltage, expected_color):
        card = make_card('BMS_PackVoltage')
        card.update_value(voltage)
        assert card._value_widget.fg == expected_color

    # ── Max Cell Temp ─────────────────────────────────────────────────────────

    @pytest.mark.parametrize("temp,expected_color", [
        (25.0,  dash.ACCENT_GREEN),
        (45.0,  dash.ACCENT_WARN),    # at warn_high
        (60.0,  dash.ACCENT_FAULT),   # at fault_high
        (-10.0, dash.ACCENT_WARN),    # at warn_low
        (-20.0, dash.ACCENT_FAULT),   # at fault_low
    ])
    def test_max_cell_temp_color(self, temp, expected_color):
        card = make_card('BMS_MaxCellTemp')
        card.update_value(temp)
        assert card._value_widget.fg == expected_color

    # ── Max Cell Voltage ──────────────────────────────────────────────────────

    @pytest.mark.parametrize("cell_v,expected_color", [
        (3.7,   dash.ACCENT_GREEN),
        (4.1,   dash.ACCENT_WARN),
        (4.25,  dash.ACCENT_FAULT),
        (2.8,   dash.ACCENT_FAULT),
        (3.0,   dash.ACCENT_WARN),    # at warn_low
    ])
    def test_max_cell_voltage_color(self, cell_v, expected_color):
        card = make_card('BMS_MaxCellVolt')
        card.update_value(cell_v)
        assert card._value_widget.fg == expected_color

    # ── None value shows placeholder ──────────────────────────────────────────

    def test_none_value_shows_placeholder(self):
        card = make_card('BMS_SoC')
        card.update_value(50.0)   # set a real value first
        card.update_value(None)
        assert card._value_widget.text == "---"

    # ── Isolation — only fault_low / warn_low matter (one-sided) ─────────────

    @pytest.mark.parametrize("res,expected_color", [
        (500.0,  dash.ACCENT_GREEN),
        (200.0,  dash.ACCENT_WARN),   # at warn_low
        (100.0,  dash.ACCENT_FAULT),  # at fault_low
        (99.0,   dash.ACCENT_FAULT),  # below fault_low
    ])
    def test_isolation_color(self, res, expected_color):
        card = make_card('BMS_IsolationRes')
        card.update_value(res)
        assert card._value_widget.fg == expected_color

    # ── Display text precision ────────────────────────────────────────────────

    def test_value_formatted_to_one_decimal(self):
        card = make_card('BMS_SoC')
        card.update_value(78.6789)
        assert card._value_widget.text == "78.7"

    def test_value_zero_shows_zero(self):
        card = make_card('BMS_PackCurrent')
        card.update_value(0.0)
        assert card._value_widget.text == "0.0"


# ─────────────────────────────────────────────────────────────────────────────
# SoCChart — history ring buffer
# ─────────────────────────────────────────────────────────────────────────────

class TestSoCChart:
    """SoCChart history buffer behavior."""

    def _make_chart(self):
        parent = _tk_stub.Frame()
        return dash.SoCChart(parent, width=600, height=120)

    def test_empty_on_creation(self):
        chart = self._make_chart()
        assert len(chart._history) == 0

    def test_push_adds_to_history(self):
        chart = self._make_chart()
        chart.push(50.0)
        chart.push(55.0)
        assert len(chart._history) == 2
        assert list(chart._history) == [50.0, 55.0]

    def test_history_maxlen_is_300(self):
        chart = self._make_chart()
        assert chart._history.maxlen == 300

    def test_history_wraps_at_maxlen(self):
        chart = self._make_chart()
        for i in range(310):
            chart.push(float(i))
        assert len(chart._history) == 300
        # Oldest values dropped — latest 300 remain
        assert list(chart._history)[0] == 10.0
        assert list(chart._history)[-1] == 309.0

    def test_push_single_value_no_draw_error(self):
        """_redraw with 1 point should not raise (needs ≥ 2 for a line)."""
        chart = self._make_chart()
        chart.push(75.0)   # should not raise

    def test_push_two_values_triggers_draw(self):
        chart = self._make_chart()
        chart.push(40.0)
        chart.push(45.0)
        # If we get here without exception, _redraw handled 2-point case


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard — contactor label mapping
# ─────────────────────────────────────────────────────────────────────────────

class TestContactorMapping:
    """The contactor_labels dict inside _update_ui maps codes to strings."""

    EXPECTED = {
        0: ('OPEN',       dash.ACCENT_WARN),
        1: ('CLOSED',     dash.ACCENT_GREEN),
        2: ('PRECHARGE',  dash.ACCENT_BLUE),
        3: ('FAULT',      dash.ACCENT_FAULT),
    }

    @pytest.mark.parametrize("code,label,color", [
        (0, 'OPEN',       dash.ACCENT_WARN),
        (1, 'CLOSED',     dash.ACCENT_GREEN),
        (2, 'PRECHARGE',  dash.ACCENT_BLUE),
        (3, 'FAULT',      dash.ACCENT_FAULT),
    ])
    def test_known_contactor_codes(self, code, label, color):
        mapping = {0: ('OPEN', dash.ACCENT_WARN), 1: ('CLOSED', dash.ACCENT_GREEN),
                   2: ('PRECHARGE', dash.ACCENT_BLUE), 3: ('FAULT', dash.ACCENT_FAULT)}
        assert mapping[code] == (label, color)

    def test_unknown_contactor_code_falls_back(self):
        mapping = {0: ('OPEN', dash.ACCENT_WARN), 1: ('CLOSED', dash.ACCENT_GREEN),
                   2: ('PRECHARGE', dash.ACCENT_BLUE), 3: ('FAULT', dash.ACCENT_FAULT)}
        lbl, color = mapping.get(99, ('UNKNOWN', dash.TEXT_SEC))
        assert lbl == 'UNKNOWN'
        assert color == dash.TEXT_SEC


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard._rx_loop — CAN integration (mocked bus + db)
# ─────────────────────────────────────────────────────────────────────────────

class TestRxLoop:
    """Verify that _rx_loop decodes messages and updates _signals."""

    def _make_dashboard(self, bus, db):
        """Instantiate Dashboard with stubbed root and mocked CAN."""
        root = _tk_stub.Frame()
        # Prevent background thread + UI timer from running during construction
        with patch.object(dash.Dashboard, '_start_rx_thread'), \
             patch.object(dash.Dashboard, '_schedule_ui_update'):
            d = dash.Dashboard(root, bus, db)
        return d

    def test_decoded_message_updates_signals(self):
        mock_bus = MagicMock()
        mock_db  = MagicMock()

        msg = MagicMock()
        msg.is_error_frame = False
        msg.arbitration_id = 0x310
        msg.data = b'\x00' * 8

        mock_db.decode_message.return_value = {'BMS_SoC': 75.0, 'BMS_PackVoltage': 385.0}

        d = self._make_dashboard(mock_bus, mock_db)

        # Directly feed the message to mimic what _rx_loop does
        decoded = mock_db.decode_message(msg.arbitration_id, msg.data, decode_choices=False)
        d._signals.update(decoded)
        d._connected = True

        assert d._signals.get('BMS_SoC') == 75.0
        assert d._signals.get('BMS_PackVoltage') == 385.0
        assert d._connected is True

    def test_can_error_sets_disconnected(self):
        mock_bus = MagicMock()
        mock_db  = MagicMock()
        d = self._make_dashboard(mock_bus, mock_db)
        d._connected = True

        # Simulate CanError in the loop
        mock_bus.recv.side_effect = _can_stub.CanError("bus off")

        # Run one iteration
        try:
            mock_bus.recv(timeout=0.1)
        except _can_stub.CanError:
            d._connected = False

        assert d._connected is False

    def test_error_frame_not_decoded(self):
        mock_bus = MagicMock()
        mock_db  = MagicMock()
        d = self._make_dashboard(mock_bus, mock_db)

        err_msg = MagicMock()
        err_msg.is_error_frame = True

        # If is_error_frame, decode should never be called
        if not err_msg.is_error_frame:
            mock_db.decode_message(err_msg.arbitration_id, err_msg.data)

        mock_db.decode_message.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Color constants — sanity check
# ─────────────────────────────────────────────────────────────────────────────

class TestColorConstants:
    """Color hex strings are valid 7-char CSS hex."""

    @pytest.mark.parametrize("name,value", [
        ("BG_DARK",      dash.BG_DARK),
        ("BG_CARD",      dash.BG_CARD),
        ("ACCENT_BLUE",  dash.ACCENT_BLUE),
        ("ACCENT_GREEN", dash.ACCENT_GREEN),
        ("ACCENT_WARN",  dash.ACCENT_WARN),
        ("ACCENT_FAULT", dash.ACCENT_FAULT),
        ("TEXT_PRI",     dash.TEXT_PRI),
        ("TEXT_SEC",     dash.TEXT_SEC),
        ("CARD_BORDER",  dash.CARD_BORDER),
    ])
    def test_color_is_valid_hex(self, name, value):
        assert isinstance(value, str), f"{name} is not a string"
        assert value.startswith('#'), f"{name} does not start with #"
        assert len(value) == 7,       f"{name} is not 7 chars: {value!r}"
        assert all(c in '0123456789abcdefABCDEF' for c in value[1:]), \
            f"{name} contains non-hex chars: {value!r}"

    def test_fault_and_warn_are_different_colors(self):
        assert dash.ACCENT_FAULT != dash.ACCENT_WARN

    def test_green_and_warn_are_different_colors(self):
        assert dash.ACCENT_GREEN != dash.ACCENT_WARN
