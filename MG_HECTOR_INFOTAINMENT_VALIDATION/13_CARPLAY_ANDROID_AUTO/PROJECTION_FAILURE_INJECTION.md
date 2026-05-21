# Projection Failure Injection

| Case | Injection | Expected Behavior |
| --- | --- | --- |
| USB unplug during launch | Disconnect cable before projection ready | IVI returns to previous screen and offers reconnect |
| Phone locked | Start projection with locked phone | Clear user prompt, no crash |
| Cable quality issue | Use controlled USB drop or hub reset | Graceful disconnect and reconnect |
| Permission revoked | Remove projection permission on phone | IVI shows actionable message |
| Power mode off | Turn KL15 off during projection | Projection stops, state restores after wake if supported |
| Audio focus conflict | Start navigation prompt during media | Correct ducking and focus behavior |
