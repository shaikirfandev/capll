# Sample System Specification Matrix
## SUV2026 — ADAS Safety Bus (CAN-HS1) — Communication Matrix v1.0

> **Project**: SUV2026 ADAS Development Program  
> **Bus**: CAN-HS1 (ADAS Safety Bus), 500 Kbps, ISO 11898-2  
> **Status**: BASELINE — For Training Reference Only  
> **Author**: Network Architecture Team  
> **Reviewed By**: System Safety, E/E Architecture

---

## Network Topology

```
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ AEB_ECU  │    │ ABS_ECU  │    │  ECM     │
        │(Radar)   │    │(Brakes)  │    │(Engine)  │
        └────┬─────┘    └────┬─────┘    └────┬─────┘
             │               │               │
     ════════╪═══════════════╪═══════════════╪════════ CAN-HS1 (500 Kbps)
             │               │               │
        ┌────┴─────┐    ┌────┴─────┐    ┌────┴─────┐
        │ EPS_ECU  │    │   CGW    │    │   IPC    │
        │(Steering)│    │(Gateway) │    │(Cluster) │
        └──────────┘    └────┬─────┘    └──────────┘
                             │
                    CAN-HS2 (Comfort Bus)
                             │
                        ┌────┴─────┐
                        │   BCM    │
                        │(Body)    │
                        └──────────┘
```

---

## Message Summary Table

| # | Message Name | ID (Hex) | ID (Dec) | DLC | Cycle | Tx ECU | ASIL | E2E |
|---|-------------|----------|----------|-----|-------|--------|------|-----|
| 1 | WheelSpeed | 0x200 | 512 | 8 | 10ms | ABS_ECU | B | Yes |
| 2 | AEB_Req | 0x244 | 580 | 8 | 20ms | AEB_ECU | B | Yes |
| 3 | VehicleStatus | 0x300 | 768 | 8 | 10ms | ECM | A | Yes |
| 4 | EPS_Status | 0x380 | 896 | 4 | 20ms | EPS_ECU | B | Yes |
| 5 | IPC_Display | 0x350 | 848 | 8 | 100ms | IPC | QM | No |
| 6 | BCM_Status | 0x420 | 1056 | 6 | 100ms | BCM | QM | No |

---

## Message 1: WheelSpeed

| Field | Value |
|-------|-------|
| Message Name | WheelSpeed |
| CAN ID | 0x200 (decimal: 512) |
| DLC | 8 bytes |
| Cycle Time | 10ms |
| Transmitter | ABS_ECU |
| Receivers | AEB_ECU, ECM, EPS_ECU, CGW |
| ASIL | B |
| E2E Protection | CRC + Alive Counter |
| Description | Four-wheel vehicle speed — safety critical for AEB and ESC |

### Signal Table

| Signal Name | Start Bit | Length | Byte Order | Type | Factor | Offset | Min | Max | Unit | Init | Invalid |
|-------------|-----------|--------|------------|------|--------|--------|-----|-----|------|------|---------|
| WheelSpeed_FL | 0 | 16 | Intel | Unsigned | 0.01 | 0 | 0 | 300.00 | km/h | 0 | 65535 |
| WheelSpeed_FR | 16 | 16 | Intel | Unsigned | 0.01 | 0 | 0 | 300.00 | km/h | 0 | 65535 |
| WheelSpeed_RL | 32 | 16 | Intel | Unsigned | 0.01 | 0 | 0 | 300.00 | km/h | 0 | 65535 |
| WheelSpeed_RR | 48 | 16 | Intel | Unsigned | 0.01 | 0 | 0 | 300.00 | km/h | 0 | 65535 |

**Bit layout:**
```
Byte:  |    B0    |    B1    |    B2    |    B3    |    B4    |    B5    |    B6    |    B7    |
Bits:  |7       0 |15      8 |23     16 |31     24 |39     32 |47     40 |55     48 |63     56 |
       [   WheelSpeed_FL    ][   WheelSpeed_FR    ][   WheelSpeed_RL    ][   WheelSpeed_RR    ]
```

