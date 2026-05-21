/**
 * @file HfpSimulator.cpp
 * @brief HFP (Hands-Free Profile) AT command simulator
 *
 * Implements HFP 1.8 AT command set for in-vehicle hands-free calls.
 * Industry use: Continental VDO cluster, Visteon cockpit domain controller.
 */
#include "bt/profiles/HfpSimulator.hpp"
#include "common/Logger.hpp"
#include <sstream>

static constexpr const char *TAG = "HFP";

namespace bt {

struct HfpSimulator::Impl {
    HfpState    state{HfpState::IDLE};
    HfpEventCb  event_cb;
    std::string active_number;
    mutable std::mutex mtx;
};

HfpSimulator::HfpSimulator() : impl_(std::make_unique<Impl>()) {}
HfpSimulator::~HfpSimulator() = default;

std::string HfpSimulator::process_at(const std::string &cmd) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    BT_LOG_DEBUG(TAG, "AT cmd: {}", cmd);

    if (cmd == "ATA") {
        // Answer call
        impl_->state = HfpState::IN_CALL;
        BT_LOG_INFO(TAG, "Call answered");
        return "OK\r\n";
    } else if (cmd.rfind("ATD", 0) == 0) {
        // Dial: ATD<number>;
        impl_->active_number = cmd.substr(3);
        if (!impl_->active_number.empty() &&
            impl_->active_number.back() == ';') {
            impl_->active_number.pop_back();
        }
        impl_->state = HfpState::CALL_SETUP_OUT;
        BT_LOG_INFO(TAG, "Dialling {}", impl_->active_number);
        return "OK\r\n+CIEV: 3,2\r\n";  // Call setup = outgoing
    } else if (cmd == "AT+CHUP" || cmd == "ATH") {
        // Hang up
        impl_->state = HfpState::IDLE;
        impl_->active_number.clear();
        BT_LOG_INFO(TAG, "Call hung up");
        return "OK\r\n+CIEV: 3,0\r\n+CIEV: 2,0\r\n";
    } else if (cmd == "AT+CIND?") {
        // Indicator status
        return "+CIND: 1,1,4,0,0,0,0\r\nOK\r\n";
    } else if (cmd == "AT+CIND=?") {
        // Indicator capabilities
        return "+CIND: (\"service\",(0,1)),"
               "(\"call\",(0,1)),"
               "(\"callsetup\",(0-3)),"
               "(\"battchg\",(0-5)),"
               "(\"signal\",(0-5)),"
               "(\"roam\",(0,1)),"
               "(\"callheld\",(0-2))\r\nOK\r\n";
    } else if (cmd == "AT+CHLD=?") {
        return "+CHLD: (0,1,2,3,4)\r\nOK\r\n";
    } else if (cmd.rfind("AT+CHLD=", 0) == 0) {
        const std::string code = cmd.substr(8);
        BT_LOG_INFO(TAG, "Call hold action: {}", code);
        return "OK\r\n";
    } else if (cmd == "AT+VTS=?" || cmd.rfind("AT+VTS=", 0) == 0) {
        return "OK\r\n";  // DTMF tone
    } else if (cmd == "AT+BRSF=20") {
        // AG supported features
        return "+BRSF: 1023\r\nOK\r\n";
    } else if (cmd.rfind("AT+BAC=", 0) == 0) {
        return "OK\r\n";  // Codec negotiation
    } else {
        BT_LOG_WARN(TAG, "Unknown AT cmd: {}", cmd);
        return "ERROR\r\n";
    }
}

HfpState HfpSimulator::state() const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return impl_->state;
}

void HfpSimulator::set_event_callback(HfpEventCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->event_cb = std::move(cb);
}

void HfpSimulator::simulate_incoming_call(const std::string &number) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->active_number = number;
    impl_->state         = HfpState::CALL_SETUP_IN;
    BT_LOG_INFO(TAG, "Simulating incoming call from {}", number);
    if (impl_->event_cb) {
        impl_->event_cb("+CLIP: \"" + number + "\",129\r\n"
                        "+CIEV: 3,1\r\n");  // Call setup = incoming
    }
}

}  // namespace bt
