# Low-Level Design (LLD)
## TCU Validation Framework v2.0.0

---

## 1. Introduction
This document provides detailed low-level design specifications for all modules, including class diagrams, sequence diagrams, and state machines.

---

## 2. Class Diagrams

### 2.1 Framework (core)

```
┌─────────────────────────────────────┐
│ Framework                           │
│─────────────────────────────────────│
│ - m_instance : Framework* (static)  │
│ - m_modules  : vector<ModuleEntry>  │
│ - m_running  : atomic<bool>         │
│ - m_shutdown : atomic<bool>         │
│ - m_cv       : condition_variable   │
│─────────────────────────────────────│
│ + get()              : Framework&   │
│ + initialize()       : bool         │
│ + register_module()  : void         │
│ + start()            : bool         │
│ + shutdown()         : void         │
│ + wait_for_shutdown(): void         │
│ + request_shutdown() : void         │
│ + health_report()    : string       │
│─────────────────────────────────────│
│ - ModuleEntry                        │
│   name     : string                 │
│   on_start : function<bool()>       │
│   on_stop  : function<void()>       │
│   on_health: function<string()>     │
└─────────────────────────────────────┘
```

### 2.2 CANManager

```
┌─────────────────────────────────────────┐
│ CANManager                              │
│─────────────────────────────────────────│
│ - m_socket    : int                     │
│ - m_interface : string                  │
│ - m_rx_thread : thread                  │
│ - m_running   : atomic<bool>            │
│ - m_tx_mutex  : mutex                   │
│ - m_cb_mutex  : mutex                   │
│ - m_callbacks : vector<RxCallback>      │
│ - m_err_cb    : ErrorCallback           │
│ - m_stats     : CANStatistics           │
│─────────────────────────────────────────│
│ + open()   : bool                       │
│ + close()  : void                       │
│ + start()  : bool                       │
│ + stop()   : void                       │
│ + send()   : bool                       │
│ + send_fd(): bool                       │
│ + register_rx_callback() : void         │
│ + set_error_callback()   : void         │
│ + get_statistics()       : CANStatistics│
│─────────────────────────────────────────│
│ - rx_thread_func()      : void          │
│ - dispatch_frame()      : void          │
└─────────────────────────────────────────┘

     CANFrame                CANFDFrame
┌──────────────┐        ┌──────────────────┐
│ id   : uint32│        │ id  : uint32      │
│ dlc  : uint8 │        │ len : uint8       │
│ data[8]: byte│        │ flags : uint8     │
│ is_extended  │        │ data[64] : byte   │
│ is_rtr       │        └──────────────────┘
└──────────────┘
```

### 2.3 UDSClient

```
┌──────────────────────────────────────────┐
│ UDSClient                                │
│──────────────────────────────────────────│
│ - m_can     : shared_ptr<CANManager>     │
│ - m_config  : ISOTPConfig                │
│ - m_rx_buf  : vector<uint8_t>            │
│ - m_rx_cv   : condition_variable         │
│ - m_rx_mutex: mutex                      │
│──────────────────────────────────────────│
│ + send_session_control()  : UDSResult    │
│ + send_ecu_reset()        : UDSResult    │
│ + read_data_by_id()       : UDSResult    │
│ + write_data_by_id()      : UDSResult    │
│ + send_security_access()  : UDSResult    │
│ + read_dtcs()             : UDSResult    │
│ + clear_dtcs()            : UDSResult    │
│ + start_routine()         : UDSResult    │
│ + request_download()      : UDSResult    │
│ + transfer_data()         : UDSResult    │
│ + transfer_exit()         : UDSResult    │
│ + send_tester_present()   : UDSResult    │
│──────────────────────────────────────────│
│ - send_isotp()            : bool         │
│ - receive_isotp()         : bool         │
│ - send_request()          : UDSResult    │
└──────────────────────────────────────────┘

ISOTPConfig:
  tx_id, rx_id       : uint32_t
  block_size         : uint8_t   (default 0 = no limit)
  separation_time_ms : uint8_t   (default 0)
  p2_timeout_ms      : uint32_t  (default 50)
  p2_star_timeout_ms : uint32_t  (default 5000)
  max_pdu_size       : uint16_t  (default 4095)
```

### 2.4 TestEngine + Test Case

