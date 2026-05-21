# Bluetooth Firmware — Test Strategy

## 1. Testing Pyramid

```
        /\
       /  \  Integration (3 suites)
      /    \  — Full stack: init → adv → scan → GATT
     /------\  — OTA: chunk transfer, CRC, abort
    /        \  — Pairing flow: Just Works / Passkey / NumComp
   /          \
  /────────────\  Unit Tests (7 suites, ~40 test cases)
 /              \  — RingBuffer, EventBus, BleAdvertiser,
/________________\   GattServer, PairingMgr, SecurityMgr, CSM
```

## 2. Unit Test Suites

| Suite | File | Key Scenarios |
|---|---|---|
| RingBuffer | `test_ring_buffer.cpp` | Empty/full, wrap-around, SPSC concurrent (10k items) |
| ConnectionStateMachine | `test_connection_statemachine.cpp` | All valid transitions, illegal transitions → ERROR, recovery |
| BleAdvertiser | `test_ble_advertiser.cpp` | Start/stop via MockBtController, invalid interval, double-start |
| GattServer | `test_gatt_server.cpp` | Add service, set/get value, read/write callbacks |
| PairingManager | `test_pairing_manager.cpp` | Initiate, accept, reject, remove bond |
| SecurityManager | `test_security_manager.cpp` | Initial level NONE, LTK generation (non-zero, 16 bytes), SMP MAC |
| EventBus | `test_event_bus.cpp` | Sync/async publish, multi-subscriber, unsubscribe, stress (1k events) |

## 3. Integration Test Suites

| Suite | File | Description |
|---|---|---|
| BT Stack | `test_bt_stack_integration.cpp` | End-to-end: init, advertise, scan (700ms), GATT register, EventBus |
| OTA | `test_ota_integration.cpp` | Single chunk, 4×16-byte chunks, bad CRC, abort, overflow, zero-size |
| Pairing Flow | `test_pairing_flow.cpp` | Just Works, Passkey Entry, Numeric Comparison, encryption after pairing |

## 4. Mock Strategy

All mocks in `tests/unit/mocks/` using GMock `MOCK_METHOD`:

| Mock | Interface Mocked |
|---|---|
| `MockBtController` | `IBluetoothController` (25 methods) |
| `MockUart` | `IUart` |
| `MockSpi` | `ISpi` |
| `MockPowerManager` | `IPower` |
| `MockRtosQueue` | `IRtosQueueBase` |

## 5. Sanitizers

| Sanitizer | CMake Flag | Catches |
|---|---|---|
| AddressSanitizer | `-DBT_ASAN=ON` | Buffer overflows, use-after-free, heap corruption |
| ThreadSanitizer | `-DBT_TSAN=ON` | Data races, lock-order inversions |
| UBSan | Enabled with ASan | Integer overflow, null dereference, misaligned access |

## 6. Coverage Target

- Unit tests: > 80% line coverage on `src/bt/` and `src/common/`
- Collected via `lcov` + reported to Codecov in CI
- Coverage flag: `-DBT_COVERAGE=ON` → adds `--coverage` to compile/link flags

## 7. CI Matrix

```yaml
matrix:
  build_type: [Debug, Release]
  sanitizer: [none, asan, tsan]
  # Release + tsan excluded (unusual combination)
```

Total: 5 CI jobs per push to main/develop.
