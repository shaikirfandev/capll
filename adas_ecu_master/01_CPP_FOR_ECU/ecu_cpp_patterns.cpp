/**
 * @file    ecu_cpp_patterns.cpp
 * @brief   Production C++ patterns for ADAS ECU development
 * @details Demonstrates: RAII, static containers, sensor abstraction,
 *          CAN signal handling, state management
 *
 * @note    Compiled with: g++ -std=c++17 -Wall -Wextra -O2
 *          For ECU target: arm-none-eabi-g++ -std=c++14 -fno-exceptions -fno-rtti
 *
 * @author  ADAS ECU Team
 * @version 1.0
 */

#include <cstdint>
#include <cstddef>
#include <cmath>
#include <cassert>
#include <array>
#include <algorithm>
#include <iostream>

// ============================================================================
// ECU TYPES — Commonly used across all ADAS modules
// ============================================================================

enum class SensorStatus : uint8_t {
    UNINITIALIZED = 0U,
    OK            = 1U,
    DEGRADED      = 2U,
    ERROR         = 3U,
    TIMEOUT       = 4U,
};

enum class AdasSystemState : uint8_t {
    INACTIVE  = 0U,
    STANDBY   = 1U,
    ACTIVE    = 2U,
    DEGRADED  = 3U,
    FAULT     = 4U,
    OVERRIDE  = 5U,
};

struct CanFrame {
    uint32_t id          = 0U;
    uint8_t  dlc         = 0U;
    uint8_t  data[8U]    = {};
    uint32_t timestamp_ms = 0U;
};

struct SensorSample {
    float    value       = 0.0F;
    uint32_t timestamp_ms = 0U;
    bool     valid       = false;
};

// ============================================================================
// STATIC RING BUFFER — Zero heap, fixed capacity, power-of-2 size
// ============================================================================

template<typename T, std::size_t Capacity>
class StaticRingBuffer {
    static_assert(Capacity > 0U,                           "Capacity must be > 0");
    static_assert((Capacity & (Capacity - 1U)) == 0U,     "Capacity must be power of 2");

public:
    bool push(const T& item) noexcept {
        if (isFull()) { return false; }
        buffer_[writeIdx_ & MASK] = item;
        ++writeIdx_;
        return true;
    }

    bool pop(T& outItem) noexcept {
        if (isEmpty()) { return false; }
        outItem = buffer_[readIdx_ & MASK];
        ++readIdx_;
        return true;
    }

    const T& peek() const noexcept {
        assert(!isEmpty());
        return buffer_[readIdx_ & MASK];
    }

    void clear() noexcept { readIdx_ = writeIdx_ = 0U; }
    bool isEmpty()  const noexcept { return writeIdx_ == readIdx_; }
    bool isFull()   const noexcept { return (writeIdx_ - readIdx_) == Capacity; }
    std::size_t size() const noexcept { return writeIdx_ - readIdx_; }
    static constexpr std::size_t capacity() { return Capacity; }

private:
    static constexpr std::size_t MASK = Capacity - 1U;
    T           buffer_[Capacity]     = {};
    std::size_t writeIdx_             = 0U;
    std::size_t readIdx_              = 0U;
};

// ============================================================================
// CAN SIGNAL DECODER — Type-safe, no dynamic allocation
// ============================================================================

/**
 * Extract a CAN signal from a frame's data bytes.
 *
 * @param data      Pointer to 8-byte CAN data
 * @param startBit  Start bit position (little-endian / Motorola per DBC definition)
 * @param bitLen    Number of bits
 * @param factor    DBC scaling factor
 * @param offset    DBC offset
 * @return          Physical value = (raw_value * factor) + offset
 */
float decodeCanSignal(const uint8_t* data, uint8_t startBit, uint8_t bitLen,
                      float factor, float offset) noexcept {
    assert(data   != nullptr);
    assert(bitLen <= 32U);

    uint32_t rawValue = 0U;
    for (uint8_t i = 0U; i < bitLen; ++i) {
        uint8_t bitPos  = startBit + i;
        uint8_t byteIdx = bitPos / 8U;
        uint8_t bitIdx  = bitPos % 8U;
        if ((data[byteIdx] >> bitIdx) & 0x01U) {
            rawValue |= (1U << i);
        }
    }

    return (static_cast<float>(rawValue) * factor) + offset;
}

// Strongly typed signal decoder for specific messages
namespace VehicleSignals {
    // CAN ID 0x100: Vehicle Speed Message (from BCM)
    // Signal: VehicleSpeed, startBit=0, len=16, factor=0.01, offset=0 → km/h
    float decodeVehicleSpeed(const CanFrame& frame) noexcept {
        if (frame.id != 0x100U || frame.dlc < 2U) { return 0.0F; }
        return decodeCanSignal(frame.data, 0U, 16U, 0.01F, 0.0F);
    }

