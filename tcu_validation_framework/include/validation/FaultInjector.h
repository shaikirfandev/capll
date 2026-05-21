/**
 * @file FaultInjector.h
 * @brief Fault injection simulation for negative/robustness testing.
 *
 * Injects controlled faults into:
 *   - CAN bus (message corruption, dropout, bus-off)
 *   - Network (latency, packet loss, disconnect)
 *   - Firmware (corrupted binary, wrong CRC)
 *   - Power (voltage drop simulation via PSU GPIO)
 *   - UDS (malformed responses, timeouts, wrong NRC)
 */

#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#include <chrono>

namespace tcu::can { class CANManager; }

namespace tcu::validation {

enum class FaultType : uint8_t {
    CAN_BUS_OFF            = 0,
    CAN_MESSAGE_DROPOUT,
    CAN_MESSAGE_CORRUPTION,
    CAN_BABBLING_NODE,
    NETWORK_PACKET_LOSS,
    NETWORK_LATENCY_INJECT,
    NETWORK_DISCONNECT,
    UDS_MALFORMED_RESPONSE,
    UDS_RESPONSE_TIMEOUT,
    UDS_WRONG_NRC,
    POWER_VOLTAGE_DROP,
    POWER_CUT,
    FIRMWARE_CORRUPT_CRC,
    FIRMWARE_WRONG_VERSION,
};

/**
 * @brief Fault injection descriptor.
 */
struct FaultSpec {
    FaultType    type;
    uint32_t     duration_ms{1000};          ///< How long the fault persists
    double       probability{1.0};           ///< 0.0–1.0 trigger probability per event
    uint32_t     target_can_id{0};           ///< For CAN faults: specific CAN ID (0 = all)
    uint8_t      corrupt_byte_index{0};      ///< For CAN corruption: which byte to flip
    uint32_t     latency_add_ms{0};          ///< For NETWORK_LATENCY_INJECT
    double       packet_loss_percent{0.0};   ///< For NETWORK_PACKET_LOSS
    std::string  description;
};

/**
 * @brief Active fault handle (RAII — fault cleared on destruction).
 */
class ActiveFault {
public:
    explicit ActiveFault(std::function<void()> clear_fn);
    ~ActiveFault();
    ActiveFault(const ActiveFault&)            = delete;
    ActiveFault& operator=(const ActiveFault&) = delete;
    /** @brief Manually clear the fault before destruction. */
    void clear();
private:
    std::function<void()> m_clear_fn;
    bool                  m_cleared{false};
};

/**
 * @brief Fault injection engine.
 *
 * Usage:
 * @code
 *   FaultInjector fi(can_mgr);
 *   {
 *       auto fault = fi.inject({FaultType::CAN_MESSAGE_DROPOUT, .duration_ms=500});
 *       // Test runs with CAN dropout active
 *   } // Fault automatically cleared
 * @endcode
 */
class FaultInjector {
public:
    explicit FaultInjector(std::shared_ptr<tcu::can::CANManager> can_mgr);
    ~FaultInjector() = default;

    /**
     * @brief Inject a fault and return a handle that clears it on destruction.
     */
    std::unique_ptr<ActiveFault> inject(const FaultSpec& spec);

    /**
     * @brief Clear all active faults immediately.
     */
    void clear_all();

    /**
     * @brief Returns the number of currently active faults.
     */
    size_t active_count() const noexcept;

private:
    void inject_can_bus_off(bool enable);
    void inject_can_dropout(uint32_t can_id, bool enable);
    void inject_network_netem(const FaultSpec& spec, bool enable);

    std::shared_ptr<tcu::can::CANManager> m_can;
    mutable std::mutex                    m_mutex;
    std::vector<FaultSpec>                m_active_faults;
};

} // namespace tcu::validation
