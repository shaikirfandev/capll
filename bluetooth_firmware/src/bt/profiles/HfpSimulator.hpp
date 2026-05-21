/**
 * @file HfpSimulator.hpp
 */
#pragma once
#include "bt/BluetoothTypes.hpp"
#include <functional>
#include <memory>
#include <string>
namespace bt {
enum class HfpState : uint8_t { IDLE, CALL_SETUP_IN, CALL_SETUP_OUT, IN_CALL, CALL_HELD };
using HfpEventCb = std::function<void(const std::string &indication)>;
class HfpSimulator {
public:
    HfpSimulator();
    ~HfpSimulator();
    std::string process_at(const std::string &cmd);
    HfpState    state() const;
    void        set_event_callback(HfpEventCb cb);
    void        simulate_incoming_call(const std::string &number);
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
