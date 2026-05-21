# CAN Interface Configuration Guide
## TCU Validation Framework v2.0.0

---

## 1. Overview

The framework uses SocketCAN (Linux kernel CAN subsystem) for all CAN communication. The `CANManager` class opens a raw CAN socket and dispatches frames via registered callbacks.

---

## 2. Interface Types

| Type | Name | Use |
|------|------|-----|
| Virtual CAN | `vcan0` | Development, CI, unit testing |
| Physical CAN (USB/PCIe) | `can0`, `can1` | Hardware testing |
| Peak PCAN | `can0` | PEAK USB adapters |
| Kvaser | `can0` | Kvaser USB adapters (via kvaser_usb driver) |

---

## 3. Virtual CAN Setup

```bash
# One-time setup
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# Or use the helper script
scripts/setup_vcan.sh
```

Verify:
```bash
ip link show vcan0
# Should print: vcan0: <NOARP,UP,LOWER_UP> ...

# Test with loopback
candump vcan0 &
cansend vcan0 123#DEADBEEF
# Expect: vcan0  123   [4]  DE AD BE EF
```

---

## 4. Physical CAN Setup

### 4.1 USB-CAN adapter (Peak, Kvaser, etc.)
```bash
# Load kernel driver
sudo modprobe peak_usb           # Peak PCAN-USB
sudo modprobe kvaser_usb         # Kvaser USB
sudo modprobe gs_usb             # Generic USB CAN

# Set bitrate and bring up
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0
```

### 4.2 List available CAN interfaces
```bash
ip -details link show type can
# Or
ls /sys/class/net/ | grep can
```

### 4.3 Bring down cleanly
```bash
sudo ip link set down can0
```

---

## 5. CAN-FD Setup

```bash
# CAN-FD requires kernel ≥ 3.18 and FD-capable hardware
sudo ip link set can0 type can \
    bitrate 500000 \
    dbitrate 2000000 \
    fd on
sudo ip link set up can0
```

Enable in framework config:
```json
{
  "can": {
    "interface": "can0",
    "bitrate": 500000,
    "fd_bitrate": 2000000,
    "enable_fd": true
  }
}
```

---

## 6. Config Reference

All `can.*` keys in `configs/default.json`:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `can.interface` | string | `"vcan0"` | SocketCAN interface name |
| `can.bitrate` | int | `500000` | Nominal bitrate (bits/sec) |
| `can.fd_bitrate` | int | `2000000` | CAN-FD data bitrate |
| `can.enable_fd` | bool | `false` | Enable CAN-FD frames |
| `can.rx_timeout_ms` | int | `100` | Rx `select()` timeout |
| `can.tx_retries` | int | `3` | Tx retry count on EAGAIN |

---

## 7. Rx Callback Filtering

Register frame callbacks with a bitmask to receive only matching IDs:

```cpp
// Receive all frames (no filter)
can_mgr->register_rx_callback(
    0x00000000,  // mask  = 0 → match any
    0x00000000,  // match = 0
    [](const tcu::CANFrame& f) {
        printf("ID=%03X DLC=%d\n", f.id, f.dlc);
    }
);

// Receive only 0x7E8 (UDS response ID)
can_mgr->register_rx_callback(
    0x7FF,   // 11-bit mask
    0x7E8,   // exact match
    on_uds_response
);

// Receive extended-ID range 0x18DA0000-0x18DAFFFF
can_mgr->register_rx_callback(
    0xFFFF0000 | CAN_EFF_FLAG,
    0x18DA0000 | CAN_EFF_FLAG,
    on_j1939_frame
);
```

---

## 8. DBC File Usage

The framework includes a stub `DBCParser` that can be extended for signal decoding.  
For immediate use with existing DBC files, use `cantools` from Python:

```bash
pip3 install cantools
```

```python
import cantools
db = cantools.database.load_file('dbc_arxml_files/tcu_signals.dbc')

msg = db.get_message_by_name('TCU_STATUS')
data = bytes([0x01, 0xF4, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
decoded = msg.decode(data)
print(decoded)  # {'SPEED': 500.0, 'GEAR': 1, ...}
```

---

## 9. CAN Traffic Capture and Replay

### 9.1 Capture to log file
```bash
candump -l vcan0
# Produces: candump-YYYY-MM-DD_HH-MM-SS.log
```

### 9.2 Replay from log
```bash
python3 tools/can_replay.py \
    --file candump-2024-01-15_10-30-00.log \
    --interface vcan0 \
    --speed 1.0 \
    --verbose
```

Options:
| Flag | Description |
|------|-------------|
| `--speed 2.0` | Replay at 2× speed |
| `--loop` | Loop indefinitely |
| `--verbose` | Print each transmitted frame |

### 9.3 Filter log by ID
```bash
grep "^(.*) vcan0 123" candump.log > filtered.log
python3 tools/can_replay.py --file filtered.log --interface vcan0
```

---

## 10. CAN Statistics

Access runtime statistics via the API or the health report:

```cpp
auto stats = can_mgr->get_statistics();
printf("RX: %llu  TX: %llu  Errors: %llu\n",
       stats.rx_count.load(),
       stats.tx_count.load(),
       stats.error_count.load());
```

Or from the CLI:
```bash
./bin/tcu_validator --config configs/default.json --simulate
# Health report prints every 30s to log
```

---

## 11. Error Handling

Register an error callback to react to CAN bus errors:

```cpp
can_mgr->set_error_callback([](uint32_t err_flags) {
    if (err_flags & CAN_ERR_BUSOFF) {
        log->error("CAN BUS-OFF detected — restarting interface");
        // Attempt recovery: ip link set can0 down && up
    }
    if (err_flags & CAN_ERR_LOSTARB) {
        log->warn("Arbitration lost");
    }
});
```

Common error flags (from `linux/can/error.h`):
| Flag | Hex | Meaning |
|------|-----|---------|
| `CAN_ERR_BUSOFF` | 0x00000040 | Bus-off state |
| `CAN_ERR_CRTL` | 0x00000004 | Controller problem (passive/warning) |
| `CAN_ERR_LOSTARB` | 0x00000002 | Lost arbitration |
| `CAN_ERR_ACK` | 0x00000020 | No ACK on transmission |