---

## Message 2: AEB_Req

| Field | Value |
|-------|-------|
| Message Name | AEB_Req |
| CAN ID | 0x244 (decimal: 580) |
| DLC | 8 bytes |
| Cycle Time | 20ms |
| Transmitter | AEB_ECU |
| Receivers | CGW, IPC, ECM, BCM |
| ASIL | B |
| E2E Protection | CRC (byte 5) + Alive Counter (bits 36–39) |
| Description | AEB deceleration request — initiates emergency braking |

### Signal Table

| Signal Name | Start Bit | Length | Byte Order | Type | Factor | Offset | Min | Max | Unit | Init | Invalid |
|-------------|-----------|--------|------------|------|--------|--------|-----|-----|------|------|---------|
| AEB_Active | 0 | 1 | Intel | Unsigned | 1 | 0 | 0 | 1 | — | 0 | — |
| AEB_State | 1 | 3 | Intel | Unsigned | 1 | 0 | 0 | 7 | — | 0 | 7 |
| AEB_Decel_Req | 4 | 8 | Intel | Unsigned | 0.1 | 0 | 0 | 25.5 | m/s² | 0 | 255 |
| AEB_Obj_Distance | 12 | 16 | Intel | Unsigned | 0.01 | 0 | 0 | 655.35 | m | 65535 | 65535 |
| AEB_TTC | 28 | 8 | Intel | Unsigned | 0.01 | 0 | 0 | 2.55 | s | 255 | 255 |
| Alive_Ctr_AEB | 36 | 4 | Intel | Unsigned | 1 | 0 | 0 | 14 | — | 0 | 15 |
| CRC_AEB | 40 | 8 | Intel | Unsigned | 1 | 0 | 0 | 255 | — | 0 | — |
| Reserved_AEB | 48 | 16 | Intel | Unsigned | 1 | 0 | 0 | 65535 | — | 0 | — |

### Value Descriptions (VAL_)

| Signal | Raw | Description |
|--------|-----|-------------|
| AEB_State | 0 | OFF |
| AEB_State | 1 | STANDBY |
| AEB_State | 2 | WARNING |
| AEB_State | 3 | ACTIVE |
| AEB_State | 4 | FAULT |
| AEB_State | 5 | DEGRADED |
| AEB_State | 6 | OVERRIDE |
| AEB_State | 7 | NOT_AVAILABLE |

---

## Message 3: VehicleStatus

| Field | Value |
|-------|-------|
| Message Name | VehicleStatus |
| CAN ID | 0x300 (decimal: 768) |
| DLC | 8 bytes |
| Cycle Time | 10ms |
| Transmitter | ECM |
| Receivers | AEB_ECU, IPC, ABS_ECU, BCM, CGW |
| ASIL | A |
| Description | Engine and powertrain state — used by AEB for active system inhibition |

### Signal Table

| Signal Name | Start Bit | Length | Byte Order | Type | Factor | Offset | Min | Max | Unit | Init |
|-------------|-----------|--------|------------|------|--------|--------|-----|-----|------|------|
| EngineSpeed | 0 | 16 | Intel | Unsigned | 0.25 | 0 | 0 | 16383.75 | rpm | 0 |
| ThrottlePos | 16 | 8 | Intel | Unsigned | 0.4 | 0 | 0 | 100 | % | 0 |
| EngineTemp | 24 | 8 | Intel | Unsigned | 0.5 | -40 | -40 | 87.5 | °C | 0 |
| EngineState | 32 | 3 | Intel | Unsigned | 1 | 0 | 0 | 6 | — | 0 |
| TransmMode | 35 | 3 | Intel | Unsigned | 1 | 0 | 0 | 5 | — | 0 |
| FuelPress | 38 | 10 | Intel | Unsigned | 0.1 | 0 | 0 | 102.3 | bar | 0 |
| Alive_Ctr_VS | 48 | 4 | Intel | Unsigned | 1 | 0 | 0 | 14 | — | 0 |
| CRC_VS | 52 | 8 | Intel | Unsigned | 1 | 0 | 0 | 255 | — | 0 |

