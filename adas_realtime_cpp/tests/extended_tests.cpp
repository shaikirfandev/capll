// ============================================================
// tests/extended_tests.cpp
//
// Production-grade test coverage for the ADAS platform:
//   1.  VehicleMotionController — grade feed-forward, jerk limiting
//   2.  EgoStateEkf             — predict/update round-trips
//   3.  RangeKalmanFilter       — convergence, outlier rejection
//   4.  AdaptiveCruiseControl   — time-gap, stop-and-go
//   5.  MpcLaneCenteringController — bounded output, heading correction
//   6.  AdasSupervisor           — full mode transitions
//   7.  DtcManager               — report / clear / confirmation logic
//   8.  TraceLogger              — SPSC push/pop
//   9.  CanCodec                 — encode/decode Intel + Motorola
//  10.  SomeIpAdasServiceStub    — method and event dispatch
//  11.  PeriodicBarrier          — wakeup timing
//  12.  SpscQueue                — wrap-around, full/empty
// ============================================================

#include "adas/can_codec.hpp"
#include "adas/controllers.hpp"
#include "adas/diagnostics.hpp"
#include "adas/estimation.hpp"
#include "adas/qnx_integration.hpp"
#include "adas/runtime.hpp"
#include "adas/sensor_fusion.hpp"
#include "adas/someip_stub.hpp"
#include "adas/spsc_queue.hpp"
#include "adas/supervisor.hpp"
#include "adas/vehicle_dynamics.hpp"
#include "adas/vehicle_gateway.hpp"

#include <cassert>
#include <chrono>
#include <cmath>
#include <iostream>

// ──────────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────────
static void check(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "[FAIL] " << message << '\n';
        std::abort();
    }
    std::cout << "[PASS] " << message << '\n';
}

static adas::SensorFrame make_nominal_frame() {
    using namespace std::chrono;
    const auto now = steady_clock::now();
    adas::SensorFrame f{};
    f.timestamp = now;
    f.vehicle.timestamp = now;
    f.vehicle.speed_mps = 20.0;
    f.vehicle.acceleration_mps2 = 0.0;
    f.vehicle.yaw_rate_radps = 0.0;
    f.vehicle.steering_angle_rad = 0.0;
    f.vehicle.lane_offset_m = 0.1;
    f.vehicle.heading_error_rad = 0.01;
    f.vehicle.driver_override = false;
    f.vehicle.brake_available = true;
    f.vehicle.steering_available = true;
    f.vehicle.valid = true;
    f.lead.longitudinal_distance_m = 50.0;
    f.lead.relative_speed_mps = -2.0;
    f.lead.confidence = 0.9;
    f.lead.valid = true;
    f.lane.lateral_offset_m = 0.1;
    f.lane.heading_error_rad = 0.01;
    f.lane.confidence = 0.9;
    f.lane.valid = true;
    return f;
}

// ──────────────────────────────────────────────────────────────────────────────
// 1. VehicleMotionController
// ──────────────────────────────────────────────────────────────────────────────
static void test_vehicle_motion_controller() {
    adas::Limits limits{};
    adas::VehicleMotionController vmc(limits);

    // Uphill grade: grade feed-forward should increase demand
    double flat_demand = vmc.compute_longitudinal(25.0, 20.0, 0.0, 0.02);
    vmc.reset();
    double uphill_demand = vmc.compute_longitudinal(25.0, 20.0, 0.05, 0.02);  // ~3 deg uphill
    check(uphill_demand > flat_demand, "VMC: uphill grade increases demand");

    // Jerk limit: demand must not jump from 0 to max in one step
    vmc.reset();
    const double first = vmc.compute_longitudinal(30.0, 0.0, 0.0, 0.02);
    check(first < limits.max_acceleration_mps2, "VMC: jerk limiter prevents instant max accel");

    // Output is clamped within limits
    check(first >= limits.max_deceleration_mps2 && first <= limits.max_acceleration_mps2,
          "VMC: output within actuator limits");
}

