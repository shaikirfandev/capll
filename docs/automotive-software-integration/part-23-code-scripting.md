# Part 23 — Code & Scripting Examples

---

## 23.1 SOME/IP Service Example (C++)

```cpp
// someip_speed_server.cpp
// A minimal SOME/IP server offering VehicleSpeedService
// Requires vsomeip library

#include <vsomeip/vsomeip.hpp>
#include <thread>
#include <iostream>

// SOME/IP Service definition
#define SPEED_SERVICE_ID     0x1234
#define SPEED_INSTANCE_ID    0x0001
#define SPEED_EVENT_ID       0x0001
#define SPEED_EVENTGROUP_ID  0x0001

std::shared_ptr<vsomeip::application> app;
std::mutex init_mutex;
std::condition_variable init_cv;
bool app_ready = false;

void run() {
    // Initialize vsomeip application
    app = vsomeip::runtime::get()->create_application("SpeedServer");
    app->init();

    // Offer the service
    app->offer_service(SPEED_SERVICE_ID, SPEED_INSTANCE_ID);
    
    // Offer event within eventgroup
    std::set<vsomeip::eventgroup_t> eventgroups;
    eventgroups.insert(SPEED_EVENTGROUP_ID);
    app->offer_event(SPEED_SERVICE_ID, SPEED_INSTANCE_ID,
                     SPEED_EVENT_ID, eventgroups,
                     vsomeip::event_type_e::ET_EVENT, 
                     std::chrono::milliseconds(100));  // 100ms periodic

    // Signal that the application is initialized
    {
        std::lock_guard<std::mutex> lk(init_mutex);
        app_ready = true;
    }
    init_cv.notify_one();

    app->start();  // blocks until app->stop() is called
}

void publish_speed(float speed_kmh) {
    // Create payload: 4 bytes float
    auto payload = vsomeip::runtime::get()->create_payload();
    std::vector<vsomeip::byte_t> data(sizeof(float));
    memcpy(data.data(), &speed_kmh, sizeof(float));
    payload->set_data(data);

    // Notify all subscribers
    app->notify(SPEED_SERVICE_ID, SPEED_INSTANCE_ID, SPEED_EVENT_ID, payload);
    std::cout << "Published speed: " << speed_kmh << " km/h\n";
}

int main() {
    std::thread t(run);

    // Wait until vsomeip is fully initialized before publishing
    {
        std::unique_lock<std::mutex> lk(init_mutex);
        init_cv.wait(lk, [] { return app_ready; });
    }

    // Simulate speed changes for 60 seconds then stop
    float speed = 0.0f;
    for (int i = 0; i < 600; ++i) {
        publish_speed(speed);
        speed += 1.0f;
        if (speed > 120.0f) speed = 0.0f;
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    app->stop();
    t.join();
    return 0;
}
```

**Explanation:**
- `vsomeip` is an open-source SOME/IP implementation
- `offer_service` announces service availability (triggers SOME/IP-SD OfferService message)
- `offer_event` configures a periodic event at 100ms
- `notify` sends current value to all subscribers

---

## 23.2 UDS Diagnostic Request/Response (Python)

