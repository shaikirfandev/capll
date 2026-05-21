/**
 * @file A2dpSimulator.hpp
 */
#pragma once
#include "bt/BluetoothTypes.hpp"
#include <functional>
#include <memory>
namespace bt {
enum class A2dpState : uint8_t { IDLE, CONNECTED, STREAMING, SUSPENDED };
using A2dpAudioCb = std::function<void(const uint8_t *sbc_frame, uint16_t len)>;
class A2dpSimulator {
public:
    A2dpSimulator();
    ~A2dpSimulator();
    BtError   connect(ConnHandle conn);
    BtError   start_stream();
    BtError   stop_stream();
    void      set_audio_callback(A2dpAudioCb cb);
    A2dpState state() const;
    uint32_t  frames_sent() const;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
