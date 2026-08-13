from __future__ import annotations

from typing import Iterable

from communication.can_interface import CANFrame, CANInterface


class CANFDInterface(CANInterface):
    """Mock CAN-FD interface extending payload support to 64 bytes."""

    def send(self, arbitration_id: int, data: bytes | bytearray | Iterable[int]) -> CANFrame:
        payload = bytes(data)
        if len(payload) > 64:
            raise ValueError("CAN-FD payload must be 64 bytes or less")
        frame = CANFrame(arbitration_id=arbitration_id, data=payload, is_fd=True)
        if arbitration_id not in self._suppressed_ids:
            self._tx_history.append(frame)
            if self.loopback:
                self._rx_queue.append(frame)
        for callback in self._callbacks.get(arbitration_id, []):
            callback(frame)
        return frame
