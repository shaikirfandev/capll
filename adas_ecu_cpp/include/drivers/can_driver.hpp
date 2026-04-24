/**
 * @file    can_driver.hpp
 * @brief   CAN bus driver abstraction layer.
 *
 * On Cortex-M4 target: wraps bxCAN / FDCAN peripheral registers directly.
 * On simulation build: wraps SocketCAN (Linux vcan0) or a loopback queue.
 *
 * Design rules (MISRA C++ 2008 / AUTOSAR C++14 compliance targets):
 *  - No dynamic memory allocation (no new/delete)
 *  - Fixed-size ring buffer for Rx
 *  - All public API returns Status — never throws
 *  - Max 8-byte CAN 2.0B frames (CAN-FD extension flags shown but not used here)
 */

#pragma once
#include "hal/hal_types.hpp"

namespace drivers {

// ── CAN Frame ─────────────────────────────────────────────────────────────────

static constexpr uint8_t CAN_MAX_DLC = 8u;

/**
 * @struct CanFrame
 * @brief  A single Classical CAN 2.0B data frame.
 *         Packed to ensure no padding between fields (used for DMA on embedded).
 */
struct PACKED CanFrame {
    uint32_t    id;                     ///< 11-bit standard or 29-bit extended ID
    uint8_t     dlc;                    ///< Data Length Code (0–8)
    uint8_t     data[CAN_MAX_DLC];      ///< Payload bytes
    TickType_t  timestamp;              ///< Reception timestamp (ms)
    bool        extended_id;            ///< true = 29-bit extended ID
    bool        remote_frame;           ///< true = RTR frame

    CanFrame() { std::memset(this, 0, sizeof(*this)); }

    /** Helper: extract big-endian uint16 from two bytes */
    uint16_t getU16BE(uint8_t byte_high, uint8_t byte_low) const {
        return static_cast<uint16_t>((data[byte_high] << 8u) | data[byte_low]);
    }

    /** Helper: extract signal bits from byte with mask+shift */
    uint8_t getBits(uint8_t byte_idx, uint8_t mask, uint8_t shift) const {
        return (data[byte_idx] & mask) >> shift;
    }
};

// ── CAN Bus Configuration ─────────────────────────────────────────────────────

enum class CanBitrate : uint32_t {
    KBPS_125  = 125'000,
    KBPS_250  = 250'000,
    KBPS_500  = 500'000,
    MBPS_1    = 1'000'000,
};

struct CanConfig {
    CanBitrate  bitrate     = CanBitrate::KBPS_500;
    uint8_t     channel     = 1;        ///< Physical CAN channel number
    bool        loopback    = false;    ///< Enable hardware loopback (test)
    bool        silent      = false;    ///< Bus-off silent mode
};

// ── CAN Driver ────────────────────────────────────────────────────────────────

/**
 * @class CanDriver
 * @brief Singleton CAN bus controller.
 *
 * Usage:
 *   auto& can = CanDriver::instance();
 *   can.init(cfg);
 *   can.transmit(frame);
 *   CanFrame rx;
 *   if (can.receive(rx) == Status::OK) { process(rx); }
 */
class CanDriver {
public:
    static constexpr uint16_t RX_BUFFER_SIZE = 64u;    ///< Ring buffer depth

    static CanDriver& instance() {
        static CanDriver inst;
        return inst;
    }

    /**
     * @brief  Initialise CAN peripheral with given config.
     * @return Status::OK on success.
     */
    Status init(const CanConfig& cfg);

    /**
     * @brief  Transmit a CAN frame. Blocks until TX FIFO has space.
     * @return Status::OK | Status::TIMEOUT | Status::FAULT
     */
    Status transmit(const CanFrame& frame);

    /**
     * @brief  Pop a received frame from the Rx ring buffer.
     * @param  out  Frame to populate.
     * @return Status::OK if frame available, Status::NOT_READY if empty.
     */
    Status receive(CanFrame& out);

    /**
     * @brief  Register a hardware ID filter for hardware pre-filtering.
     * @param  id     Frame ID to accept
     * @param  mask   Mask applied before comparison (0 = wildcard bit)
     */
    Status addFilter(uint32_t id, uint32_t mask);

    /** Returns true if the bus is in bus-off error state. */
    bool isBusOff() const { return bus_off_; }

    /** Error counters from CAN peripheral error status register */
    uint8_t txErrorCount() const { return tx_err_; }
    uint8_t rxErrorCount() const { return rx_err_; }

    /** Called from ISR — do not call from application code */
    void onRxIsr(const CanFrame& frame);

private:
    CanDriver() = default;
    CanDriver(const CanDriver&) = delete;
    CanDriver& operator=(const CanDriver&) = delete;

    // ── Ring buffer ──────────────────────────────────────────────────────────
    CanFrame    rx_buf_[RX_BUFFER_SIZE];
    uint16_t    rx_head_  = 0;
    uint16_t    rx_tail_  = 0;
    uint16_t    rx_count_ = 0;

    bool        initialised_  = false;
    bool        bus_off_      = false;
    uint8_t     tx_err_       = 0;
    uint8_t     rx_err_       = 0;
    CanConfig   cfg_;
};

} // namespace drivers
