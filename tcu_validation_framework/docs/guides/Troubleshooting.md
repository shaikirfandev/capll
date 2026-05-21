# Troubleshooting Guide
## TCU Validation Framework v2.0.0

---

## 1. Build Issues

### CMake version too old
```
CMake Error: CMake 3.18 or higher is required.
```
**Fix:**
```bash
# Ubuntu 20.04 — install newer CMake via Kitware APT
wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc | sudo apt-key add -
sudo add-apt-repository 'deb https://apt.kitware.com/ubuntu/ focal main'
sudo apt-get update && sudo apt-get install cmake
```

### FetchContent download fails
```
CMake Error at CMakeLists.txt:XX: Failed to download spdlog
```
**Fix:**
- Check internet access from the build machine
- Use `FETCHCONTENT_FULLY_DISCONNECTED=ON` with pre-downloaded sources
- Behind a proxy: set `https_proxy` environment variable before running cmake

### Sanitizer library missing
```
/usr/bin/ld: cannot find -lasan
```
**Fix:**
```bash
sudo apt-get install libasan6 libubsan1
```
Or disable sanitizers:
```bash
cmake -S . -B build/Debug -DENABLE_SANITIZERS=OFF
```

---

## 2. CAN Interface Issues

### `open()` returns false — interface not found
```
[error] [CANManager] Failed to find interface: can0
```
**Check:**
```bash
ip link show type can
ls /sys/class/net/
```
**Fix:** Use `vcan0` for development, or load the correct kernel driver for your hardware:
```bash
sudo modprobe peak_usb   # PEAK USB adapters
sudo modprobe kvaser_usb  # Kvaser
```

### `bind()` fails with ENXIO
Interface exists but SocketCAN is not the type.  
**Fix:**
```bash
# Verify interface type
ip -details link show can0 | grep "link/can"
# If missing, interface is not a CAN interface
```

### CAN frames not received (vcan0 loopback)
When using vcan0 for loopback tests, sender and receiver share the same socket. The kernel loops back transmitted frames automatically on vcan0.  
**Debug:**
```bash
candump vcan0 &
cansend vcan0 123#DEADBEEF
# Should see output from candump
```

If `candump` shows nothing, vcan0 is not up:
```bash
sudo ip link set up vcan0
```

### `ENOBUFS` on send — TX queue overflow
**Fix:** Increase socket TX buffer:
```bash
sudo ip link set can0 txqueuelen 1000
```

---

## 3. UDS Timeout Issues

### `UDSResult.success = false`, `error_message = "P2 timeout"`
**Cause:** ECU is not responding within P2 timeout (default 50 ms).

**Checks:**
1. Is the UDS TX/RX CAN ID correct?
   ```json
   { "uds": { "tx_id": "0x7E0", "rx_id": "0x7E8" } }
   ```
2. Is the ECU powered and in Default Session?
3. Is CAN traffic visible?
   ```bash
   candump can0 | grep "7E"
   ```
4. Increase P2 timeout:
   ```json
   { "uds": { "p2_timeout_ms": 200 } }
   ```

### NRC 0x78 (responsePending) loop not terminating
ECU is taking longer than `p2_star_timeout_ms` (default 5000 ms) to complete the service.  
**Fix:**
```json
{ "uds": { "p2_star_timeout_ms": 15000 } }
```

### NRC 0x22 (conditionsNotCorrect)
ECU refuses the service in current state.  
**Check:**
- Send `session_control(EXTENDED)` or `session_control(PROGRAMMING)` first
- Clear any active DTCs that may block the service
- Verify ignition cycle requirements for the target service

### NRC 0x33 (securityAccessDenied)
- ECU is locked after too many failed security access attempts
- Key algorithm is incorrect
- Wait 10+ minutes or perform a power cycle to reset the lockout counter

---

## 4. OTA Issues

### `check_for_updates()` returns `nullopt` in production mode
**Check:**
- MQTT broker is reachable: `mosquitto_sub -h broker-host -t '#' -v`
- TLS certificates are correct and not expired
- Device ID matches server-side record

### OTA acknowledge fails
The `acknowledge_ota()` publish returns false.  
**Check:**
- `is_connected()` returns true before calling acknowledge
- MQTT broker allows publish on the OTA ACK topic

### OTA progress not visible on server
Verify the progress topic path configured on the OEM SDK side. The framework publishes to `telematics/progress/{device_id}` by default.

---

## 5. Firmware Flash Issues

### CRC-32 mismatch before flash
```
[error] [FirmwareFlasher] CRC-32 verification failed: expected=0x12345678 computed=0xABCDEF01
```
**Cause:** Firmware file is corrupted or truncated during transfer.  
**Fix:** Re-download the firmware file and verify its checksum:
```bash
python3 -c "
import zlib, sys
data = open(sys.argv[1], 'rb').read()
print(hex(zlib.crc32(data) & 0xFFFFFFFF))
" firmware/tcu.hex
```

### Flash fails at "Transfer Data" block N
**Checks:**
1. `block_size` is too large — try 128 instead of 256
2. ECU flash write timing — increase `p2_star_timeout_ms`
3. Supply voltage dropped during flash — monitor with multimeter

### ECU does not respond after reset
The ECU may be in an inconsistent state.  
**Recovery options:**
1. Power cycle the ECU
2. Use the RFP CLI path as a fallback (bypasses UDS)
3. If hardware bootloader is available, trigger it via BOOT pin

---

## 6. Test Engine Issues

### Tests always return TIMEOUT
- `timeout_ms` is too small for the operation being tested
- Background threads (Rx, heartbeat) are blocking test execution
- ASan slow-down: sanitizer builds are 2–5× slower

**Fix:** Increase timeout, or disable sanitizers for timing-sensitive tests:
```bash
cmake -S . -B build/NoSan -DENABLE_SANITIZERS=OFF -DCMAKE_BUILD_TYPE=Debug
```

### `SKIP` verdict unexpectedly
The `precondition` lambda returned false.  
**Debug:** Add a log line inside the precondition:
```cpp
.precondition = [&]() {
    bool ok = can_mgr->is_open();
    if (!ok) log->warn("Precondition failed: CAN not open");
    return ok;
}
```

---

## 7. Config Issues

### Config key returns default value unexpectedly
**Check dot-path:**
```bash
# Verify structure with jq
jq '.can.interface' configs/default.json
```

**Check env override format:**
```bash
# Correct
export TCU_CFG_CAN_INTERFACE=vcan0   # → can.interface

# Wrong — double underscore creates nested keys
export TCU_CFG_CAN__INTERFACE=vcan0  # → can..interface (invalid)
```

### Hot reload not triggering
- The mtime polling interval is 1 second — edits must be saved completely before the check fires
- On NFS or Docker bind mounts, mtime may not update as expected

---

## 8. Logging Issues

### No log output
`Logger::init()` was not called before first use. Ensure `initialize()` is called on the Framework.

### Log file not created
Check that the directory exists and is writable:
```bash
ls -la logs/
# If missing:
mkdir -p logs && chmod 755 logs
```

### Too verbose / not verbose enough
```bash
export TCU_CFG_LOGGING_LEVEL=warn    # Only warnings and above
export TCU_CFG_LOGGING_LEVEL=debug   # Everything
```

Or at runtime:
```bash
./bin/tcu_validator --verbose --config configs/default.json
```
