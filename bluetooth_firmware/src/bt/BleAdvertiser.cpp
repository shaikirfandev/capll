/**
 * @file BleAdvertiser.cpp
 * @brief BLE Advertising implementation
 *
 * Handles ADV_IND, ADV_NONCONN_IND, ADV_SCAN_IND packets with proper
 * AD type encoding per Bluetooth Core Spec 5.3 §11.1.3.
 *
 * In production automotive systems (e.g. Continental ADAS gateway ECU),
 * the advertiser broadcasts vehicle VIN hash + diagnostic session status
 * as manufacturer-specific data for authorised workshop tablets.
 */

#include "bt/BleAdvertiser.hpp"
#include "bt/IBluetoothController.hpp"
#include "common/Logger.hpp"
#include <cstring>
#include <mutex>
#include <stdexcept>

static constexpr const char *TAG = "BleAdvertiser";

// AD type codes (Bluetooth SIG assigned numbers)
static constexpr uint8_t AD_FLAGS               = 0x01U;
static constexpr uint8_t AD_UUID16_INCOMPLETE   = 0x02U;
static constexpr uint8_t AD_UUID16_COMPLETE      = 0x03U;
static constexpr uint8_t AD_LOCAL_NAME_SHORT    = 0x08U;
static constexpr uint8_t AD_LOCAL_NAME_COMPLETE = 0x09U;
static constexpr uint8_t AD_TX_POWER            = 0x0AU;
static constexpr uint8_t AD_MANUFACTURER_DATA   = 0xFFU;

// Flag values
static constexpr uint8_t FLAG_LE_GENERAL_DISC   = 0x02U;
static constexpr uint8_t FLAG_BR_EDR_NOT_SUPP   = 0x04U;

namespace bt {

struct BleAdvertiser::Impl {
    IBluetoothController *controller{nullptr};
    std::atomic<bool>     advertising{false};
    AdvParams             params{};
    AdvData               adv_data{};
    AdvData               scan_rsp{};
    mutable std::mutex    mtx;
};

BleAdvertiser::BleAdvertiser(IBluetoothController *controller)
    : impl_(std::make_unique<Impl>()) {
    if (!controller) {
        throw std::invalid_argument("BleAdvertiser: null controller");
    }
    impl_->controller = controller;
}

BleAdvertiser::~BleAdvertiser() {
    if (impl_->advertising.load()) {
        (void)stop();
    }
}

BtError BleAdvertiser::start(const AdvParams &params,
                               const AdvData   &adv_data,
                               const AdvData   &scan_rsp) {
    std::lock_guard<std::mutex> lock(impl_->mtx);

    if (impl_->advertising.load()) {
        BT_LOG_WARN(TAG, "start() called while already advertising");
        return BtError::ERR_INVALID_STATE;
    }

    if (params.interval_min_ms > params.interval_max_ms) {
        BT_LOG_ERROR(TAG, "Invalid interval: min={} > max={}",
                     params.interval_min_ms, params.interval_max_ms);
        return BtError::ERR_INVALID_PARAM;
    }
    if (params.interval_min_ms < 20U || params.interval_max_ms > 10240U) {
        BT_LOG_ERROR(TAG, "Interval out of spec [20-10240]ms");
        return BtError::ERR_INVALID_PARAM;
    }

    impl_->params   = params;
    impl_->adv_data = adv_data;
    impl_->scan_rsp = scan_rsp;

    const BtError err = impl_->controller->start_advertising(params, adv_data, scan_rsp);
    if (err != BtError::OK) {
        BT_LOG_ERROR(TAG, "Controller start_advertising failed: {}",
                     bt_error_str(err));
        return err;
    }

    impl_->advertising.store(true);
    BT_LOG_INFO(TAG, "BLE advertising started type={} interval=[{}-{}]ms",
                static_cast<int>(params.type),
                params.interval_min_ms, params.interval_max_ms);
    return BtError::OK;
}

BtError BleAdvertiser::stop() {
    if (!impl_->advertising.load()) {
        return BtError::ERR_INVALID_STATE;
    }
    const BtError err = impl_->controller->stop_advertising();
    if (err == BtError::OK) {
        impl_->advertising.store(false);
        BT_LOG_INFO(TAG, "BLE advertising stopped");
    }
    return err;
}

BtError BleAdvertiser::update_adv_data(const AdvData &adv_data) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->adv_data = adv_data;
    if (impl_->advertising.load()) {
        // Re-apply with current params (hot update)
        return impl_->controller->start_advertising(impl_->params,
                                                     impl_->adv_data,
                                                     impl_->scan_rsp);
    }
    return BtError::OK;
}

bool BleAdvertiser::is_advertising() const {
    return impl_->advertising.load();
}

// ─────────────────────────────────────────────────────────────────────────────
// Static factory helpers for common automotive AD records
// ─────────────────────────────────────────────────────────────────────────────
AdvData BleAdvertiser::make_automotive_adv(std::string_view device_name,
                                            uint16_t service_uuid,
                                            uint16_t company_id,
                                            const uint8_t *mfr_data,
                                            uint8_t mfr_len) {
    AdvData adv{};

    // Flags: LE General Discoverable, BR/EDR Not Supported
    const uint8_t flags = FLAG_LE_GENERAL_DISC | FLAG_BR_EDR_NOT_SUPP;
    adv.append(AD_FLAGS, &flags, 1U);

    // Complete list of 16-bit service UUIDs
    const uint8_t uuid_bytes[2] = {
        static_cast<uint8_t>(service_uuid & 0xFFU),
        static_cast<uint8_t>((service_uuid >> 8U) & 0xFFU)
    };
    adv.append(AD_UUID16_COMPLETE, uuid_bytes, 2U);

    // Shortened local name (fits remaining bytes in 31-byte payload)
    const uint8_t max_name_len = std::min(static_cast<uint8_t>(device_name.size()),
                                          static_cast<uint8_t>(10U));
    adv.append(AD_LOCAL_NAME_SHORT,
               reinterpret_cast<const uint8_t *>(device_name.data()),
               max_name_len);

    // Manufacturer specific data (company_id + payload)
    if (mfr_data != nullptr && mfr_len > 0U) {
        std::vector<uint8_t> mfr_record;
        mfr_record.push_back(static_cast<uint8_t>(company_id & 0xFFU));
        mfr_record.push_back(static_cast<uint8_t>((company_id >> 8U) & 0xFFU));
        mfr_record.insert(mfr_record.end(), mfr_data, mfr_data + mfr_len);
        adv.append(AD_MANUFACTURER_DATA, mfr_record.data(),
                   static_cast<uint8_t>(mfr_record.size()));
    }

    BT_LOG_DEBUG(TAG, "Built automotive AdvData: {} bytes total", adv.length);
    return adv;
}

AdvData BleAdvertiser::make_scan_response(std::string_view full_name,
                                           int8_t tx_power_dbm) {
    AdvData scan_rsp{};

    // Complete local name in scan response (longer than adv data allows)
    scan_rsp.append(AD_LOCAL_NAME_COMPLETE,
                    reinterpret_cast<const uint8_t *>(full_name.data()),
                    static_cast<uint8_t>(
                        std::min(full_name.size(), static_cast<std::size_t>(29U))));

    // TX Power level
    const uint8_t txp = static_cast<uint8_t>(tx_power_dbm);
    scan_rsp.append(AD_TX_POWER, &txp, 1U);

    return scan_rsp;
}

}  // namespace bt
