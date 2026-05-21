/**
 * @file ConnectionStateMachine.cpp
 * @brief Bluetooth connection FSM implementation
 *
 * FSM transitions:
 *   IDLE → ADVERTISING  (START_ADV)
 *   ADVERTISING → IDLE  (STOP_ADV)
 *   IDLE → CONNECTING   (CONNECT_REQ)
 *   CONNECTING → CONNECTED (CONNECTED)
 *   CONNECTED → PAIRING  (PAIR_START)
 *   PAIRING → PAIRED     (PAIR_COMPLETE)
 *   CONNECTED/PAIRED → DISCONNECTING (DISCONNECT_REQ)
 *   DISCONNECTING → IDLE (DISCONNECTED)
 *   Any → ERROR          (ERROR)
 */

#include "bt/ConnectionStateMachine.hpp"
#include "common/Logger.hpp"

static constexpr const char *TAG = "ConnFSM";

namespace bt {

ConnectionStateMachine::ConnectionStateMachine(IEventBus *event_bus)
    : event_bus_(event_bus)
    , state_(ConnState::IDLE)
{
    build_table();
}

void ConnectionStateMachine::build_table() {
    auto log_transition = [](ConnState from, ConnEvent ev, ConnState to) {
        BT_LOG_INFO(TAG, "State: {} --[{}]--> {}",
                    conn_state_str(from),
                    static_cast<int>(ev),
                    conn_state_str(to));
    };

    // IDLE transitions
    add(ConnState::IDLE, ConnEvent::START_ADV,     ConnState::ADVERTISING,   log_transition);
    add(ConnState::IDLE, ConnEvent::CONNECT_REQ,   ConnState::CONNECTING,    log_transition);

    // ADVERTISING transitions
    add(ConnState::ADVERTISING, ConnEvent::STOP_ADV,     ConnState::IDLE,      log_transition);
    add(ConnState::ADVERTISING, ConnEvent::CONNECTED,    ConnState::CONNECTED, log_transition);
    add(ConnState::ADVERTISING, ConnEvent::ERROR,        ConnState::ERROR,     log_transition);

    // CONNECTING transitions
    add(ConnState::CONNECTING, ConnEvent::CONNECTED,    ConnState::CONNECTED, log_transition);
    add(ConnState::CONNECTING, ConnEvent::TIMEOUT,      ConnState::IDLE,      log_transition);
    add(ConnState::CONNECTING, ConnEvent::ERROR,        ConnState::ERROR,     log_transition);

    // CONNECTED transitions
    add(ConnState::CONNECTED, ConnEvent::PAIR_START,    ConnState::PAIRING,       log_transition);
    add(ConnState::CONNECTED, ConnEvent::DISCONNECT_REQ,ConnState::DISCONNECTING, log_transition);
    add(ConnState::CONNECTED, ConnEvent::DISCONNECTED,  ConnState::IDLE,          log_transition);
    add(ConnState::CONNECTED, ConnEvent::ERROR,         ConnState::ERROR,         log_transition);

    // PAIRING transitions
    add(ConnState::PAIRING, ConnEvent::PAIR_COMPLETE,  ConnState::PAIRED,        log_transition);
    add(ConnState::PAIRING, ConnEvent::DISCONNECT_REQ, ConnState::DISCONNECTING, log_transition);
    add(ConnState::PAIRING, ConnEvent::ERROR,          ConnState::ERROR,         log_transition);

    // PAIRED transitions
    add(ConnState::PAIRED, ConnEvent::DISCONNECT_REQ,  ConnState::DISCONNECTING, log_transition);
    add(ConnState::PAIRED, ConnEvent::DISCONNECTED,    ConnState::IDLE,          log_transition);
    add(ConnState::PAIRED, ConnEvent::ERROR,           ConnState::ERROR,         log_transition);

    // DISCONNECTING transitions
    add(ConnState::DISCONNECTING, ConnEvent::DISCONNECTED, ConnState::IDLE, log_transition);
    add(ConnState::DISCONNECTING, ConnEvent::ERROR,        ConnState::ERROR, log_transition);

    // ERROR → IDLE (recovery via explicit reset event)
    add(ConnState::ERROR, ConnEvent::DISCONNECT_REQ, ConnState::IDLE, log_transition);
}

void ConnectionStateMachine::add(ConnState from, ConnEvent ev, ConnState to,
                                  ActionFn action, GuardFn guard) {
    table_[{from, ev}] = Transition{to, std::move(action), std::move(guard)};
}

BtError ConnectionStateMachine::process_event(ConnEvent event) {
    std::lock_guard<std::mutex> lock(mtx_);
    const auto key = std::make_pair(state_, event);
    auto it = table_.find(key);
    if (it == table_.end()) {
        BT_LOG_WARN(TAG, "No transition from {} on event {}",
                    conn_state_str(state_), static_cast<int>(event));
        return BtError::ERR_INVALID_STATE;
    }
    const Transition &t = it->second;
    if (t.guard && !t.guard(state_, event)) {
        BT_LOG_WARN(TAG, "Guard rejected transition from {} on event {}",
                    conn_state_str(state_), static_cast<int>(event));
        return BtError::ERR_INVALID_STATE;
    }
    const ConnState prev = state_;
    state_ = t.next_state;
    if (t.action) {
        t.action(prev, event, state_);
    }
    return BtError::OK;
}

ConnState ConnectionStateMachine::current_state() const {
    std::lock_guard<std::mutex> lock(mtx_);
    return state_;
}

bool ConnectionStateMachine::can_transition(ConnEvent event) const {
    std::lock_guard<std::mutex> lock(mtx_);
    return table_.find({state_, event}) != table_.end();
}

}  // namespace bt
