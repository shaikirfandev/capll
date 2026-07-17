# Trace Event Codes — ADAS Real-Time Platform

## Subsystem IDs

| ID | Name |
|---|---|
| 0 | Supervisor |
| 1 | Sensor fusion (EKF) |
| 2 | Vehicle gateway |
| 3 | Runtime shell |
| 4 | CAN adapter |
| 5 | SOME/IP adapter |
| 6 | Diagnostics |

## Event codes (hex)

### Supervisor (subsystem 0)

| Code | Level | Description |
|---|---|---|
| 0x0001 | Info | Cycle start |
| 0x0002 | Info | Longitudinal mode changed |
| 0x0003 | Info | Lateral mode changed |
| 0x0010 | Warning | Frame stale — standby activated |
| 0x0011 | Warning | Frame invalid — standby activated |
| 0x0012 | Warning | Driver override detected |
| 0x0013 | Warning | Brake unavailable |
| 0x0014 | Warning | Steering unavailable |
| 0x0015 | Warning | Lead object unavailable |
| 0x0016 | Warning | Lane model unavailable |
| 0x0020 | Error | AEB triggered — `value_a` = TTC (s) |
| 0x0030 | Fatal | Configuration invalid — control inhibited |

### EKF (subsystem 1)

| Code | Level | Description |
|---|---|---|
| 0x0101 | Info | EKF initialized |
| 0x0110 | Warning | Wheel speed update rejected |
| 0x0111 | Warning | Yaw rate update rejected |
| 0x0112 | Warning | Lateral accel update rejected |
| 0x0120 | Error | NaN detected in state — filter reset |

### Gateway (subsystem 2)

| Code | Level | Description |
|---|---|---|
| 0x0201 | Info | Frame published |
| 0x0202 | Info | Command written |
| 0x0210 | Warning | Frame queue overrun (frame dropped) |
| 0x0220 | Error | Gateway write failure |

### Runtime (subsystem 3)

| Code | Level | Description |
|---|---|---|
| 0x0301 | Info | Cycle completed — `value_a` = execution µs |
| 0x0310 | Warning | Deadline missed — `value_a` = execution µs, `value_b` = limit µs |

### CAN adapter (subsystem 4)

| Code | Level | Description |
|---|---|---|
| 0x0401 | Info | Frame received |
| 0x0410 | Warning | Signal out of range — ignored |
| 0x0411 | Warning | Counter / CRC failure |
| 0x0420 | Error | DLC too small — frame dropped |

### SOME/IP adapter (subsystem 5)

| Code | Level | Description |
|---|---|---|
| 0x0501 | Info | Service discovered |
| 0x0510 | Warning | Service lost |
| 0x0511 | Warning | Method call failed |
| 0x0520 | Error | Event notification failed |

## Usage in real-time code

```cpp
TraceRecord rec;
rec.timestamp_us = std::chrono::duration_cast<std::chrono::microseconds>(
    TimePoint::clock::now().time_since_epoch()).count();
rec.level        = TraceLevel::Warning;
rec.subsystem_id = 0U;   // supervisor
rec.event_code   = 0x0010U;
rec.value_a      = static_cast<float>(frame_age_ms);
trace_logger.push(rec);
```

## Off-path consumer

A background thread calls `TraceLogger::pop()` and either serializes to a binary ring file or forwards over a non-real-time Ethernet socket to a host logging tool (e.g., Vector Logging Console, CANoe).
