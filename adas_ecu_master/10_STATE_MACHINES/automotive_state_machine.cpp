/**
 * @file    automotive_state_machine.cpp
 * @brief   Hierarchical State Machine (HSM) for Automotive ECU
 * @details Template HSM framework + LKA/ACC combined state machine demo.
 *          Patterns used in AUTOSAR SWC state management.
 *
 * Compile: g++ -std=c++17 -Wall -Wextra -O2 automotive_state_machine.cpp -o hsm
 */

#include <cstdint>
#include <cstddef>
#include <array>
#include <functional>
#include <iostream>
#include <string>

// ============================================================================
// GENERIC EVENT TYPE
// ============================================================================

using EventId = uint32_t;

// Define event IDs as constexpr to avoid MISRA global array issues
namespace Events {
    static constexpr EventId NONE              = 0U;
    static constexpr EventId IGNITION_ON       = 1U;
    static constexpr EventId IGNITION_OFF      = 2U;
    static constexpr EventId FEATURE_ENABLE    = 3U;
    static constexpr EventId FEATURE_DISABLE   = 4U;
    static constexpr EventId SPEED_OK          = 5U;
    static constexpr EventId SPEED_LOW         = 6U;
    static constexpr EventId LANE_OK           = 7U;
    static constexpr EventId LANE_LOST         = 8U;
    static constexpr EventId DRIVER_OVERRIDE   = 9U;
    static constexpr EventId OVERRIDE_RELEASED = 10U;
    static constexpr EventId FAULT_DETECTED    = 11U;
    static constexpr EventId FAULT_CLEARED     = 12U;
    static constexpr EventId TIMER_EXPIRED     = 13U;
    static constexpr EventId LEAD_DETECTED     = 14U;
    static constexpr EventId LEAD_LOST         = 15U;
}

struct Event {
    EventId  id        = Events::NONE;
    float    param     = 0.0F;   // Optional event parameter
    uint32_t timestamp = 0U;
};

// ============================================================================
// STATE MACHINE RESULT
// ============================================================================

enum class SmResult : uint8_t {
    HANDLED    = 0U,  // Event consumed, transition occurred or no-op
    UNHANDLED  = 1U,  // Event not handled by this state — propagate to parent
};

// ============================================================================
// HSM STATE BASE (pure interface — AUTOSAR-style)
// ============================================================================

class IState {
public:
    virtual ~IState() = default;
    virtual void     onEntry() noexcept    = 0;
    virtual void     onExit() noexcept     = 0;
    virtual SmResult onEvent(const Event& e) noexcept = 0;
    virtual const char* name() const noexcept = 0;
};

// ============================================================================
// ADAS SYSTEM STATE MACHINE
// State hierarchy:
//
//   ECU_ROOT
//   ├── SLEEP
//   ├── INIT
//   └── OPERATIONAL
//       ├── STANDBY
//       ├── ACTIVE
//       │   ├── LKA_CORRECTING
//       │   └── ACC_FOLLOWING
//       └── FAULT
//
// ============================================================================

// Forward declare HSM manager
class AdasHsm;

// ============================================================================
// CONCRETE STATES
// ============================================================================

class SleepState : public IState {
public:
    explicit SleepState(AdasHsm& hsm) : hsm_(hsm) {}
    void onEntry() noexcept override;
    void onExit()  noexcept override;
    SmResult onEvent(const Event& e) noexcept override;
    const char* name() const noexcept override { return "SLEEP"; }
private:
    AdasHsm& hsm_;
};

class InitState : public IState {
public:
    explicit InitState(AdasHsm& hsm) : hsm_(hsm) {}
    void onEntry() noexcept override;
    void onExit()  noexcept override;
    SmResult onEvent(const Event& e) noexcept override;
    const char* name() const noexcept override { return "INIT"; }
private:
    AdasHsm& hsm_;
};

class StandbyState : public IState {
public:
    explicit StandbyState(AdasHsm& hsm) : hsm_(hsm) {}
    void onEntry() noexcept override;
    void onExit()  noexcept override;
    SmResult onEvent(const Event& e) noexcept override;
    const char* name() const noexcept override { return "STANDBY"; }
private:
    AdasHsm& hsm_;
};

class LkaCorrecting : public IState {
public:
    explicit LkaCorrecting(AdasHsm& hsm) : hsm_(hsm) {}
    void onEntry() noexcept override;
    void onExit()  noexcept override;
    SmResult onEvent(const Event& e) noexcept override;
    const char* name() const noexcept override { return "LKA_CORRECTING"; }
private:
    AdasHsm& hsm_;
};

class AccFollowing : public IState {
public:
    explicit AccFollowing(AdasHsm& hsm) : hsm_(hsm) {}
    void onEntry() noexcept override;
    void onExit()  noexcept override;
    SmResult onEvent(const Event& e) noexcept override;
    const char* name() const noexcept override { return "ACC_FOLLOWING"; }
private:
    AdasHsm& hsm_;
};

