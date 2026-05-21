/**
 * @file BleScanner.hpp
 */
#pragma once
#include "bt/IBleScanner.hpp"
#include <memory>
namespace bt {
class IBluetoothController;
class BleScanner final : public IBleScanner {
public:
    explicit BleScanner(IBluetoothController *controller);
    ~BleScanner() override;
    BtError start_scan(uint16_t win, uint16_t intv, bool active, bool dedup) override;
    BtError stop_scan()                                                       override;
    void    set_scan_callback(ScanResultCb cb)                                override;
    bool    is_scanning() const                                               override;
    BtError set_rssi_filter(int8_t min_rssi)                                  override;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
