# Bluetooth Firmware — Interview Q&A

> 20 senior-level interview questions derived from this codebase.
> Target: Harman, Qualcomm Automotive, Bosch, Continental, KPIT, Aptiv, Valeo.

---

## Q1. Why is `BluetoothController` a Singleton? What are the risks?

**A:** Hardware imposes the constraint — only one HCI UART exists, so multiple instances would race on the same file descriptor. A Meyers Singleton (`static BluetoothController inst; return inst;`) is thread-safe since C++11.

**Risks:** Hard to unit-test (mock injection is difficult), global mutable state makes reasoning harder. Mitigated by extracting the `IBluetoothController` interface — tests inject a mock without touching the singleton.

---

## Q2. How does your EventBus guarantee thread safety?

**A:** The subscriber map is guarded by `std::shared_mutex`:
- `subscribe()`/`unsubscribe()` take an exclusive write lock.
- `publish()` iterates subscribers under a shared (read) lock, allowing concurrent readers.

`publish_async()` enqueues to `std::queue<BtEvent>` under a regular mutex, then signals a `condition_variable`. A dedicated dispatch thread drains the queue — callers never block.

---

## Q3. Explain the CRTP `StateMachine` template.

**A:** Curiously Recurring Template Pattern allows compile-time polymorphism:
```cpp
class ConnectionStateMachine
    : public StateMachine<ConnectionStateMachine, ConnState, ConnEvent>
```
The base class owns the transition table `map<{State,Event}, Transition>` where `Transition = {next_state, action_fn, guard_fn}`. `process_event()` looks up the pair, checks the guard, executes the action, and transitions — no virtual dispatch overhead.

---

## Q4. How does the lock-free RingBuffer work? When is it safe?

**A:** Head (write index, owned by producer) and tail (read index, owned by consumer) are `std::atomic<uint32_t>` on separate cache lines (64-byte alignment). The producer checks `(head+1) % N != tail` before writing; the consumer checks `head != tail` before reading. **Safe only for Single Producer Single Consumer (SPSC)** — adding a second producer would require a CAS loop or a mutex.

---

## Q5. What does Pimpl give you? Where does it cost?

**A:**
- **Benefits:** Clients don't recompile when private fields change (ABI firewall), hides implementation headers, enables forward declarations.
- **Cost:** One heap allocation per object, one pointer indirection per member access. In hot paths (e.g., GATT notify per packet), consider flattening the Pimpl.

---

## Q6. How does OtaManager handle a partial write (power loss mid-transfer)?

**A:** In this simulation the firmware accumulates to a RAM buffer — a power loss loses everything. In production (Nordic DFU / MCUboot), the approach is:
1. Write chunks to a secondary flash bank (bank B).
2. CRC-verify the entire image in bank B before the swap.
3. Write a "pending swap" flag to a persistent location.
4. Reboot — bootloader checks flag, swaps banks atomically, clears flag.

`abort_ota()` in this code clears the buffer and resets state — equivalent to reverting before the swap.

---

## Q7. What is the difference between `GattProp` and `GattPerm`?

**A:**
- `GattProp` (Characteristic Properties) — advertised in the characteristic declaration: `READ`, `WRITE`, `NOTIFY`, `INDICATE`, `WRITE_WITHOUT_RESPONSE`. These tell the client what operations are possible.
- `GattPerm` (Attribute Permissions) — enforced by the ATT layer: whether authentication/encryption is required to read or write. A characteristic can have `PROP::NOTIFY` but require `PERM::READ_ENCRYPTED` — the client must encrypt before subscribing.

---

## Q8. How does your Pairing implementation prevent MITM attacks?

**A:** Just Works offers no MITM protection (but encrypts the link). Passkey Entry and Numeric Comparison provide MITM protection — an eavesdropper cannot complete the protocol without observing/confirming the 6-digit value displayed on both devices. In this simulation, `generate_passkey()` uses Mersenne Twister — **not cryptographically secure**. Production uses the BT SIG SMP AES-CMAC based confirmation value (`Cb = f4(PKb, PKa, Nb, 0)`).

---

## Q9. Why does `ConnectionStateMachine` have an ERROR state? How do you recover?

**A:** Any unexpected event (e.g., CONNECTED event when already in CONNECTED state) transitions to ERROR — the FSM never silently ignores invalid input. Recovery: send `DISCONNECT_REQ` → transitions ERROR → IDLE, resetting the machine for reuse. This models real-world stack recovery where a link layer error forces reconnection.

---

## Q10. Explain the A2DP SBC streaming simulation.

**A:** `A2dpSimulator::start_stream()` launches a `std::thread` that sleeps 10ms per iteration (simulating 44.1kHz stereo at ~128kbps SBC → ~128 bytes per 10ms Bluetooth slot). The callback delivers `std::vector<uint8_t>` frames to the audio HAL. `frames_sent()` is an atomic counter useful for throughput testing. Production: frames come from an audio pipeline (e.g., AudioFlinger on Android) via the A2DP Sink/Source profile.

---

## Q11. What is an ATT handle and how are they allocated?

**A:** A 16-bit identifier for every attribute in the GATT server. Allocation in `GattServer::add_service()`:
1. Service declaration handle (type = 0x2800/0x2801)
2. Characteristic declaration handle (type = 0x2803)  
3. Characteristic value handle (the one clients read/write)
4. CCCD descriptor handle (0x2902) — allocated only if char has NOTIFY/INDICATE

