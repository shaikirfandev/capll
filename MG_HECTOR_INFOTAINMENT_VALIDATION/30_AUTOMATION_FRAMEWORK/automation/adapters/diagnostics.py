from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UdsResponse:
    request: str
    response: str
    positive: bool
    notes: str = ""


class DiagnosticsAdapter:
    def __init__(self, safe_mode: bool = True) -> None:
        self.safe_mode = safe_mode

    def send(self, request: str) -> UdsResponse:
        request = request.upper().strip()
        if request == "10 03":
            return UdsResponse(request, "50 03", True, "extended session")
        if request.startswith("22 F1 80"):
            return UdsResponse(request, "62 F1 80 4D 47 48 5F 49 56 49", True, "software id stub")
        if request.startswith("19 02"):
            return UdsResponse(request, "59 02 00", True, "no DTC stub")
        if self.safe_mode and (request.startswith("2E") or request.startswith("31 01")):
            return UdsResponse(request, "7F " + request[:2] + " 22", False, "blocked by safe mode")
        return UdsResponse(request, "7F " + request[:2] + " 31", False, "not implemented in dry-run")

