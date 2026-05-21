# API Reference
## TCU Validation Framework v2.0.0

All public APIs are in the `tcu` namespace. Headers are in `include/`.

---

## 1. Framework — `include/core/Framework.h`

### `tcu::Framework::get()`
```cpp
static Framework& get();
```
Returns the global singleton instance. Thread-safe via `call_once`.

### `initialize()`
```cpp
bool initialize();
```
Initialises the logging subsystem and prepares the Framework for module registration.  
Returns `true` on success. Must be called before `register_module()`.

### `register_module()`
```cpp
void register_module(
    const std::string& name,
    std::function<bool()> on_start,
    std::function<void()> on_stop,
    std::function<std::string()> on_health = nullptr
);
```
Registers a module for lifecycle management. Modules are started in registration order and stopped in reverse order.

### `start()`
```cpp
bool start();
```
Calls `on_start()` for each registered module in order. Returns `false` if any module fails to start.

### `wait_for_shutdown()`
```cpp
void wait_for_shutdown();
```
Blocks the calling thread until `request_shutdown()` is called.

### `request_shutdown()`
```cpp
void request_shutdown();
```
Triggers graceful shutdown. Wakes `wait_for_shutdown()` and calls `on_stop()` for each module in reverse order.

### `health_report()`
```cpp
std::string health_report();
```
Returns a formatted multi-line string with each module's health status.

---

## 2. CANManager — `include/can/CANManager.h`

### Constructor
```cpp
explicit CANManager(const std::string& interface = "vcan0", bool enable_fd = false);
```

### `open()`
```cpp
bool open();
```
Opens the SocketCAN socket and binds to the configured interface. Enables CAN-FD if `enable_fd=true`.

### `start()` / `stop()`
```cpp
bool start();
void stop();
```
Starts/stops the background Rx thread.

### `send()`
```cpp
bool send(const CANFrame& frame);
```
Sends a CAN 2.0 frame. Thread-safe (mutex-protected).

### `send_fd()`
```cpp
bool send_fd(const CANFDFrame& frame);
```
Sends a CAN-FD frame. Requires `enable_fd=true`.

### `register_rx_callback()`
```cpp
void register_rx_callback(
    uint32_t id_mask,
    uint32_t id_match,
    std::function<void(const CANFrame&)> callback
);
```
Registers a receive callback. Fires when `(received_id & id_mask) == id_match`.

### `set_error_callback()`
```cpp
void set_error_callback(std::function<void(uint32_t error_flags)> callback);
```

### `get_statistics()`
```cpp
CANStatistics get_statistics() const;
```

---

## 3. UDSClient — `include/diagnostics/UDSClient.h`

All methods return `UDSResult`:
```cpp
struct UDSResult {
    bool success{false};
    uint8_t nrc{0x00};             // Negative Response Code (0 = positive)
    std::vector<uint8_t> data;     // Response payload
    std::string error_message;
};
```

### `set_isotp_config()`
```cpp
void set_isotp_config(const ISOTPConfig& config);
```

### `send_session_control()`
```cpp
UDSResult send_session_control(UDSSession session);
```
Sessions: `DEFAULT(0x01)`, `PROGRAMMING(0x02)`, `EXTENDED(0x03)`

### `send_ecu_reset()`
```cpp
UDSResult send_ecu_reset(uint8_t reset_type = 0x01);
```
Types: `HARD(0x01)`, `KEY_OFF_ON(0x02)`, `SOFT(0x03)`

### `read_data_by_id()`
```cpp
UDSResult read_data_by_id(uint16_t did);
```

### `write_data_by_id()`
```cpp
UDSResult write_data_by_id(uint16_t did, const std::vector<uint8_t>& data);
```

### `send_security_access()`
```cpp
UDSResult send_security_access(uint8_t level, std::function<std::vector<uint8_t>(const std::vector<uint8_t>&)> key_calculator);
```
Performs the full request-seed / send-key exchange.

### `read_dtcs()`
```cpp
UDSResult read_dtcs(uint8_t status_mask = 0xFF);
```

