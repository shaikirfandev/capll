/**
 * @file IGattServer.hpp
 * @brief GATT Server interface — attribute database and notification engine
 */

#pragma once

#include "BluetoothTypes.hpp"
#include <functional>

namespace bt {

/// Callback for ATT Read request — caller fills in @p value, returns ATT error
using GattReadCb  = std::function<uint8_t(ConnHandle hdl, AttHandle att,
                                           std::vector<uint8_t> &value)>;
/// Callback for ATT Write request — returns ATT error code (0 = success)
using GattWriteCb = std::function<uint8_t(ConnHandle hdl, AttHandle att,
                                           const std::vector<uint8_t> &value)>;

class IGattServer {
public:
    virtual ~IGattServer() = default;

    // ── Service management ───────────────────────────────────────────────────
    virtual BtError add_service(GattServiceDef &service) = 0;
    virtual BtError remove_service(Uuid16 service_uuid) = 0;

    // ── Characteristic callbacks ─────────────────────────────────────────────
    virtual void set_read_callback(AttHandle handle, GattReadCb cb) = 0;
    virtual void set_write_callback(AttHandle handle, GattWriteCb cb) = 0;

    // ── Server-initiated operations ──────────────────────────────────────────
    /**
     * @brief Send a GATT notification (no acknowledgement from client).
     * @note Requires client to have written CCCD = 0x0001 (notify enabled).
     */
    virtual BtError notify(ConnHandle conn, AttHandle att_handle,
                            const uint8_t *data, uint16_t len) = 0;

    /**
     * @brief Send a GATT indication (client must acknowledge).
     * @note Requires CCCD = 0x0002 (indicate enabled).
     */
    virtual BtError indicate(ConnHandle conn, AttHandle att_handle,
                              const uint8_t *data, uint16_t len) = 0;

    // ── Attribute value management ───────────────────────────────────────────
    virtual BtError set_value(AttHandle handle,
                               const uint8_t *data,
                               uint16_t len) = 0;
    virtual BtError get_value(AttHandle handle,
                               std::vector<uint8_t> &out) const = 0;
};

}  // namespace bt
