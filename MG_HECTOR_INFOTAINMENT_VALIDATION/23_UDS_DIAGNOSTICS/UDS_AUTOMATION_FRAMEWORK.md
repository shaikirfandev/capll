# UDS Automation Framework

## Service Coverage

- `0x10`: diagnostic session control.
- `0x11`: ECU reset.
- `0x14`: clear diagnostic information.
- `0x19`: read DTC information.
- `0x22`: read data by identifier.
- `0x27`: security access, stubbed only in training.
- `0x2E`: write data by identifier, restricted to approved bench cases.
- `0x31`: routine control.

## Automation Rules

- Never brute force seed/key.
- Always restore default session after tests.
- Capture precondition, request, response, NRC and timing.
- Keep destructive services behind an explicit safety flag.
