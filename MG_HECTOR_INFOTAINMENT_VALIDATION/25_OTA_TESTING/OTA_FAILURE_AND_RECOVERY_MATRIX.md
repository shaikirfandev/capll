# OTA Failure And Recovery Matrix

| Phase | Failure Injection | Expected Recovery |
| --- | --- | --- |
| Download | network loss | pause/resume or retry with user-visible state |
| Verification | package hash mismatch | reject package and keep current version |
| Install | KL15 off | follow power policy and resume or rollback |
| First boot | service crash | rollback or safe mode per spec |
| Post-update | config migration failure | preserve critical user data or reset with notice |