    // CAN ID 0x200: Steering Message (from EPS)
    // Signal: SteeringAngle, startBit=0, len=16, factor=0.1, offset=-3276.8 → degrees
    float decodeSteeringAngle(const CanFrame& frame) noexcept {
        if (frame.id != 0x200U || frame.dlc < 2U) { return 0.0F; }
        return decodeCanSignal(frame.data, 0U, 16U, 0.1F, -3276.8F);
    }
}

// ============================================================================
// ABSTRACT SENSOR INTERFACE + CONCRETE IMPLEMENTATIONS
// ============================================================================

class ISensor {
public:
    virtual ~ISensor() = default;

    virtual bool         init()                    = 0;
    virtual void         update()                  = 0;
    virtual SensorStatus getStatus() const         = 0;
    virtual SensorSample getLatest() const         = 0;
    virtual const char*  getName()   const         = 0;

    bool isHealthy() const noexcept {
        return getStatus() == SensorStatus::OK;
    }
};

// Simulated radar sensor: provides distance to lead vehicle
class RadarSensor : public ISensor {
public:
    static constexpr float MIN_RANGE_M = 0.5F;
    static constexpr float MAX_RANGE_M = 200.0F;

    bool init() override {
        status_  = SensorStatus::OK;
        failCnt_ = 0U;
        std::cout << "[Radar] Initialised\n";
        return true;
    }

    void update() override {
        // In production: read from CAN Rx buffer / SPI / UART
        // Here: simulate sinusoidal distance for testing
        simulatedTime_ += 0.02F;  // 20ms cycle
        float simDist = 30.0F + 20.0F * std::sin(simulatedTime_ * 0.3F);

        if (simDist >= MIN_RANGE_M && simDist <= MAX_RANGE_M) {
            latest_.value        = simDist;
            latest_.valid        = true;
            latest_.timestamp_ms = static_cast<uint32_t>(simulatedTime_ * 1000.0F);
            status_              = SensorStatus::OK;
            failCnt_             = 0U;
        } else {
            ++failCnt_;
            if (failCnt_ > MAX_FAIL_COUNT) {
                status_        = SensorStatus::ERROR;
                latest_.valid  = false;
            }
        }
    }

    SensorStatus getStatus() const override { return status_; }
    SensorSample getLatest() const override { return latest_; }
    const char*  getName()   const override { return "RADAR_FRONT"; }

private:
    static constexpr uint32_t MAX_FAIL_COUNT = 5U;
    SensorStatus status_        = SensorStatus::UNINITIALIZED;
    SensorSample latest_        = {};
    float        simulatedTime_ = 0.0F;
    uint32_t     failCnt_       = 0U;
};

// Simulated camera sensor: provides lane offset
class CameraLaneSensor : public ISensor {
public:
    bool init() override {
        status_ = SensorStatus::OK;
        std::cout << "[Camera] Initialised\n";
        return true;
    }

    void update() override {
        simulatedTime_ += 0.02F;
        // Simulate lane offset oscillating around centre
        latest_.value        = 0.15F * std::sin(simulatedTime_ * 0.5F);
        latest_.valid        = true;
        latest_.timestamp_ms = static_cast<uint32_t>(simulatedTime_ * 1000.0F);
    }

    SensorStatus getStatus() const override { return status_; }
    SensorSample getLatest() const override { return latest_; }
    const char*  getName()   const override { return "CAMERA_FRONT"; }

private:
    SensorStatus status_        = SensorStatus::UNINITIALIZED;
    SensorSample latest_        = {};
    float        simulatedTime_ = 0.0F;
};

// ============================================================================
// SENSOR MANAGER — Statically allocated, manages up to N sensors
// ============================================================================

class SensorManager {
public:
    static constexpr std::size_t MAX_SENSORS = 8U;

    bool registerSensor(ISensor& sensor) noexcept {
        if (count_ >= MAX_SENSORS) { return false; }
        sensors_[count_++] = &sensor;
        return true;
    }

    bool initAll() noexcept {
        bool allOk = true;
        for (std::size_t i = 0U; i < count_; ++i) {
            if (!sensors_[i]->init()) {
                allOk = false;
            }
        }
        return allOk;
    }

    void updateAll() noexcept {
        for (std::size_t i = 0U; i < count_; ++i) {
            sensors_[i]->update();
        }
    }

    ISensor* findByName(const char* name) noexcept {
        for (std::size_t i = 0U; i < count_; ++i) {
            if (std::string(sensors_[i]->getName()) == name) {
                return sensors_[i];
            }
        }
        return nullptr;
    }

