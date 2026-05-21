/**
 * @file IConnectionStateMachine.hpp
 * @brief Connection FSM interface
 */

#pragma once

#include "BluetoothTypes.hpp"

namespace bt {

enum class ConnEvent : uint8_t {
    START_ADV       = 0,
    STOP_ADV        = 1,
    CONNECT_REQ     = 2,
    CONNECTED       = 3,
    PAIR_START      = 4,
    PAIR_COMPLETE   = 5,
    DISCONNECT_REQ  = 6,
    DISCONNECTED    = 7,
    ERROR           = 8,
    TIMEOUT         = 9,
};

class IConnectionStateMachine {
public:
    virtual ~IConnectionStateMachine() = default;

    virtual BtError process_event(ConnEvent event) = 0;
    virtual ConnState current_state() const = 0;
    virtual bool can_transition(ConnEvent event) const = 0;
};

}  // namespace bt
