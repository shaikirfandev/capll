#!/usr/bin/env python3
"""Section 10: ECU power-mode state machine test automation example."""

from dataclasses import dataclass
from enum import Enum
from typing import List


class PowerState(str, Enum):
    OFF = "OFF"
    ACC = "ACC"
    IGN_ON = "IGN_ON"
    CRANK = "CRANK"
    RUN = "RUN"
    SLEEP = "SLEEP"


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


class PowerModeStateMachine:
    def __init__(self) -> None:
        self.state = PowerState.OFF

    def transition(self, event: str) -> bool:
        rules = {
            (PowerState.OFF, "key_insert"): PowerState.ACC,
            (PowerState.ACC, "ignition_on"): PowerState.IGN_ON,
            (PowerState.IGN_ON, "start_button"): PowerState.CRANK,
            (PowerState.CRANK, "engine_speed_valid"): PowerState.RUN,
            (PowerState.RUN, "key_off_timeout"): PowerState.SLEEP,
            (PowerState.SLEEP, "sleep_complete"): PowerState.OFF,
            (PowerState.SLEEP, "wake_event"): PowerState.ACC,
        }

        key = (self.state, event)
        if key not in rules:
            return False

        self.state = rules[key]
        return True


def run_power_mode_tests() -> List[CheckResult]:
    results: List[CheckResult] = []

    sm = PowerModeStateMachine()

    nominal_events = [
        "key_insert",
        "ignition_on",
        "start_button",
        "engine_speed_valid",
        "key_off_timeout",
        "sleep_complete",
    ]

    nominal_ok = all(sm.transition(e) for e in nominal_events)
    results.append(CheckResult(
        name="Nominal startup/shutdown path",
        passed=nominal_ok and sm.state == PowerState.OFF,
        details=f"final_state={sm.state.value}",
    ))

    sm = PowerModeStateMachine()
    invalid_ok = not sm.transition("start_button")
    results.append(CheckResult(
        name="Reject invalid transition from OFF",
        passed=invalid_ok and sm.state == PowerState.OFF,
        details="start_button should be ignored in OFF",
    ))

    sm = PowerModeStateMachine()
    for e in ["key_insert", "ignition_on", "start_button", "engine_speed_valid", "key_off_timeout"]:
        sm.transition(e)
    wake_ok = sm.state == PowerState.SLEEP and sm.transition("wake_event") and sm.state == PowerState.ACC
    results.append(CheckResult(
        name="Wake event from SLEEP",
        passed=wake_ok,
        details=f"state_after_wake={sm.state.value}",
    ))

    return results


def main() -> None:
    results = run_power_mode_tests()
    passed = sum(1 for r in results if r.passed)

    print("=== Power Mode State Machine Report ===")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name}: {r.details}")
    print(f"Summary: {passed}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
