from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

import pytest

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from adas.acc import ACCController
from adas.aeb import AEBController
from adas.bsd import BSDController
from adas.fcw import FCWController
from adas.lka import LKAController
from communication.can_interface import CANInterface
from communication.uds_interface import MockUDSServer
from diagnostics.dtc import DTCManager
from diagnostics.uds_client import UDSClient
from safety.fault_injection import FaultInjector
from vehicle.scenario import ScenarioLoader
from vehicle.vehicle_state import VehicleState


@pytest.fixture()
def acc_controller() -> ACCController:
    controller = ACCController()
    controller.set_speed(100.0)
    return controller


@pytest.fixture()
def aeb_controller() -> AEBController:
    return AEBController()


@pytest.fixture()
def lka_controller() -> LKAController:
    return LKAController()


@pytest.fixture()
def fcw_controller() -> FCWController:
    return FCWController()


@pytest.fixture()
def bsd_controller() -> BSDController:
    return BSDController()


@pytest.fixture()
def vehicle_state() -> VehicleState:
    return VehicleState(speed_mps=30.0, yaw_rate=0.0)


@pytest.fixture()
def can_interface() -> CANInterface:
    return CANInterface(channel="virtual", loopback=True)


@pytest.fixture()
def uds_client() -> UDSClient:
    dtc_manager = DTCManager()
    server = MockUDSServer(dtc_manager=dtc_manager)
    return UDSClient(server=server)


@pytest.fixture()
def fault_injector(can_interface: CANInterface) -> FaultInjector:
    return FaultInjector(can_interface=can_interface)


@pytest.fixture()
def scenario_loader() -> ScenarioLoader:
    return ScenarioLoader(base_path=ROOT / "test_data" / "scenarios")


@pytest.fixture()
def load_scenarios(scenario_loader: ScenarioLoader) -> Callable[[str], list]:
    return scenario_loader.load
