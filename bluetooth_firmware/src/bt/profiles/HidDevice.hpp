/**
 * @file HidDevice.hpp
 */
#pragma once
#include "bt/BluetoothTypes.hpp"
#include <functional>
#include <memory>
namespace bt {
using HidReportCb = std::function<void(const uint8_t *report, uint16_t len)>;
class HidDevice {
public:
    HidDevice();
    ~HidDevice();
    static const uint8_t *get_report_descriptor(uint16_t &out_len);
    BtError send_key_report(uint8_t modifier, uint8_t keycode);
    BtError send_key_release();
    void    set_report_callback(HidReportCb cb);
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
