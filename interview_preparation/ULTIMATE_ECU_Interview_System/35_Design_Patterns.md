# Design Patterns Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Design patterns are assessed in senior-level interviews at Harman, KPIT, Continental, and Qualcomm Automotive. You are expected to explain patterns with **automotive ECU context** — not abstract examples. Key patterns used in production automotive software: Singleton (ECU service manager), Observer (CAN signal subscription), Strategy (OTA variant selection), State Machine (ECU boot/OTA/diagnostics), Factory (sensor/protocol object creation), and Command (UDS service handler).

**Key areas probed:**
- Creational: Singleton, Factory, Builder
- Structural: Adapter, Facade, Proxy
- Behavioural: Observer, Strategy, State, Command, Template Method
- Automotive-specific patterns (not GoF): FSM, Event-driven, Layered Architecture
- Anti-patterns: God Object, Magic Numbers, Copy-Paste

---

## CREATIONAL PATTERNS

---

### Q1. Singleton in automotive — ECU service registry. What are the pitfalls?

**Short Answer:** Singleton ensures only one instance exists globally. In automotive, it's used for service managers (CAN manager, DTC manager) that must be shared across modules. Pitfalls: testing difficulty, global state, initialisation order.

**Detailed Expert Answer:**

```cpp
/* Thread-safe Singleton — C++11 (guaranteed by standard: static init is thread-safe) */
class CANManager {
public:
    static CANManager &instance(void) {
        static CANManager s_instance;   /* Initialised once, thread-safe */
        return s_instance;
    }
    
    /* Delete copy/move to enforce single instance */
    CANManager(const CANManager &) = delete;
    CANManager &operator=(const CANManager &) = delete;
    
    void open(const char *iface) {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_fd = can_socket_open(iface);
    }
    
    bool send(const CANFrame &f) {
        std::lock_guard<std::mutex> lock(m_mutex);
        return can_send_frame(m_fd, f.id, f.data, f.dlc) == 0;
    }
    
private:
    CANManager() = default;
    ~CANManager() { if (m_fd >= 0) close(m_fd); }
    
    std::mutex m_mutex;
    int        m_fd = -1;
};

/* Usage from any module */
void send_speed_signal(float speed) {
    CANFrame f = encode_speed(speed);
    CANManager::instance().send(f);
}

/* Pitfall 1: Testing — can't inject mock CANManager */
/* Fix: use Dependency Injection alongside Singleton, or reset for tests: */
#ifdef UNIT_TEST
void CANManager::reset_for_test(void) { /* allow re-init in tests */ }
#endif

/* Pitfall 2: Initialisation order fiasco */
/* If CANManager::instance() is called during construction of another static */
/* C++11 local-static guarantees this is safe (initialised on first call) */

/* Pitfall 3: Never use double-checked locking manually in C++11 */
/* Static local init is already thread-safe — no manual locking needed */
```

---

### Q2. Factory Pattern — automotive sensor/protocol object creation.

**Short Answer:** Factory decouples object creation from usage. The client requests an object by type, and the factory decides which concrete class to instantiate. In automotive, used to create different sensor objects (CAN, LIN, Ethernet) or protocol handlers.

**Detailed Expert Answer:**

```cpp
/* Protocol handler factory — creates appropriate handler based on config */
class IProtocolHandler {
public:
    virtual ~IProtocolHandler() = default;
    virtual bool open(void) = 0;
    virtual bool send_frame(const Frame &frame) = 0;
    virtual std::optional<Frame> recv_frame(int timeout_ms) = 0;
};

class CANHandler final : public IProtocolHandler {
    std::string m_iface;
    int         m_fd = -1;
public:
    explicit CANHandler(const std::string &iface) : m_iface(iface) {}
    bool open(void) override {
        m_fd = can_socket_open(m_iface.c_str());
        return m_fd >= 0;
    }
    bool send_frame(const Frame &frame) override { /* CAN TX */ return true; }
    std::optional<Frame> recv_frame(int timeout_ms) override { /* CAN RX */ return std::nullopt; }
};

class EthernetHandler final : public IProtocolHandler {
    std::string m_ip;
    uint16_t    m_port;
public:
    EthernetHandler(std::string ip, uint16_t port) : m_ip(std::move(ip)), m_port(port) {}
    bool open(void) override { /* TCP connect */ return true; }
    bool send_frame(const Frame &frame) override { /* TCP send */ return true; }
    std::optional<Frame> recv_frame(int timeout_ms) override { return std::nullopt; }
};

class LINHandler final : public IProtocolHandler {
    /* LIN over UART */
public:
    bool open(void) override { /* UART open */ return true; }
    bool send_frame(const Frame &frame) override { return true; }
    std::optional<Frame> recv_frame(int timeout_ms) override { return std::nullopt; }
};

/* Factory function — create based on config */
enum class ProtocolType { CAN, ETHERNET, LIN };

std::unique_ptr<IProtocolHandler> create_handler(ProtocolType type,
                                                  const std::string &param,
                                                  uint16_t port = 0) {
    switch (type) {
    case ProtocolType::CAN:
        return std::make_unique<CANHandler>(param);
    case ProtocolType::ETHERNET:
        return std::make_unique<EthernetHandler>(param, port);
    case ProtocolType::LIN:
        return std::make_unique<LINHandler>();
    default:
        return nullptr;
    }
}

/* Usage — client doesn't know concrete type */
void setup_ecu_protocol(const std::string &config_protocol) {
    ProtocolType type = (config_protocol == "CAN") ? ProtocolType::CAN :
                        (config_protocol == "ETH") ? ProtocolType::ETHERNET :
                        ProtocolType::LIN;
    
    auto handler = create_handler(type, "can0");
    if (handler && handler->open()) {
        /* Use handler — works for any protocol */
        run_communication_loop(*handler);
    }
}
```