```
┌─────────────────────────────────────────────┐
│ TestEngine                                  │
│─────────────────────────────────────────────│
│ - m_tests     : vector<TestCase>            │
│ - m_listeners : vector<IResultListener*>    │
│ - m_mode      : ExecutionMode               │
│ - m_stop      : bool                        │
│─────────────────────────────────────────────│
│ + add_test()        : void                  │
│ + run()             : TestSuiteResult       │
│ + run_single()      : TestResult            │
│ + run_filtered()    : TestSuiteResult       │
│ + add_listener()    : void                  │
│ + clear_tests()     : void                  │
│─────────────────────────────────────────────│
│ - execute_test()    : TestResult            │
│ - run_with_timeout(): TestResult            │
│ - notify_*()        : void                  │
└─────────────────────────────────────────────┘

TestCase:
  id          : string
  description : string
  tags        : vector<string>
  precondition: function<bool()>
  test_fn     : function<TestResult()>
  cleanup     : function<void()>
  timeout_ms  : uint32_t
  retry_count : uint32_t
  critical    : bool

TestResult:
  test_id  : string
  verdict  : TestVerdict {PASS, FAIL, SKIP, TIMEOUT, ERROR}
  message  : string
  duration_ms : uint64_t
  timestamp   : time_point
  details     : map<string,string>
```

### 2.5 FaultInjector

```
┌──────────────────────────────────────────────┐
│ FaultInjector                                │
│──────────────────────────────────────────────│
│ - m_can      : shared_ptr<CANManager>        │
│ - m_sdk      : shared_ptr<TelematicsSDKAdapter>│
│ - m_active   : map<FaultType, ActiveFault>   │
│ - m_ref_cnt  : map<FaultType, int>           │
│ - m_mutex    : mutex                         │
│──────────────────────────────────────────────│
│ + inject()     : shared_ptr<ActiveFault>     │
│ + clear_fault(): void                        │
│ + clear_all()  : void                        │
│ + is_active()  : bool                        │
│ + active_faults(): vector<FaultType>         │
│──────────────────────────────────────────────│
│ - apply_fault()   : void                     │
│ - restore_fault() : void                     │
└──────────────────────────────────────────────┘

FaultType enum:
  CAN_BUS_OFF, CAN_DROPOUT, CAN_CORRUPTION,
  NETWORK_LATENCY, NETWORK_LOSS,
  UDS_MALFORMED, POWER_CUT, FIRMWARE_CORRUPT,
  OTA_INTERRUPTED, OTA_WRONG_VERSION,
  SECURITY_ATTACK, MEMORY_PRESSURE, CPU_SPIKE
```

---

## 3. Sequence Diagrams

### 3.1 UDS Firmware Flash Sequence

```
Test        FirmwareFlasher    UDSClient        ECU
 │                │               │               │
 │ flash_via_uds()│               │               │
 │───────────────>│               │               │
 │                │ send_session  │               │
 │                │ (PROGRAMMING) │               │
 │                │──────────────>│  0x10 02     │
 │                │               │──────────────>│
 │                │               │  0x50 02     │
 │                │               │<──────────────│
 │                │ security_access               │
 │                │──────────────>│  0x27 01     │
 │                │               │──────────────>│
 │                │               │  0x67 01 SEED│
 │                │               │<──────────────│
 │                │               │  0x27 02 KEY │
 │                │               │──────────────>│
 │                │               │  0x67 02     │
 │                │               │<──────────────│
 │                │ start_routine │               │
 │                │ (ERASE_MEMORY)│               │
 │                │──────────────>│  0x31 01 FF00│
 │                │               │──────────────>│
 │                │               │  0x71 01 FF00│
 │                │               │<──────────────│
 │                │ request_download              │
 │                │──────────────>│  0x34        │
 │                │               │──────────────>│
 │                │               │  0x74 maxBlock│
 │                │               │<──────────────│
 │                │ [for each block]              │
 │                │ transfer_data │               │
 │                │──────────────>│  0x36 seq data│
 │                │               │──────────────>│
 │                │               │  0x76 seq    │
 │                │               │<──────────────│
 │                │ transfer_exit │               │
 │                │──────────────>│  0x37        │
 │                │               │──────────────>│
 │                │               │  0x77        │
 │                │               │<──────────────│
 │                │ ecu_reset     │               │
 │                │──────────────>│  0x11 01     │
 │                │               │──────────────>│
 │ PASS           │               │               │
 │<───────────────│               │               │
```

