/**
 * @file HidDevice.cpp
 * @brief HID Device profile — keyboard/mouse report simulation
 *
 * Simulates a BLE HID device (e.g. steering wheel remote control in automotive,
 * or wireless keyboard for infotainment). HID descriptor follows USB HID spec.
 */
#include "bt/profiles/HidDevice.hpp"
#include "common/Logger.hpp"

static constexpr const char *TAG = "HID";

// Standard BLE HID keyboard report descriptor (abbreviated)
static constexpr uint8_t HID_REPORT_DESCRIPTOR[] = {
    0x05U, 0x01U,  // Usage Page (Generic Desktop)
    0x09U, 0x06U,  // Usage (Keyboard)
    0xA1U, 0x01U,  // Collection (Application)
    0x05U, 0x07U,  //   Usage Page (Key Codes)
    0x19U, 0xE0U,  //   Usage Minimum (224)
    0x29U, 0xE7U,  //   Usage Maximum (231)
    0x15U, 0x00U,  //   Logical Minimum (0)
    0x25U, 0x01U,  //   Logical Maximum (1)
    0x75U, 0x01U,  //   Report Size (1)
    0x95U, 0x08U,  //   Report Count (8)
    0x81U, 0x02U,  //   Input (Data, Variable, Absolute) — modifier keys
    0x95U, 0x01U,  //   Report Count (1)
    0x75U, 0x08U,  //   Report Size (8)
    0x81U, 0x03U,  //   Input (Constant) — reserved byte
    0x95U, 0x06U,  //   Report Count (6)
    0x75U, 0x08U,  //   Report Size (8)
    0x15U, 0x00U,  //   Logical Minimum (0)
    0x25U, 0x65U,  //   Logical Maximum (101)
    0x05U, 0x07U,  //   Usage Page (Key Codes)
    0x19U, 0x00U,  //   Usage Minimum (0)
    0x29U, 0x65U,  //   Usage Maximum (101)
    0x81U, 0x00U,  //   Input (Data, Array) — key array
    0xC0U           // End Collection
};

namespace bt {

struct HidDevice::Impl {
    bool       connected{false};
    HidReportCb report_cb;
    mutable std::mutex mtx;
};

HidDevice::HidDevice() : impl_(std::make_unique<Impl>()) {}
HidDevice::~HidDevice() = default;

const uint8_t *HidDevice::get_report_descriptor(uint16_t &out_len) {
    out_len = static_cast<uint16_t>(sizeof(HID_REPORT_DESCRIPTOR));
    return HID_REPORT_DESCRIPTOR;
}

BtError HidDevice::send_key_report(uint8_t modifier, uint8_t keycode) {
    // HID keyboard report: [modifier, reserved, key0..key5]
    std::array<uint8_t, 8> report{modifier, 0x00U, keycode, 0, 0, 0, 0, 0};
    BT_LOG_DEBUG(TAG, "HID key report modifier=0x{:02X} key=0x{:02X}",
                 modifier, keycode);
    std::lock_guard<std::mutex> lock(impl_->mtx);
    if (impl_->report_cb) {
        impl_->report_cb(report.data(), static_cast<uint16_t>(report.size()));
    }
    return BtError::OK;
}

BtError HidDevice::send_key_release() {
    std::array<uint8_t, 8> report{};  // All zeros = no key pressed
    std::lock_guard<std::mutex> lock(impl_->mtx);
    if (impl_->report_cb) {
        impl_->report_cb(report.data(), static_cast<uint16_t>(report.size()));
    }
    return BtError::OK;
}

void HidDevice::set_report_callback(HidReportCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->report_cb = std::move(cb);
}

}  // namespace bt
