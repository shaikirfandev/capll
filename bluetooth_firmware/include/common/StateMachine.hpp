/**
 * @file StateMachine.hpp
 * @brief CRTP-based compile-time state machine template
 *
 * Usage:
 *   class MyFSM : public StateMachine<MyFSM, MyState, MyEvent> {
 *       TransitionTable build_table() const { ... }
 *   };
 */

#pragma once

#include <functional>
#include <map>
#include <optional>
#include <stdexcept>
#include <tuple>

namespace bt {

/**
 * @class StateMachine
 * @brief CRTP state machine template
 *
 * @tparam Derived   Concrete FSM class (for CRTP)
 * @tparam StateT    State enum type
 * @tparam EventT    Event enum type
 */
template<typename Derived, typename StateT, typename EventT>
class StateMachine {
public:
    using ActionFn     = std::function<void(StateT from, EventT event, StateT to)>;
    using GuardFn      = std::function<bool(StateT from, EventT event)>;
    using TransitionKey = std::pair<StateT, EventT>;

    struct Transition {
        StateT    next_state;
        ActionFn  action;   // Optional: called on state entry
        GuardFn   guard;    // Optional: must return true for transition to occur
    };

    using TransitionTable = std::map<TransitionKey, Transition>;

    explicit StateMachine(StateT initial) : current_state_(initial) {}

    /**
     * @brief Process an event and potentially transition state.
     * @return true if a transition occurred.
     */
    bool process(EventT event) {
        const auto key = std::make_pair(current_state_, event);
        const auto &table = derived().get_table();
        auto it = table.find(key);
        if (it == table.end()) {
            return false;  // No transition defined — ignore
        }
        const Transition &t = it->second;

        // Check guard
        if (t.guard && !t.guard(current_state_, event)) {
            return false;  // Guard rejected
        }

        const StateT prev = current_state_;
        current_state_ = t.next_state;

        // Execute action
        if (t.action) {
            t.action(prev, event, current_state_);
        }
        return true;
    }

    StateT state() const noexcept { return current_state_; }

    bool can_process(EventT event) const {
        const auto key = std::make_pair(current_state_, event);
        const auto &table = derived().get_table();
        return table.find(key) != table.end();
    }

protected:
    StateT current_state_;

private:
    Derived &derived()             { return static_cast<Derived &>(*this); }
    const Derived &derived() const { return static_cast<const Derived &>(*this); }
};

}  // namespace bt
