/**
 * @file ISecurityManager.hpp
 * @brief Security Manager Protocol (SMP) interface
 */
#pragma once
#include "BluetoothTypes.hpp"
namespace bt {
class ISecurityManager {
public:
    virtual ~ISecurityManager() = default;
    virtual BtError start_encryption(ConnHandle conn, const PairingKeys &keys) = 0;
    virtual BtError generate_ltk(PairingKeys &out_keys) = 0;
    virtual BtError derive_irk(const BdAddr &peer_id_addr, std::array<uint8_t,16> &out_irk) = 0;
    virtual bool    verify_smp_mac(ConnHandle conn, const uint8_t *data, uint16_t len) = 0;
    virtual SecurityLevel current_security_level(ConnHandle conn) const = 0;
};
}
