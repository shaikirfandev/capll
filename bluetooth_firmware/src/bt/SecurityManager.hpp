/**
 * @file SecurityManager.hpp
 */
#pragma once
#include "bt/ISecurityManager.hpp"
#include <memory>
namespace bt {
class SecurityManager final : public ISecurityManager {
public:
    SecurityManager();
    ~SecurityManager() override;
    BtError       start_encryption(ConnHandle conn, const PairingKeys &keys)               override;
    BtError       generate_ltk(PairingKeys &out_keys)                                      override;
    BtError       derive_irk(const BdAddr &peer, std::array<uint8_t,16> &out_irk)          override;
    bool          verify_smp_mac(ConnHandle conn, const uint8_t *data, uint16_t len)       override;
    SecurityLevel current_security_level(ConnHandle conn)                            const override;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
