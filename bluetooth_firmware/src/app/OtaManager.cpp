/**
 * @file OtaManager.cpp
 * @brief OTA firmware update over BLE — Nordic DFU-inspired implementation
 *
 * Supports chunked firmware transfer over GATT Write Without Response,
 * CRC-32 verification, and atomic swap mechanism for fail-safe updates.
 *
 * Automotive use: KPIT/Continental OTA campaigns for TCU firmware updates
 * pushed via BLE from mobile service apps (ISO 27145 / OEM-specific).
 */

#include "app/OtaManager.hpp"
#include "common/Logger.hpp"
#include <numeric>
#include <mutex>
#include <vector>

static constexpr const char *TAG = "OtaManager";

namespace bt::app {

// Software CRC-32 (IEEE 802.3 polynomial)
static uint32_t crc32_update(uint32_t crc, const uint8_t *data, uint16_t len) {
    static constexpr uint32_t POLY = 0xEDB88320UL;
    crc = ~crc;
    for (uint16_t i = 0; i < len; ++i) {
        crc ^= data[i];
        for (int j = 0; j < 8; ++j) {
            crc = (crc & 1U) ? ((crc >> 1U) ^ POLY) : (crc >> 1U);
        }
    }
    return ~crc;
}

struct OtaManager::Impl {
    OtaState state{OtaState::IDLE};
    ConnHandle active_conn{INVALID_CONN_HANDLE};

    uint32_t expected_size{0};
    uint32_t expected_crc32{0};
    uint32_t received_bytes{0};
    uint32_t running_crc{0};

    std::vector<uint8_t> firmware_buffer;  // In-memory for simulation

    OtaProgressCb progress_cb;
    OtaCompleteCb complete_cb;
    mutable std::mutex mtx;
};

OtaManager::OtaManager() : impl_(std::make_unique<Impl>()) {}
OtaManager::~OtaManager() = default;

BtError OtaManager::start_ota(ConnHandle conn, uint32_t expected_size,
                                uint32_t expected_crc32) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    if (impl_->state != OtaState::IDLE) {
        BT_LOG_WARN(TAG, "OTA already in progress");
        return BtError::ERR_INVALID_STATE;
    }
    if (expected_size == 0 || expected_size > 1024U * 1024U) {  // Max 1 MB
        return BtError::ERR_INVALID_PARAM;
    }

    impl_->state          = OtaState::INITIATED;
    impl_->active_conn    = conn;
    impl_->expected_size  = expected_size;
    impl_->expected_crc32 = expected_crc32;
    impl_->received_bytes = 0;
    impl_->running_crc    = 0;
    impl_->firmware_buffer.clear();
    impl_->firmware_buffer.reserve(expected_size);

    BT_LOG_INFO(TAG, "OTA started conn=0x{:04X} size={} crc=0x{:08X}",
                conn, expected_size, expected_crc32);
    impl_->state = OtaState::RECEIVING;
    return BtError::OK;
}

BtError OtaManager::write_chunk(const uint8_t *data, uint16_t len) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    if (impl_->state != OtaState::RECEIVING) {
        return BtError::ERR_INVALID_STATE;
    }
    if (!data || len == 0) { return BtError::ERR_INVALID_PARAM; }

    // Overflow guard
    if (impl_->received_bytes + len > impl_->expected_size) {
        BT_LOG_ERROR(TAG, "OTA overflow: received+chunk={} > expected={}",
                     impl_->received_bytes + len, impl_->expected_size);
        impl_->state = OtaState::ERROR;
        return BtError::ERR_BUFF_OVERFLOW;
    }

    impl_->firmware_buffer.insert(impl_->firmware_buffer.end(), data, data + len);
    impl_->running_crc     = crc32_update(impl_->running_crc, data, len);
    impl_->received_bytes += len;

    BT_LOG_DEBUG(TAG, "OTA chunk len={} total_rx={}/{}", len,
                 impl_->received_bytes, impl_->expected_size);

    if (impl_->progress_cb) {
        impl_->progress_cb(impl_->received_bytes, impl_->expected_size);
    }

    // Check if transfer complete
    if (impl_->received_bytes == impl_->expected_size) {
        impl_->state = OtaState::VERIFYING;
        BT_LOG_INFO(TAG, "OTA transfer complete — verifying CRC...");

        const bool crc_ok = (impl_->running_crc == impl_->expected_crc32);
        if (crc_ok) {
            BT_LOG_INFO(TAG, "OTA CRC OK (0x{:08X}) — applying update",
                        impl_->running_crc);
            impl_->state = OtaState::APPLYING;
            // Simulate apply delay (production: flash write + bank swap)
            impl_->state = OtaState::COMPLETE;
            if (impl_->complete_cb) {
                impl_->complete_cb(true, "OTA update successful");
            }
        } else {
            BT_LOG_ERROR(TAG, "OTA CRC MISMATCH: got=0x{:08X} expected=0x{:08X}",
                         impl_->running_crc, impl_->expected_crc32);
            impl_->state = OtaState::ERROR;
            if (impl_->complete_cb) {
                impl_->complete_cb(false, "CRC mismatch");
            }
            return BtError::ERR_OTA_ABORT;
        }
    }
    return BtError::OK;
}

BtError OtaManager::abort_ota() {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    if (impl_->state == OtaState::IDLE) { return BtError::OK; }
    BT_LOG_WARN(TAG, "OTA aborted at {}%",
                (impl_->received_bytes * 100U) / std::max(impl_->expected_size, 1U));
    impl_->state = OtaState::IDLE;
    impl_->firmware_buffer.clear();
    if (impl_->complete_cb) { impl_->complete_cb(false, "Aborted by user"); }
    return BtError::OK;
}

OtaState OtaManager::state() const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return impl_->state;
}

void OtaManager::on_progress(OtaProgressCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->progress_cb = std::move(cb);
}

void OtaManager::on_complete(OtaCompleteCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->complete_cb = std::move(cb);
}

}  // namespace bt::app