### Value Descriptions

| Signal | Raw | Description |
|--------|-----|-------------|
| EngineState | 0 | OFF |
| EngineState | 1 | CRANKING |
| EngineState | 2 | IDLE |
| EngineState | 3 | RUNNING |
| EngineState | 4 | OVERHEATING |
| EngineState | 5 | SHUTDOWN |
| EngineState | 6 | FAULT |
| TransmMode | 0 | PARK |
| TransmMode | 1 | REVERSE |
| TransmMode | 2 | NEUTRAL |
| TransmMode | 3 | DRIVE |
| TransmMode | 4 | SPORT |
| TransmMode | 5 | MANUAL |

---

## Message 4: EPS_Status

| Field | Value |
|-------|-------|
| Message Name | EPS_Status |
| CAN ID | 0x380 (decimal: 896) |
| DLC | 4 bytes |
| Cycle Time | 20ms |
| Transmitter | EPS_ECU |
| Receivers | AEB_ECU, IPC, CGW, BCM |
| ASIL | B |
| Description | Electric power steering state — steering angle for AEB path prediction |

### Signal Table

| Signal Name | Start Bit | Length | Byte Order | Type | Factor | Offset | Min | Max | Unit | Init |
|-------------|-----------|--------|------------|------|--------|--------|-----|-----|------|------|
| SteeringAngle | 0 | 16 | Intel | Signed | 0.1 | 0 | -3276.8 | 3276.7 | deg | 0 |
| SteeringTorque | 16 | 10 | Intel | Signed | 0.01 | -5.12 | -5.12 | 5.11 | Nm | 0 |
| EPS_State | 26 | 3 | Intel | Unsigned | 1 | 0 | 0 | 7 | — | 0 |
| EPS_Warning | 29 | 1 | Intel | Unsigned | 1 | 0 | 0 | 1 | — | 0 |
| Alive_Ctr_EPS | 30 | 2 | Intel | Unsigned | 1 | 0 | 0 | 3 | — | 0 |

### Value Descriptions

| Signal | Raw | Description |
|--------|-----|-------------|
| EPS_State | 0 | INIT |
| EPS_State | 1 | ACTIVE |
| EPS_State | 2 | DEGRADED |
| EPS_State | 3 | FAULT |
| EPS_State | 4 | OVERRIDE |
| EPS_State | 7 | NOT_AVAILABLE |

---

## Message 5: IPC_Display

| Field | Value |
|-------|-------|
| Message Name | IPC_Display |
| CAN ID | 0x350 (decimal: 848) |
| DLC | 8 bytes |
| Cycle Time | 100ms |
| Transmitter | IPC |
| Receivers | CGW |
| ASIL | QM |
| Description | Instrument cluster display commands and warning indicators |

### Signal Table

| Signal Name | Start Bit | Length | Byte Order | Type | Factor | Offset | Min | Max | Unit |
|-------------|-----------|--------|------------|------|--------|--------|-----|-----|------|
| Display_Speed | 0 | 12 | Intel | Unsigned | 0.1 | 0 | 0 | 409.5 | km/h |
| Display_RPM | 12 | 14 | Intel | Unsigned | 0.5 | 0 | 0 | 8191.5 | rpm |
| Display_Fuel_Pct | 26 | 8 | Intel | Unsigned | 0.5 | 0 | 0 | 127.5 | % |
| Display_Gear | 34 | 4 | Intel | Unsigned | 1 | 0 | 0 | 9 | — |
| MIL_On | 38 | 1 | Intel | Unsigned | 1 | 0 | 0 | 1 | — |
| ABS_Warning | 39 | 1 | Intel | Unsigned | 1 | 0 | 0 | 1 | — |
| EPS_Warning_Disp | 40 | 1 | Intel | Unsigned | 1 | 0 | 0 | 1 | — |
| Door_Ajar_Any | 41 | 1 | Intel | Unsigned | 1 | 0 | 0 | 1 | — |
| Alive_Ctr_IPC | 48 | 4 | Intel | Unsigned | 1 | 0 | 0 | 14 | — |
| CRC_IPC | 52 | 8 | Intel | Unsigned | 1 | 0 | 0 | 255 | — |