### `clear_dtcs()`
```cpp
UDSResult clear_dtcs(uint32_t group = 0xFFFFFF);
```

### `start_routine()` / `stop_routine()` / `request_routine_result()`
```cpp
UDSResult start_routine(uint16_t routine_id, const std::vector<uint8_t>& params = {});
UDSResult stop_routine(uint16_t routine_id);
UDSResult request_routine_result(uint16_t routine_id);
```

### `request_download()`
```cpp
UDSResult request_download(uint32_t memory_address, uint32_t memory_size);
```

### `transfer_data()`
```cpp
UDSResult transfer_data(uint8_t block_sequence, const std::vector<uint8_t>& data);
```

### `transfer_exit()`
```cpp
UDSResult transfer_exit();
```

### `send_tester_present()`
```cpp
UDSResult send_tester_present(bool suppress_response = true);
```

---

## 4. TestEngine — `include/validation/TestEngine.h`

### `add_test()`
```cpp
void add_test(TestCase test);
```

### `run()`
```cpp
TestSuiteResult run(const std::string& suite_name = "Default Suite");
```

### `run_single()`
```cpp
TestResult run_single(const std::string& test_id);
```

### `run_filtered()`
```cpp
TestSuiteResult run_filtered(const std::string& tag, const std::string& suite_name = "Filtered");
```

### `set_execution_mode()`
```cpp
void set_execution_mode(ExecutionMode mode);
```
Modes: `SEQUENTIAL`, `PARALLEL`

### `set_stop_on_first_fail()`
```cpp
void set_stop_on_first_fail(bool stop);
```

### `add_listener()`
```cpp
void add_listener(IResultListener* listener);
```

**IResultListener interface:**
```cpp
class IResultListener {
public:
    virtual void on_suite_start(const std::string& name, size_t count) = 0;
    virtual void on_test_result(const TestResult& result) = 0;
    virtual void on_suite_end(const TestSuiteResult& result) = 0;
    virtual ~IResultListener() = default;
};
```

---

## 5. FaultInjector — `include/validation/FaultInjector.h`

### `inject()`
```cpp
std::shared_ptr<ActiveFault> inject(FaultType type, uint32_t duration_ms = 0, const std::string& params = "");
```
Returns an RAII guard. The fault is active while the guard is alive. If `duration_ms > 0`, a background timer clears the fault after that duration.

**FaultType values:**
| Enum Value | Effect |
|-----------|--------|
| `CAN_BUS_OFF` | Stops CANManager completely |
| `CAN_DROPOUT` | Stops CANManager Rx thread |
| `CAN_CORRUPTION` | Applies impossible filter |
| `NETWORK_LATENCY` | Sets sim latency in telematics |
| `NETWORK_LOSS` | Sets sim loss percentage |
| `UDS_MALFORMED` | — reserved — |
| `POWER_CUT` | Logs and signals framework |
| `FIRMWARE_CORRUPT` | Marks firmware state as corrupted |
| `OTA_INTERRUPTED` | Sets OTA sim state to interrupted |
| `OTA_WRONG_VERSION` | Injects wrong version OTA package |
| `SECURITY_ATTACK` | Logs security event, increments counter |
| `MEMORY_PRESSURE` | Allocates 50 MB block |
| `CPU_SPIKE` | Spawns busy-loop threads (core × 2) |

### `clear_fault()`
```cpp
void clear_fault(FaultType type);
```

### `clear_all()`
```cpp
void clear_all();
```

### `is_active()`
```cpp
bool is_active(FaultType type) const;
```

---

## 6. TelematicsSDKAdapter — `include/telematics/TelematicsSDKAdapter.h`

### `connect()` / `disconnect()`
```cpp
bool connect();
void disconnect();
```

### `publish_telemetry()`
```cpp
bool publish_telemetry(const TelemetryData& data);
```

### `check_for_updates()`
```cpp
std::optional<OTAPackageInfo> check_for_updates();
```

### `acknowledge_ota()`
```cpp
bool acknowledge_ota(const std::string& version);
```

