/**
 * @file IBluetoothController.hpp
 * @brief Pure abstract interface for the Bluetooth controller (HCI layer abstraction)
 *
 * This interface decouples the upper stack (L2CAP, HCI command dispatch)
 * from the underlying transport (UART H4, SDIO, USB). Implementations exist
 * for: simulated (test), Qualcomm QCA6391, TI CC2652, NXP KW45, Nordic nRF5340.
 */

#pragma once

#include "BluetoothTypes.hpp"
#include <functional>
#include <memory>

namespace bt {

/// Callback type for incoming HCI events and ACL data
using HciEventCb  = std::function<void(const uint8_t *data, uint16_t len)>;
using HciAclDataCb = std::function<void(ConnHandle handle, const uint8_t *data, uint16_t len)>;

/**
 * @interface IBluetoothController
 * @brief Hardware Abstraction Layer for Bluetooth Controller
 *
 * Represents the boundary between the firmware stack and the physical
 * Bluetooth radio chip. All HCI commands are sent through this interface,
 * and HCI events are delivered via registered callbacks.
 *
 * Thread safety: All methods must be thread-safe. Implementations shall
 * use internal locking if the underlying transport is not thread-safe.
 */
class IBluetoothController {
public:
    virtual ~IBluetoothController() = default;

    // ── Lifecycle ────────────────────────────────────────────────────────────
    /**
     * @brief Initialise the Bluetooth controller hardware and transport.
     * @return BtError::OK on success.
     */
    virtual BtError initialise(BtMode mode) = 0;

    /**
     * @brief Reset the controller (HCI Reset command).
     * @return BtError::OK when controller has acknowledged the reset.
     */
    virtual BtError reset() = 0;

    /**
     * @brief Deinitialise and power down the radio.
     */
    virtual void shutdown() = 0;

    // ── Identity ─────────────────────────────────────────────────────────────
    /**
     * @brief Read the controller's public device address.
     */
    virtual BdAddr get_public_address() const = 0;

    /**
     * @brief Set a random address (for privacy).
     */
    virtual BtError set_random_address(const BdAddr &addr) = 0;

    /**
     * @brief Set the local device name (GAP device name characteristic).
     */
    virtual BtError set_device_name(std::string_view name) = 0;

    // ── HCI transport ────────────────────────────────────────────────────────
    /**
     * @brief Send a raw HCI command to the controller.
     * @param opcode HCI opcode (OCF | OGF << 10)
     * @param params Command parameters
     * @param len    Parameter length in bytes
     * @return BtError::OK if the command was queued successfully.
     */
    virtual BtError send_hci_command(uint16_t opcode,
                                      const uint8_t *params,
                                      uint8_t len) = 0;

    /**
     * @brief Send ACL data to a connected peer.
     * @param handle  Connection handle
     * @param data    ACL payload
     * @param len     Payload length
     * @return BtError::OK if queued. ERR_NO_RESOURCES if HCI buffer full.
     */
    virtual BtError send_acl_data(ConnHandle handle,
                                   const uint8_t *data,
                                   uint16_t len) = 0;

    // ── Callbacks ────────────────────────────────────────────────────────────
    /**
     * @brief Register callback for incoming HCI events from the controller.
     * @note Called from controller ISR or reader thread — must be fast.
     */
    virtual void register_event_callback(HciEventCb cb) = 0;

    /**
     * @brief Register callback for incoming ACL data from a peer device.
     */
    virtual void register_acl_callback(HciAclDataCb cb) = 0;

    // ── BLE operations ───────────────────────────────────────────────────────
    virtual BtError start_advertising(const AdvParams &params,
                                       const AdvData   &adv_data,
                                       const AdvData   &scan_rsp) = 0;
    virtual BtError stop_advertising() = 0;

    virtual BtError start_scan(uint16_t window_ms,
                                uint16_t interval_ms,
                                bool     active_scan,
                                bool     filter_duplicates) = 0;
    virtual BtError stop_scan() = 0;

    virtual BtError create_ble_connection(const BdAddr &peer_addr,
                                           bool          peer_is_random) = 0;

    // ── Classic BT operations ────────────────────────────────────────────────
    virtual BtError set_connectable(bool enable) = 0;
    virtual BtError set_discoverable(bool enable, uint16_t timeout_sec) = 0;
    virtual BtError start_inquiry(uint8_t duration_s, uint8_t max_responses) = 0;

    // ── Connection management ────────────────────────────────────────────────
    virtual BtError disconnect(ConnHandle handle, uint8_t reason) = 0;

    /**
     * @brief Update BLE connection parameters.
     * @note Requires CONNECTED state. Both central and peripheral can request.
     */
    virtual BtError update_conn_params(ConnHandle handle,
                                        uint16_t interval_min_ms,
                                        uint16_t interval_max_ms,
                                        uint16_t latency,
                                        uint16_t supervision_timeout_ms) = 0;

    // ── Power management ────────────────────────────────────────────────────
    virtual BtError set_power_state(PowerState state) = 0;
    virtual PowerState get_power_state() const = 0;

    /**
     * @brief Set TX power level in dBm (-40 to +20).
     */
    virtual BtError set_tx_power(int8_t dbm) = 0;

    // ── Diagnostics ─────────────────────────────────────────────────────────
    virtual int8_t get_rssi(ConnHandle handle) = 0;

    /**
     * @brief Read controller version information.
     */
    struct ControllerVersion {
        uint8_t  hci_version;
        uint16_t hci_revision;
        uint8_t  lmp_version;
        uint16_t manufacturer_id;
        uint16_t lmp_subversion;
    };
    virtual ControllerVersion get_version() const = 0;
};

}  // namespace bt
