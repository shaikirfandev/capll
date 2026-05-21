#pragma once
/**
 * @file can_bus_sim.hpp
 * @brief Virtual CAN bus simulator for SIL testing.
 *
 * In a real HIL setup this would use SocketCAN (Linux vcan0) or a vendor API
 * (PEAK PCAN, Vector XL-driver, Kvaser CANlib).
 *
 * This class provides:
 *   1. A virtual CAN bus (in-process ring buffer) for unit/SIL testing.
 *   2. A SocketCAN backend (ifdef ADAS_USE_SOCKETCAN) for vcan0 on Linux.
 *   3. DBC-aware signal encoding/decoding helpers.
 *
 * SIGNAL ENCODING (J1939 / custom)
 * ─────────────────────────────────
 *   Raw value = (Physical - Offset) / Scale
 *   Packed into frame using start_bit and length via bit-field manipulation.
 *
 * ADAS CAN IDs (simplified)
 * ──────────────────────────
 *   0x100  – EGO_SPEED          (speed [m/s], factor=0.01, offset=0)
 *   0x101  – EGO_ACCEL          (accel [m/s²], factor=0.01, offset=-20)
 *   0x200  – CONTROL_CMD        (throttle, brake, steer)
 *   0x300  – OBJECT_LIST_0..15  (tracked objects from fusion)
 *   0x400  – DTC_REPORT         (fault codes)
 */

#include "hal.hpp"

#include <atomic>
#include <functional>
#include <mutex>
#include <thread>
#include <vector>
#include <queue>

namespace adas {
namespace hil {

// ─── CAN signal descriptor ────────────────────────────────────────────────────

struct CanSignal {
    const char* name;
    uint32_t    can_id;
    uint8_t     start_bit;   ///< LSB position in the 64-bit frame data
    uint8_t     length;      ///< Signal length [bits]
    float       scale;
    float       offset;
    bool        is_signed;
};

// Pre-defined ADAS signals
namespace signals {
    constexpr CanSignal EGO_SPEED   = {"EGO_SPEED",  0x100, 0,  16, 0.01f,   0.f,  false};
    constexpr CanSignal EGO_ACCEL   = {"EGO_ACCEL",  0x101, 0,  16, 0.01f, -20.f,  true};
    constexpr CanSignal THROTTLE    = {"THROTTLE",   0x200, 0,   8, 0.01f,   0.f,  false};
    constexpr CanSignal BRAKE       = {"BRAKE",      0x200, 8,   8, 0.01f,   0.f,  false};
    constexpr CanSignal STEER_ANGLE = {"STEER_ANGLE",0x200, 16, 16, 0.01f, -10.f,  true};
    constexpr CanSignal DTC_ID      = {"DTC_ID",     0x400, 0,  16, 1.0f,    0.f,  false};
    constexpr CanSignal DTC_STATUS  = {"DTC_STATUS", 0x400, 16,  8, 1.0f,    0.f,  false};
}

// ─── Signal encode/decode helpers ────────────────────────────────────────────

/// Encode physical value into a CAN frame at the signal's bit position
void encodeSignal(CanFrame& frame, const CanSignal& sig, float physical_value);

/// Decode physical value from a CAN frame
float decodeSignal(const CanFrame& frame, const CanSignal& sig);

// ─── SimHal: in-process CAN bus for SIL ──────────────────────────────────────

/**
 * @class SimHal
 * @brief IHal implementation using an in-process virtual CAN bus.
 *
 * All tx frames are immediately echoed back to all registered RX callbacks
 * (simulating a shared bus). Useful for:
 *   - Unit testing the CAN encoding/decoding without hardware.
 *   - SIL closed-loop: algorithm Tx → sim model Rx → response Tx → algo Rx.
 */
class SimHal : public IHal {
public:
    SimHal();
    ~SimHal() override;

    bool open()  override;
    void close() override;

    bool txCan(const CanFrame& frame) override;
    void registerCanRxCallback(CanRxCallback cb) override;
    void registerGpsCallback(GpsCallback cb) override;
    void registerImuCallback(ImuCallback cb) override;

    bool isSimulation() const override { return true; }

    /// Inject a frame from the simulation side (as if received from bus)
    void injectFrame(const CanFrame& frame);

    /// Inject GPS data
    void injectGps(const GpsPosition& gps);

    /// Inject IMU data
    void injectImu(const ImuData& imu);

    /// Retrieve all frames that were transmitted by the ADAS algorithm
    std::vector<CanFrame> drainTxLog();

private:
    std::mutex               mutex_;
    std::vector<CanRxCallback> rx_callbacks_;
    GpsCallback              gps_callback_;
    ImuCallback              imu_callback_;
    std::vector<CanFrame>    tx_log_;
    bool                     open_{false};
};

// ─── SocketCanHal: real vcan/can interface ────────────────────────────────────

#ifdef ADAS_USE_SOCKETCAN
/**
 * @class SocketCanHal
 * @brief IHal implementation using Linux SocketCAN.
 *
 * Usage (bring up vcan0 first):
 *   sudo modprobe vcan
 *   sudo ip link add dev vcan0 type vcan
 *   sudo ip link set up vcan0
 *
 * Then construct SocketCanHal("vcan0").
 */
class SocketCanHal : public IHal {
public:
    explicit SocketCanHal(const char* interface_name);
    ~SocketCanHal() override;

    bool open()  override;
    void close() override;
    bool txCan(const CanFrame& frame) override;
    void registerCanRxCallback(CanRxCallback cb) override;
    void registerGpsCallback(GpsCallback cb)     override;
    void registerImuCallback(ImuCallback cb)      override;
    bool isSimulation() const override { return false; }

private:
    void rxThreadLoop();

    const char*            iface_name_;
    int                    sock_fd_{-1};
    std::thread            rx_thread_;
    std::atomic<bool>      rx_stop_{false};
    std::mutex             cb_mutex_;
    std::vector<CanRxCallback> rx_callbacks_;
    GpsCallback            gps_cb_;
    ImuCallback            imu_cb_;
};
#endif  // ADAS_USE_SOCKETCAN

}  // namespace hil
}  // namespace adas
