/**
 * @file BleAdvertiser.hpp
 */
#pragma once
#include "bt/IBleAdvertiser.hpp"
#include <memory>
#include <string_view>

namespace bt {
class IBluetoothController;

class BleAdvertiser final : public IBleAdvertiser {
public:
    explicit BleAdvertiser(IBluetoothController *controller);
    ~BleAdvertiser() override;

    BtError start(const AdvParams &p, const AdvData &adv, const AdvData &rsp) override;
    BtError stop()                                                             override;
    BtError update_adv_data(const AdvData &adv_data)                           override;
    bool    is_advertising() const                                             override;

    // Static helpers for building standard AD records
    static AdvData make_automotive_adv(std::string_view device_name,
                                        uint16_t service_uuid,
                                        uint16_t company_id = 0x0000U,
                                        const uint8_t *mfr_data = nullptr,
                                        uint8_t mfr_len = 0U);
    static AdvData make_scan_response(std::string_view full_name,
                                       int8_t tx_power_dbm = 0);

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