```python
# uds_read_dtc.py
# Reads all active DTCs from an ECU using python-uds over ISO-TP/CAN

import udsoncan
from udsoncan.connections import IsoTPSocketConnection
from udsoncan.client import Client
import logging

logging.basicConfig(level=logging.INFO)

def read_all_dtcs(interface='vcan0', rx_id=0x7A8, tx_id=0x7A0):
    """
    Connect to ECU and read all active DTCs.
    
    Args:
        interface: SocketCAN interface name
        rx_id: CAN ID for ECU responses
        tx_id: CAN ID for tester requests
    """
    # Establish ISO-TP connection over SocketCAN
    conn = IsoTPSocketConnection(interface, rxid=rx_id, txid=tx_id)
    conn.open()

    config = {
        'security_algo': None,        # no security access needed for DTC read
        'request_timeout': 2.0,       # 2 second timeout per request
    }

    with Client(conn, request_timeout=2.0, config=config) as client:
        try:
            # Step 1: Switch to Extended Diagnostic Session (0x10 0x03)
            print("Switching to Extended Diagnostic Session...")
            client.change_session(
                udsoncan.services.DiagnosticSessionControl.Session.extendedDiagnosticSession
            )

            # Step 2: Read all DTCs with any status (0x19 0x02 0xFF)
            print("Reading all DTCs...")
            response = client.get_dtc_by_status_mask(0xFF)

            if response.positive:
                dtcs = response.service_data.dtcs
                print(f"\nFound {len(dtcs)} DTC(s):")
                for dtc in dtcs:
                    # DTC ID is a 3-byte integer; decode status byte
                    status = dtc.status
                    print(f"  DTC: {dtc.id:#08x} | "
                          f"Confirmed: {status.confirmed_dtc} | "
                          f"Pending: {status.pending_dtc} | "
                          f"MIL: {status.warning_indicator_requested}")
            else:
                print(f"Negative response: NRC {response.code:#04x}")

        except udsoncan.exceptions.NegativeResponseException as e:
            print(f"ECU rejected request: {e}")
        except Exception as e:
            print(f"Error: {e}")

    conn.close()

if __name__ == '__main__':
    read_all_dtcs()
```

---

## 23.3 CAN Message Send/Receive in Python (python-can)

```python
# can_integration_test.py
# Send and receive CAN messages for integration verification

import can
import time
import struct

# Send an EngineSpeed message (0x0C8) with speed = 2000 RPM
def send_engine_speed(bus: can.Bus, rpm: float) -> None:
    """
    Encode and send EngineSpeed CAN message.
    Signal: bytes 0-1, Intel byte order, factor=0.25, offset=0
    Raw value = rpm / 0.25
    """
    raw = int(rpm / 0.25)                # scale to raw value
    data = struct.pack('<H', raw)         # 2 bytes, little-endian (Intel)
    data += bytes(6)                     # pad to 8 bytes
    msg = can.Message(
        arbitration_id=0x0C8,
        data=data,
        is_extended_id=False
    )
    bus.send(msg)
    print(f"Sent EngineSpeed: {rpm} RPM (raw={raw:#06x})")

# Receive and decode VehicleSpeed message (0x0C9)
def receive_vehicle_speed(bus: can.Bus, timeout: float = 1.0) -> float | None:
    """
    Wait for VehicleSpeed CAN message and decode it.
    Signal: bytes 0-1, Intel byte order, factor=0.25, offset=0
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        msg = bus.recv(timeout=0.1)
        if msg and msg.arbitration_id == 0x0C9:
            raw = struct.unpack_from('<H', msg.data, 0)[0]  # little-endian 16-bit
            speed_kmh = raw * 0.25
            print(f"Received VehicleSpeed: {speed_kmh:.2f} km/h (raw={raw:#06x})")
            return speed_kmh
    print("VehicleSpeed message not received within timeout")
    return None

if __name__ == '__main__':
    # Use virtual CAN for testing (run: sudo modprobe vcan && sudo ip link add vcan0 type vcan && sudo ip link set vcan0 up)
    with can.Bus(interface='socketcan', channel='vcan0', bitrate=500000) as bus:
        send_engine_speed(bus, 2000.0)
        speed = receive_vehicle_speed(bus, timeout=2.0)
        if speed is not None:
            print(f"Test PASS: received speed {speed:.1f} km/h")
        else:
            print("Test FAIL: no VehicleSpeed message received")
```

---

## 23.4 CANoe CAPL Test Script

