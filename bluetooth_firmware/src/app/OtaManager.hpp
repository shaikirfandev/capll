/**
 * @file OtaManager.hpp
 */
#pragma once
#include "app/IOtaManager.hpp"
#include <memory>
namespace bt::app {
class OtaManager final : public IOtaManager {
public:
    OtaManager(); ~OtaManager() override;
    BtError  start_ota(ConnHandle conn, uint32_t size, uint32_t crc32) override;
    BtError  write_chunk(const uint8_t *data, uint16_t len)            override;
    BtError  abort_ota()                                               override;
    OtaState state() const                                             override;
    void     on_progress(OtaProgressCb cb)                             override;
    void     on_complete(OtaCompleteCb cb)                             override;
private:
    struct Impl; std::unique_ptr<Impl> impl_;
};
}