// ──────────────────────────────────────────────────────────────────────────────
// 2. EgoStateEkf
// ──────────────────────────────────────────────────────────────────────────────
static void test_ego_state_ekf() {
    adas::EgoStateEkf ekf;
    ekf.reset(20.0, 0.1);

    // Predict 100 ms, speed unchanged (no measurement)
    for (int i = 0; i < 5; ++i) ekf.predict(0.02);
    auto state = ekf.state();
    check(state.valid, "EKF: valid after predict");
    check(std::abs(state.speed_mps - 20.0) < 0.5, "EKF: speed stable after free-run predict");

    // Wheel speed correction
    bool ok = ekf.update_wheel_speed(21.0);
    check(ok, "EKF: wheel speed update accepted");
    state = ekf.state();
    check(state.speed_mps > 20.0 && state.speed_mps <= 21.0, "EKF: speed pulled toward measurement");

    // Yaw rate correction
    ok = ekf.update_yaw_rate(0.2);
    check(ok, "EKF: yaw rate update accepted");

    // Lateral accel correction
    ok = ekf.update_lateral_accel(4.0);  // ~20 m/s * 0.2 rad/s = 4 m/s²
    check(ok, "EKF: lateral accel update accepted");

    // NaN measurement must be rejected
    check(!ekf.update_wheel_speed(std::numeric_limits<double>::quiet_NaN()),
          "EKF: NaN measurement rejected");
}

// ──────────────────────────────────────────────────────────────────────────────
// 3. RangeKalmanFilter — convergence
// ──────────────────────────────────────────────────────────────────────────────
static void test_range_kalman_filter() {
    adas::RangeKalmanFilter kf;
    kf.reset(50.0, -5.0);
    check(kf.initialized(), "KF: initialized after reset");

    // Drive several updates at consistent measurements; range should converge.
    double range = 50.0;
    for (int i = 0; i < 50; ++i) {
        range -= 5.0 * 0.02;  // constant-speed closure
        kf.update(range, -5.0, 0.02);
    }
    const double error = std::abs(kf.range_m() - range);
    check(error < 1.5, "KF: range converges to truth within 1.5 m");

    // Outlier (impossible range) must not corrupt estimate significantly
    const double before = kf.range_m();
    kf.update(-10.0, -5.0, 0.02);  // Negative range: update returns false, state unchanged
    check(std::abs(kf.range_m() - before) < 0.5, "KF: negative range rejected (no large state jump)");
}

// ──────────────────────────────────────────────────────────────────────────────
// 4. AdaptiveCruiseControl
// ──────────────────────────────────────────────────────────────────────────────
static void test_acc() {
    adas::Limits limits{};
    adas::AdaptiveCruiseControl acc(limits);

    // No lead: pure speed control, should demand positive acceleration to reach set speed
    adas::VehicleState ego{};
    ego.speed_mps = 15.0;
    ego.valid = true;
    adas::LeadObject no_lead{};
    no_lead.valid = false;
    const double demand_free = acc.compute(ego, no_lead, 27.78, 0.02);
    check(demand_free > 0.0, "ACC: demands acceleration when below set speed");

    // Close lead at low relative speed: should reduce demand
    adas::LeadObject close_lead{};
    close_lead.valid = true;
    close_lead.longitudinal_distance_m = 8.0;  // Inside time-gap
    close_lead.relative_speed_mps = 0.0;
    close_lead.confidence = 0.9;
    const double demand_close = acc.compute(ego, close_lead, 27.78, 0.02);
    check(demand_close < demand_free, "ACC: reduces demand when lead is too close");

    // Output always within limits
    check(demand_close >= limits.max_deceleration_mps2 && demand_close <= limits.max_acceleration_mps2,
          "ACC: output within limits");
}

// ──────────────────────────────────────────────────────────────────────────────
// 5. MPC lane centering
// ──────────────────────────────────────────────────────────────────────────────
static void test_mpc_lcc() {
    adas::Limits limits{};
    adas::MpcLaneCenteringController mpc(limits);

    adas::VehicleState ego{};
    ego.speed_mps = 20.0;

    // Large lateral offset: MPC should command steering toward center
    adas::LaneModel lane{};
    lane.lateral_offset_m = 0.6;
    lane.heading_error_rad = 0.05;
    lane.confidence = 0.9;
    lane.valid = true;

    double cmd = mpc.compute(ego, lane, 0.02);
    check(cmd != 0.0, "MPC: non-zero command for lateral offset");
    check(std::abs(cmd) <= limits.max_steering_angle_rad, "MPC: output within steering limit");

    // Multiple steps converge (bounded prediction horizon)
    for (int i = 0; i < 50; ++i) {
        lane.lateral_offset_m *= 0.95;  // Slowly converge
        cmd = mpc.compute(ego, lane, 0.02);
    }
    check(std::abs(cmd) <= limits.max_steering_angle_rad, "MPC: stays within limit after 50 steps");
}