```c
/*
 * TC_AEB_001.can
 * CANoe CAPL Test Script: Verify AEB brake command is sent within 150ms
 * of detecting collision object
 */
variables {
  // Test parameters
  float g_pedestrianDistance = 10.0;  // meters: simulated pedestrian ahead
  float g_egoSpeed = 50.0;            // km/h: simulated ego speed
  dword g_aebStartTime;
  int   g_aebTriggered;

  message AEB_BrakeRequest aeb_msg;
}

// Test case entry point
testcase TC_AEB_001_CollisionAvoidanceTiming() {
  float latencyMs;

  testStep("TC_AEB_001", "Simulating pedestrian at %.1f m, ego speed %.1f km/h",
           g_pedestrianDistance, g_egoSpeed);

  // Step 1: Set up simulation: pedestrian ahead, vehicle moving
  $Radar_Sim::ObjectDistance  = g_pedestrianDistance;
  $Radar_Sim::ObjectType      = 1;  // 1 = pedestrian
  $Ego_Sim::VehicleSpeed      = g_egoSpeed;
  g_aebTriggered = 0;
  g_aebStartTime = timeNow();  // record start time in 10us ticks

  // Step 2: Wait for AEB brake request (max 150ms)
  testWaitForTimeout(150);  // 150ms timeout

  // Step 3: Check result
  if (g_aebTriggered) {
    latencyMs = (timeNow() - g_aebStartTime) / 100.0;  // convert ticks to ms
    testStepPass("AEB_Triggered",
                 "AEB triggered after %.1f ms (requirement: <150ms)", latencyMs);
  } else {
    testStepFail("AEB_Triggered", "AEB brake request NOT received within 150ms");
  }
}

// CAN message handler: detect AEB brake request
on message AEB_BrakeRequest {
  if (this.BrakeRequest > 0 && !g_aebTriggered) {
    g_aebTriggered = 1;
  }
}
```

---

## 23.5 pytest + Log Parsing Automation

```python
# test_can_log_analysis.py
# pytest test that parses a CANoe ASCII log file and verifies signal timing

import pytest
import re
from pathlib import Path

LOG_FILE = Path("logs/integration_test_run1.asc")
EXPECTED_PERIOD_MS = 10.0
TOLERANCE_MS = 2.0

def parse_can_log(filepath: Path, arb_id: int) -> list[float]:
    """
    Parse CANoe ASC log file, return list of timestamps (seconds) for given CAN ID.
    
    ASC format:
       0.002450 1  0C9             Rx   d 8 00 00 00 00 00 00 00 00
    """
    timestamps = []
    pattern = re.compile(
        rf'^\s*(\d+\.\d+)\s+\d+\s+0*{arb_id:X}\s+[RT]x', re.IGNORECASE
    )
    with filepath.open('r') as f:
        for line in f:
            m = pattern.match(line)
            if m:
                timestamps.append(float(m.group(1)))
    return timestamps

@pytest.fixture(scope="module")
def vehicle_speed_timestamps():
    return parse_can_log(LOG_FILE, 0x0C9)

def test_vehicle_speed_signal_present(vehicle_speed_timestamps):
    """VehicleSpeed message must appear in log"""
    assert len(vehicle_speed_timestamps) > 0, \
        "VehicleSpeed (0x0C9) not found in log"

def test_vehicle_speed_period(vehicle_speed_timestamps):
    """VehicleSpeed must be sent every 10ms ±2ms"""
    assert len(vehicle_speed_timestamps) >= 10, "Not enough samples"
    
    periods = [
        (vehicle_speed_timestamps[i+1] - vehicle_speed_timestamps[i]) * 1000
        for i in range(len(vehicle_speed_timestamps) - 1)
    ]
    
    violations = [p for p in periods if abs(p - EXPECTED_PERIOD_MS) > TOLERANCE_MS]
    assert len(violations) == 0, \
        f"{len(violations)} period violations found: {violations[:5]}"
    
    avg_period = sum(periods) / len(periods)
    print(f"\nAverage VehicleSpeed period: {avg_period:.2f} ms")
```

---

## 23.6 Yocto Recipe Snippet

```bitbake
# recipes-connectivity/some-ip-stack/some-ip-stack_1.5.0.bb
SUMMARY = "SOME/IP middleware stack for Automotive Ethernet"
HOMEPAGE = "https://github.com/COVESA/vsomeip"
LICENSE = "MPL-2.0"
LIC_FILES_CHKSUM = "file://LICENSE;md5=815ca599c9df247a0c7f619bab123dad"

SRC_URI = "gitsm://github.com/COVESA/vsomeip.git;branch=master"
SRCREV = "3.3.8"

S = "${WORKDIR}/git"

inherit cmake pkgconfig

DEPENDS = "boost"

EXTRA_OECMAKE = " \
    -DENABLE_SIGNAL_HANDLING=1 \
    -DDIAGNOSIS_ADDRESS=0x10 \
"

FILES:${PN} += "${sysconfdir}/vsomeip/"

do_install:append() {
    # Install default configuration for vehicle network
    install -d ${D}${sysconfdir}/vsomeip
    install -m 0644 ${S}/config/vsomeip.json ${D}${sysconfdir}/vsomeip/
}
```

