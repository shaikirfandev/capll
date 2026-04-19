# Automotive & Embedded Systems Glossary
## A-Z Reference for Automotive Testing Engineers

---

## A

| Term | Full Form | Definition |
|---|---|---|
| **ACK** | Acknowledgement | CAN frame field where receivers confirm correct reception |
| **ACC** | Adaptive Cruise Control | ADAS feature that maintains following distance to lead vehicle |
| **ADAS** | Advanced Driver Assistance Systems | Electronic systems that assist the driver (AEB, LKA, ACC, BSD, etc.) |
| **ADC** | Analog-to-Digital Converter | Converts analog sensor voltage to digital value (MCAL layer) |
| **AEB** | Autonomous Emergency Braking | Automatically applies brakes to prevent/reduce collision |
| **ARXML** | AUTOSAR XML | XML-based file format for all AUTOSAR model data |
| **ASIL** | Automotive Safety Integrity Level | Risk classification (QM, A, B, C, D) per ISO 26262 |
| **ASC** | ASCII CAN Log | Text-based CAN bus log format (Vector) |
| **ASPICE** | Automotive SPICE | Software process capability assessment model for automotive |
| **AUTOSAR** | AUTomotive Open System ARchitecture | Standardized ECU software architecture consortium/standard |

---

## B

| Term | Full Form | Definition |
|---|---|---|
| **BCM** | Body Control Module | ECU controlling body electronics (lights, locks, wipers) |
| **BLF** | Binary Logging File | Vector's binary CAN log file format |
| **BS** | Block Size | CAN TP flow control field – number of CFs before next FC |
| **BSW** | Basic Software | Pre-configured AUTOSAR software below the RTE |
| **BSD** | Blind Spot Detection | ADAS feature alerting driver to vehicles in blind spots |

---

## C

| Term | Full Form | Definition |
|---|---|---|
| **CAN** | Controller Area Network | Serial bus protocol developed by Bosch for vehicle networks |
| **CAN FD** | CAN Flexible Data-Rate | Extended CAN with up to 64-byte payload and higher bit rates |
| **CAPL** | Communication Access Programming Language | Vector's scripting language for CANoe/CANalyzer |
| **CF** | Consecutive Frame | CAN TP frame type carrying subsequent data segments |
| **CRC** | Cyclic Redundancy Check | Error detection field in CAN frames and safety data |
| **C/S** | Client/Server | AUTOSAR SWC communication port type for function calls |

---

## D

| Term | Full Form | Definition |
|---|---|---|
| **DBC** | DataBase CAN | Text file format describing CAN messages and signals |
| **DC** | Diagnostic Coverage | % of hardware failure modes detected by safety mechanisms |
| **DCM** | Diagnostic Communication Manager | AUTOSAR BSW module handling UDS requests |
| **DEM** | Diagnostic Event Manager | AUTOSAR module managing DTCs and event memory |
| **DIO** | Digital Input/Output | Microcontroller GPIO driver (MCAL layer) |
| **DLC** | Data Length Code | CAN frame field indicating number of data bytes (0–8) |
| **DoIP** | Diagnostics over Internet Protocol | ISO 13400 diagnostic protocol over Ethernet |
| **DOORS** | Dynamic Object-Oriented Requirements System | IBM requirements management tool |
| **DRE** | Defect Removal Efficiency | % of defects found before release |
| **DTC** | Diagnostic Trouble Code | Standardized fault code stored in ECU memory |
| **DUT** | Device Under Test | The ECU or system being tested |

---

## E

| Term | Full Form | Definition |
|---|---|---|
| **ECU** | Electronic Control Unit | Embedded computer in a vehicle |
| **EID** | Entity Identification | 6-byte DoIP identifier (MAC address based) |
| **EMC** | Electromagnetic Compatibility | Testing that ECUs don't emit/are immune to EM interference |
| **EPS** | Electric Power Steering | ECU-controlled steering assistance |
| **ESC/ESP** | Electronic Stability Control/Program | Prevents vehicle skidding by applying individual wheel brakes |
| **EV** | Electric Vehicle | Vehicle powered by electric motor(s) and battery |

---

## F