---

## BEHAVIOURAL PATTERNS

---

### Q3. Observer Pattern — CAN signal subscription system.

**Short Answer:** Observer defines a one-to-many dependency: when one object changes state, all its observers are notified. In automotive ECUs, signal subscribers (telemetry, display, diagnostics) observe CAN signal updates.

**Detailed Expert Answer:**

```cpp
/* CAN Signal Observer System — used in Adaptive AUTOSAR and TCU software */

class ISignalObserver {
public:
    virtual ~ISignalObserver() = default;
    virtual void on_signal_update(uint32_t signal_id, float value) = 0;
};

class CANSignalBus {
public:
    using ObserverId = uint32_t;
    
    /* Subscribe to a specific signal ID */
    ObserverId subscribe(uint32_t signal_id, ISignalObserver *observer) {
        std::lock_guard<std::mutex> lock(m_mutex);
        ObserverId id = m_next_id++;
        m_subscribers[signal_id].push_back({id, observer});
        return id;
    }
    
    /* Unsubscribe */
    void unsubscribe(uint32_t signal_id, ObserverId obs_id) {
        std::lock_guard<std::mutex> lock(m_mutex);
        auto &subs = m_subscribers[signal_id];
        subs.erase(
            std::remove_if(subs.begin(), subs.end(),
                           [obs_id](const auto &e) { return e.first == obs_id; }),
            subs.end()
        );
    }
    
    /* Publish signal update (called from CAN Rx processing) */
    void publish(uint32_t signal_id, float value) {
        std::vector<ISignalObserver*> to_notify;
        {
            std::lock_guard<std::mutex> lock(m_mutex);
            auto it = m_subscribers.find(signal_id);
            if (it == m_subscribers.end()) return;
            for (const auto &[id, obs] : it->second) {
                if (obs != nullptr) to_notify.push_back(obs);
            }
        }
        /* Notify outside lock to prevent deadlock */
        for (auto *obs : to_notify) {
            obs->on_signal_update(signal_id, value);
        }
    }
    
private:
    std::mutex m_mutex;
    std::unordered_map<uint32_t, std::vector<std::pair<ObserverId, ISignalObserver*>>>
        m_subscribers;
    ObserverId m_next_id = 1;
};

/* Concrete observers */
class TelemetryModule : public ISignalObserver {
    CANSignalBus::ObserverId m_sub_id = 0;
    CANSignalBus &m_bus;
    
public:
    explicit TelemetryModule(CANSignalBus &bus) : m_bus(bus) {
        m_sub_id = bus.subscribe(SIGNAL_VEHICLE_SPEED, this);
    }
    ~TelemetryModule() { m_bus.unsubscribe(SIGNAL_VEHICLE_SPEED, m_sub_id); }
    
    void on_signal_update(uint32_t signal_id, float value) override {
        if (signal_id == SIGNAL_VEHICLE_SPEED) {
            mqtt_publish("vehicle/speed", value);
        }
    }
};

class ODOModule : public ISignalObserver {
public:
    void on_signal_update(uint32_t signal_id, float value) override {
        if (signal_id == SIGNAL_WHEEL_SPEED) {
            accumulate_distance(value);
        }
    }
};
```

---

### Q4. State Machine Pattern — OTA Update state machine.

**Short Answer:** State pattern encapsulates states as objects, eliminating large if/switch chains. Each state handles its own transitions. In automotive, OTA, diagnostics, and communication managers are implemented as explicit state machines.

**Detailed Expert Answer:**

