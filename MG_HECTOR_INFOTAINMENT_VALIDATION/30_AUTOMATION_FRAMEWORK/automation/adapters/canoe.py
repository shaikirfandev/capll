from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class CanoeConfig:
    config_path: str
    dry_run: bool = True


class CanoeAdapter:
    def __init__(self, config: CanoeConfig) -> None:
        self.config = config
        self.measurement_running = False

    def open_configuration(self) -> None:
        if self.config.dry_run:
            print(f"DRY_RUN CANoe open {self.config.config_path}")
            return
        raise NotImplementedError("Wire to CANoe COM on a Windows bench host.")

    def start_measurement(self) -> None:
        if self.config.dry_run:
            print("DRY_RUN CANoe start measurement")
            self.measurement_running = True
            return
        raise NotImplementedError("Call CANoe.Application.Measurement.Start().")

    def stop_measurement(self) -> None:
        if self.config.dry_run:
            print("DRY_RUN CANoe stop measurement")
            self.measurement_running = False
            return
        raise NotImplementedError("Call CANoe.Application.Measurement.Stop().")

    def set_signal(self, name: str, value: int | float) -> None:
        if self.config.dry_run:
            print(f"DRY_RUN CANoe set {name}={value}")
            return
        raise NotImplementedError("Map to environment variables, system variables or CAPL functions.")

    def wait(self, seconds: float) -> None:
        time.sleep(seconds)