Handles increment from 0x0001 sequentially. The service must declare the handle range in the service declaration (not shown in this simulation for brevity).

---

## Q12. How does `L2capManager` differ from a raw HCI ACL connection?

**A:** HCI ACL is the raw data pipe (identified by `ConnHandle`). L2CAP multiplexes multiple logical channels over it using PSM (Protocol/Service Multiplexer) and CID (Channel ID). L2CAP also provides flow control, segmentation/reassembly, and MTU negotiation. In this implementation, `register_psm()` maps a PSM to a data handler; `open_channel()` allocates a dynamic CID (starts at 0x0040 per BT spec) and returns it to the caller.

---

## Q13. What would change to port from simulation to real hardware (TI CC2642R)?

**A:**
1. Replace `BluetoothController` with TI BLE5-Stack `HCI_*` API calls.
2. Replace `StdThread*` with `FreeRTOS*` implementations of the same RTOS interfaces.
3. Replace `UartDriver` with TI UART DMA driver (`UARTCC26X2.h`).
4. Replace `GpioDriver` with TI GPIO driver (`GPIO.h`).
5. Remove `std::thread`, `std::mutex` — use `osMutexId_t`, `osThreadId_t`.
6. All application/profile code is unchanged — interfaces absorb the hardware difference.

---

## Q14. How is the `BtError` propagation mechanism (BT_TRY) inspired by Rust?

**A:** Rust's `?` operator: if a function returns `Err(e)`, it immediately returns that error from the calling function. `BT_TRY(expr)` expands to:
```cpp
{ BtError _e = (expr); if (_e != BtError::OK) return _e; }
```
This eliminates nested `if (err != OK) return err;` boilerplate while keeping explicit error handling — no exceptions thrown.

---

## Q15. What is the difference between `publish()` and `publish_async()` in EventBus?

**A:**
- `publish()` — synchronous: iterates all subscribers on the **caller's thread** under a shared lock. Subscribers run before `publish()` returns. Risk: if a subscriber takes the mutex or does I/O, it blocks the caller (e.g., HCI interrupt context).
- `publish_async()` — non-blocking: enqueues `BtEvent` to an internal `std::queue`, signals the dispatch thread via `condition_variable`, and returns immediately. The dispatch thread runs subscribers in the background. Use for events originating in interrupt context or timing-sensitive paths.

---

## Q16. Why use `std::variant<...>` for `BtEvent` instead of virtual inheritance?

**A:** `std::variant` is a type-safe discriminated union — no heap allocation, no vtable, compile-time exhaustive checks via `std::visit`. With virtual inheritance, adding a new event type requires a new class, a vtable entry, and a heap allocation per event. With `variant`, adding `EvtNewEvent` means extending the `using BtEvent = std::variant<..., EvtNewEvent>` — compile error if any `std::visit` lambda doesn't handle it.

---

## Q17. How does CCCD (Client Characteristic Configuration Descriptor) work?

**A:** A 2-byte descriptor at handle `value_handle + 1` that a connected client writes to opt into `NOTIFY` (bit 0) or `INDICATE` (bit 1). The server reads the CCCD before calling `notify()` — if the client hasn't subscribed (value = 0x0000), the notification is dropped. In `GattServer::add_service()`, a CCCD handle is allocated automatically when the characteristic has `GattProp::NOTIFY` or `INDICATE`.

---

## Q18. Describe the HFP call flow from incoming call to answer.

**A:**
1. HFP AG (phone) sends `+CLIP: "+1234567890",145` — caller ID.
2. AG sends `+CIEV: 3,1` — call setup indicator = incoming.
3. User sends `ATA` — HF accepts the call.
4. AG sends `+CIEV: 2,1` — call active indicator = active.
5. Audio connection established (eSCO/SCO link).
6. End call: `AT+CHUP` or `ATH` → `+CIEV: 2,0`.

`HfpSimulator::process_at()` handles all these AT commands and returns the correct response strings.

---

## Q19. What makes the `RingBuffer` suitable for DMA → CPU data transfer?

**A:** DMA writes bytes to the ring buffer as the UART receives them (producer = DMA, runs at interrupt level). The CPU reads from the buffer at task level (consumer). Because they run on separate "threads" (interrupt vs. task) and never share ownership of the same index, no mutex is needed. The only requirement is that `head` and `tail` are `std::atomic` with at least `memory_order_acquire` on read and `memory_order_release` on write to prevent CPU reordering.

---

## Q20. How would you add a new BT profile (e.g., PBAP) to this architecture?

**A:**
1. Define `IPbap` interface in `include/bt/IPbap.hpp` with `pull_phonebook()`, `pull_vcards()`.
2. Create `src/bt/profiles/PbapClient.cpp` implementing `IPbap` using `RfcommSimulator` for the transport (PBAP uses RFCOMM + OBEX).
3. Register an RFCOMM service record (PBAP PSM = 0x0019).
4. Add `PbapClient.cpp` to `CMakeLists.txt` `bt_core` source list.
5. Instantiate in `main.cpp`.

No existing code changes — Open/Closed Principle satisfied by the interface-driven architecture.