| Term | Full Form | Definition |
|---|---|---|
| **FC** | Flow Control | CAN TP frame sent by receiver to manage data flow |
| **FCW** | Forward Collision Warning | ADAS alert for imminent front collision |
| **FF** | First Frame | CAN TP frame type initiating a multi-frame message |
| **FIT** | Failures In Time | Hardware failure rate: 1 failure per 10^9 hours |
| **FlexRay** | — | High-speed, deterministic automotive bus (10 Mbps) |
| **FMEA** | Failure Mode and Effects Analysis | Bottom-up safety analysis of hardware components |
| **FSC** | Functional Safety Concept | ISO 26262 work product defining how safety goals are achieved |
| **FTA** | Fault Tree Analysis | Top-down logical analysis of failure causes |
| **FTTI** | Fault-Tolerant Time Interval | Max time from fault to ECU reaching safe state |

---

## G

| Term | Full Form | Definition |
|---|---|---|
| **GID** | Group Identification | DoIP group identifier for ECU clusters |
| **GPIO** | General Purpose Input/Output | Digital I/O pins on a microcontroller |
| **GW** | Gateway | ECU bridging different vehicle bus networks |

---

## H

| Term | Full Form | Definition |
|---|---|---|
| **HARA** | Hazard Analysis and Risk Assessment | ISO 26262 process for identifying hazards and assigning ASILs |
| **HIL** | Hardware-in-the-Loop | Test method connecting real ECU to simulated vehicle environment |
| **HMI** | Human-Machine Interface | dashboard/display/touchscreen user interface in a vehicle |

---

## I

| Term | Full Form | Definition |
|---|---|---|
| **I2C** | Inter-Integrated Circuit | Short-range serial bus for sensors/ICs on a board |
| **IL** | Interaction Layer | CANoe layer that manages message sending via DBC |
| **ISO** | International Organization for Standardization | Global standards body |

---

## K

| Term | Full Form | Definition |
|---|---|---|
| **KWP2000** | Keyword Protocol 2000 | Legacy diagnostic protocol (ISO 14230), precursor to UDS |

---

## L

| Term | Full Form | Definition |
|---|---|---|
| **LDF** | LIN Description File | Database file describing LIN bus signals and schedules |
| **LDW** | Lane Departure Warning | ADAS alert when vehicle drifts from lane |
| **LIN** | Local Interconnect Network | Low-speed serial bus for body electronics |
| **LiDAR** | Light Detection And Ranging | Laser-based 3D environment sensor used in ADAS |
| **LKA** | Lane Keep Assist | ADAS feature that actively steers to keep vehicle in lane |

---

## M

| Term | Full Form | Definition |
|---|---|---|
| **MC/DC** | Modified Condition/Decision Coverage | Code coverage criterion required for ASIL C/D |
| **MCAL** | Microcontroller Abstraction Layer | Lowest AUTOSAR layer – hardware drivers |
| **MDF** | Measurement Data Format | Standard format for measurement data (MDF4 = latest) |
| **MIL** | Model-in-the-Loop | Test level where all software is modeled (pre-implementation) |
| **MIL** | Malfunction Indicator Lamp | Dashboard warning light for emission/drivetrain faults |
| **MPU** | Memory Protection Unit | Hardware unit that prevents unauthorized memory access |
| **MTTC** | Mean Time To Close | Average time to close a defect from discovery |

---

## N

| Term | Full Form | Definition |
|---|---|---|
| **NRC** | Negative Response Code | UDS error code in 0x7F negative response frame |
| **NvM** | Non-volatile Memory Manager | AUTOSAR module for persistent data storage (EEPROM/Flash) |

---

## O

| Term | Full Form | Definition |
|---|---|---|
| **OBD** | On-Board Diagnostics | Standardized vehicle self-diagnostic system |
| **ODX** | Open Diagnostic Data Exchange | XML format for diagnostic data (ISO 22901) |
| **OS** | Operating System | AUTOSAR real-time OS based on OSEK |
| **OTA** | Over-The-Air | Wireless software update mechanism for vehicle ECUs |
| **OSEK** | Offene Systeme und deren Schnittstellen für die Elektronik | German automotive real-time OS standard (basis for AUTOSAR OS) |