// ──────────────────────────────────────────────────────────────────────────────
// 6. AdasSupervisor — comprehensive mode transitions
// ──────────────────────────────────────────────────────────────────────────────
static void test_supervisor() {
    using namespace std::chrono;
    adas::AdasSupervisor supervisor;
    check(supervisor.configuration_valid(), "Supervisor: default config valid");

    // Normal active operation
    auto frame = make_nominal_frame();
    const auto now = steady_clock::now();
    auto cmd = supervisor.step(frame, now, 0.02);
    check(cmd.longitudinal_mode == adas::ControlMode::Active, "Supervisor: longitudinal active");
    check(cmd.lateral_mode == adas::ControlMode::Active, "Supervisor: lateral active");
    check(std::abs(cmd.requested_steering_angle_rad) <= 0.55, "Supervisor: steering within limits");

    // AEB trigger: close high-speed lead
    frame = make_nominal_frame();
    frame.lead.longitudinal_distance_m = 6.0;
    frame.lead.relative_speed_mps = -15.0;
    frame.lead.confidence = 0.95;
    cmd = supervisor.step(frame, now + 20ms, 0.02);
    check(cmd.aeb_request, "Supervisor: AEB triggered on close-speed lead");
    check(cmd.requested_acceleration_mps2 <= -4.0, "Supervisor: AEB commands strong deceleration");

    // Driver override
    frame = make_nominal_frame();
    frame.vehicle.driver_override = true;
    cmd = supervisor.step(frame, now + 40ms, 0.02);
    check(cmd.longitudinal_mode == adas::ControlMode::Standby, "Supervisor: standby on driver override");
    check(adas::has_fault(cmd.faults, adas::Fault::DriverOverride), "Supervisor: fault flag set on override");

    // Stale frame
    frame = make_nominal_frame();
    frame.timestamp = now - 200ms;
    cmd = supervisor.step(frame, now, 0.02);
    check(cmd.longitudinal_mode == adas::ControlMode::Standby, "Supervisor: standby on stale frame");
    check(adas::has_fault(cmd.faults, adas::Fault::FrameStale), "Supervisor: stale fault bit set");

    // Invalid frame (negative speed)
    frame = make_nominal_frame();
    frame.vehicle.speed_mps = -1.0;
    cmd = supervisor.step(frame, now, 0.02);
    check(adas::has_fault(cmd.faults, adas::Fault::FrameInvalid), "Supervisor: invalid frame rejected");

    // Brake unavailable → fault on longitudinal
    frame = make_nominal_frame();
    frame.vehicle.brake_available = false;
    cmd = supervisor.step(frame, now + 60ms, 0.02);
    check(cmd.longitudinal_mode == adas::ControlMode::Fault, "Supervisor: fault on brake unavailable");
    check(adas::has_fault(cmd.faults, adas::Fault::BrakeUnavailable), "Supervisor: brake fault bit set");

    // Steering unavailable → degraded lateral
    frame = make_nominal_frame();
    frame.vehicle.steering_available = false;
    cmd = supervisor.step(frame, now + 80ms, 0.02);
    check(cmd.lateral_mode == adas::ControlMode::Degraded, "Supervisor: degraded lateral, steering unavailable");

    // Low lane confidence → degraded lateral
    frame = make_nominal_frame();
    frame.lane.confidence = 0.1;
    cmd = supervisor.step(frame, now + 100ms, 0.02);
    check(cmd.lateral_mode == adas::ControlMode::Degraded, "Supervisor: degraded lateral, low lane confidence");

    // Invalid configuration
    adas::AdasConfiguration bad_cfg;
    bad_cfg.limits.max_acceleration_mps2 = -1.0;  // Invalid!
    adas::AdasSupervisor bad_supervisor(bad_cfg);
    check(!bad_supervisor.configuration_valid(), "Supervisor: invalid config detected");
    cmd = bad_supervisor.step(make_nominal_frame(), now, 0.02);
    check(cmd.longitudinal_mode == adas::ControlMode::Fault, "Supervisor: fault mode on invalid config");
}

