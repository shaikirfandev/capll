# TCU Firmware Flashing Guide
## TCU Validation Framework v2.0.0

---

## 1. Overview

The framework supports two firmware flashing paths:

| Method | Protocol | When to use |
|--------|----------|-------------|
| UDS Flash | ISO 14229 (0x34/0x36/0x37) over CAN/ISO-TP | Standard OEM ECU programming |
| RFP CLI | Renesas Flash Programmer CLI via subprocess | Renesas RL78/RH850/RX microcontrollers |

Both paths are implemented in `src/firmware/FirmwareFlasher.cpp` and perform a CRC-32 integrity check before any flash attempt.

---

## 2. Prerequisites

### Hardware
- CAN interface: `can0` (physical) or `vcan0` (simulation)
- ECU powered and in a valid state (not in Safe Mode or bootloop)
- Sufficient supply voltage (flash typically requires ≥ 12V stable)

### Software
- `tcu_validator` built in Release mode:
  ```bash
  BUILD_TYPE=Release scripts/build.sh
  ```
- For RFP path: `rfp-cli` must be in `PATH` or configured at `firmware.rfp_tool_path`

---

## 3. UDS Flash Path

### 3.1 Flash sequence (automatic)
```
Programming Session (0x10 02)
  → Security Access: Request Seed (0x27 01) → Compute Key → Send Key (0x27 02)
  → Erase Memory Routine (0x31 01 FF00 xx)
  → Request Download (0x34) — negotiate block size
  → Transfer Data (0x36) × N blocks — 256 bytes each
  → Transfer Exit (0x37)
  → Check Programming Integrity Routine (0x31 01 02 02)
  → ECU Reset Hard (0x11 01)
```

### 3.2 CAN interface configuration
```bash
# Physical CAN at 500 kbps
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0

# Verify
ip link show can0
```

### 3.3 Config for UDS flash
```json
{
  "can": {
    "interface": "can0",
    "bitrate": 500000
  },
  "uds": {
    "tx_id": "0x7E0",
    "rx_id": "0x7E8",
    "p2_timeout_ms": 50,
    "p2_star_timeout_ms": 10000
  },
  "firmware": {
    "method": "uds",
    "target_address": "0x08000000",
    "erase_routine_id": "0xFF00",
    "checksum_routine_id": "0x0202",
    "block_size": 256,
    "security_level": 1
  }
}
```

### 3.4 Running a UDS flash
```bash
FIRMWARE_FILE=firmware/tcu_v2.1.0.hex \
CAN_INTERFACE=can0 \
FLASH_METHOD=uds \
scripts/flash_firmware.sh
```

Or via tcu_validator directly:
```bash
build/Release/bin/tcu_validator \
    --config configs/production.json \
    --interface can0 \
    --suite FirmwareFlash
```

### 3.5 Expected console output
```
[12:00:00.100] [info] [FirmwareFlasher] CRC-32 check: PASS (0xCBF43926)
[12:00:00.150] [info] [UDSClient] Programming session: OK
[12:00:00.200] [info] [UDSClient] Security access level 1: OK
[12:00:01.000] [info] [FirmwareFlasher] Erase: OK (850ms)
[12:00:01.050] [info] [FirmwareFlasher] Download negotiated: max_block=256
[12:00:05.000] [info] [FirmwareFlasher] Transfer: 100% (512 blocks, 131072 bytes)
[12:00:05.100] [info] [UDSClient] Integrity check: OK
[12:00:05.200] [info] [UDSClient] ECU reset: OK
[12:00:05.201] [info] [FirmwareFlasher] Flash complete
```

---

## 4. RFP CLI Path

### 4.1 Install Renesas Flash Programmer CLI
Download from Renesas website and install:
```bash
sudo apt-get install ./rfp-linux-x64.deb
which rfp-cli     # Should print /usr/bin/rfp-cli
```

### 4.2 Config for RFP
```json
{
  "firmware": {
    "method": "rfp",
    "rfp_tool_path": "/usr/bin/rfp-cli",
    "rfp_device": "RH850/C1x",
    "rfp_interface": "E2",
    "rfp_clock_khz": 6000
  }
}
```

### 4.3 Running an RFP flash
```bash
FIRMWARE_FILE=firmware/tcu_v2.1.0.mot \
FLASH_METHOD=rfp \
scripts/flash_firmware.sh
```

### 4.4 RFP progress output
The framework parses `rfp-cli` stdout for `Progress: NN%` patterns and forwards them to the progress callback registered in the test suite.

---

## 5. CRC-32 Pre-Flash Validation

Before any flash operation, the framework verifies file integrity:

```cpp
// Performed automatically in FirmwareFlasher::flash_via_uds() / flash_via_rfp()
bool ok = CRCValidator::verify_file(firmware_path, expected_crc32);
```

To compute the expected CRC of a firmware file manually:
```bash
python3 -c "
import struct, zlib, sys
data = open(sys.argv[1], 'rb').read()
crc = zlib.crc32(data) & 0xFFFFFFFF
print(f'CRC-32: 0x{crc:08X}')
" firmware/tcu_v2.1.0.hex
```

Then add to your test config:
```json
{
  "firmware": {
    "expected_crc32": "0xCBF43926"
  }
}
```

---

## 6. Simulation Mode Flash Test

To verify the flash logic without real hardware:

```bash
./build/Debug/bin/tcu_validator \
    --config configs/test.json \
    --simulate \
    --suite FirmwareFlash
```

In simulation mode:
- UDS responses are provided by a mock ECU callback registered in `main.cpp`
- No physical CAN frames are sent
- Progress callbacks still fire, allowing verification of the flash flow
- CRC validation is still performed on the firmware file

---

## 7. Troubleshooting

### "NRC 0x22 — conditionsNotCorrect"
ECU is not in Programming Session. Check:
- ECU is not in Safe Mode
- No active DTCs blocking programming
- `session_control(PROGRAMMING)` is being called first

### "NRC 0x36 — requestSequenceError"
Wrong sequence: `request_download()` must be called before `transfer_data()`.

### "NRC 0x31 — requestOutOfRange"
Erase routine ID or memory address is incorrect for this ECU. Verify with OEM documentation.

### "Security access failed: NRC 0x35 invalidKey"
Key calculation is wrong. Verify your seed-key algorithm matches the ECU's expected algorithm.

### "Transfer timeout after N blocks"
- P2* timeout too short — increase `p2_star_timeout_ms` to 15000
- ECU internal flash write latency exceeded — use `send_tester_present()` in the inter-block gap

### RFP: "rfp-cli exited with code 1"
- Check that the device is correctly identified: `rfp_device` must match exactly
- Verify USB/JTAG probe is connected and recognised by the OS
- Run `rfp-cli --list` to list available devices
