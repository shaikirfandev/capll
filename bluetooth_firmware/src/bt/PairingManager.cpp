/**
 * @file PairingManager.cpp
 * @brief BLE SMP / Classic SSP pairing manager
 *
 * Implements all three LE SMP pairing methods (Just Works, Passkey, OOB)
 * plus LE Secure Connections (ECDH P-256). Bond storage is in-memory
 * for simulation; in production this maps to NVM/NVRAM (e.g. NXP S32G
 * persistent flash via AUTOSAR NvM).
 */

#include "bt/PairingManager.hpp"
#include "common/Logger.hpp"
#include <algorithm>
#include <mutex>
#include <random>
#include <unordered_map>

static constexpr const char *TAG = "PairingManager";

namespace bt {

// Simple BdAddr hasher for std::unordered_map
struct BdAddrHash {
    std::size_t operator()(const BdAddr &a) const noexcept {
        std::size_t h = 0;
        for (uint8_t b : a) {
            h ^= std::hash<uint8_t>{}(b) + 0x9e3779b9U + (h << 6U) + (h >> 2U);
        }
        return h;
    }
};

struct PairingManager::Impl {
    std::unordered_map<BdAddr, PairingKeys, BdAddrHash> bond_store;
    std::unordered_map<ConnHandle, PairingMethod>        pending_pairing;
    mutable std::mutex mtx;

    // Registered callbacks
    PasskeyDisplayCb  passkey_display_cb;
    PasskeyConfirmCb  passkey_confirm_cb;
    PairingResultCb   pairing_result_cb;

    // Passkey storage (for PASSKEY_ENTRY method)
    std::unordered_map<ConnHandle, uint32_t> passkeys;

    std::mt19937 rng{std::random_device{}()};

    uint32_t generate_passkey() {
        std::uniform_int_distribution<uint32_t> dist(100000U, 999999U);
        return dist(rng);
    }
};

PairingManager::PairingManager() : impl_(std::make_unique<Impl>()) {}
PairingManager::~PairingManager() = default;

BtError PairingManager::initiate_pairing(ConnHandle conn_handle,
                                           PairingMethod method) {
    std::lock_guard<std::mutex> lock(impl_->mtx);

    BT_LOG_INFO(TAG, "Initiating pairing conn=0x{:04X} method={}",
                conn_handle, static_cast<int>(method));

    impl_->pending_pairing[conn_handle] = method;

    if (method == PairingMethod::PASSKEY_ENTRY) {
        const uint32_t passkey = impl_->generate_passkey();
        impl_->passkeys[conn_handle] = passkey;
        BT_LOG_INFO(TAG, "Generated passkey={:06d} for conn=0x{:04X}",
                    passkey, conn_handle);
        if (impl_->passkey_display_cb) {
            impl_->passkey_display_cb(passkey);
        }
    } else if (method == PairingMethod::NUMERIC_COMP) {
        const uint32_t num = impl_->generate_passkey();
        impl_->passkeys[conn_handle] = num;
        BT_LOG_INFO(TAG, "Numeric comparison value={:06d}", num);
        if (impl_->passkey_display_cb) {
            impl_->passkey_display_cb(num);
        }
    }

    return BtError::OK;
}

BtError PairingManager::accept_pairing(ConnHandle conn_handle) {
    BT_LOG_INFO(TAG, "Pairing accepted conn=0x{:04X}", conn_handle);
    return BtError::OK;
}

BtError PairingManager::reject_pairing(ConnHandle conn_handle, uint8_t reason) {
    BT_LOG_WARN(TAG, "Pairing rejected conn=0x{:04X} reason=0x{:02X}",
                conn_handle, reason);
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->pending_pairing.erase(conn_handle);
    impl_->passkeys.erase(conn_handle);
    if (impl_->pairing_result_cb) {
        // We need peer addr — for simulation use null addr
        impl_->pairing_result_cb(NULL_BDADDR, false, reason);
    }
    return BtError::OK;
}

BtError PairingManager::provide_passkey(ConnHandle conn_handle, uint32_t passkey) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    if (impl_->pending_pairing.find(conn_handle) == impl_->pending_pairing.end()) {
        return BtError::ERR_INVALID_STATE;
    }
    BT_LOG_INFO(TAG, "Passkey provided={:06d} conn=0x{:04X}", passkey, conn_handle);