---

## 23.7 GitHub Actions CI/CD YAML for Embedded Build

```yaml
# .github/workflows/adas-ecu-build.yml
name: ADAS ECU CI/CD Pipeline

on:
  push:
    branches: [main, develop, "release/**"]
  pull_request:
    branches: [develop]

env:
  BUILD_TYPE: Release
  TOOLCHAIN: arm-none-eabi

jobs:
  # Job 1: Static analysis (parallel with build)
  static-analysis:
    name: Static Analysis (MISRA)
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      
      - name: Install cppcheck
        run: sudo apt-get install -y cppcheck

      - name: Run MISRA check
        run: |
          cppcheck --enable=all \
                   --addon=misra.py \
                   --error-exitcode=1 \
                   --xml --xml-version=2 \
                   -I include/ src/ 2> misra_report.xml
      
      - name: Upload MISRA report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: misra-report
          path: misra_report.xml

  # Job 2: Build and unit test
  build-and-test:
    name: Build & Unit Test
    runs-on: ubuntu-22.04
    container:
      image: ghcr.io/my-org/arm-build-env:latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
      
      - name: Configure (host build for unit tests)
        run: |
          cmake -B build-host -S . \
            -DBUILD_TESTS=ON \
            -DCMAKE_BUILD_TYPE=Debug
      
      - name: Build host tests
        run: cmake --build build-host --parallel 4
      
      - name: Run unit tests
        run: |
          cd build-host
          ctest --output-on-failure --output-junit unit_test_results.xml
      
      - name: Configure (cross-compile for ARM target)
        run: |
          cmake -B build-arm -S . \
            -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake \
            -DCMAKE_BUILD_TYPE=${{ env.BUILD_TYPE }}
      
      - name: Build firmware
        run: cmake --build build-arm --parallel 4
      
      - name: Publish test results
        uses: dorny/test-reporter@v1
        if: always()
        with:
          name: Unit Test Results
          path: build-host/unit_test_results.xml
          reporter: java-junit
      
      - name: Upload firmware artifacts
        uses: actions/upload-artifact@v4
        with:
          name: adas-firmware-${{ github.sha }}
          path: |
            build-arm/adas_ecu.hex
            build-arm/adas_ecu.elf
            build-arm/adas_ecu.srec
          retention-days: 30
  
  # Job 3: Package release (only on release branches)
  package-release:
    name: Create Release Package
    needs: [static-analysis, build-and-test]
    if: startsWith(github.ref, 'refs/heads/release/')
    runs-on: ubuntu-22.04
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Download firmware
        uses: actions/download-artifact@v4
        with:
          name: adas-firmware-${{ github.sha }}
          path: firmware/
      
      - name: Generate build manifest
        run: |
          cat > firmware/build_manifest.json << EOF
          {
            "product": "ADAS_ECU",
            "git_commit": "${{ github.sha }}",
            "git_branch": "${{ github.ref_name }}",
            "build_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
            "build_number": "${{ github.run_number }}"
          }
          EOF
      
      - name: Create release archive
        run: |
          cd firmware/
          sha256sum adas_ecu.hex > SHA256SUMS.txt
          zip -r ../adas-ecu-release-${{ github.run_number }}.zip .
      
      - name: Upload release package
        uses: actions/upload-artifact@v4
        with:
          name: release-package-${{ github.run_number }}
          path: adas-ecu-release-*.zip
          retention-days: 90
```

---

## Summary

| Example | Key Points |
|---|---|
| SOME/IP server (C++) | vsomeip, offer_service, notify |
| UDS Python | python-uds, DTC read, session management |
| python-can | CAN send/receive, encoding, SocketCAN |
| CAPL | CANoe test automation, timing verification |
| pytest log analysis | ASC log parsing, period verification |
| Yocto recipe | bitbake, cmake inherit, vsomeip |
| GitHub Actions | Parallel jobs, cross-compile, artifact upload |

---

*Next: [Part 24 — Interview Preparation](part-24-interview-preparation.md)*
