/**
 * @file IBleScanner.hpp
 * @brief BLE Scanner interface
 */
#pragma once
#include "BluetoothTypes.hpp"
#include <functional>
namespace bt {
using ScanResultCb = std::function<void(const EvtBleAdv &result)>;
class IBleScanner {
public:
    virtual ~IBleScanner() = default;
    virtual BtError start_scan(uint16_t window_ms, uint16_t interval_ms, bool active, bool filter_dup) = 0;
    virtual BtError stop_scan() = 0;
    virtual void    set_scan_callback(ScanResultCb cb) = 0;
    virtual bool    is_scanning() const = 0;
    virtual BtError set_rssi_filter(int8_t min_rssi) = 0;
};
}