### `report_ota_progress()`
```cpp
void report_ota_progress(int percent, const std::string& status_msg);
```

### Simulation API (test injection)
```cpp
void sim_inject_ota(const OTAPackageInfo& pkg);
void sim_set_network_metrics(double latency_ms, double loss_pct);
std::vector<std::string> sim_get_published() const;
void sim_clear_published();
```

---

## 7. FirmwareFlasher — `include/firmware/FirmwareFlasher.h`

### `flash_via_uds()`
```cpp
bool flash_via_uds(const std::string& firmware_path, uint32_t target_address);
```

### `flash_via_rfp()`
```cpp
bool flash_via_rfp(const std::string& firmware_path, const std::string& device_id);
```

### `set_progress_callback()`
```cpp
void set_progress_callback(std::function<void(int percent, const std::string& msg)> cb);
```

---

## 8. ConfigManager — `include/config/ConfigManager.h`

### `load()`
```cpp
bool load(const std::string& path);
```

### `load_overlay()`
```cpp
bool load_overlay(const std::string& path);
```
Deep-merges JSON onto current config.

### `load_profile()`
```cpp
bool load_profile(const std::string& profile_name, const std::string& base_dir = "configs/");
```

### `get<T>()`
```cpp
template<typename T>
T get(const std::string& dot_path, const T& default_value = T{}) const;
```
Supported types: `std::string`, `bool`, `int`, `double`, `std::vector<T>`.

### `set_*()`
```cpp
void set_string(const std::string& dot_path, const std::string& value);
void set_bool(const std::string& dot_path, bool value);
void set_int(const std::string& dot_path, int value);
void set_double(const std::string& dot_path, double value);
```

### `has()` / `remove()`
```cpp
bool has(const std::string& dot_path) const;
void remove(const std::string& dot_path);
```

### `enable_hot_reload()`
```cpp
void enable_hot_reload(bool enable, uint32_t poll_interval_ms = 1000);
```

### `global_config()`
```cpp
static ConfigManager& global_config();
```
Returns the process-wide singleton ConfigManager.

---

## 9. Logger — `include/logging/Logger.h`

### `init()`
```cpp
static bool init(const std::string& log_file_path = "logs/tcu.log",
                 spdlog::level::level_enum level = spdlog::level::info);
```

### `get()`
```cpp
static std::shared_ptr<spdlog::logger> get(const std::string& name = "tcu");
```

### `set_level()` / `set_global_level()`
```cpp
static void set_level(const std::string& name, spdlog::level::level_enum level);
static void set_global_level(spdlog::level::level_enum level);
```

### `ScopedTimer`
```cpp
class ScopedTimer {
public:
    explicit ScopedTimer(const std::string& operation_name,
                         const std::string& logger_name = "tcu");
    ~ScopedTimer();  // Logs µs elapsed
};
```

---

## 10. ReportGenerator — `include/reporting/ReportGenerator.h`

### `generate()`
```cpp
bool generate(const TestSuiteResult& result,
              const std::string& output_dir,
              const std::string& base_filename,
              ReportFormat format = ReportFormat::ALL);
```
`ReportFormat`: `HTML`, `JSON`, `CSV`, `ALL`

Output files:
- `{output_dir}/{base_filename}.html`
- `{output_dir}/{base_filename}.json`
- `{output_dir}/{base_filename}.csv`

---

## 11. CRCValidator — `include/firmware/CRCValidator.h`

### `compute_crc32()`
```cpp
static uint32_t compute_crc32(const uint8_t* data, size_t length);
```
CRC-32/ISO-HDLC polynomial: `0xEDB88320`, init: `0xFFFFFFFF`.

### `compute_crc16()`
```cpp
static uint16_t compute_crc16_ccitt(const uint8_t* data, size_t length);
```
CRC-16/CCITT-FALSE polynomial: `0x1021`, init: `0xFFFF`.

### `verify_file()`
```cpp
static bool verify_file(const std::string& path, uint32_t expected_crc32);
```
Streams file in 4096-byte chunks. Returns `true` if computed CRC matches expected.
