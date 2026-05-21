# Architecture Document — Bluetooth Firmware v2.1.0

## 1. Overview

This document describes the software architecture of the Bluetooth Firmware project — a production-representative C++17 implementation of a complete BT/BLE stack for embedded automotive ECUs.

**Scope:** All software layers from HAL drivers up to application-level connection management, OTA, and diagnostics.

---

## 2. Architectural Layers

### Layer 0 — RTOS Abstraction
| Class | Interface | Description |
|---|---|---|
| `StdThreadTask` | `IRtosTask` | Wraps `std::thread` |
| `StdMutex` | `IRtosMutex` | Wraps `std::timed_mutex` |
| `StdQueueBase` | `IRtosQueueBase` | Wraps `std::queue + condvar` |
| `StdSemaphore` | `IRtosSemaphore` | Counting semaphore via condvar |

On FreeRTOS target, replace each `Std*` concrete class with `FreeRTOS*` implementations of the same interface — **zero application-layer changes required**.

### Layer 1 — HAL
| Class | Interface | Description |
|---|---|---|
| `UartDriver` | `IUart` | LPUART DMA simulation, `inject_rx()` test hook |
| `SpiDriver` | `ISpi` | SPI loopback simulation |
| `GpioDriver` | `IGpio` | Pin state map + IRQ simulation |
| `PowerManager` | `IPower` | Power FSM: ACTIVE/SLEEP/OFF |

### Layer 2 — BT Stack Core
| Class | Interface | Description |
|---|---|---|
| `BluetoothController` | `IBluetoothController` | HCI transport singleton |
| `EventBus` | `IEventBus` | Sync + async BtEvent dispatch |
| `ConnectionStateMachine` | `IConnectionStateMachine` | 10-state FSM |
| `GattServer` | `IGattServer` | ATT handle allocation, CCCD |
| `GattClient` | `IGattClient` | Service discovery, notify subscribe |
| `BleAdvertiser` | `IBleAdvertiser` | AD record builder, automotive AD data |
| `BleScanner` | `IBleScanner` | RSSI-filtered scan results |
| `PairingManager` | `IPairingManager` | SMP pairing methods, bond storage |
| `SecurityManager` | `ISecurityManager` | LTK/IRK generation, encryption |
| `L2capManager` | `IL2capManager` | PSM registry, CID allocation |
| `AttProtocol` | — | ATT PDU encoder/decoder |
| `RfcommSimulator` | — | RFCOMM MUX over L2CAP |

### Layer 3 — BT Profiles
| Class | Description |
|---|---|
| `A2dpSimulator` | SBC audio streaming, state: IDLE/CONNECTED/STREAMING |
| `HfpSimulator` | AT command handler (ATA, ATD, AT+CHUP, AT+CIND, etc.) |
| `HidDevice` | USB HID keyboard report descriptor, key reports |

### Layer 4 — Application
| Class | Interface | Description |
|---|---|---|
| `ConnectionManager` | `IConnectionManager` | Multi-connection mgmt, reconnection |
| `OtaManager` | `IOtaManager` | DFU: chunked transfer, CRC-32, FSM |
| `DiagnosticsModule` | `IDiagnosticsModule` | Health counters, rolling event log |

---

## 3. Key Design Patterns

### 3.1 Pimpl (Pointer to Implementation)
Every concrete class uses:
```cpp
struct Impl { /* private fields */ };
std::unique_ptr<Impl> impl_;
```
Benefits: fast recompilation, ABI stability, strong encapsulation.

### 3.2 Singleton (BluetoothController)
Hardware mirrors the singleton constraint — only one HCI transport exists. Implemented as a `static` local variable in `instance()` (Meyers Singleton — thread-safe since C++11).

### 3.3 Observer (EventBus)
```
Publisher     → publish(BtEvent)  → EventBus → subscriber callbacks
              → publish_async()   → queue    → async dispatch thread
```
Thread safety: `std::shared_mutex` for subscriber map (allows concurrent reads).

### 3.4 CRTP StateMachine
```cpp
template<typename Derived, typename StateT, typename EventT>
class StateMachine {
    std::map<std::pair<StateT,EventT>, Transition> table_;
};
```
`ConnectionStateMachine : StateMachine<ConnectionStateMachine, ConnState, ConnEvent>`

### 3.5 Lock-Free SPSC RingBuffer
Cache-line aligned `std::atomic<uint32_t>` head/tail. Single producer single consumer — no mutex. Used for HCI RX DMA → event pump thread.

---

## 4. Thread Model

| Thread | Purpose |
|---|---|
| Main thread | Init sequence, demo loop |
| `BluetoothController::event_pump_` | Dispatches simulated HCI events |
| `EventBus::dispatch_thread_` | Async BtEvent delivery to subscribers |
| `BleScanner::scan_thread_` | Generates simulated scan results every 300ms |
| `A2dpSimulator::stream_thread_` | Sends 128-byte SBC frames every 10ms |
| Per `StdThreadTask` | User-created tasks via RTOS abstraction |

---

## 5. Data Flow — BLE Connection

```
BleAdvertiser::start()
    → IBluetoothController::start_advertising()
    → [peer device connects]
    → HCI LE Connection Complete event
    → EventBus::publish(EvtConnected)
    → ConnectionManager::on_connected()
    → PairingManager::initiate_pairing()
    → [pairing complete]
    → GattServer (service discovery)
    → GattServer::notify()  // Battery level, HRM, etc.
    → ConnectionManager::disconnect()
    → HCI Disconnection Complete event
    → EventBus::publish(EvtDisconnected)
```

---

## 6. OTA Data Flow

```
OtaManager::start_ota(conn, size, expected_crc32)
    → state = RECEIVING
    → write_chunk(data, len) × N
        → accumulate to firmware_buffer
        → running_crc updated via CRC-32/IEEE 802.3
    → [last chunk]
        → state = VERIFYING
        → CRC check: running_crc == expected_crc32?
        → OK  → state = APPLYING → COMPLETE
        → FAIL → state = ERROR, complete_cb(false)
```