---

## Message 6: BCM_Status

| Field | Value |
|-------|-------|
| Message Name | BCM_Status |
| CAN ID | 0x420 (decimal: 1056) |
| DLC | 6 bytes |
| Cycle Time | 100ms |
| Transmitter | BCM |
| Receivers | CGW, IPC, AEB_ECU |
| ASIL | QM |
| Description | Body control module — door, lock, ignition, light status |

### Signal Table

| Signal Name | Start Bit | Length | Byte Order | Type | Factor | Offset | Min | Max | Unit |
|-------------|-----------|--------|------------|------|--------|--------|-----|-----|------|
| DoorFL_Status | 0 | 2 | Intel | Unsigned | 1 | 0 | 0 | 3 | — |
| DoorFR_Status | 2 | 2 | Intel | Unsigned | 1 | 0 | 0 | 3 | — |
| DoorRL_Status | 4 | 2 | Intel | Unsigned | 1 | 0 | 0 | 3 | — |
| DoorRR_Status | 6 | 2 | Intel | Unsigned | 1 | 0 | 0 | 3 | — |
| Hood_Status | 8 | 1 | Intel | Unsigned | 1 | 0 | 0 | 1 | — |
| Trunk_Status | 9 | 1 | Intel | Unsigned | 1 | 0 | 0 | 1 | — |
| IgnitionState | 10 | 3 | Intel | Unsigned | 1 | 0 | 0 | 4 | — |
| HazardActive | 13 | 1 | Intel | Unsigned | 1 | 0 | 0 | 1 | — |
| LowBeam | 14 | 1 | Intel | Unsigned | 1 | 0 | 0 | 1 | — |
| HighBeam | 15 | 1 | Intel | Unsigned | 1 | 0 | 0 | 1 | — |
| WiperState | 16 | 3 | Intel | Unsigned | 1 | 0 | 0 | 4 | — |
| Alive_Ctr_BCM | 40 | 4 | Intel | Unsigned | 1 | 0 | 0 | 14 | — |
| CRC_BCM | 44 | 8 | Intel | Unsigned | 1 | 0 | 0 | 255 | — |

### Value Descriptions

| Signal | Raw | Description |
|--------|-----|-------------|
| DoorXX_Status | 0 | CLOSED |
| DoorXX_Status | 1 | OPEN |
| DoorXX_Status | 2 | AJAR |
| DoorXX_Status | 3 | NOT_AVAILABLE |
| IgnitionState | 0 | OFF |
| IgnitionState | 1 | ACC |
| IgnitionState | 2 | ON |
| IgnitionState | 3 | START |
| IgnitionState | 4 | NOT_AVAILABLE |
| WiperState | 0 | OFF |
| WiperState | 1 | INTERMITTENT |
| WiperState | 2 | LOW |
| WiperState | 3 | HIGH |
| WiperState | 4 | WASH |

---

## ECU Node List

| ECU Name | Full Name | Supplier | Location |
|----------|-----------|---------|---------|
| AEB_ECU | Advanced Emergency Braking ECU | Continental | Front bumper |
| ABS_ECU | Anti-lock Braking System ECU | Bosch | Engine bay |
| ECM | Engine Control Module | Bosch | Engine bay |
| EPS_ECU | Electric Power Steering ECU | Jtekt | Steering column |
| IPC | Instrument Panel Cluster | Marelli | Dashboard |
| BCM | Body Control Module | Continental | Dashboard |
| CGW | Central Gateway ECU | Vector | Center console |

---

## Change History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 0.1 | 2025-01-10 | J. Smith | Initial draft |
| 0.5 | 2025-03-15 | J. Smith | Added E2E fields, ASIL assignments |
| 1.0 | 2026-05-27 | Shaik Irfan | Baseline for training |
