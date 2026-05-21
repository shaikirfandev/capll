# OOP (Object-Oriented Programming) Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

OOP is probed in all senior C++ automotive roles. At Harman, Continental, Qualcomm Automotive, and KPIT, interviewers want to see **automotive contextual application** of OOP — not just textbook definitions. You need to explain how RAII prevents resource leaks in ECU drivers, how polymorphism enables sensor abstraction, and why virtual functions have overhead implications in embedded.

**Key areas probed:**
- Four pillars (encapsulation, inheritance, polymorphism, abstraction)
- Virtual functions and vtable internals
- Abstract classes and pure virtual functions
- RAII (Resource Acquisition Is Initialisation)
- Rule of Zero / Three / Five
- Liskov Substitution Principle and how to violate it
- Object slicing
- Multiple inheritance pitfalls (diamond problem)
- Interface design for sensor/protocol abstraction
- OOP performance in embedded (vtable overhead, avoiding RTTI)

---

## BEGINNER QUESTIONS

---

### Q1. What is RAII and why is it critical in automotive embedded C++?

**Short Answer:** RAII binds resource lifetime to object lifetime. The constructor acquires the resource; the destructor releases it. This guarantees release even if an exception occurs or a return statement is hit mid-function — preventing resource leaks in ECU drivers.

**Detailed Expert Answer:**

```cpp
/* WITHOUT RAII — classic C-style, error-prone */
bool process_can_data(const char *iface) {
    int fd = open_can_socket(iface);
    if (fd < 0) return false;
    
    configure_can_socket(fd);
    
    if (!validate_data()) {
        close(fd);      /* Must remember to close on every exit path! */
        return false;
    }
    
    send_can_frame(fd);
    close(fd);          /* Must remember here too */
    return true;
}
/* If a new return path is added later and developer forgets close() → FD leak */
/* After ~1000 reconnects in fleet: ECU runs out of file descriptors */

/* WITH RAII — C++ RAII wrapper */
class CANSocket {
    int m_fd = -1;
    
public:
    explicit CANSocket(const char *iface) {
        m_fd = open_can_socket(iface);
        if (m_fd < 0) throw std::runtime_error("Cannot open CAN socket");
    }
    
    ~CANSocket() noexcept {
        if (m_fd >= 0) close(m_fd);  /* Always closes — no matter how we exit */
    }
    
    /* Move-only — socket can't be copied (two owners = double close = bug) */
    CANSocket(const CANSocket&) = delete;
    CANSocket &operator=(const CANSocket&) = delete;
    CANSocket(CANSocket&& o) noexcept : m_fd(o.m_fd) { o.m_fd = -1; }
    CANSocket &operator=(CANSocket&& o) noexcept {
        if (this != &o) { if (m_fd >= 0) close(m_fd); m_fd = o.m_fd; o.m_fd = -1; }
        return *this;
    }
    
    int fd(void) const noexcept { return m_fd; }
    bool valid(void) const noexcept { return m_fd >= 0; }
    
    void send_frame(const can_frame &frame) {
        if (write(m_fd, &frame, sizeof(frame)) != sizeof(frame)) {
            throw std::runtime_error("CAN write failed");
        }
    }
};

/* Clean version with RAII */
bool process_can_data(const char *iface) {
    CANSocket sock(iface);     /* Constructor opens socket */
    if (!sock.valid()) return false;
    
    configure_can_socket(sock.fd());
    
    if (!validate_data()) return false;  /* Destructor closes socket automatically */
    
    struct can_frame frame = build_frame();
    sock.send_frame(frame);
    return true;
    /* CANSocket destructor runs here — socket always closed */
}
```

**RAII for automotive resources:**
```cpp
/* ===== Mutex RAII (std::lock_guard) ===== */
std::mutex g_state_mutex;

void update_ecu_state(ECUState new_state) {
    std::lock_guard<std::mutex> lock(g_state_mutex);  /* Lock on entry */
    g_ecu_state = new_state;
    notify_state_change(new_state);
}  /* lock_guard destructor → mutex.unlock() — even if exception thrown */

/* ===== Memory RAII (unique_ptr) ===== */
void process_ota_packet(const uint8_t *raw, size_t len) {
    auto packet = std::make_unique<OTAPacket>(raw, len);
    packet->verify();
    packet->flash_write();
}  /* unique_ptr destructor → delete packet — no delete needed */

/* ===== File RAII (POSIX) ===== */
class AutoFile {
    FILE *m_fp = nullptr;
public:
    explicit AutoFile(const char *path, const char *mode)
        : m_fp(fopen(path, mode)) {}
    ~AutoFile() { if (m_fp) fclose(m_fp); }
    FILE *get(void) const noexcept { return m_fp; }
    bool ok(void) const noexcept { return m_fp != nullptr; }
};
```

