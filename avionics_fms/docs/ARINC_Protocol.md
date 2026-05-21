# ARINC 429 Protocol Reference
## Avionics FMS v3.2.1

## 1. Word Format (32-bit, LSB-first on bus)

```
Bit 32  31   30 29  28..11  10..9   8..1
+-----+----+----+--+-------+------+------+
| PAR | SSM[1:0] | DATA    | SDI  | LABEL|
+-----+----+----+--+-------+------+------+
 Parity Sign/Status Matrix  Source/Dest   Label (octal, reversed)
```

| Field | Bits | Description |
|-------|------|-------------|
| Label | 1-8  | Identifies parameter (octal, LSB-first transmitted) |
| SDI   | 9-10 | Source/Destination Identifier |
| Data  | 11-29| BNR or BCD payload |
| SSM   | 29-30| Sign/Status Matrix |
| Parity| 31   | Odd parity |

## 2. SSM Values
| Value | Binary | Meaning |
|-------|--------|---------|
| NORMAL_OP | 11 | Data valid, normal operation |
| NO_COMPUTED_DATA | 10 | No computed data available |
| FUNCTIONAL_TEST  | 01 | Functional test in progress |
| FAILURE_WARNING  | 00 | Equipment failure |

## 3. Common Labels (Octal)

| Label | Octal | Parameter | Range | Resolution |
|-------|-------|-----------|-------|------------|
| 0203  | 0203  | Pressure Altitude | +/- 131072 ft | 1 ft |
| 0206  | 0206  | Computed Airspeed | 0..512 kt | 0.25 kt |
| 0210  | 0210  | Mach Number | 0..4.096 | 0.000488 |
| 0270  | 0270  | True Heading | 0..360 deg | 0.00549 deg |
| 0361  | 0361  | Ground Speed | 0..2048 kt | 0.5 kt |
| 0174  | 0174  | Wind Speed | 0..256 kt | 1 kt |

## 4. BNR Encoding

```
range    = max_value - min_value
resolution = range / 2^(N-1)   where N = number of data bits
counts    = round(value / resolution)
word_data = counts & ((1 << N) - 1)  // N-bit 2's complement
```

Example: Altitude 35000 ft, 18-bit BNR, resolution 1.0 ft
- counts = 35000
- Encoded = 0x8878 (18-bit)

## 5. Label Reversal

Labels are transmitted LSB-first. Software must reverse the 8-bit label:
- Label 203 octal = 0x83 = 10000011b
- Reversed = 11000001b = 0xC1 = 0301 octal

## 6. Bus Timing

| Speed | Bit rate | Word time |
|-------|---------|-----------|
| Low   | 12.5 kbps | 2.56 ms |
| High  | 100 kbps  | 0.32 ms |

Labels refreshed at 12.5–100 Hz depending on parameter.