```cpp
/* OTA Update State Machine — used in TCU/telematics ECUs */

enum class OTAState {
    IDLE,
    DOWNLOADING,
    VERIFYING,
    INSTALLING,
    REBOOTING,
    FAILED,
    SUCCESS
};

class OTAStateMachine {
public:
    using StateHandler = std::function<OTAState(void)>;
    
    void run(void) {
        while (m_state != OTAState::SUCCESS && m_state != OTAState::FAILED) {
            OTAState next = m_handlers.at(m_state)();
            if (next != m_state) {
                on_transition(m_state, next);
                m_state = next;
            }
        }
    }
    
    OTAState get_state(void) const { return m_state; }
    
private:
    OTAState m_state = OTAState::IDLE;
    
    std::unordered_map<OTAState, StateHandler> m_handlers = {
        {OTAState::IDLE,        [this]{ return handle_idle();        }},
        {OTAState::DOWNLOADING, [this]{ return handle_downloading(); }},
        {OTAState::VERIFYING,   [this]{ return handle_verifying();   }},
        {OTAState::INSTALLING,  [this]{ return handle_installing();  }},
        {OTAState::REBOOTING,   [this]{ return handle_rebooting();   }},
    };
    
    OTAState handle_idle(void) {
        if (!ota_server_check_update_available()) return OTAState::IDLE;
        log_info("OTA: Update available — starting download");
        return OTAState::DOWNLOADING;
    }
    
    OTAState handle_downloading(void) {
        OTAResult r = ota_download_package(m_pkg_path, &m_progress);
        if (r == OTA_OK)        return OTAState::VERIFYING;
        if (r == OTA_IN_PROG)   return OTAState::DOWNLOADING;  /* Stay */
        log_error("OTA: Download failed");
        return OTAState::FAILED;
    }
    
    OTAState handle_verifying(void) {
        if (!sha256_verify_file(m_pkg_path, m_expected_hash)) {
            log_error("OTA: Hash verification failed");
            return OTAState::FAILED;
        }
        if (!signature_verify(m_pkg_path, m_root_cert)) {
            log_error("OTA: Signature verification failed");
            return OTAState::FAILED;
        }
        return OTAState::INSTALLING;
    }
    
    OTAState handle_installing(void) {
        if (!flash_write_package(m_pkg_path)) {
            log_error("OTA: Flash write failed");
            return OTAState::FAILED;
        }
        return OTAState::REBOOTING;
    }
    
    OTAState handle_rebooting(void) {
        log_info("OTA: Rebooting to apply update");
        system_schedule_reboot(5000);  /* Reboot in 5s */
        return OTAState::SUCCESS;
    }
    
    void on_transition(OTAState from, OTAState to) {
        /* Log, update DTC, publish to telemetry */
        const char *from_str = ota_state_name(from);
        const char *to_str   = ota_state_name(to);
        log_info("OTA: %s → %s", from_str, to_str);
        DEM_ClearDTC(DTC_OTA_FAILURE);  /* Clear on successful transition */
    }
    
    std::string m_pkg_path    = "/tmp/ota_pkg.bin";
    std::string m_expected_hash;
    std::string m_root_cert   = "/etc/certs/ota_root.pem";
    int         m_progress    = 0;
};
```

---

## ADVANCED QUESTIONS

---

### Q5. Strategy Pattern — OTA download strategy selection (SOTA vs FOTA vs delta).

