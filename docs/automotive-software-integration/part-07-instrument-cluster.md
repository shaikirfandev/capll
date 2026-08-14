# Part 7 — Instrument Cluster Integration

---

## 7.1 Cluster Architecture

The instrument cluster displays driving information to the driver: speed, RPM, warnings, telltales, and ADAS visualization.

```
+----------------------------------------------------------+
|                    DISPLAY (TFT/OLED)                    |
+----------------------------------------------------------+
|                  GRAPHICS ENGINE                         |
|  Qt / OpenGL ES / Vulkan / GPU                           |
+----------------------------------------------------------+
|               APPLICATION LAYER                         |
|  Speedometer | Tachometer | Fuel | ADAS Display         |
|  Warning Manager | Telltale Manager                      |
+----------------------------------------------------------+
|              MIDDLEWARE / SIGNAL MANAGER                 |
|  SOME/IP Client | CAN Signal Handler | IPC               |
+----------------------------------------------------------+
|              OS                                          |
|  Linux (PREEMPT_RT) | QNX | AUTOSAR Adaptive             |
+----------------------------------------------------------+
|              DRIVER LAYER                                |
|  Display Driver | GPU Driver | CAN Driver | ETH Driver   |
+----------------------------------------------------------+
|              HARDWARE                                    |
|  SoC (R-Car H3/M3, i.MX8, SA8295P)                     |
|  TFT / OLED display | GPU | CAN controller              |
+----------------------------------------------------------+
```

---

## 7.2 Display Types

| Type | Features | Use |
|---|---|---|
| TFT LCD | Good brightness, cost-effective | Traditional clusters |
| OLED | High contrast, true black, fast response | Premium clusters |
| Mini-LED LCD | High local dimming | Mid-range premium |
| Curved / freeform | Aesthetic, complex optical design | High-end |

Typical cluster resolution: 1920×720 (panoramic), 1920×1080 (standard digital).

---

## 7.3 Vehicle Signal Integration

### CAN-Based Cluster

Classic cluster architecture reads vehicle data from CAN bus:

```
Vehicle Speed (0x0C9) ─────┐
Engine RPM     (0x0C8) ─────┤──→ CAN Bus → Cluster ECU CAN Driver
Fuel Level     (0x349) ─────┤                     ↓
Door Status    (0x395) ─────┘             Signal Manager
Gear Position  (0x0DF) ─────               (decodes CAN frames)
                                                    ↓
                                          Application layer
                                          (updates display values)
```

### Ethernet-Based Cluster (Modern)

Modern clusters receive signals via SOME/IP over Automotive Ethernet:

```
Central Gateway ECU
  → SOME/IP "VehicleStateService"
  → ClusterECU subscribes via SOME/IP-SD
  → Receives signal bundle (speed, RPM, fuel, gear, warnings)
  → Signal Manager dispatches to application components
```

---

## 7.4 Telltales and Warning Indicators

A **telltale** is a warning light (e.g., check engine, low fuel, seatbelt, battery).

### Telltale Integration

```
DTC set in Engine ECU → CAN signal "MIL_Request = 1" sent
Cluster receives signal → Warning Manager activates MIL telltale
Warning Manager calls graphics layer → render orange engine icon
Driver sees warning
```

### Telltale Priority System

When multiple warnings occur simultaneously, the cluster must show them in priority order:
- P0: Safety-critical (ABS failure, airbag fault)
- P1: Powertrain warnings (engine temp, oil pressure)
- P2: Informational (low fuel, door open)

---

## 7.5 Graphics Stack

### OpenGL ES Pipeline

```
Application (Qt/C++) → Scene graph → OpenGL ES commands → GPU driver → framebuffer → display
```

### Vulkan
Modern clusters use Vulkan for lower CPU overhead and better multi-threading.