// ──────────────────────────────────────────────────────────────────────────────
// 7. DtcManager
// ──────────────────────────────────────────────────────────────────────────────
static void test_dtc_manager() {
    adas::DtcManager dtc;
    const auto now = std::chrono::steady_clock::now();

    // First report: Pending
    dtc.report(0xC0A000U, now);
    check(dtc.active_count() == 1U, "DTC: first report creates entry");
    adas::DiagnosticEvent buf[4];
    dtc.snapshot(buf, 4);
    check(buf[0].status == adas::DtcStatus::Pending, "DTC: first occurrence is Pending");
    check(buf[0].occurrence_counter == 1U, "DTC: occurrence counter = 1");

    // Second report: Confirmed
    dtc.report(0xC0A000U, now);
    dtc.snapshot(buf, 4);
    check(buf[0].status == adas::DtcStatus::Confirmed, "DTC: second occurrence Confirmed");
    check(buf[0].occurrence_counter == 2U, "DTC: occurrence counter = 2");

    // Distinct DTC
    dtc.report(0xC0B000U, now);
    check(dtc.active_count() == 2U, "DTC: second distinct DTC added");

    // Clear single
    dtc.clear(0xC0A000U);
    check(dtc.active_count() == 1U, "DTC: single clear removes entry");

    // Clear all
    dtc.clear_all();
    check(dtc.active_count() == 0U, "DTC: clear_all empties table");
}

// ──────────────────────────────────────────────────────────────────────────────
// 8. TraceLogger (SPSC ring buffer for structured records)
// ──────────────────────────────────────────────────────────────────────────────
static void test_trace_logger() {
    adas::TraceLogger logger;
    check(logger.empty(), "Trace: initially empty");

    adas::TraceRecord rec;
    rec.timestamp_us = 12345;
    rec.level = adas::TraceLevel::Warning;
    rec.event_code = 0x0042U;
    rec.value_a = 3.14F;
    logger.push(rec);
    check(!logger.empty(), "Trace: not empty after push");

    const auto popped = logger.pop();
    check(popped.has_value(), "Trace: pop returns value");
    check(popped->timestamp_us == 12345, "Trace: timestamp preserved");
    check(popped->event_code == 0x0042U, "Trace: event code preserved");
    check(logger.empty(), "Trace: empty after single pop");

    // Fill ring to capacity and verify no overflow crash
    for (std::size_t i = 0; i < adas::TraceLogger::kCapacity + 10; ++i) {
        logger.push(rec);
    }
    std::size_t count = 0;
    while (logger.pop().has_value()) ++count;
    check(count <= adas::TraceLogger::kCapacity, "Trace: ring buffer never overflows");
}

// ──────────────────────────────────────────────────────────────────────────────
// 9. CAN codec — Intel and Motorola
// ──────────────────────────────────────────────────────────────────────────────
static void test_can_codec() {
    adas::CanFrame frame{};
    frame.dlc = 8U;

    // Encode vehicle speed 55.5 km/h = 55.5 m/s (using signal: factor=0.01)
    const double speed_value = 55.5;
    bool ok = adas::encode(frame, adas::signals::kVehicleSpeed, speed_value);
    check(ok, "CAN: speed encode succeeds");

    double decoded = 0.0;
    ok = adas::decode(frame, adas::signals::kVehicleSpeed, decoded);
    check(ok, "CAN: speed decode succeeds");
    check(std::abs(decoded - speed_value) < 0.02, "CAN: speed round-trip within 0.02");

    // Signed yaw rate
    const double yaw = -12.34;
    ok = adas::encode(frame, adas::signals::kYawRate, yaw);
    check(ok, "CAN: yaw rate encode succeeds");
    ok = adas::decode(frame, adas::signals::kYawRate, decoded);
    check(ok, "CAN: yaw rate decode succeeds");
    check(std::abs(decoded - yaw) < 0.02, "CAN: yaw rate round-trip within 0.02");

    // Out-of-range value must fail
    ok = adas::encode(frame, adas::signals::kVehicleSpeed, 99999.0);
    check(!ok, "CAN: out-of-range encode rejected");

    // Steering angle
    const double steer = 250.0;
    adas::CanFrame frame2{};
    frame2.dlc = 8U;
    ok = adas::encode(frame2, adas::signals::kSteeringAngle, steer);
    check(ok, "CAN: steering encode succeeds");
    ok = adas::decode(frame2, adas::signals::kSteeringAngle, decoded);
    check(ok, "CAN: steering decode succeeds");
    check(std::abs(decoded - steer) < 0.2, "CAN: steering round-trip within 0.2");
}

