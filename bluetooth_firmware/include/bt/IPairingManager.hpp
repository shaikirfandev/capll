/**
 * @file IPairingManager.hpp
 * @brief Pairing and bonding management interface
 */

#pragma once

#include "BluetoothTypes.hpp"
#include <functional>

namespace bt {

using PasskeyDisplayCb  = std::function<void(uint32_t passkey)>;
using PasskeyConfirmCb  = std::function<void(uint32_t displayed_passkey, bool &user_confirmed)>;
using PairingResultCb   = std::function<void(const BdAddr &peer, bool success, uint8_t reason)>;

class IPairingManager {
public:
    virtual ~IPairingManager() = default;

    /**
     * @brief Initiate pairing with a connected peer.
     * @param conn_handle Active connection handle
     * @param method      Pairing method preference
     */
    virtual BtError initiate_pairing(ConnHandle conn_handle,
                                      PairingMethod method) = 0;

    /**
     * @brief Accept incoming pairing request from peer.
     */
    virtual BtError accept_pairing(ConnHandle conn_handle) = 0;

    /**
     * @brief Reject incoming pairing request.
     */
    virtual BtError reject_pairing(ConnHandle conn_handle, uint8_t reason) = 0;

    /**
     * @brief Provide passkey entered by user (for PASSKEY_ENTRY method).
     */
    virtual BtError provide_passkey(ConnHandle conn_handle, uint32_t passkey) = 0;

    /**
     * @brief Confirm numeric comparison result.
     * @param confirmed true if user accepted the displayed numbers match.
     */
    virtual BtError confirm_numeric(ConnHandle conn_handle, bool confirmed) = 0;

    /**
     * @brief Retrieve stored bonding keys for a peer device.
     */
    virtual std::optional<PairingKeys> get_bond_info(const BdAddr &peer) const = 0;

    /**
     * @brief Remove all bonding data for a peer.
     */
    virtual BtError remove_bond(const BdAddr &peer) = 0;

    /**
     * @brief Remove all stored bonds.
     */
    virtual BtError remove_all_bonds() = 0;

    /**
     * @brief Check if a peer device is currently bonded.
     */
    virtual bool is_bonded(const BdAddr &peer) const = 0;

    // ── Callbacks ────────────────────────────────────────────────────────────
    virtual void on_passkey_display(PasskeyDisplayCb cb) = 0;
    virtual void on_passkey_confirm(PasskeyConfirmCb cb) = 0;
    virtual void on_pairing_result(PairingResultCb  cb) = 0;
};

}  // namespace bt
