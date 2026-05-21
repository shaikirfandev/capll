# Power Cycle Simulations

| State | KL30 | KL15 | ACC | Expected IVI |
| --- | --- | --- | --- | --- |
| Vehicle off | ON | OFF | OFF | sleep or retained low-power state |
| Accessory | ON | OFF | ON | limited infotainment mode |
| Ignition | ON | ON | ON | full feature availability |
| Crank | ON | transient | transient | no corruption, defined audio/camera behavior |
| Low voltage | below threshold | variable | variable | warning, graceful shutdown or inhibit |
