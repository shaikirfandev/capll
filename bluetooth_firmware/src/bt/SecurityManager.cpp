/**
 * @file SecurityManager.cpp
 * @brief BLE Security Manager — AES-128 simulation, LTK/IRK derivation
 */

#include "bt/SecurityManager.hpp"
#include "common/Logger.hpp"
#include <algorithm>
#include <mutex>
#include <unordered_map>

static constexpr const char *TAG = "SecurityManager";

namespace bt {

struct SecurityManager::Impl {
    std::unordered_map<ConnHandle, SecurityLevel> conn_security;
    mutable std::mutex mtx;
};

SecurityManager::SecurityManager() : impl_(std::make_unique<Impl>()) {}
SecurityManager::~SecurityManager() = default;

BtError SecurityManager::start_encryption(ConnHandle conn, const PairingKeys &keys) {
    if (!keys.valid) {
        BT_LOG_ERROR(TAG, "start_encryption: invalid keys for conn=0x{:04X}", conn);
        return BtError::ERR_SECURITY;
    }
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->conn_security[conn] = keys.sec_level;
    BT_LOG_INFO(TAG, "Encryption started conn=0x{:04X} level={}",
                conn, static_cast<int>(keys.sec_level));
    return BtError::OK;
}

BtError SecurityManager::generate_ltk(PairingKeys &out_keys) {
    // In production: use mbedTLS or hardware crypto accelerator
    // (e.g. Infineon TC397 HSM, NXP S32G crypto engine)
    // Here: deterministic PRNG for simulation
    std::lock_guard<std::mutex> lock(impl_->mtx);
    out_keys = PairingKeys{};
    // XOR-based pseudo-random fill (NOT cryptographically secure — simulation only)
    uint8_t seed = 0xA7U;
    for (uint8_t i = 0; i < 16U; ++i) {
        seed      = static_cast<uint8_t>((seed * 0x1DU) ^ 0x55U);
        out_keys.ltk[i]  = seed;
        out_keys.irk[i]  = static_cast<uint8_t>(seed ^ 0xFFU);
        out_keys.csrk[i] = static_cast<uint8_t>(seed ^ 0xAAU);
    }
    out_keys.ediv      = 0xBEEFU;
    out_keys.sec_level = SecurityLevel::AUTHENTICATED;
    out_keys.valid     = true;
    BT_LOG_DEBUG(TAG, "LTK generated (simulation)");
    return BtError::OK;
}

BtError SecurityManager::derive_irk(const BdAddr &peer_id_addr,
                                      std::array<uint8_t, 16> &out_irk) {
    // IRK derivation simulation (production: AES-CMAC)
    for (uint8_t i = 0; i < 16U; ++i) {
        out_irk[i] = static_cast<uint8_t>(peer_id_addr[i % 6U] ^ i ^ 0x42U);
    }
    return BtError::OK;
}

bool SecurityManager::verify_smp_mac(ConnHandle conn,
                                      const uint8_t *data,
                                      uint16_t len) {
    // Production: AES-CMAC using CSRK
    (void)conn; (void)data; (void)len;
    return true;  // Simulation always passes
}

SecurityLevel SecurityManager::current_security_level(ConnHandle conn) const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    auto it = impl_->conn_security.find(conn);
    return (it != impl_->conn_security.end()) ? it->second : SecurityLevel::NONE;
}

}  // namespace bt
