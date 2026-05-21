# Integration Guide
## TCU Validation Framework v2.0.0

This guide explains how to integrate the framework with real OEM telematics hardware and SDKs, replacing the built-in simulation mode.

---

## 1. Replacing Simulation Mode

The framework ships with `simulation_mode: true` in `configs/default.json`. In simulation mode, the `TelematicsSDKAdapter` stores all published telemetry in-memory and responds to OTA queries from injected test data.

To connect to a real OEM SDK or MQTT broker, disable simulation mode:

```json
// configs/production.json  (overlay)
{
  "telematics": {
    "simulation_mode": false,
    "server_url": "mqtts://your-oemcloud.example.com:8883",
    "device_id": "TCU_VIN_ABCDE12345678",
    "tls": {
      "ca_cert":     "/etc/tcu/certs/ca.pem",
      "client_cert": "/etc/tcu/certs/client.pem",
      "client_key":  "/etc/tcu/certs/client.key"
    }
  }
}
```

Run with:
```bash
./bin/tcu_validator --config configs/default.json --profile production
```

---

## 2. Implementing a Real OEM SDK Backend

The `TelematicsSDKAdapter` has an internal `SDK` struct that wraps the OEM SDK calls. To integrate a real SDK:

1. Open `src/telematics/TelematicsSDKAdapter.cpp`
2. Find the `#ifdef SIMULATION_MODE` blocks and the `connect_real()` stub
3. Replace stubs with your OEM SDK calls

Example structure (vendor SDK is fictitious):
```cpp
// In TelematicsSDKAdapter.cpp — replace simulation connect with:
#include <OEMTelematicsSDK.h>

bool TelematicsSDKAdapter::connect_real() {
    OEMConfig cfg;
    cfg.server_url   = m_config.server_url;
    cfg.device_id    = m_config.device_id;
    cfg.ca_cert_path = m_config.tls_ca_cert;
    cfg.cert_path    = m_config.tls_client_cert;
    cfg.key_path     = m_config.tls_client_key;

    m_sdk_handle = OEMTelematicsSDK::create(cfg);
    return m_sdk_handle && m_sdk_handle->connect(30'000 /* ms timeout */);
}
```

---

## 3. CAN Interface Configuration

### 3.1 Physical CAN (production)
```bash
# Configure CAN bitrate and bring up interface
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0
```

Update config:
```json
{
  "can": {
    "interface": "can0",
    "bitrate": 500000,
    "enable_fd": false
  }
}
```

### 3.2 CAN-FD (optional)
```bash
sudo ip link set can0 type can bitrate 500000 dbitrate 2000000 fd on
sudo ip link set up can0
```

Config:
```json
{
  "can": {
    "interface": "can0",
    "bitrate": 500000,
    "fd_bitrate": 2000000,
    "enable_fd": true
  }
}
```

### 3.3 Virtual CAN (development/CI)
```bash
scripts/setup_vcan.sh
```

---

## 4. UDS ECU Configuration

Match your ECU's CAN IDs and ISO-TP settings:

```json
{
  "uds": {
    "tx_id":              "0x7E0",
    "rx_id":              "0x7E8",
    "p2_timeout_ms":      50,
    "p2_star_timeout_ms": 5000,
    "block_size":         0,
    "separation_time_ms": 0
  }
}
```

For extended CAN IDs (29-bit):
```cpp
// In code, set the EFF flag on the CANFrame:
CANFrame frame;
frame.id = 0x18DA00F1 | CAN_EFF_FLAG;
```

---

## 5. Adding Custom Test Cases

```cpp
#include "validation/TestEngine.h"
#include "can/CANManager.h"

tcu::TestEngine engine;

engine.add_test({
    .id          = "TC_CUSTOM_001",
    .description = "Custom ECU heartbeat check",
    .tags        = {"heartbeat", "custom"},
    .precondition = [&]() {
        return can_mgr->is_open();
    },
    .test_fn = [&]() -> tcu::TestResult {
        // Send request frame
        tcu::CANFrame frame;
        frame.id  = 0x100;
        frame.dlc = 1;
        frame.data[0] = 0xAA;
        can_mgr->send(frame);

        // Wait for response (implement your own receive wait)
        std::this_thread::sleep_for(std::chrono::milliseconds(100));

        return tcu::TestResult{
            .test_id = "TC_CUSTOM_001",
            .verdict = tcu::TestVerdict::PASS,
            .message = "Heartbeat received"
        };
    },
    .cleanup = [&]() { /* teardown if needed */ },
    .timeout_ms = 500,
    .retry_count = 2,
    .critical = false
});

auto result = engine.run("Custom Suite");
```

---

## 6. Extending the Reporting

Implement `IResultListener` for real-time progress feeds:

```cpp
class DashboardFeed : public tcu::IResultListener {
public:
    void on_suite_start(const std::string& name, size_t count) override {
        // Push to WebSocket or REST endpoint
    }
    void on_test_result(const tcu::TestResult& r) override {
        // Stream result to dashboard
    }
    void on_suite_end(const tcu::TestSuiteResult& r) override {
        // Final summary push
    }
};

DashboardFeed feed;
engine.add_listener(&feed);
```

---

## 7. Security Configuration (Production)

### mTLS Certificates
Generate self-signed certs for dev/staging:
```bash
# CA
openssl req -x509 -newkey rsa:4096 -keyout ca.key -out ca.pem -days 365 -nodes

# Client cert
openssl req -newkey rsa:4096 -keyout client.key -out client.csr -nodes
openssl x509 -req -in client.csr -CA ca.pem -CAkey ca.key -out client.pem -days 365

sudo cp ca.pem client.pem client.key /etc/tcu/certs/
sudo chmod 640 /etc/tcu/certs/client.key
```

### UDS Security Access Key
Provide the key calculator that matches your ECU's seed-key algorithm:
```cpp
auto key_from_seed = [](const std::vector<uint8_t>& seed) {
    // Your OEM algorithm here
    std::vector<uint8_t> key = seed;
    for (auto& b : key) b ^= 0xAA;  // Example only
    return key;
};

uds_client->send_security_access(0x01, key_from_seed);
```

---

## 8. Environment Variable Overrides

Any config key can be overridden at runtime without modifying JSON files:

```bash
export TCU_CFG_CAN_INTERFACE=can0
export TCU_CFG_TELEMATICS_SERVER_URL=mqtts://prod.example.com:8883
export TCU_CFG_LOGGING_LEVEL=warn
./bin/tcu_validator --config configs/default.json
```

Pattern: `TCU_CFG_<SECTION>_<KEY>` → `section.key`  
First underscore after `TCU_CFG_` maps to `.`, subsequent underscores are kept.