### 3.2 OTA Detection and Acknowledge Sequence

```
TestEngine    TelematicsSDKAdapter    OEM SDK / MQTT
    │                  │                    │
    │ check_for_updates│                    │
    │─────────────────>│                    │
    │                  │ sim_inject_ota()   │
    │                  │ OR poll OEM SDK    │
    │                  │<───────────────────│
    │ OTAPackageInfo{} │                    │
    │<─────────────────│                    │
    │                  │                    │
    │ acknowledge_ota  │                    │
    │─────────────────>│ publish ACK        │
    │                  │───────────────────>│
    │                  │                    │
    │ report_progress  │                    │
    │ (0, "Preparing") │                    │
    │─────────────────>│ publish progress   │
    │                  │───────────────────>│
    │                  │                    │
    │ [flash firmware] │                    │
    │                  │                    │
    │ report_progress  │                    │
    │ (100, "Complete")│                    │
    │─────────────────>│ publish progress   │
    │                  │───────────────────>│
```

### 3.3 Fault Injection RAII Sequence

```
Test           FaultInjector       CANManager
 │                   │                  │
 │ inject(CAN_DROPOUT│                  │
 │ , 1000ms)         │                  │
 │──────────────────>│ stop()          │
 │                   │────────────────>│ (CAN Rx stops)
 │ [scope guard alive│                  │
 │  → fault active]  │                  │
 │                   │                  │
 │ [verify behavior  │                  │
 │  under dropout]   │                  │
 │                   │                  │
 │ [scope guard dtor]│                  │
 │──────────────────>│ start()         │
 │                   │────────────────>│ (CAN Rx resumes)
 │                   │                  │
 │ PASS / FAIL       │                  │
```

---

## 4. State Machines

### 4.1 Framework Lifecycle

```
        ┌────────────┐
  ─────>│ CREATED    │
        └─────┬──────┘
              │ initialize()
        ┌─────▼──────┐
        │ INITIALIZED│
        └─────┬──────┘
              │ start()
        ┌─────▼──────┐
        │  RUNNING   │◄── request_shutdown() triggered
        └─────┬──────┘    externally (signal or API call)
              │ request_shutdown()
        ┌─────▼──────┐
        │ SHUTTING   │
        │ DOWN       │
        └─────┬──────┘
              │ all modules stopped
        ┌─────▼──────┐
        │  STOPPED   │
        └────────────┘
```

### 4.2 UDS ISO-TP State Machine

```
               send request PDU
IDLE ─────────────────────────────> WAITING_SF_FF
                                         │
                            ┌────────────┴─────────────┐
                            │ SF received               │ FF received
                       ┌────▼────┐               ┌─────▼──────┐
                       │COMPLETE │               │ RECV_CF    │
                       └─────────┘               │ (send FC)  │
                                                  └─────┬──────┘
                                                        │ all CFs received
                                                  ┌─────▼──────┐
                                                  │  COMPLETE  │
                                                  └────────────┘
                                    (any NRC 0x78) ─► WAITING_SF_FF
                                    (timeout)      ─► TIMEOUT error
```

---

## 5. Key Data Structures

### 5.1 CANStatistics
```cpp
struct CANStatistics {
    std::atomic<uint64_t> rx_count{0};
    std::atomic<uint64_t> tx_count{0};
    std::atomic<uint64_t> error_count{0};
    std::atomic<uint64_t> overflow_count{0};
    std::chrono::steady_clock::time_point start_time;
};
```

### 5.2 TestSuiteResult
```cpp
struct TestSuiteResult {
    std::string suite_name;
    std::vector<TestResult> results;
    uint32_t total{0}, passed{0}, failed{0}, skipped{0}, timed_out{0};
    uint64_t duration_ms{0};
    std::chrono::system_clock::time_point timestamp;
};
```

### 5.3 OTAPackageInfo
```cpp
struct OTAPackageInfo {
    std::string version;
    std::string download_url;
    uint64_t    file_size{0};
    std::string checksum;
    std::string release_notes;
};
```

### 5.4 TelemetryData
```cpp
struct TelemetryData {
    double      latitude{0.0}, longitude{0.0};
    double      speed_kmh{0.0};
    double      battery_voltage{0.0};
    std::string signal_quality;
    uint32_t    uptime_seconds{0};
    std::string firmware_version;
    std::map<std::string, std::string> custom_fields;
};
```
