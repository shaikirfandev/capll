/**
 * @file A2dpSimulator.cpp
 * @brief A2DP (Advanced Audio Distribution Profile) simulation
 *
 * Simulates AVDTP signalling and SBC codec framing.
 * Industry application: Harman/Samsung infotainment head units, Bosch
 * multimedia ECU for BT audio streaming from smartphones.
 */
#include "bt/profiles/A2dpSimulator.hpp"
#include "common/Logger.hpp"
#include <thread>
#include <chrono>

static constexpr const char *TAG = "A2DP";

// AVDTP signal identifiers
static constexpr uint8_t AVDTP_DISCOVER          = 0x01U;
static constexpr uint8_t AVDTP_GET_CAPABILITIES  = 0x02U;
static constexpr uint8_t AVDTP_SET_CONFIGURATION = 0x03U;
static constexpr uint8_t AVDTP_OPEN              = 0x06U;
static constexpr uint8_t AVDTP_START             = 0x07U;
static constexpr uint8_t AVDTP_CLOSE             = 0x08U;
static constexpr uint8_t AVDTP_SUSPEND           = 0x09U;

namespace bt {

struct A2dpSimulator::Impl {
    ConnHandle        conn{INVALID_CONN_HANDLE};
    A2dpState         state{A2dpState::IDLE};
    A2dpAudioCb       audio_cb;
    uint32_t          frames_sent{0};
    std::thread       stream_thread;
    std::atomic<bool> streaming{false};
    mutable std::mutex mtx;
};

A2dpSimulator::A2dpSimulator() : impl_(std::make_unique<Impl>()) {}
A2dpSimulator::~A2dpSimulator() { stop_stream(); }

BtError A2dpSimulator::connect(ConnHandle conn) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    if (impl_->state != A2dpState::IDLE) {
        return BtError::ERR_ALREADY_CONNECTED;
    }
    impl_->conn  = conn;
    impl_->state = A2dpState::CONNECTED;
    BT_LOG_INFO(TAG, "A2DP connected conn=0x{:04X}", conn);
    return BtError::OK;
}

BtError A2dpSimulator::start_stream() {
    {
        std::lock_guard<std::mutex> lock(impl_->mtx);
        if (impl_->state != A2dpState::CONNECTED) {
            return BtError::ERR_INVALID_STATE;
        }
        impl_->state = A2dpState::STREAMING;
    }
    impl_->streaming.store(true);
    // Simulate audio streaming thread (44.1kHz stereo SBC frames)
    impl_->stream_thread = std::thread([this]() {
        while (impl_->streaming.load()) {
            // SBC frame: ~128 bytes per frame at 44.1kHz, ~10ms batching
            std::array<uint8_t, 128> sbc_frame{};
            // Fill with sine-wave approximation (simulation)
            for (uint8_t i = 0; i < 128U; ++i) {
                sbc_frame[i] = static_cast<uint8_t>(
                    128U + static_cast<uint8_t>(
                        127.0 * 0.5 * (1.0 + static_cast<double>(i % 32) / 32.0)));
            }
            {
                std::lock_guard<std::mutex> lock(impl_->mtx);
                if (impl_->audio_cb) {
                    impl_->audio_cb(sbc_frame.data(),
                                   static_cast<uint16_t>(sbc_frame.size()));
                }
                impl_->frames_sent++;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    });
    BT_LOG_INFO(TAG, "A2DP streaming started");
    return BtError::OK;
}

BtError A2dpSimulator::stop_stream() {
    impl_->streaming.store(false);
    if (impl_->stream_thread.joinable()) {
        impl_->stream_thread.join();
    }
    {
        std::lock_guard<std::mutex> lock(impl_->mtx);
        if (impl_->state == A2dpState::STREAMING) {
            impl_->state = A2dpState::CONNECTED;
        }
    }
    BT_LOG_INFO(TAG, "A2DP stream stopped, frames_sent={}", impl_->frames_sent);
    return BtError::OK;
}

void A2dpSimulator::set_audio_callback(A2dpAudioCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->audio_cb = std::move(cb);
}

A2dpState A2dpSimulator::state() const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return impl_->state;
}

uint32_t A2dpSimulator::frames_sent() const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return impl_->frames_sent;
}

}  // namespace bt