    void printStatus() const noexcept {
        std::cout << "=== Sensor Status ===\n";
        for (std::size_t i = 0U; i < count_; ++i) {
            const char* statusStr = "UNKNOWN";
            switch (sensors_[i]->getStatus()) {
            case SensorStatus::OK:            statusStr = "OK";      break;
            case SensorStatus::DEGRADED:      statusStr = "DEGRADED"; break;
            case SensorStatus::ERROR:         statusStr = "ERROR";   break;
            case SensorStatus::TIMEOUT:       statusStr = "TIMEOUT"; break;
            case SensorStatus::UNINITIALIZED: statusStr = "UNINIT";  break;
            }
            std::cout << "  " << sensors_[i]->getName() << ": " << statusStr << "\n";
        }
    }

private:
    ISensor*    sensors_[MAX_SENSORS] = {};
    std::size_t count_                = 0U;
};

// ============================================================================
// PID CONTROLLER — Used in LKA lateral control and ACC speed control
// ============================================================================

class PidController {
public:
    struct Params {
        float kp           = 1.0F;
        float ki           = 0.0F;
        float kd           = 0.0F;
        float outputMin    = -1.0F;
        float outputMax    =  1.0F;
        float integralClamp = 10.0F;  // Anti-windup
    };

    explicit PidController(const Params& params) noexcept : p_(params) {}

    /**
     * Compute PID output.
     * @param setpoint  Desired value
     * @param measured  Measured value
     * @param dt_s      Time delta in seconds
     * @return          Clamped control output
     */
    float compute(float setpoint, float measured, float dt_s) noexcept {
        if (dt_s <= 0.0F) { return 0.0F; }

        const float error = setpoint - measured;

        // Proportional
        const float pTerm = p_.kp * error;

        // Integral with anti-windup clamp
        integral_ += error * dt_s;
        integral_  = std::clamp(integral_, -p_.integralClamp, p_.integralClamp);
        const float iTerm = p_.ki * integral_;

        // Derivative (filtered to reduce noise)
        const float derivative = (error - prevError_) / dt_s;
        const float dTerm      = p_.kd * derivative;
        prevError_ = error;

        const float output = pTerm + iTerm + dTerm;
        return std::clamp(output, p_.outputMin, p_.outputMax);
    }

    void reset() noexcept {
        integral_ = 0.0F;
        prevError_ = 0.0F;
    }

private:
    Params p_;
    float  integral_  = 0.0F;
    float  prevError_ = 0.0F;
};

// ============================================================================
// MAIN: DEMONSTRATE PATTERNS
// ============================================================================

int main() {
    std::cout << "=== ADAS ECU C++ Patterns Demo ===\n\n";

    // --- Static Ring Buffer ---
    StaticRingBuffer<CanFrame, 16U> canRxBuf;
    CanFrame frame{};
    frame.id  = 0x100U;
    frame.dlc = 8U;
    frame.data[0] = 0x64U;  // Speed = 100 * 0.01 = 1.0 km/h raw
    frame.data[1] = 0x27U;
    canRxBuf.push(frame);
    std::cout << "CAN RX buffer size: " << canRxBuf.size() << "/16\n";

    // --- Signal Decoding ---
    CanFrame speedFrame{};
    speedFrame.id  = 0x100U;
    speedFrame.dlc = 8U;
    // Encode 100.00 km/h: raw = 10000, hex = 0x2710
    speedFrame.data[0] = 0x10U;
    speedFrame.data[1] = 0x27U;
    float speed = VehicleSignals::decodeVehicleSpeed(speedFrame);
    std::cout << "Decoded vehicle speed: " << speed << " km/h\n";

    // --- Sensor Manager ---
    RadarSensor     radar;
    CameraLaneSensor camera;
    SensorManager   sensorMgr;

    sensorMgr.registerSensor(radar);
    sensorMgr.registerSensor(camera);
    sensorMgr.initAll();

    // --- PID Controller ---
    PidController::Params lkaPidParams;
    lkaPidParams.kp          = 0.5F;
    lkaPidParams.ki          = 0.1F;
    lkaPidParams.kd          = 0.05F;
    lkaPidParams.outputMin   = -5.0F;   // Max steering correction -5 degrees
    lkaPidParams.outputMax   =  5.0F;
    PidController lkaPid(lkaPidParams);

    // --- Simulate 10 task cycles (20ms each) ---
    std::cout << "\n=== Simulation: 10 Task Cycles (20ms) ===\n";
    for (int cycle = 0; cycle < 10; ++cycle) {
        sensorMgr.updateAll();

        SensorSample laneSample = camera.getLatest();
        SensorSample radarSample = radar.getLatest();

        float steeringCorrection = 0.0F;
        if (laneSample.valid) {
            steeringCorrection = lkaPid.compute(0.0F, laneSample.value, 0.02F);
        }

        std::cout << "Cycle " << cycle + 1
                  << "  LaneOffset: " << laneSample.value << "m"
                  << "  RadarDist: "  << radarSample.value << "m"
                  << "  SteerCorr: "  << steeringCorrection << "deg\n";
    }

    sensorMgr.printStatus();
    return 0;
}
