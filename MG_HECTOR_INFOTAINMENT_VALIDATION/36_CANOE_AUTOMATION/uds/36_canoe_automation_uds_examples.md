# UDS Examples: CANoe Automation

These examples use representative diagnostic identifiers. Replace with the released diagnostic specification.

## Session Control

| Step | Request | Expected Positive Response | Purpose |
| --- | --- | --- | --- |
| Default session | `10 01` | `50 01` | Return ECU to normal diagnostic behavior |
| Extended session | `10 03` | `50 03` | Enable deeper IVI diagnostic reads |
| Programming session | `10 02` | `50 02` | Used only for flashing or OTA recovery validation |

## DID Reads

| DID | Request | Expected | Validation Use |
| --- | --- | --- | --- |
| `F180` | `22 F1 80` | bootloader/software ID | release evidence |
| `F187` | `22 F1 87` | manufacturer spare part number | ECU identification |
| `F190` | `22 F1 90` | VIN | vehicle personalization and traceability |
| `D100` | `22 D1 00` | IVI boot KPI snapshot | performance validation |
| `D200` | `22 D2 00` | connectivity state | feature validation |

## DTC Validation

- Inject signal timeout in CANoe.
- Wait for diagnostic debounce time.
- Send `19 02 FF`.
- Verify DTC status bit and aging behavior.
- Remove fault, perform recovery sequence and clear DTC only if test plan requires `14 FF FF FF`.

## Negative Responses to Expect

- `7F 22 31`: request out of range for unsupported DID.
- `7F 27 35`: invalid key during security access.
- `7F 31 22`: conditions not correct when routine is requested in wrong power mode.