class OverrideState : public IState {
public:
    explicit OverrideState(AdasHsm& hsm) : hsm_(hsm) {}
    void onEntry() noexcept override;
    void onExit()  noexcept override;
    SmResult onEvent(const Event& e) noexcept override;
    const char* name() const noexcept override { return "DRIVER_OVERRIDE"; }
private:
    AdasHsm& hsm_;
};

class FaultState : public IState {
public:
    explicit FaultState(AdasHsm& hsm) : hsm_(hsm) {}
    void onEntry() noexcept override;
    void onExit()  noexcept override;
    SmResult onEvent(const Event& e) noexcept override;
    const char* name() const noexcept override { return "FAULT"; }
private:
    AdasHsm& hsm_;
};

// ============================================================================
// HSM MANAGER — controls current state + transition table
// ============================================================================

class AdasHsm {
public:
    AdasHsm() :
        sleepSt_(*this), initSt_(*this), standbySt_(*this),
        lkaSt_(*this), accSt_(*this), overrideSt_(*this), faultSt_(*this)
    {
        current_ = &sleepSt_;
    }

    void dispatch(const Event& e) noexcept {
        SmResult r = current_->onEvent(e);
        if (r == SmResult::UNHANDLED) {
            // In a real HSM, propagate to parent state
            // Here we log and ignore
            std::cout << "  [HSM] Event " << e.id << " unhandled in " << current_->name() << "\n";
        }
    }

    void transition(IState* next) noexcept {
        std::cout << "  [HSM] " << current_->name() << " --> " << next->name() << "\n";
        current_->onExit();
        current_ = next;
        current_->onEntry();
    }

    const char* getCurrentStateName() const noexcept {
        return current_->name();
    }

    // State accessors
    IState& sleepState()    noexcept { return sleepSt_; }
    IState& initState()     noexcept { return initSt_; }
    IState& standbyState()  noexcept { return standbySt_; }
    IState& lkaState()      noexcept { return lkaSt_; }
    IState& accState()      noexcept { return accSt_; }
    IState& overrideState() noexcept { return overrideSt_; }
    IState& faultState()    noexcept { return faultSt_; }

private:
    SleepState     sleepSt_;
    InitState      initSt_;
    StandbyState   standbySt_;
    LkaCorrecting  lkaSt_;
    AccFollowing   accSt_;
    OverrideState  overrideSt_;
    FaultState     faultSt_;
    IState*        current_ = nullptr;
};

// ============================================================================
// STATE IMPLEMENTATIONS
// ============================================================================

void SleepState::onEntry()  noexcept { std::cout << "  [ENTRY] " << name() << "\n"; }
void SleepState::onExit()   noexcept { std::cout << "  [EXIT]  " << name() << "\n"; }
SmResult SleepState::onEvent(const Event& e) noexcept {
    if (e.id == Events::IGNITION_ON) {
        hsm_.transition(&hsm_.initState());
        return SmResult::HANDLED;
    }
    return SmResult::UNHANDLED;
}

void InitState::onEntry()  noexcept { std::cout << "  [ENTRY] " << name() << " — running self-check\n"; }
void InitState::onExit()   noexcept { std::cout << "  [EXIT]  " << name() << "\n"; }
SmResult InitState::onEvent(const Event& e) noexcept {
    if (e.id == Events::IGNITION_OFF) {
        hsm_.transition(&hsm_.sleepState());
        return SmResult::HANDLED;
    }
    if (e.id == Events::SPEED_OK) {
        // Init complete — system ready
        hsm_.transition(&hsm_.standbyState());
        return SmResult::HANDLED;
    }
    if (e.id == Events::FAULT_DETECTED) {
        hsm_.transition(&hsm_.faultState());
        return SmResult::HANDLED;
    }
    return SmResult::UNHANDLED;
}

void StandbyState::onEntry()  noexcept { std::cout << "  [ENTRY] " << name() << " — LKA/ACC ready\n"; }
void StandbyState::onExit()   noexcept { std::cout << "  [EXIT]  " << name() << "\n"; }
SmResult StandbyState::onEvent(const Event& e) noexcept {
    if (e.id == Events::IGNITION_OFF)      { hsm_.transition(&hsm_.sleepState());    return SmResult::HANDLED; }
    if (e.id == Events::FAULT_DETECTED)    { hsm_.transition(&hsm_.faultState());    return SmResult::HANDLED; }
    if (e.id == Events::LANE_OK)           { hsm_.transition(&hsm_.lkaState());      return SmResult::HANDLED; }
    if (e.id == Events::LEAD_DETECTED)     { hsm_.transition(&hsm_.accState());      return SmResult::HANDLED; }
    if (e.id == Events::DRIVER_OVERRIDE)   { hsm_.transition(&hsm_.overrideState()); return SmResult::HANDLED; }
    return SmResult::UNHANDLED;
}

