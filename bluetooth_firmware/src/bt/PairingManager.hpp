/**
 * @file PairingManager.hpp
 */
#pragma once
#include "bt/IPairingManager.hpp"
#include <memory>

namespace bt {
class PairingManager final : public IPairingManager {
public:
    PairingManager();
    ~PairingManager() override;
    BtError                    initiate_pairing(ConnHandle conn, PairingMethod method)  override;
    BtError                    accept_pairing(ConnHandle conn)                          override;
    BtError                    reject_pairing(ConnHandle conn, uint8_t reason)          override;
    BtError                    provide_passkey(ConnHandle conn, uint32_t passkey)       override;
    BtError                    confirm_numeric(ConnHandle conn, bool confirmed)         override;
    std::optional<PairingKeys> get_bond_info(const BdAddr &peer)                 const override;
    BtError                    remove_bond(const BdAddr &peer)                         override;
    BtError                    remove_all_bonds()                                       override;
    bool                       is_bonded(const BdAddr &peer)                     const override;
    void                       on_passkey_display(PasskeyDisplayCb cb)                 override;
    void                       on_passkey_confirm(PasskeyConfirmCb cb)                 override;
    void                       on_pairing_result(PairingResultCb cb)                   override;
private:
    void _complete_pairing(ConnHandle conn, bool success, uint8_t reason);
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
