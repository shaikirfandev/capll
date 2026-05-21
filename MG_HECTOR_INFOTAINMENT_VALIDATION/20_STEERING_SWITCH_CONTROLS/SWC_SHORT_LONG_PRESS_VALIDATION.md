# Steering Switch Short/Long Press Validation

| Button | Short Press Expected | Long Press Expected |
| --- | --- | --- |
| Volume Up | volume +1 step | repeated volume increase |
| Track Next | next track/station | seek/fast forward if supported |
| Phone | accept/end call | reject or phone menu if specified |
| Voice | voice assistant start | alternate assistant/projection assistant if specified |

Validate debounce, repeated frame handling, stuck button timeout and priority during reverse camera or call state.
