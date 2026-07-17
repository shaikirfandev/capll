# QNX, AUTOSAR, CAN, Ethernet and SOME/IP Adapters

The C++ core deliberately has no direct dependency on a network stack, QNX API, AUTOSAR API, CUDA, DriveOS, or Qualcomm SDK. This separation maintains deterministic unit-test behavior and prevents platform details from entering the safety-control code. Create target adapters in a separately reviewed integration repository or target-specific layer.

## QNX Neutrino deployment

Create one periodic control thread that invokes `ControlRuntime::run_cycle()` every 20 ms. The target adapter must configure its scheduling policy, priority, CPU affinity, memory locking, stack allocation, and watchdog according to the platform safety architecture. The control-thread contract is:

1. Consume one coherent `SensorFrame` snapshot from an SPSC queue.
2. Call `run_cycle()` with the monotonic timestamp and measured period.
3. Pass `ActuatorCommand` through the guarded actuator gateway.
4. Record `CycleHealth` to a non-real-time diagnostic publisher.

Do not perform socket reads, DNS, SOME/IP discovery, dynamic allocation, file writes, console output, D-Bus operations, or blocking mutex acquisition in this task. QNX receive threads must timestamp and validate traffic before publishing it.

Measure WCET with QNX tracing on the actual NVIDIA DRIVE or Qualcomm target, under representative perception and Ethernet load. GPU/NPU inference is asynchronous upstream work; its output is valid only after its own deadline, coordinate-frame, and freshness validation.

## AUTOSAR Classic mapping

| Core concept | AUTOSAR Classic mapping |
|---|---|
| `SensorFrame` | Sender/receiver data elements collected by an input adapter SWC |
| `ControlRuntime::run_cycle()` | 20 ms timing-event runnable via generated RTE |
| `ActuatorCommand` | Sender port to a validated actuator-arbitration SWC |
| `Fault` / `CycleHealth` | Diagnostic event and mode-management inputs |
| CAN/Ethernet integrity | COM/PduR/SoAd plus configured E2E and deadline monitoring |

Use generated RTE headers only in the adapter. The application runnable converts RTE data to a coherent frame after checking validity/status flags. Keep C++ exceptions, RTTI, heap allocation, and unbounded containers disabled or governed by the selected platform/coding standard.

## AUTOSAR Adaptive mapping

Run the core inside an Execution Management supervised process. The adapter translates ara::com service samples (typically SOME/IP) into `SensorFrame` values, preserving source timestamp and data validity. Publish commands as a separate service and let a dedicated actuator service enforce E2E, lifecycle, and authority rules. Integrate health reports with Health Management and diagnostics according to the program architecture.

## Protocol adapter checklist

### CAN / CAN-FD

- Decode only messages with expected identifier, DLC, alive counter and CRC/E2E profile.
- Apply DBC scaling, offsets, signedness, and little/big endian conversion in one adapter.
- Reject repeated/rolled-back counters and timestamp every accepted data set.
- Use a signal timeout that is shorter than the controller's accepted frame age.

### Automotive Ethernet / SOME/IP

- Authenticate or segment ingress per the cybersecurity architecture.
- Enforce service/version/interface contracts, payload length, sequence, and timeouts.
- Treat service availability as a lifecycle event; do not block the controller waiting for discovery.
- Keep the source timestamp rather than substituting receive time when calculating data age.

## CANoe and HIL evidence

CANoe/CAPL may act as restbus simulation and fault injector. Build reusable scenarios for valid traffic, counter/CRC errors, delayed frames, signal freezes, dropped services, cut-in, pedestrian/vehicle braking targets, lane disappearance, and driver override. Record controller input timestamp, output command, fault mask, and test verdict. HIL tests must exercise the actual QNX adapter and target gateway—not just the portable core.