---

### Q2. What is the Rule of Five? Write one for an automotive ECU class.

**Short Answer:** The Rule of Five states: if you define any of (destructor, copy constructor, copy assignment, move constructor, move assignment), you should define all five. This ensures correct resource management for classes that own resources.

**Detailed Expert Answer:**

```cpp
/* ECU TCP connection — owns socket file descriptor (a resource) */
class TCPConnection {
    int         m_sockfd = -1;
    std::string m_host;
    uint16_t    m_port = 0;
    
public:
    /* Constructor */
    TCPConnection(const std::string &host, uint16_t port)
        : m_host(host), m_port(port) {
        m_sockfd = tcp_connect(host.c_str(), port);
        if (m_sockfd < 0) throw std::runtime_error("Connection failed");
    }
    
    /* 1. DESTRUCTOR — releases the resource */
    ~TCPConnection() noexcept {
        if (m_sockfd >= 0) {
            shutdown(m_sockfd, SHUT_RDWR);
            close(m_sockfd);
        }
    }
    
    /* 2. COPY CONSTRUCTOR — deleted (can't copy a TCP socket) */
    TCPConnection(const TCPConnection &) = delete;
    
    /* 3. COPY ASSIGNMENT — deleted */
    TCPConnection &operator=(const TCPConnection &) = delete;
    
    /* 4. MOVE CONSTRUCTOR — transfers ownership */
    TCPConnection(TCPConnection &&other) noexcept
        : m_sockfd(other.m_sockfd)
        , m_host(std::move(other.m_host))
        , m_port(other.m_port) {
        other.m_sockfd = -1;  /* Source no longer owns socket */
        other.m_port   = 0;
    }
    
    /* 5. MOVE ASSIGNMENT — releases old, transfers new */
    TCPConnection &operator=(TCPConnection &&other) noexcept {
        if (this != &other) {
            /* Release current resource */
            if (m_sockfd >= 0) { shutdown(m_sockfd, SHUT_RDWR); close(m_sockfd); }
            /* Take ownership from other */
            m_sockfd   = other.m_sockfd;
            m_host     = std::move(other.m_host);
            m_port     = other.m_port;
            other.m_sockfd = -1;
            other.m_port   = 0;
        }
        return *this;
    }
    
    /* Business logic */
    ssize_t send(const void *data, size_t len) {
        return write(m_sockfd, data, len);
    }
};

/* Rule of Zero — prefer to let compiler generate all five */
/* Use this when your class only contains RAII members: */
class OTAManager {
    TCPConnection         m_conn;   /* RAII member */
    std::unique_ptr<Cert> m_cert;   /* RAII member */
    std::vector<uint8_t>  m_buf;    /* RAII member */
    
    /* NO destructor, copy/move defined — compiler handles it correctly */
    /* TCPConnection is move-only → OTAManager is automatically move-only */
};
```

---

## INTERMEDIATE QUESTIONS

---

### Q3. Explain virtual functions and vtable layout. What is the cost in automotive embedded?

**Short Answer:** Virtual functions are resolved at runtime through a vtable — a per-class array of function pointers. Each polymorphic object has a hidden `vptr` pointing to its class vtable. Cost: one extra pointer per object, one indirect call per virtual dispatch.

**Detailed Expert Answer:**

```
Vtable layout for sensor abstraction:

ISensor (abstract base class):
  vtable: [0]: ISensor::~ISensor  
          [1]: ISensor::read() = 0
          [2]: ISensor::get_id() = 0

SpeedSensor (derived):
  vtable: [0]: SpeedSensor::~SpeedSensor
          [1]: SpeedSensor::read()      ← overrides
          [2]: SpeedSensor::get_id()    ← overrides

CameraSensor (derived):
  vtable: [0]: CameraSensor::~CameraSensor
          [1]: CameraSensor::read()
          [2]: CameraSensor::get_id()

Object memory layout:
SpeedSensor obj:
┌───────────────────┐
│ vptr ─────────────┼──▶ SpeedSensor::vtable[0..2]
│ m_can_id          │
│ m_last_reading    │
└───────────────────┘
```

