/**
 * @file IBleAdvertiser.hpp
 * @brief BLE Advertiser interface
 */
#pragma once
#include "BluetoothTypes.hpp"
namespace bt {
class IBleAdvertiser {
public:
    virtual ~IBleAdvertiser() = default;
    virtual BtError start(const AdvParams &params, const AdvData &adv_data, const AdvData &scan_rsp) = 0;
    virtual BtError stop() = 0;
    virtual BtError update_adv_data(const AdvData &adv_data) = 0;
    virtual bool    is_advertising() const = 0;
};
}
