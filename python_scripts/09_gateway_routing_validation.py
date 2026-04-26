#!/usr/bin/env python3
"""Section 9: CAN-to-Ethernet gateway routing validation example."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CanFrame:
    t_ms: int
    can_id: int
    data: bytes


@dataclass
class EthPacket:
    t_ms: int
    topic: str
    payload: bytes


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


class MockGateway:
    def __init__(self, route_table: Dict[int, str], base_latency_ms: int = 3) -> None:
        self.route_table = route_table
        self.base_latency_ms = base_latency_ms

    def forward(self, frame: CanFrame) -> Optional[EthPacket]:
        topic = self.route_table.get(frame.can_id)
        if topic is None:
            return None

        # Example transport transformation: prepend CAN ID for traceability.
        payload = frame.can_id.to_bytes(2, "big") + frame.data
        return EthPacket(
            t_ms=frame.t_ms + self.base_latency_ms,
            topic=topic,
            payload=payload,
        )


def run_gateway_tests() -> List[CheckResult]:
    gateway = MockGateway(
        route_table={
            0x120: "vehicle/speed",
            0x130: "engine/rpm",
            0x220: "body/door_status",
        },
        base_latency_ms=4,
    )

    input_frames = [
        CanFrame(100, 0x120, bytes([0x13, 0x88])),
        CanFrame(110, 0x130, bytes([0x2E, 0xE0])),
        CanFrame(120, 0x555, bytes([0x00, 0x01])),  # unmapped
        CanFrame(130, 0x220, bytes([0x01])),
    ]

    outputs = [gateway.forward(f) for f in input_frames]
    routed = [p for p in outputs if p is not None]

    results: List[CheckResult] = []

    results.append(CheckResult(
        name="Expected number of routed packets",
        passed=len(routed) == 3,
        details=f"routed={len(routed)}, expected=3",
    ))

    # Validate unmapped frame drop behavior.
    dropped_unmapped = outputs[2] is None
    results.append(CheckResult(
        name="Drop unmapped CAN ID",
        passed=dropped_unmapped,
        details="CAN ID 0x555 should not be forwarded",
    ))

    # Latency check.
    latencies = [pkt.t_ms - frame.t_ms for frame, pkt in zip(input_frames, outputs) if pkt is not None]
    max_latency = max(latencies)
    results.append(CheckResult(
        name="Gateway latency within limit",
        passed=max_latency <= 10,
        details=f"max_latency={max_latency}ms, limit=10ms",
    ))

    # Payload integrity: first two bytes should contain original CAN ID.
    integrity_ok = True
    for frame, pkt in zip(input_frames, outputs):
        if pkt is None:
            continue
        can_id_from_payload = int.from_bytes(pkt.payload[:2], "big")
        if can_id_from_payload != frame.can_id or pkt.payload[2:] != frame.data:
            integrity_ok = False
            break

    results.append(CheckResult(
        name="Payload integrity preserved",
        passed=integrity_ok,
        details="CAN ID and data preserved in forwarded payload",
    ))

    return results


def main() -> None:
    results = run_gateway_tests()
    passed = sum(1 for r in results if r.passed)

    print("=== Gateway Routing Validation Report ===")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name}: {r.details}")
    print(f"Summary: {passed}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
