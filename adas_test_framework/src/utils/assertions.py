from __future__ import annotations


def assert_within_tolerance(actual: float, expected: float, tolerance: float, label: str = "value") -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"{label}={actual} outside tolerance ±{tolerance} around {expected}")


def assert_signal_in_range(value: float, minimum: float, maximum: float, label: str = "signal") -> None:
    if not minimum <= value <= maximum:
        raise AssertionError(f"{label}={value} outside range [{minimum}, {maximum}]")


def assert_state_in(state: object, allowed_states: tuple[object, ...], label: str = "state") -> None:
    if state not in allowed_states:
        raise AssertionError(f"{label}={state!r} not in {allowed_states!r}")


def assert_monotonic(values: list[float], increasing: bool = True, label: str = "series") -> None:
    pairs = zip(values, values[1:])
    valid = all(a <= b for a, b in pairs) if increasing else all(a >= b for a, b in pairs)
    if not valid:
        direction = "increasing" if increasing else "decreasing"
        raise AssertionError(f"{label} is not monotonic {direction}: {values}")
