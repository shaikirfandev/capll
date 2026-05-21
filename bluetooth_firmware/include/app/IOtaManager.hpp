/**
 * @file IOtaManager.hpp
 * @brief OTA firmware update manager interface
 */
#pragma once
#include "../bt/BluetoothTypes.hpp"
#include <functional>
namespace bt::app {
enum class OtaState : uint8_t { IDLE, INITIATED, RECEIVING, VERIFYING, APPLYING, COMPLETE, ERROR };
using OtaProgressCb = std::function<void(uint32_t rx, uint32_t total)>;
using OtaCompleteCb = std::function<void(bool success, std::string_view reason)>;
class IOtaManager {
public:
    virtual ~IOtaManager() = default;
    virtual BtError start_ota(ConnHandle conn, uint32_t expected_size, uint32_t expected_crc32) = 0;
    virtual BtError write_chunk(const uint8_t *data, uint16_t len) = 0;
    virtual BtError abort_ota() = 0;
    virtual OtaState state() const = 0;
    virtual void on_progress(OtaProgressCb cb) = 0;
    virtual void on_complete(OtaCompleteCb cb) = 0;
};
}