### Qt Automotive Suite
Qt provides automotive-grade HMI framework:
- Qt Quick (QML-based declarative UI)
- Qt 3D for 3D gauges
- Qt Safe Renderer (ISO 26262 certified rendering for safety-critical telltales)

### Display Composition

```
Layer 1: Background / gauge face (static, rendered infrequently)
Layer 2: Dynamic values (speed needle, RPM bar) — updated every frame
Layer 3: Warning overlays (telltales) — updated on event
Layer 4: ADAS visualization (object overlays) — updated at 20-60Hz

GPU compositor (Wayland/Weston or proprietary) combines layers → display
```

---

## 7.6 ADAS Visualization in Cluster

Modern clusters show ADAS status:
- Vehicle ahead representation
- Lane lines
- ACC set speed
- Speed limit sign (TSR)
- Warning alerts (AEB, LKA)

**Integration:**
1. ADAS Domain Controller sends object list via SOME/IP
2. Cluster subscribes to ADAS visualization service
3. Cluster application renders vehicles/pedestrians/lane lines
4. Uses camera images + object bounding boxes or abstract icons

---

## 7.7 Functional Safety in Cluster

The cluster is safety-relevant: it must display critical warnings (low oil pressure, brake failure) even when the SoC is overloaded.

**Safety split architecture:**
```
+------------------------+   +-------------------+
| Main SoC (QM)          |   | Safety MCU (ASIL-B)|
| Rich HMI, ADAS display |   | Telltales rendering|
| Qt, Linux              |   | Qt Safe Renderer   |
+------------------------+   +-------------------+
         Both write to display; safety MCU has priority override
```

---

## 7.8 Cluster Integration Sequence

```
1. Hardware bring-up
   - Boot SoC, verify display initialized (MIPI DSI / LVDS output)
   - Verify GPU driver operational

2. OS/BSP bring-up
   - Linux/QNX boots
   - Wayland compositor starts
   - Qt application launches

3. Communication integration
   - CAN driver receives signals
   - OR: SOME/IP-SD subscribes to VehicleStateService
   - Verify signals arriving in signal manager

4. Application integration
   - Speedometer reads VehicleSpeed signal → updates needle angle
   - Tachometer reads EngineRPM → updates arc fill
   - Verify display values match CANoe injected signals

5. Warning integration
   - Inject DTC in CANoe → set MIL_Request CAN signal
   - Verify MIL telltale lights in cluster

6. ADAS integration
   - Inject SOME/IP ObjectList from ADAS simulator
   - Verify object representation appears in cluster display

7. Performance testing
   - Measure frame rate (target: 60Hz for smooth animation)
   - Measure GPU/CPU load
   - Measure boot-to-telltale time (critical: must display within 1 second of startup)
```

---

## 7.9 Common Cluster Integration Defects

| Defect | Cause | Fix |
|---|---|---|
| Cluster freezes after 30 min | GPU driver memory leak | Update GPU driver, add watchdog |
| Wrong speed shown | CAN endianness mismatch | Check Intel vs Motorola byte order |
| Telltale not showing | Wrong CAN signal ID in config | Verify DBC signal mapping |
| ADAS display flickering | SOME/IP event arriving too fast | Add rate limiting in subscriber |
| Boot time too slow | Too many init services | Optimize Yocto/init systemd services |
| Cluster shows wrong gear | Gear signal offset incorrect | Correct scaling in signal manager |

---

## Summary

| Layer | Key Integration |
|---|---|
| Hardware | SoC, display, GPU, CAN controller |
| BSP/OS | Yocto Linux or QNX, GPU driver, display driver |
| Middleware | CAN/SOME/IP signal manager, IPC |
| Graphics | Qt/OpenGL ES/Vulkan, Wayland compositor |
| Application | Speedometer, tachometer, warnings, ADAS visualization |
| Safety | Qt Safe Renderer, safety MCU for critical telltales |

---

*Next: [Part 8 — Telematics / TCU Integration](part-08-telematics-tcu.md)*
