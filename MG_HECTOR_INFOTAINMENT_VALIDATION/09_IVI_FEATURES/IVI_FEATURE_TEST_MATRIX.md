# IVI Feature Test Matrix

| Feature | Nominal | Negative | Boundary | Stress | Evidence |
| --- | --- | --- | --- | --- | --- |
| Radio | Tune valid station | Weak signal | band edge frequency | 200 station changes | audio log, screen video |
| Media Player | Play indexed USB file | corrupt file | max file count | 8 h playback | logcat, audio trace |
| Bluetooth Audio | A2DP playback | phone disconnect | codec switch | 500 reconnect cycles | BT snoop, logcat |
| Phone | Incoming/outgoing call | call drop | contact name length | repeated call cycles | HFP logs |
| Navigation | Route guidance | GNSS loss | route recalculation | long route | location logs |
| Voice Assistant | Wake word/button | no network | noisy cabin | repeated commands | audio and app logs |
| Touchscreen | tap/swipe | rapid touches | screen corners | 1000 interactions | screen recording |
| Theme | day/night switch | invalid config | low voltage switch | repeated switching | screenshot diff |
| Language | change locale | missing string | long translation | repeated changes | UI checklist |