```cpp
/* Interface definition */
class ISensor {
public:
    virtual ~ISensor() = default;                  /* Virtual destructor essential! */
    virtual float read(void) = 0;                  /* Pure virtual */
    virtual uint8_t get_id(void) const = 0;
    virtual const char *get_type(void) const = 0;
};

/* Concrete implementations */
class SpeedSensor final : public ISensor {
    uint32_t m_can_id;
    float    m_last_speed = 0.0f;
    
public:
    explicit SpeedSensor(uint32_t can_id) : m_can_id(can_id) {}
    
    float read(void) override {
        /* Read from CAN signal cache */
        m_last_speed = g_can_signals.get_speed(m_can_id);
        return m_last_speed;
    }
    uint8_t get_id(void) const override { return static_cast<uint8_t>(m_can_id); }
    const char *get_type(void) const override { return "SPEED"; }
};

class CameraSensor final : public ISensor {
    int m_camera_idx;
public:
    explicit CameraSensor(int idx) : m_camera_idx(idx) {}
    float read(void) override { return static_cast<float>(camera_get_confidence(m_camera_idx)); }
    uint8_t get_id(void) const override { return static_cast<uint8_t>(0x80 + m_camera_idx); }
    const char *get_type(void) const override { return "CAMERA"; }
};

/* Polymorphic usage */
void log_all_sensors(const std::vector<std::unique_ptr<ISensor>> &sensors) {
    for (const auto &sensor : sensors) {
        printf("[%s id=%02X] = %.2f\n",
               sensor->get_type(), sensor->get_id(), sensor->read());
    }
}
```

**Virtual function cost in automotive embedded:**
```
Cost analysis on Cortex-M7 (400 MHz):

Direct call:       BL func_addr        → 1 cycle
Virtual call:      LDR R0, [obj]       → load vptr (1 cycle + cache)
                   LDR R1, [R0, #8]    → load vtable entry (1 cycle + cache)
                   BLX R1              → indirect branch (3-5 cycles)
Total overhead: ~5-6 cycles + potential I-cache miss

For RT tasks at 1kHz (1ms period): 
  5000 cycle budget per task tick
  10 virtual calls = 60 cycles extra = 1.2% overhead → acceptable

For fast ISR (10μs, 4000 cycle budget):
  10 virtual calls = 60 cycles = 1.5% → borderline
  For <10μs ISR: prefer non-virtual, template CRTP, or direct function pointer

RTTI (dynamic_cast, typeid) — MUCH worse:
  -fno-rtti: disable entirely (AUTOSAR, embedded standard practice)
  -fno-exceptions: also typically disabled in embedded
```

**CRTP — zero-cost polymorphism:**
```cpp
/* Curiously Recurring Template Pattern — resolved at compile time */
template<typename Derived>
class SensorBase {
public:
    float read(void) {
        return static_cast<Derived*>(this)->read_impl();  /* No vtable! */
    }
};

class TempSensor : public SensorBase<TempSensor> {
public:
    float read_impl(void) { return adc_read_celsius(); }  /* Inlined */
};

/* Compiler resolves at compile time → as fast as direct call */
/* Cost: larger binary (template instantiation per type) */
/* Downside: can't store mixed types in same container (no runtime polymorphism) */
```

---

## ADVANCED QUESTIONS

---

### Q4. Describe the diamond problem and how to solve it with virtual inheritance.