void LkaCorrecting::onEntry()  noexcept { std::cout << "  [ENTRY] " << name() << " — PID applying torque\n"; }
void LkaCorrecting::onExit()   noexcept { std::cout << "  [EXIT]  " << name() << "\n"; }
SmResult LkaCorrecting::onEvent(const Event& e) noexcept {
    if (e.id == Events::LANE_LOST)         { hsm_.transition(&hsm_.standbyState());  return SmResult::HANDLED; }
    if (e.id == Events::DRIVER_OVERRIDE)   { hsm_.transition(&hsm_.overrideState()); return SmResult::HANDLED; }
    if (e.id == Events::FAULT_DETECTED)    { hsm_.transition(&hsm_.faultState());    return SmResult::HANDLED; }
    if (e.id == Events::IGNITION_OFF)      { hsm_.transition(&hsm_.sleepState());    return SmResult::HANDLED; }
    return SmResult::UNHANDLED;
}

void AccFollowing::onEntry()  noexcept { std::cout << "  [ENTRY] " << name() << " — gap PID active\n"; }
void AccFollowing::onExit()   noexcept { std::cout << "  [EXIT]  " << name() << "\n"; }
SmResult AccFollowing::onEvent(const Event& e) noexcept {
    if (e.id == Events::LEAD_LOST)         { hsm_.transition(&hsm_.standbyState());  return SmResult::HANDLED; }
    if (e.id == Events::DRIVER_OVERRIDE)   { hsm_.transition(&hsm_.overrideState()); return SmResult::HANDLED; }
    if (e.id == Events::FAULT_DETECTED)    { hsm_.transition(&hsm_.faultState());    return SmResult::HANDLED; }
    if (e.id == Events::IGNITION_OFF)      { hsm_.transition(&hsm_.sleepState());    return SmResult::HANDLED; }
    return SmResult::UNHANDLED;
}

void OverrideState::onEntry()  noexcept { std::cout << "  [ENTRY] " << name() << " — driver in control\n"; }
void OverrideState::onExit()   noexcept { std::cout << "  [EXIT]  " << name() << "\n"; }
SmResult OverrideState::onEvent(const Event& e) noexcept {
    if (e.id == Events::OVERRIDE_RELEASED) { hsm_.transition(&hsm_.standbyState());  return SmResult::HANDLED; }
    if (e.id == Events::FAULT_DETECTED)    { hsm_.transition(&hsm_.faultState());    return SmResult::HANDLED; }
    if (e.id == Events::IGNITION_OFF)      { hsm_.transition(&hsm_.sleepState());    return SmResult::HANDLED; }
    return SmResult::UNHANDLED;
}

void FaultState::onEntry()  noexcept { std::cout << "  [ENTRY] " << name() << " — DTC logged, output zeroed\n"; }
void FaultState::onExit()   noexcept { std::cout << "  [EXIT]  " << name() << "\n"; }
SmResult FaultState::onEvent(const Event& e) noexcept {
    // FAULT is latching — only ignition cycle clears it
    if (e.id == Events::IGNITION_OFF) {
        hsm_.transition(&hsm_.sleepState());
        return SmResult::HANDLED;
    }
    return SmResult::UNHANDLED;
}

// ============================================================================
// MAIN — WALK THROUGH SCENARIOS
// ============================================================================

int main() {
    std::cout << "=== Automotive HSM Demo ===\n\n";

    AdasHsm hsm;
    uint32_t ts = 0U;

    auto send = [&](EventId id, const char* desc, float param = 0.0F) {
        ts += 100U;
        std::cout << "\n[t=" << ts << "ms] Event: " << desc << "\n";
        hsm.dispatch(Event{id, param, ts});
        std::cout << "  Current state: " << hsm.getCurrentStateName() << "\n";
    };

    // Scenario 1: Normal start-up → LKA active
    send(Events::IGNITION_ON,       "Ignition ON");
    send(Events::SPEED_OK,          "Init self-check passed");
    send(Events::LANE_OK,           "Camera: lane markers detected");

    // Scenario 2: Driver grabs wheel
    send(Events::DRIVER_OVERRIDE,   "Driver steering torque > 2.5 Nm");
    send(Events::OVERRIDE_RELEASED, "Driver releases wheel (3s hold expired)");

    // Scenario 3: Lead vehicle detected
    send(Events::LEAD_DETECTED,     "Radar: vehicle at 80m");
    send(Events::LEAD_LOST,         "Radar: lead vehicle changed lane");

    // Scenario 4: Fault
    send(Events::LANE_OK,           "Camera: lane recovered");
    send(Events::FAULT_DETECTED,    "EPS fault active!");
    send(Events::FAULT_CLEARED,     "Fault clear attempt (IGNORED — latching)");
    send(Events::IGNITION_OFF,      "Ignition OFF — clears fault");

    std::cout << "\n=== HSM Demo complete ===\n";
    return 0;
}
