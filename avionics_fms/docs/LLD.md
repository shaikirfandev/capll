# Low-Level Design (LLD)
## Avionics FMS v3.2.1 — DO-178C DAL-B

## 1. Haversine Navigation (LLD-NAV-2, LLD-NAV-3)

```
Given: P1 = (lat1, lon1), P2 = (lat2, lon2) in radians

a = sin²((lat2-lat1)/2) + cos(lat1)·cos(lat2)·sin²((lon2-lon1)/2)
c = 2·atan2(√a, √(1-a))
distance_nm = R_EARTH_NM × c

bearing_rad = atan2(sin(Δlon)·cos(lat2),
                    cos(lat1)·sin(lat2) - sin(lat1)·cos(lat2)·cos(Δlon))
bearing_deg = (bearing_rad × 180/π + 360) mod 360
```

## 2. Cross-Track Error (LLD-NAV-4)

```
Given: Angular distance d13 = distance(P1, P3) / R_EARTH
       Bearing θ13 = bearing(P1, P3)
       Bearing θ12 = bearing(P1, P2)

XTE = asin(sin(d13) × sin(θ13 - θ12)) × R_EARTH_NM
```

## 3. BNR Encoding (LLD-COM-1, LLD-COM-2, LLD-COM-3)

```
// Encode
scaled = round(value / resolution)
mask   = (1 << bits) - 1
data   = scaled & mask         // Two's complement, N bits
word   = reverse8(label)       // Bits [7:0]
       | (sdi & 3) << 8        // Bits [9:8]
       | data << 10             // Bits [28:10] for 19 bits or [27:10] for 18 bits
       | ssm << 29              // Bits [30:29]
parity = odd_parity(bits[30:0])
word  |= parity << 31

// Decode
raw   = (word >> 10) & mask
if (raw & (1 << (bits-1))): val = raw - (1 << bits)  // sign extend
else:                         val = raw
result = val × resolution
```

## 4. EKF Predict/Update (LLD-INT-2, LLD-INT-3)

### State Vector (6 DOF simplified)
```
x = [lat, lon, alt, vel_N, vel_E, vel_D]^T
```

### Predict (INS propagation)
```
dt = 0.1 s (10 Hz)
lat += vel_N × dt / R_EARTH × (180/π)
lon += vel_E × dt / (R_EARTH × cos(lat)) × (180/π)
P[i][i] += Q[i]    (process noise)
```

### Update (GPS measurement)
```
// Innovation
dy = z_GPS - H × x

// Simplified diagonal Kalman gain
K[i] = P[i][i] / (P[i][i] + R[i])

// State update
x += K × dy

// Covariance update (simplified)
P[i][i] *= (1 - K[i])

// ANP computation
ANP_nm = 2σ_horiz / 1852 m
       = 2 × sqrt(P[0][0] + P[1][1]) / 1852
```

## 5. LNAV Roll Command (LLD-GNC-3)

```
K_LNAV = 3.0  // gain: 3 deg roll per nm XTE
roll_cmd = clamp(K_LNAV × XTE, -25.0, +25.0)  // ±25° bank limit
```

## 6. VNAV VS Command (LLD-GNC-4, LLD-GNC-5)

```
K_VNAV = 10.0  // gain: 10 fpm per ft altitude error
vs_cmd = clamp(K_VNAV × (target_alt - current_alt), -6000.0, +6000.0)
```

## 7. Watchdog Timer (LLD-SAF-1)

```cpp
void kick() { last_kick_ = steady_clock::now(); }
bool is_expired() {
    auto elapsed_ms = duration_cast<milliseconds>(now() - last_kick_).count();
    return elapsed_ms > period_ms_;
}
```

## 8. ARINC 429 Label Reversal

```
ARINC 429 specifies label bits are transmitted LSB-first.
Software stores labels in natural bit order (MSB first).
Before encoding, reverse the 8-bit label:

reverse_label(0x83):
  0x83 = 10000011b → reversed → 11000001b = 0xC1
```

## 9. Odd Parity Calculation

```cpp
uint32_t compute_parity(uint32_t word) {
    uint32_t p = word & 0x7FFFFFFF;  // bits 1-31
    p ^= p >> 16; p ^= p >> 8; p ^= p >> 4;
    p ^= p >> 2;  p ^= p >> 1;
    return (~p) & 1;  // odd: 1 if even number of ones
}
```
