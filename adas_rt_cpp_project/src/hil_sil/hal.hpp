#pragma once
/**
 * @file hal.hpp
 * @brief Hardware Abstraction Layer (HAL) for HIL/SIL portability.
 *
 * PURPOSE
 * ───────
 * The HAL decouples the ADAS algorithm from the physical hardware interface.
 * In production (HIL), the concrete implementation calls into the real
 * CAN/Ethernet driver. In SIL, the implementation reads from simulation files
 * or a virtual CAN interface (vcan0).
 *
 * PATTERN: Strategy (compile-time injection via template) + runtime injection
 * via abstract base class (IHal).
 *
 * SIL vs HIL ENVIRONMENT
 * ──────────────────────
 *   SIL (Software-In-the-Loop):
 *     • All ECU code runs on a host PC.
 *     • Sensor data injected from recorded traces (MDF4/CSV) or simulation
 *       model (MATLAB/Simulink AUTOSAR model).
 *     • Time is simulated (deterministic replay).
 *     • Tools: CANoe + CAPL scripts, vcan + socketcan, or custom harness.
 *
 *   HIL (Hardware-In-the-Loop):
 *     • Real ECU hardware connected to a HIL rig (dSPACE, NI PXI, SCALEXIO).
 *     • Real-time simulator generates physical bus signals.
 *     • Same ADAS C++ code runs on the target SoC.
 *     • Tools: CANalyzer, CANoe, INCA, CANape.
 */

#include <cstdint>
#include <functional>
#include <vector>

namespace adas {
namespace hil {

// ─── CAN frame ────────────────────────────────────────────────────────────────

struct CanFrame {
    uint32_t id;          ///< CAN ID (11 or 29-bit)
    uint8_t  dlc;         ///< Data Length Code [0-8]
    uint8_t  data[8];
    uint64_t timestamp_us;
    bool     is_extended; ///< true for 29-bit CAN ID
};

// ─── Sensor data from HIL rig ─────────────────────────────────────────────────

struct GpsPosition {
    double   latitude_deg;
    double   longitude_deg;
    float    altitude_m;
    float    accuracy_m;
    uint64_t timestamp_us;
};

struct ImuData {
    float    accel_x, accel_y, accel_z;   ///< [m/s²]
    float    gyro_x,  gyro_y,  gyro_z;    ///< [rad/s]
    uint64_t timestamp_us;
};

// ─── Callbacks ────────────────────────────────────────────────────────────────

using CanRxCallback  = std::function<void(const CanFrame&)>;
using GpsCallback    = std::function<void(const GpsPosition&)>;
using ImuCallback    = std::function<void(const ImuData&)>;

// ─── Abstract HAL interface ───────────────────────────────────────────────────

/**
 * @class IHal
 * @brief Pure interface for all hardware I/O.
 *
 * Concrete subclasses:
 *   - CanHal      (real CAN via SocketCAN / PEAK PCAN)
 *   - SimHal      (virtual CAN for SIL via socketcan vcan0)
 *   - ReplayHal   (replays recorded MDF4/CSV sensor data)
 */
class IHal {
public:
    virtual ~IHal() = default;

    /// Open hardware / simulation channel
    virtual bool open()  = 0;

    /// Close channel and release resources
    virtual void close() = 0;

    /// Transmit a CAN frame
    virtual bool txCan(const CanFrame& frame) = 0;

    /// Register callback for received CAN frames (called from RX thread)
    virtual void registerCanRxCallback(CanRxCallback cb) = 0;

    /// Register GPS data callback
    virtual void registerGpsCallback(GpsCallback cb) = 0;

    /// Register IMU data callback
    virtual void registerImuCallback(ImuCallback cb) = 0;

    /// True if running in simulation mode
    virtual bool isSimulation() const = 0;
};

}  // namespace hil
}  // namespace adas
