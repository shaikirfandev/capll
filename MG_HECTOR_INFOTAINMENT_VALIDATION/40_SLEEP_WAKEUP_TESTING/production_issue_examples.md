# Production Issue Examples: Sleep Wakeup Testing

## Issue A: Timeout After Wakeup

Symptom: Feature unavailable for the first few seconds after ignition on.

Likely causes: delayed dependency service, missing wakeup message, network management startup order, slow storage mount or Android service not ready.

RCA evidence: power mode trace, IVI boot state, logcat service timestamps, DTC snapshot and reproduction video.

## Issue B: Wrong State After Sleep

Symptom: IVI displays stale state or ignores the first user action after wakeup.

Likely causes: cached vehicle property not invalidated, missed CAN frame during suspend, app state restoration issue or race in service binding.

## Issue C: Regression After OTA

Symptom: Feature passed in previous release but fails after software update.

Likely causes: changed permissions, updated middleware API, config migration failure or incompatible calibration.