**Expert Answer:**
```cpp
/* Different OTA strategies for different deployment scenarios */

class IUpdateStrategy {
public:
    virtual ~IUpdateStrategy() = default;
    virtual bool download(const std::string &url, const std::string &dest) = 0;
    virtual const char *name(void) const = 0;
};

/* Full OTA package download */
class FullOTAStrategy final : public IUpdateStrategy {
public:
    bool download(const std::string &url, const std::string &dest) override {
        return https_download_file(url, dest, /* resume= */false);
    }
    const char *name(void) const override { return "FULL_OTA"; }
};

/* Delta OTA — only download diff, apply to existing firmware */
class DeltaOTAStrategy final : public IUpdateStrategy {
    std::string m_current_version;
public:
    explicit DeltaOTAStrategy(std::string ver) : m_current_version(std::move(ver)) {}
    bool download(const std::string &url, const std::string &dest) override {
        std::string delta_url = url + "?from=" + m_current_version;
        if (!https_download_file(delta_url, dest + ".delta", true)) return false;
        return bsdiff_apply(get_current_firmware_path(), dest + ".delta", dest);
    }
    const char *name(void) const override { return "DELTA_OTA"; }
};

/* Resumable download — for poor cellular connectivity */
class ResumableOTAStrategy final : public IUpdateStrategy {
public:
    bool download(const std::string &url, const std::string &dest) override {
        size_t offset = get_partial_download_size(dest);
        if (offset > 0) log_info("OTA: Resuming from byte %zu", offset);
        return https_download_file_range(url, dest, offset);
    }
    const char *name(void) const override { return "RESUMABLE_OTA"; }
};

/* Context that uses strategy */
class OTADownloader {
    std::unique_ptr<IUpdateStrategy> m_strategy;
public:
    void set_strategy(std::unique_ptr<IUpdateStrategy> s) {
        m_strategy = std::move(s);
    }
    
    bool execute(const std::string &url, const std::string &dest) {
        if (!m_strategy) { log_error("No strategy set"); return false; }
        log_info("OTA: Using strategy: %s", m_strategy->name());
        return m_strategy->download(url, dest);
    }
};

/* Factory selects strategy based on network conditions and SW versions */
std::unique_ptr<IUpdateStrategy> select_ota_strategy(const DeviceInfo &info) {
    if (info.delta_capable && info.has_current_fw) {
        return std::make_unique<DeltaOTAStrategy>(info.current_version);
    }
    if (info.poor_connectivity) {
        return std::make_unique<ResumableOTAStrategy>();
    }
    return std::make_unique<FullOTAStrategy>();
}
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q6. You see a God Object (1 class with 5000 lines) in an ECU codebase at your new company. How do you refactor it without breaking production?

**Expert Answer:**

"This is a code health problem that requires careful incremental refactoring — not a big-bang rewrite.

**Phase 1 — Understand before touching:**
```bash
# Measure dependencies
grep -n '#include\|using\|extern' ecu_manager.cpp | wc -l
# Check what calls into it
grep -rn 'EcuManager::' src/ | awk -F: '{print $1}' | sort -u
# This shows 47 files call into EcuManager — careful!
```

**Phase 2 — Extract natural seams:**
```cpp
/* God Object before — EcuManager has everything */
class EcuManager {  /* 5000 lines! */
    int m_can_fd;
    DTCList m_dtcs;
    OTAState m_ota_state;
    MQTTClient m_mqtt;
    GPSData m_gps;
    void handle_can(void);
    void handle_dtc(void);
    void handle_ota(void);
    void handle_mqtt(void);
    void handle_gps(void);
    /* ... 200 more methods ... */
};

/* Step 1: Extract CANController without changing EcuManager's interface */
class CANController {
public:
    bool open(const char *iface);
    bool send(const CANFrame &frame);
    std::optional<CANFrame> recv(int timeout_ms);
};

/* Step 2: Add CANController as member, delegate existing methods */
class EcuManager {
    CANController m_can;  /* New extracted class */
    /* ... keep all other fields for now ... */
    
    void handle_can(void) {
        m_can.process();   /* Delegate to extracted class */
    }
};

/* Step 3: Repeat for DTCManager, OTAManager, TelematicsClient */
/* After 4 iterations: */
class EcuManager {   /* Now 200 lines — orchestrator only */
    CANController      m_can;
    DTCManager         m_dtc;
    OTAManager         m_ota;
    TelematicsClient   m_telematics;
    GPSProcessor       m_gps;
};
```

**Production rules:**
```
1. Never refactor in the same PR as bug fixes
2. Add unit tests BEFORE refactoring (characterisation tests)
3. Rename → extract → delegate → verify (in that order)
4. One class at a time — each refactoring is a separate review
5. Keep old method names as delegation wrappers during transition
6. Verify with system-level tests that ECU behaviour unchanged
```

**Production Insight (KPIT, Tata Motors project):** A 6000-line God Object in a telematics ECU was broken into 7 focused classes over 3 months. No regression in field despite 150,000+ units deployed. Key: the characterisation test suite captured all observable ECU behaviours before refactoring began."

---

## CHEAT SHEET — Design Patterns

```
Creational:
  Singleton:   One global instance (use sparingly — makes testing hard)
  Factory:     Create objects by type without knowing concrete class
  Builder:     Construct complex objects step by step (config objects)

Structural:
  Adapter:     Wrap incompatible interface (old CAN API → new IProtocol)
  Facade:      Simplify complex subsystem (ECU startup sequence)
  Proxy:       Substitute for an object (mock CAN controller in tests)

Behavioural:
  Observer:    CAN signal subscribers notified on update
  Strategy:    OTA download strategy swappable at runtime
  State:       OTA/boot/diagnostic state machine with explicit state objects
  Command:     UDS service handler — encapsulates a request as an object
  Template Method: Algorithm skeleton in base, steps in derived

Automotive pattern recognition:
  "Subscribe to signal changes"     → Observer
  "Different sensor implementations" → Factory + Interface (polymorphism)
  "Boot/OTA/diagnostic flow"        → State Machine
  "Choose algorithm at runtime"     → Strategy
  "Only one CAN manager"            → Singleton (with care)
  "Simplify complex startup code"   → Facade

Anti-patterns to call out in interview:
  God Object: one class that does everything → extract into SRP classes
  Magic Numbers: use named constants (MISRA C:2012 Rule 7.2)
  Copy-Paste code: extract into reusable function
  Global variables everywhere: inject as constructor parameters instead
```