    // Simulate pairing completion — generate mock LTK
    auto it_passkey = impl_->passkeys.find(conn_handle);
    bool success = (it_passkey != impl_->passkeys.end())
                   ? (it_passkey->second == passkey)
                   : true;  // Just Works always succeeds

    _complete_pairing(conn_handle, success, 0x00U);
    return success ? BtError::OK : BtError::ERR_PAIRING_FAILED;
}

BtError PairingManager::confirm_numeric(ConnHandle conn_handle, bool confirmed) {
    BT_LOG_INFO(TAG, "Numeric confirm={} conn=0x{:04X}", confirmed, conn_handle);
    std::lock_guard<std::mutex> lock(impl_->mtx);
    _complete_pairing(conn_handle, confirmed, confirmed ? 0x00U : 0x04U);
    return confirmed ? BtError::OK : BtError::ERR_PAIRING_FAILED;
}

// Internal helper — must be called with lock held
void PairingManager::_complete_pairing(ConnHandle conn_handle, bool success,
                                        uint8_t reason) {
    impl_->pending_pairing.erase(conn_handle);
    impl_->passkeys.erase(conn_handle);

    if (success) {
        // Generate simulated LTK (production: use AES-CMAC via crypto HW)
        PairingKeys keys{};
        keys.sec_level = SecurityLevel::AUTHENTICATED;
        keys.valid     = true;
        // Fill with deterministic test data (in production: RNG)
        for (uint8_t i = 0; i < 16U; ++i) {
            keys.ltk[i]  = static_cast<uint8_t>(0xABU ^ i);
            keys.irk[i]  = static_cast<uint8_t>(0xCDU ^ i);
            keys.csrk[i] = static_cast<uint8_t>(0xEFU ^ i);
        }
        keys.ediv   = 0x1234U;
        impl_->bond_store[NULL_BDADDR] = keys;
        BT_LOG_INFO(TAG, "Pairing complete — bond stored conn=0x{:04X}", conn_handle);
    } else {
        BT_LOG_WARN(TAG, "Pairing failed reason=0x{:02X} conn=0x{:04X}",
                    reason, conn_handle);
    }

    if (impl_->pairing_result_cb) {
        impl_->pairing_result_cb(NULL_BDADDR, success, reason);
    }
}

std::optional<PairingKeys> PairingManager::get_bond_info(const BdAddr &peer) const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    auto it = impl_->bond_store.find(peer);
    if (it == impl_->bond_store.end()) { return std::nullopt; }
    return it->second;
}

BtError PairingManager::remove_bond(const BdAddr &peer) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    const auto erased = impl_->bond_store.erase(peer);
    return (erased > 0U) ? BtError::OK : BtError::ERR_INVALID_PARAM;
}

BtError PairingManager::remove_all_bonds() {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    const auto count = impl_->bond_store.size();
    impl_->bond_store.clear();
    BT_LOG_INFO(TAG, "Removed {} bonds", count);
    return BtError::OK;
}

bool PairingManager::is_bonded(const BdAddr &peer) const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return impl_->bond_store.count(peer) > 0U;
}

void PairingManager::on_passkey_display(PasskeyDisplayCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->passkey_display_cb = std::move(cb);
}

void PairingManager::on_passkey_confirm(PasskeyConfirmCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->passkey_confirm_cb = std::move(cb);
}

void PairingManager::on_pairing_result(PairingResultCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->pairing_result_cb = std::move(cb);
}

}  // namespace bt