// ──────────────────────────────────────────────────────────────────────────────
// 10. SOME/IP stub
// ──────────────────────────────────────────────────────────────────────────────
static void test_someip_stub() {
    adas::SomeIpAdasServiceStub stub;

    double received_speed = 0.0;
    bool received_enabled = false;

    stub.on_set_cruise_speed([&](double s) -> bool {
        received_speed = s;
        return true;
    });
    stub.on_set_enabled([&](bool e) -> bool {
        received_enabled = e;
        return true;
    });

    bool ok = stub.simulate_set_cruise_speed(27.78);
    check(ok, "SOME/IP: SetCruiseSpeed dispatch succeeds");
    check(std::abs(received_speed - 27.78) < 0.001, "SOME/IP: cruise speed value delivered");

    ok = stub.simulate_set_enabled(true);
    check(ok, "SOME/IP: SetEnabled dispatch succeeds");
    check(received_enabled, "SOME/IP: enabled value delivered");

    adas::AdasStatusEvent ev{};
    ev.requested_acceleration_mps2 = 1.5F;
    ev.longitudinal_mode = static_cast<std::uint8_t>(adas::ControlMode::Active);
    ok = stub.notify_status(ev);
    check(ok, "SOME/IP: notify_status accepted");
    check(stub.last_event().has_value(), "SOME/IP: last event stored");
    check(stub.last_event()->longitudinal_mode == static_cast<std::uint8_t>(adas::ControlMode::Active),
          "SOME/IP: event mode field correct");
}

// ──────────────────────────────────────────────────────────────────────────────
// 11. PeriodicBarrier
// ──────────────────────────────────────────────────────────────────────────────
static void test_periodic_barrier() {
    using namespace std::chrono;
    adas::qnx::PeriodicBarrier barrier(10ms);

    const auto start = steady_clock::now();
    barrier.wait();
    const auto elapsed = duration_cast<milliseconds>(steady_clock::now() - start);

    // Should be close to 10 ms — allow 20 ms margin for scheduler jitter in CI
    check(elapsed.count() >= 5 && elapsed.count() < 50, "PeriodicBarrier: wakeup in expected window");
}

// ──────────────────────────────────────────────────────────────────────────────
// 12. SpscQueue — wrap-around and edge cases
// ──────────────────────────────────────────────────────────────────────────────
static void test_spsc_queue() {
    adas::SpscQueue<std::uint32_t, 8> q;

    // Fill to capacity (7 items for capacity-8 queue)
    for (std::uint32_t i = 0; i < 7; ++i) {
        check(q.try_push(i), "SPSC: push succeeds while not full");
    }
    check(!q.try_push(99U), "SPSC: push fails when full");

    // Drain
    for (std::uint32_t i = 0; i < 7; ++i) {
        const auto v = q.try_pop();
        check(v.has_value() && *v == i, "SPSC: FIFO order preserved");
    }
    check(!q.try_pop().has_value(), "SPSC: pop returns nullopt when empty");

    // Wrap-around: push and pop alternately
    for (int round = 0; round < 20; ++round) {
        q.try_push(static_cast<std::uint32_t>(round));
        const auto v = q.try_pop();
        check(v.has_value(), "SPSC: wrap-around push/pop succeeds");
    }
}

// ──────────────────────────────────────────────────────────────────────────────
// Entry point
// ──────────────────────────────────────────────────────────────────────────────
int main() {
    test_vehicle_motion_controller();
    test_ego_state_ekf();
    test_range_kalman_filter();
    test_acc();
    test_mpc_lcc();
    test_supervisor();
    test_dtc_manager();
    test_trace_logger();
    test_can_codec();
    test_someip_stub();
    test_periodic_barrier();
    test_spsc_queue();
    std::cout << "\nAll extended ADAS tests passed.\n";
}
