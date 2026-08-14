# Part 8 — Telematics / TCU Integration

---

## 8.1 What is a TCU?

A **TCU (Telematics Control Unit)** connects the vehicle to external networks (cellular, Wi-Fi, Bluetooth) for:
- Remote monitoring and diagnostics
- eCall emergency services
- OTA software updates
- Fleet management
- Connected services (traffic, weather, parking)

---

## 8.2 TCU Hardware Architecture

```
+----------------------------------------------------------+
|                      TCU Hardware                        |
|                                                          |
|  +-------------+  +--------+  +--------+  +-----------+ |
|  | Application |  |  MCU   |  | Modem  |  |  GNSS     | |
|  | Processor   |  | (Safety|  | (LTE/5G|  | (GPS/GLO  | |
|  | (Linux)     |  |  MCU)  |  | /NB-IoT|  | NASS/BeiD)| |
|  +-------------+  +--------+  +--------+  +-----------+ |
|                                                          |
|  +-------------+  +--------+  +--------+  +-----------+ |
|  |  Bluetooth  |  |  Wi-Fi |  | eSIM / |  | CAN / ETH | |
|  |  Module     |  | Module |  | SIM    |  | Interface | |
|  +-------------+  +--------+  +--------+  +-----------+ |
|                                                          |
|  Power management, Security IC (HSM), Secure storage    |
+----------------------------------------------------------+
```

### Key Hardware Components

| Component | Function |
|---|---|
| Application Processor | Linux OS, cloud connectivity, OTA management |
| Safety MCU | Watchdog, power control, eCall trigger |
| Cellular Modem | LTE Cat-M1/NB1/LTE-V2/5G, AT commands, PPP/NDIS |
| GNSS Module | Position tracking (GPS, GLONASS, Galileo) |
| Bluetooth | BLE for digital key, phone connectivity |
| Wi-Fi | Hotspot, OTA download, Android Auto Wi-Fi |
| eSIM | Over-the-air SIM provisioning, multi-operator |
| CAN Interface | Vehicle network access |
| Ethernet | High-speed vehicle network access |

---

## 8.3 TCU Software Architecture

```
+----------------------------------------------------------+
|               CLOUD CONNECTIVITY LAYER                   |
|  MQTT Client | HTTP/HTTPS | WebSocket | AMQP             |
+----------------------------------------------------------+
|               APPLICATION LAYER                          |
|  eCall App | Remote Diag | OTA Manager | Fleet Agent     |
|  GNSS Tracker | Remote Command | Telemetry Agent         |
+----------------------------------------------------------+
|               MIDDLEWARE                                 |
|  Modem Manager | Network Manager | SOME/IP Client        |
|  CAN Manager | Crypto Library | Certificate Store        |
+----------------------------------------------------------+
|               OS (Embedded Linux / QNX)                  |
+----------------------------------------------------------+
|               DRIVERS                                    |
|  Modem Driver (USB/PCIe) | GNSS Driver | CAN Driver     |
|  Bluetooth Driver | Wi-Fi Driver                         |
+----------------------------------------------------------+
|               HARDWARE                                   |
+----------------------------------------------------------+
```

---

## 8.4 TCU Connectivity Protocols

### Cellular (LTE/5G)

```
Modem initialization flow:
1. Linux boots, ModemManager detects modem via USB/PCIe
2. AT command: AT+CREG? → check SIM registered
3. AT command: AT+CGDCONT=1,"IP","internet" → set APN
4. AT command: ATD*99# → establish PPP data call
5. pppd creates ppp0 interface with IP address
6. Application connects to cloud backend over ppp0
```

### MQTT (Message Queuing Telemetry Transport)

```
Vehicle Telemetry flow:
TCU collects: {speed, location, rpm, fuel, dtcs}
TCU → MQTT Publish → topic: "vehicle/VIN123/telemetry"
Cloud Broker → subscribers: fleet dashboard, analytics
Cloud → MQTT Publish → topic: "vehicle/VIN123/command"
TCU → MQTT Subscribe → receives remote commands
```

### HTTP/HTTPS

Used for OTA package downloads, API calls:
```
TCU → HTTPS GET https://ota.oem.com/packages/latest
     ← HTTP 200 + firmware package (TLS 1.2/1.3 protected)
TCU downloads to flash partition
TCU verifies signature
TCU triggers bootloader to install
```

### TLS (Transport Layer Security)

