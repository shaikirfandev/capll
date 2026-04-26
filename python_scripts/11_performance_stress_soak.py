#!/usr/bin/env python3
"""Section 11: Performance/stress/soak testing automation example."""

from dataclasses import dataclass
from statistics import mean, pstdev
from typing import List
import random


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    index = int((p / 100.0) * (len(sorted_vals) - 1))
    return sorted_vals[index]


def generate_latency_samples(sample_count: int, seed: int = 42) -> (List[float], int):
    rng = random.Random(seed)
    latencies: List[float] = []
    drops = 0

    for i in range(sample_count):
        # Drop model
        if rng.random() < 0.0015:
            drops += 1
            continue

        # Normal traffic latency profile in ms
        latency = rng.gauss(5.5, 1.2)

        # Rare stress spikes
        if i % 2000 == 0 and i > 0:
            latency += rng.uniform(8.0, 15.0)

        latencies.append(max(latency, 0.5))

    return latencies, drops


def run_performance_suite() -> List[CheckResult]:
    sample_count = 20000
    latencies, drops = generate_latency_samples(sample_count)
    delivered = len(latencies)

    avg = mean(latencies)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    max_latency = max(latencies)
    jitter = pstdev(latencies)
    drop_rate = (drops / sample_count) * 100.0

    results = [
        CheckResult(
            name="Drop rate threshold",
            passed=drop_rate <= 0.5,
            details=f"drop_rate={drop_rate:.3f}%, limit=0.500%",
        ),
        CheckResult(
            name="P95 latency threshold",
            passed=p95 <= 10.0,
            details=f"p95={p95:.2f}ms, limit=10.00ms",
        ),
        CheckResult(
            name="P99 latency threshold",
            passed=p99 <= 15.0,
            details=f"p99={p99:.2f}ms, limit=15.00ms",
        ),
        CheckResult(
            name="Max latency threshold",
            passed=max_latency <= 30.0,
            details=f"max={max_latency:.2f}ms, limit=30.00ms",
        ),
        CheckResult(
            name="Latency jitter threshold",
            passed=jitter <= 2.5,
            details=f"sigma={jitter:.2f}ms, limit=2.50ms",
        ),
        CheckResult(
            name="Soak mean latency trend",
            passed=avg <= 7.0,
            details=f"mean={avg:.2f}ms, delivered={delivered}/{sample_count}",
        ),
    ]

    return results


def main() -> None:
    results = run_performance_suite()
    passed = sum(1 for r in results if r.passed)

    print("=== Performance / Stress / Soak Report ===")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name}: {r.details}")
    print(f"Summary: {passed}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