**Expert Answer:**
```cpp
/* Diamond inheritance problem */
class Vehicle {
public:
    void set_speed(float s) { m_speed = s; }
    float get_speed(void) const { return m_speed; }
protected:
    float m_speed = 0.0f;
};

class ElectricDrive : public Vehicle {
public:
    void set_motor_torque(float t) { m_torque = t; }
protected:
    float m_torque = 0.0f;
};

class RegenerativeBraking : public Vehicle {
public:
    void brake(float force) { m_brake_force = force; }
protected:
    float m_brake_force = 0.0f;
};

/* Diamond: HybridECU inherits Vehicle TWICE */
class HybridECU : public ElectricDrive, public RegenerativeBraking {
    /* m_speed is ambiguous! Two copies of Vehicle::m_speed */
};

HybridECU ecu;
/* ecu.get_speed(); */ /* ERROR: ambiguous — which Vehicle base? */
ecu.ElectricDrive::get_speed();  /* Must qualify — ugly */

/* FIX: virtual inheritance — only ONE copy of Vehicle */
class ElectricDrive_V    : public virtual Vehicle { /* ... */ };
class RegenerativeBraking_V : public virtual Vehicle { /* ... */ };
class HybridECU_V : public ElectricDrive_V, public RegenerativeBraking_V {
    /* Only one Vehicle base — m_speed shared */
};

HybridECU_V ecu2;
ecu2.get_speed();  /* Unambiguous — one Vehicle */

/* Cost of virtual inheritance:
   - Extra pointer in object (virtual base pointer)
   - Constructor complexity (most-derived class must init virtual base)
   
   Automotive recommendation: avoid diamond — use composition over inheritance */
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q5. You have a sensor abstraction class. A new sensor has different timing requirements. How do you extend without breaking existing code?

**Expert Answer — Open/Closed Principle in automotive context:**

```cpp
/* Original interface */
class ISensor {
public:
    virtual ~ISensor() = default;
    virtual float read(void) = 0;
    virtual uint32_t get_update_rate_hz(void) const = 0;
};

/* New requirement: some sensors have asynchronous read (camera, radar) */
/* WRONG: modify ISensor interface → breaks all existing implementations */
class ISensor_BAD {
    virtual float read(void) = 0;
    virtual void read_async(std::function<void(float)> cb) = 0;  /* Added! */
    /* All existing sensors now must implement this — breaking change! */
};

/* CORRECT: extend with new interface, keep ISensor intact */
class IAsyncSensor : public ISensor {
public:
    virtual ~IAsyncSensor() = default;
    virtual void read_async(std::function<void(float)> cb) = 0;
};

/* Async sensor implements both */
class RadarSensor final : public IAsyncSensor {
    float m_last_dist = 0.0f;
public:
    float read(void) override { return m_last_dist; }  /* Sync: return cached */
    uint32_t get_update_rate_hz(void) const override { return 20U; }
    void read_async(std::function<void(float)> cb) override {
        /* Start DMA radar read, call cb when done */
        radar_start_measurement([cb, this](float d) {
            m_last_dist = d;
            cb(d);
        });
    }
};

/* Existing SpeedSensor unchanged — still only ISensor */

/* Sensor manager: use IAsyncSensor if available */
void SensorManager::update(ISensor &sensor) {
    if (auto *async = dynamic_cast<IAsyncSensor*>(&sensor)) {
        /* Has async capability — use it */
        /* NOTE: dynamic_cast requires RTTI — OK here if RTTI enabled */
        /* Alternative: add virtual bool supports_async() const = 0 to avoid RTTI */
        async->read_async([&](float v) { store_reading(sensor.get_id(), v); });
    } else {
        store_reading(sensor.get_id(), sensor.read());
    }
}
```

---

## CHEAT SHEET — OOP

```
Four OOP pillars in automotive context:
  Encapsulation:    CANSocket class hides fd, provides clean send/recv API
  Inheritance:      SpeedSensor is-a ISensor, adds automotive-specific read()
  Polymorphism:     SensorManager holds ISensor*, calls read() on any sensor
  Abstraction:      ISensor defines WHAT (read, get_id) not HOW

Virtual function essentials:
  Always make base class destructor virtual (or delete copy)
  = 0 → pure virtual → class is abstract (cannot instantiate)
  override keyword → compiler checks you actually override a virtual
  final keyword → no further override allowed (enables devirtualisation)
  
RAII pattern:
  Resource acquired in constructor → released in destructor
  Works even with exceptions, early returns
  Use for: sockets, file descriptors, mutexes, DMA buffers, hardware peripherals

Rule of Five (if you own a resource):
  1. Destructor: release resource
  2. Copy constructor: delete or deep copy
  3. Copy assignment: delete or deep copy + self-assign check
  4. Move constructor: steal resource, zero out source
  5. Move assignment: release old, steal new, zero out source
  
  Rule of Zero: prefer RAII members — let compiler generate all five

Embedded OOP cost:
  vtable: 1 pointer per object + 1 indirect call overhead (5-6 cycles ARM)
  RTTI: dynamic_cast, typeid — disable with -fno-rtti
  Exceptions: disable with -fno-exceptions
  CRTP: zero-cost compile-time polymorphism (preferred for tight loops)

Object slicing (common bug):
  Base b = Derived();  ← copies only Base part, virtual functions lost!
  Fix: always pass polymorphic objects by pointer or reference
```