All TCU cloud communication uses TLS 1.2 or 1.3:
- Server certificate verified against OEM CA
- Client certificate (mutual TLS) for authentication
- Certificate stored in HSM (Hardware Security Module)

---

## 8.5 TCU Functions

### eCall (Emergency Call — ETSI EN 16072)

eCall automatically contacts emergency services (112 in Europe) after a crash:

```
Crash detected by airbag ECU → CAN signal "CrashEvent = 1"
TCU MCU receives CrashEvent
TCU establishes cellular call to 112
TCU transmits MSD (Minimum Set of Data):
  - Vehicle VIN
  - GPS coordinates
  - Direction of travel
  - Number of occupants
  - Timestamp
Emergency services dispatch rescue
```

### Remote Diagnostics

```
Cloud backend → HTTPS POST "DiagnosticRequest" → TCU
TCU → DoIP → Target ECU
Target ECU → UDS response (DTC list, sensor values)
TCU → HTTPS POST response → Cloud backend
Fleet manager sees DTC data in dashboard
```

### Remote Commands

```
Mobile App → Cloud → MQTT → TCU
Commands: door_unlock, climate_start, horn_honk, locate
TCU → CAN message → Body ECU / HVAC ECU
ECU executes command
ECU confirms → CAN → TCU → cloud → mobile app
```

### Vehicle Tracking

```
GNSS receiver → position fix (lat, lon, alt, speed, heading)
TCU application reads NMEA sentences via UART
TCU packages position + timestamp → MQTT publish
Cloud stores in time-series database
Fleet dashboard shows real-time vehicle position on map
```

### OTA — see Part 11 for full detail

---

## 8.6 Full TCU Integration Flow

```
Vehicle                  TCU                    Cloud

CAN Bus      ──→     CAN Manager      ──→    MQTT Broker
(speed, rpm, gear,   (reads signals,          (fleet backend)
 DTCs, door states)   formats telemetry)

                     GNSS Module      ──→    Location DB
                     (position track)

Airbag ECU   ──→     eCall App        ──→    Emergency Services
(crash signal)       (MSD + voice call)

OTA Update   ←───    OTA Manager      ←──    OTA Server
(bootloader)         (download, verify,
                      install update)

Remote CMD   ←───    Command Handler  ←──    Mobile App
(door unlock)        (validates, routes)
```

---

## 8.7 Security in TCU

TCU is a primary attack surface for vehicle cybersecurity:

| Security Measure | Description |
|---|---|
| TLS 1.2/1.3 | All cloud communication encrypted |
| Mutual TLS (mTLS) | Both client and server authenticate |
| Certificate pinning | Prevent MITM attacks |
| HSM (Hardware Security Module) | Keys never leave HSM |
| Secure Boot | Verify firmware integrity on boot |
| Signed OTA packages | Firmware signed with OEM private key |
| Network firewall | TCU has IP firewall blocking unauthorized access |
| IDS (Intrusion Detection) | Monitor for anomalous CAN/network traffic |

---

## 8.8 TCU Integration Example — Fleet Tracking

**Objective:** Enable fleet manager to track 100 vehicles in real time.

**Integration steps:**
1. TCU CAN Manager reads VehicleSpeed (0x0C9), GNSS position
2. TCU packages data: `{vin, lat, lon, speed, timestamp}` every 10 seconds
3. TCU publishes via MQTT over LTE to cloud broker
4. Cloud broker distributes to fleet dashboard
5. Fleet dashboard displays map with vehicle icons
6. Test: inject known GPS coordinates, verify in dashboard

**Common integration issues:**
- GNSS cold start takes 45 seconds — implement AGPS (assisted GPS) with cloud data
- MQTT connection drops on cellular handover — implement reconnection with QoS 1
- TCU resets when cellular modem hangs — implement modem watchdog via AT commands

---

## Summary

| Component | Protocol | Key Integration |
|---|---|---|
| Cellular modem | AT commands, PPP, NDIS | ModemManager, APN config |
| Cloud telemetry | MQTT over TLS | Broker config, topic design |
| Remote diagnostics | UDS over DoIP over HTTPS | DoIP channel setup |
| eCall | IN-BAND audio + MSD | Airbag CAN signal handling |
| OTA | HTTPS + signed packages | Bootloader integration |
| Security | TLS, mTLS, HSM | Certificate lifecycle |

---

*Next: [Part 9 — ECU Flashing & Deployment](part-09-ecu-flashing.md)*