---

## P

| Term | Full Form | Definition |
|---|---|---|
| **PDU** | Protocol Data Unit | Data unit exchanged between AUTOSAR COM layers |
| **PIL** | Processor-in-the-Loop | Test level running production code on target processor |
| **PMHF** | Probabilistic Metric for random Hardware Failures | ISO 26262 hardware safety metric (FIT target) |
| **PWM** | Pulse Width Modulation | Signal technique used to control motors, actuators |

---

## R

| Term | Full Form | Definition |
|---|---|---|
| **RTE** | Runtime Environment | AUTOSAR auto-generated middleware implementing VFB |
| **RTM** | Requirements Traceability Matrix | Links requirements to test cases and results |

---

## S

| Term | Full Form | Definition |
|---|---|---|
| **S/R** | Sender/Receiver | AUTOSAR SWC port type for data flow communication |
| **SAE** | Society of Automotive Engineers | US standards organization (e.g., J1939) |
| **SCALEXIO** | — | dSPACE modular HIL real-time hardware platform |
| **SF** | Single Frame | CAN TP frame type for messages ≤ 7 bytes |
| **SIL** | Software-in-the-Loop | Test level with production code on PC simulation |
| **SoC** | System on Chip | Integrated circuit combining CPU, memory, peripherals |
| **SOME/IP** | Scalable service-Oriented MiddlewarE over IP | AUTOSAR Ethernet middleware protocol |
| **SOTIF** | Safety Of The Intended Function | ISO 21448 standard for ADAS perception insufficiency |
| **SPI** | Serial Peripheral Interface | Synchronous serial communication protocol for sensors |
| **STmin** | Separation Time Minimum | CAN TP: minimum time between consecutive frames |
| **SWC** | Software Component | Modular unit of application code in AUTOSAR |

---

## T

| Term | Full Form | Definition |
|---|---|---|
| **TCS** | Traction Control System | Prevents wheel spin during acceleration |
| **TEC** | Transmit Error Counter | CAN error counter, > 127 = error passive, 255 = bus-off |
| **TSC** | Technical Safety Concept | ISO 26262 system-level safety requirements work product |

---

## U

| Term | Full Form | Definition |
|---|---|---|
| **UDS** | Unified Diagnostic Services | ISO 14229 diagnostic protocol used in modern vehicles |
| **UCM** | Update and Configuration Management | AUTOSAR AP module for OTA software updates |

---

## V

| Term | Full Form | Definition |
|---|---|---|
| **VFB** | Virtual Function Bus | AUTOSAR concept – SWCs communicate as if on a virtual bus |
| **VIN** | Vehicle Identification Number | 17-character unique vehicle identifier |
| **VLAN** | Virtual Local Area Network | Logical network segmentation over Ethernet |

---

## W

| Term | Full Form | Definition |
|---|---|---|
| **WdgM** | Watchdog Manager | AUTOSAR module managing software and hardware watchdogs |

---

## X

| Term | Full Form | Definition |
|---|---|---|
| **XCP** | Universal Measurement and Calibration Protocol | Protocol for ECU parameter calibration and data measurement |

---

## Quick Reference: Common Standards

| Standard | Topic |
|---|---|
| ISO 11898 | CAN (Controller Area Network) |
| ISO 14229 | UDS (Unified Diagnostic Services) |
| ISO 15765 | CAN Transport Protocol (ISO-TP) |
| ISO 13400 | DoIP (Diagnostics over IP) |
| ISO 26262 | Functional Safety for Road Vehicles |
| ISO 21448 | SOTIF (Safety of the Intended Function) |
| ISO 11992 | CAN for truck/trailer |
| SAE J1939 | Heavy-duty vehicle CAN |
| SAE J1979 | OBD-II diagnostic services |
| AUTOSAR CP | Classic Platform ECU architecture |
| AUTOSAR AP | Adaptive Platform (ADAS, OTA) |
| ASPICE | Automotive SPICE process assessment |
| MISRA C | C coding standard for safety-critical systems |
| IEC 61508 | Functional Safety (parent standard of ISO 26262) |
