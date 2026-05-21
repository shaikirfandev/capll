/**
 * @file ConnectionStateMachine.hpp
 */
#pragma once
#include "bt/IConnectionStateMachine.hpp"
#include "bt/IEventBus.hpp"
#include <functional>
#include <map>
#include <mutex>
#include <memory>

namespace bt {

class ConnectionStateMachine final : public IConnectionStateMachine {
public:
    using ActionFn = std::function<void(ConnState from, ConnEvent ev, ConnState to)>;
    using GuardFn  = std::function<bool(ConnState from, ConnEvent ev)>;

    struct Transition {
        ConnState next_state;
        ActionFn  action;
        GuardFn   guard;
    };

    explicit ConnectionStateMachine(IEventBus *event_bus = nullptr);

    BtError   process_event(ConnEvent event)          override;
    ConnState current_state()                   const override;
    bool      can_transition(ConnEvent event)   const override;

private:
    void build_table();
    void add(ConnState from, ConnEvent ev, ConnState to,
             ActionFn action = {}, GuardFn guard = {});

    using TransitionKey = std::pair<ConnState, ConnEvent>;
    std::map<TransitionKey, Transition> table_;
    ConnState                           state_;
    IEventBus                          *event_bus_{nullptr};
    mutable std::mutex                  mtx_;
};

}  // namespace bt
