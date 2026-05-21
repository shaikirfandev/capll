# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Effects Ana# Failure Mode and Eundant) |
| F06 | ADC | Airspeed fail | Wrong CAS/TAS | Major | Low | ADC_AIRSPEED_FAIL fault | INS-computed airspeed backup |
| F07 | ARINC 429 | Bus timeout | Stale sensor data | Major | Low | BUS_ARINC429_TIMEOUT fault | DataBusMonitor 1s timeout |
| F08 | AFDX | Network A+B fail | Loss of avionics data | Hazardous | Very Low | BUS_AFDX_TIMEOUT fault | Physical redundancy required |
| F09 | Navigation | RNP exceeded | Not RNP-AR capable | Major | Low | NAV_RNP_EXCEEDED fault | Conventional nav reversion |
| F10 | FaultManager | Fault table overflow (>64) | Lost fault record | Major | Very Low | Static analysis, bounded array | Return ERR_BUFFER_FULL |
| F11 | Watchdog | Kick timeout (main loop hang) | Undetected software failure | Catastrophic | Very Low | HW watchdog expiry → reset | Watchdog DAL-A, 500ms timeout |
| F12 | GuidanceComputer | XTE > 10 nm | Gross navigation error | Hazardous | Very Low | Monitor XTE, crew alert | LNAV 25° bank limit, overspeed protection |

**Probability Classes:** Very Low (<1e-7/hr), Low (<1e-5/hr), Medium (<1e-3/hr)  
**Severity Classes (JAR 25.1309):** Minor / Major / Hazardous / Catastrophic
