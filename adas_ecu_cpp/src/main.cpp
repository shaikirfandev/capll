/**
 * @file    main.cpp
 * @brief   ADAS ECU Application — Entry point and task definitions.
 *
 * Execution model (Cyclic Executive):
 *
 *   10ms: Task_FastSensors  — decode incoming CAN messages
 *   20ms: Task_Control      — run ACC + LKA + BSD (all 50Hz features)
 *   50ms: Task_MediumCycle  — run Parking + HHA (20Hz features)
 *  100ms: Task_Diagnostics  — DTC check + fault monitoring
 * 1000ms: Task_Background   — ECU health log, scheduler stats
 *
 * CAN message flow:
 *
 *   [Radar 0x200] ──────────────┐
 *   [Camera 0x201] ─────────────┤
 *   [BSD Radar 0x202] ──────────┤
 *   [Ultrasonic 0x203] ─────────┤─→ SensorFusion::update()
 *   [VehicleSpeed 0x100] ───────┤         │
 *   [SteeringAngle 0x101] ──────┤         ▼
 *   [DriverInputs 0x400] ───────┤   World Model
 *   [GearShifter 0x401] ────────┘         │
 *                                         ├─→ AccController::tick()  → 0x300, 0x301
 *                                         ├─→ LkaController::tick()  → 0x302, 0x303, 0x500
 *                                         ├─→ BsdController::tick()  → 0x304
 *                                         ├─→ ParkingController::tick() → 0x305
 *                                         └─→ HhaController::tick()  → 0x306
 */

#include "hal/hal_types.hpp"
#include "hal/hal_timer.hpp"
#include "drivers/can_driver.hpp"
#include "drivers/can_messages.hpp"
#include "rtos/scheduler.hpp"
#include "features/sensor_fusion.hpp"
#include "features/acc_controller.hpp"
#include "features/lka_controller.hpp"
#include "features/bsd_controller.hpp"
#include "features/parking_controller.hpp"
#include "features/hha_controller.hpp"
#include "diagnostics/dtc_manager.hpp"

#include <cstdio>
#include <cmath>

// ── Global: last decoded input messages ───────────────────────────────────────
// (In a real AUTOSAR stack these would be in RTE (Runtime Environment) ports)
static messages::MsgVehicleSpeed  g_speed;
static messages::MsgSteeringAngle g_steer;
static messages::MsgWheelSpeeds   g_wheels;
static messages::MsgRadarObject   g_radar;
static messages::MsgCameraLane    g_camera;
static messages::MsgBSDRadar      g_bsd_radar;
static messages::MsgUltrasonic    g_ultrasonic;
static messages::MsgDriverInputs  g_driver;
static messages::MsgGearShifter   g_gear;

// ── CAN receive decode dispatch ───────────────────────────────────────────────
static void dispatchRxFrame(const drivers::CanFrame& f) {
    switch (f.id) {
        case messages::MsgVehicleSpeed::ID:   g_speed.decode(f);     break;
        case messages::MsgSteeringAngle::ID:  g_steer.decode(f);     break;
        case messages::MsgWheelSpeeds::ID:    g_wheels.decode(f);    break;
        case messages::MsgRadarObject::ID:    g_radar.decode(f);     break;
        case messages::MsgCameraLane::ID:     g_camera.decode(f);    break;
        case messages::MsgBSDRadar::ID:       g_bsd_radar.decode(f); break;
        case messages::MsgUltrasonic::ID:     g_ultrasonic.decode(f);break;
        case messages::MsgDriverInputs::ID:   g_driver.decode(f);    break;
        case messages::MsgGearShifter::ID:    g_gear.decode(f);      break;
        default: break;
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// TASK: Fast Sensor Read (10ms)
// – Read all available CAN frames and decode into global message structs
// ═══════════════════════════════════════════════════════════════════════════════
static void Task_FastSensors() {
    auto& can = drivers::CanDriver::instance();
    drivers::CanFrame frame;

    // Drain entire Rx ring buffer each cycle
    while (can.receive(frame) == Status::OK) {
        dispatchRxFrame(frame);
    }

    // CAN bus health DTC reporting
    auto& dtc = diagnostics::DtcManager::instance();
    if (can.isBusOff()) {
        // On bus-off error we can't send/receive — report internally
        // In production this would trigger a bus-off recovery sequence
    }

    // Radar timeout monitoring: if no valid radar message for 500ms → DTC
    static TickType_t last_radar_tick = 0u;
    if (g_radar.valid) {
        last_radar_tick = hal::Timer::getTick();
        dtc.reportPassed(diagnostics::DtcId::RADAR_COMM_LOSS);
    } else if (hal::Timer::elapsed(last_radar_tick) > 500u) {
        dtc.reportFault(diagnostics::DtcId::RADAR_COMM_LOSS);
    }

    // Camera timeout: 2s
    static TickType_t last_camera_tick = 0u;
    if (g_camera.left_quality > 0u || g_camera.right_quality > 0u) {
        last_camera_tick = hal::Timer::getTick();
        dtc.reportPassed(diagnostics::DtcId::CAMERA_COMM_LOSS);
    } else if (hal::Timer::elapsed(last_camera_tick) > 2000u) {
        dtc.reportFault(diagnostics::DtcId::CAMERA_COMM_LOSS);
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// TASK: Control Cycle (20ms)
// – Run sensor fusion then all 20ms ADAS features
// ═══════════════════════════════════════════════════════════════════════════════
static void Task_Control() {
    auto& fusion   = features::SensorFusion::instance();
    auto& acc      = features::AccController::instance();
    auto& lka      = features::LkaController::instance();
    auto& bsd      = features::BsdController::instance();
    auto& can      = drivers::CanDriver::instance();

    // ── Update world model ─────────────────────────────────────────────────────
    fusion.update(g_radar, g_camera, g_bsd_radar, g_ultrasonic,
                  g_speed, g_steer, g_driver, g_gear);

    const auto& vehicle = fusion.vehicleState();
    const auto& target  = fusion.frontTarget();
    const auto& lane    = fusion.laneModel();
    const auto& blind   = fusion.blindZone();

    // ── ACC ────────────────────────────────────────────────────────────────────
    acc.tick(vehicle, target, g_driver);

    messages::MsgACCStatus  acc_status;
    messages::MsgACCControl acc_ctrl;
    acc.getStatusMsg(acc_status);
    acc.getControlMsg(acc_ctrl);

    drivers::CanFrame acc_status_frame;
    drivers::CanFrame acc_ctrl_frame;
    acc_status.encode(acc_status_frame);
    acc_ctrl.encode(acc_ctrl_frame);
    can.transmit(acc_status_frame);
    can.transmit(acc_ctrl_frame);

    // ── LKA ────────────────────────────────────────────────────────────────────
    lka.tick(vehicle, lane, g_driver);

    messages::MsgLKAStatus    lka_status;
    messages::MsgLKATorqueCmd lka_torque;
    lka.getLKAStatusMsg(lka_status);
    lka.getLKATorqueMsg(lka_torque);

    drivers::CanFrame lka_sts_frame, lka_torq_frame;
    lka_status.encode(lka_sts_frame);
    lka_torque.encode(lka_torq_frame);
    can.transmit(lka_sts_frame);
    can.transmit(lka_torq_frame);

    // ── BSD ────────────────────────────────────────────────────────────────────
    bsd.tick(vehicle, blind, g_driver);

    messages::MsgBSDStatus bsd_status;
    bsd.getBSDStatusMsg(bsd_status);

    drivers::CanFrame bsd_frame;
    bsd_status.encode(bsd_frame);
    can.transmit(bsd_frame);
}

// ═══════════════════════════════════════════════════════════════════════════════
// TASK: Medium Cycle (50ms)
// – Parking assistance + HHA (slower sensors, 20Hz update enough)
// ═══════════════════════════════════════════════════════════════════════════════
static void Task_MediumCycle() {
    auto& park = features::ParkingController::instance();
    auto& hha  = features::HhaController::instance();
    auto& can  = drivers::CanDriver::instance();
    auto& fusion = features::SensorFusion::instance();

    const auto& vehicle  = fusion.vehicleState();
    const auto& parking  = fusion.parkingModel();

    // ── Parking ────────────────────────────────────────────────────────────────
    park.tick(vehicle, parking, g_driver);

    messages::MsgParkStatus park_status;
    park.getParkStatusMsg(park_status);

    drivers::CanFrame park_frame;
    park_status.encode(park_frame);
    can.transmit(park_frame);

    // ── Hill Hold Assist ───────────────────────────────────────────────────────
    hha.tick(vehicle);

    messages::MsgHHAStatus hha_status;
    hha.getHHAStatusMsg(hha_status);

    drivers::CanFrame hha_frame;
    hha_status.encode(hha_frame);
    can.transmit(hha_frame);

    // ── LDW (on slow HMI cycle) ────────────────────────────────────────────────
    messages::MsgLDWWarning ldw;
    features::LkaController::instance().getLDWMsg(ldw);

    drivers::CanFrame ldw_frame;
    ldw.encode(ldw_frame);
    can.transmit(ldw_frame);
}

// ═══════════════════════════════════════════════════════════════════════════════
// TASK: Diagnostics (100ms)
// – DTC end-of-cycle, fault summary
// ═══════════════════════════════════════════════════════════════════════════════
static void Task_Diagnostics() {
    auto& dtc  = diagnostics::DtcManager::instance();
    auto& sched = rtos::Scheduler::instance();

    // Report scheduler overruns as DTC
    if (sched.hasOverrun()) {
        dtc.reportFault(diagnostics::DtcId::TASK_OVERRUN);
    } else {
        dtc.reportPassed(diagnostics::DtcId::TASK_OVERRUN);
    }

    // DTC cycle end — update status bit flags
    dtc.endOfCycle();
}

// ═══════════════════════════════════════════════════════════════════════════════
// TASK: Background Monitor (1000ms)
// – Logging, ECU state print, scheduler statistics
// ═══════════════════════════════════════════════════════════════════════════════
static void Task_Background() {
    auto& dtc    = diagnostics::DtcManager::instance();
    auto& acc    = features::AccController::instance();
    auto& lka    = features::LkaController::instance();
    auto& fusion = features::SensorFusion::instance();
    auto& sched  = rtos::Scheduler::instance();

    const auto& v = fusion.vehicleState();

    std::printf("\n══════════════════════════════════════════════════\n");
    std::printf("  ADAS ECU  tick=%-8u  speed=%.1f km/h\n",
                hal::Timer::getTick(), v.speed_kph);
    std::printf("  ACC: state=%-3u  set=%.0fkm/h  AEB=%d\n",
                static_cast<uint8_t>(acc.getState()),
                acc.getSetSpeed(),
                acc.isAEBActive() ? 1 : 0);
    std::printf("  LKA: state=%-3u  torque=%.2f Nm  LDW=%d\n",
                static_cast<uint8_t>(lka.getState()),
                lka.getTorque(),
                lka.isLDWActive() ? 1 : 0);
    std::printf("  Target: dist=%.1fm  relV=%.2fm/s  TTC=%.2fs\n",
                fusion.frontTarget().distance_m,
                fusion.frontTarget().rel_velocity_mps,
                fusion.frontTarget().ttc_s);
    std::printf("  DTCs: active=%u  confirmed=%u\n",
                dtc.activeCount(), dtc.confirmedCount());

    // Print confirmed DTC list if any
    if (dtc.confirmedCount() > 0u) {
        diagnostics::DtcId dtc_list[32];
        uint8_t n = dtc.getConfirmedDTCs(dtc_list, 32u);
        std::printf("  Confirmed DTC list:\n");
        for (uint8_t i = 0; i < n; i++) {
            std::printf("    [%u] 0x%06X\n", i, static_cast<uint32_t>(dtc_list[i]));
        }
    }

    // Print scheduler stats
    std::printf("  Scheduler tasks (%u):\n", sched.taskCount());
    for (uint8_t i = 0; i < sched.taskCount(); i++) {
        const auto& t = sched.getTask(i);
        std::printf("    %-22s period=%-4ums overruns=%u maxExec=%ums\n",
                    t.name, t.period_ms, t.overrun_count, t.max_exec_us);
    }
    std::printf("══════════════════════════════════════════════════\n\n");
}

// ═══════════════════════════════════════════════════════════════════════════════
// Simulation: inject test stimulus frames after startup
// (On real ECU this would come from physical bus)
// ═══════════════════════════════════════════════════════════════════════════════
#ifdef SIMULATION_BUILD

static void injectSimulationFrames() {
    auto& can = drivers::CanDriver::instance();

    static TickType_t last_inject = 0u;
    TickType_t now = hal::Timer::getTick();
    if (now - last_inject < 100u) return;
    last_inject = now;

    static float sim_speed = 0.0f;
    static float sim_dist  = 100.0f;
    static int   sim_step  = 0;

    // Simulation scenario: accelerate → ACC activation → closing target → decel
    sim_step++;
    if      (sim_step < 50)  { sim_speed += 1.0f; }          // Accelerate to 80 km/h
    else if (sim_step < 100) { sim_dist  -= 1.0f; }           // Target closing in
    else if (sim_step < 120) { sim_dist = 8.0f; }             // Critical TTC zone
    else if (sim_step < 150) { sim_dist += 2.0f; }            // Target pulling away
    else                     { sim_step = 0; sim_speed = 0.0f; sim_dist = 100.0f; }

    // Build VehicleSpeed frame
    {
        drivers::CanFrame f;
        f.id  = messages::MsgVehicleSpeed::ID;
        f.dlc = messages::MsgVehicleSpeed::DLC;
        uint16_t raw = static_cast<uint16_t>(sim_speed / 0.01f);
        f.data[0] = raw & 0xFFu;
        f.data[1] = (raw >> 8u) & 0xFFu;
        f.data[2] = 0x01u;  // valid
        f.data[3] = 0x00u;  // forward
        can.onRxIsr(f);
    }

    // Build RadarObject frame
    {
        drivers::CanFrame f;
        f.id  = messages::MsgRadarObject::ID;
        f.dlc = messages::MsgRadarObject::DLC;
        uint16_t raw_dist = static_cast<uint16_t>(std::max(0.0f, sim_dist) / 0.01f);
        float    ttc      = (sim_speed > 0.01f) ? (sim_dist / (sim_speed / 3.6f)) : 99.0f;
        f.data[0] = raw_dist & 0xFFu;
        f.data[1] = (raw_dist >> 8u) & 0xFFu;
        f.data[4] = (sim_dist < 150.0f) ? 0x01u : 0x00u;  // valid when target < 150m
        f.data[5] = 0x01u;  // ObjectType::CAR
        f.data[6] = static_cast<uint8_t>(std::min(ttc / 0.1f, 255.0f));
        can.onRxIsr(f);
    }

    // Build DriverInputs frame (ACC set at startup)
    {
        drivers::CanFrame f;
        f.id  = messages::MsgDriverInputs::ID;
        f.dlc = messages::MsgDriverInputs::DLC;
        if (sim_step == 50) {
            f.data[0] = BIT(0);   // ACC set pressed
            f.data[1] = 80u;      // set speed = 80 km/h
        }
        f.data[3] = 0u;           // brake = 0
        f.data[4] = 0u;           // accel = 0
        can.onRxIsr(f);
    }

    // Build CameraLane frame (good lane quality)
    {
        drivers::CanFrame f;
        f.id     = messages::MsgCameraLane::ID;
        f.dlc    = messages::MsgCameraLane::DLC;
        f.data[0] = 3u;   // left quality = 3
        f.data[1] = 3u;   // right quality = 3
        // small positive left offset (slight right drift)
        int16_t lo = static_cast<int16_t>(0.05f / 0.001f);
        f.data[2] = lo & 0xFFu;
        f.data[3] = (lo >> 8u) & 0xFFu;
        can.onRxIsr(f);
    }

    // Build GearShifter frame (DRIVE)
    {
        drivers::CanFrame f;
        f.id     = messages::MsgGearShifter::ID;
        f.dlc    = messages::MsgGearShifter::DLC;
        f.data[0] = static_cast<uint8_t>(messages::MsgGearShifter::Gear::DRIVE);
        f.data[1] = 0x01u;  // valid
        can.onRxIsr(f);
    }
}
#endif

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════
int main() {
    // ── 1. Hardware / HAL initialisation ──────────────────────────────────────
    hal::Timer::init();

    std::printf("╔══════════════════════════════════════════════════╗\n");
    std::printf("║  ADAS ECU Firmware  v%d.%d.%d                      ║\n",
                ADAS_ECU_VERSION_MAJOR,
                ADAS_ECU_VERSION_MINOR,
                ADAS_ECU_VERSION_PATCH);
    std::printf("║  Built: %s  %s               ║\n", __DATE__, __TIME__);
#ifdef SIMULATION_BUILD
    std::printf("║  Mode: SIMULATION                                ║\n");
#else
    std::printf("║  Mode: EMBEDDED                                  ║\n");
#endif
    std::printf("╚══════════════════════════════════════════════════╝\n\n");

    // ── 2. CAN driver init ────────────────────────────────────────────────────
    drivers::CanConfig can_cfg;
    can_cfg.bitrate  = drivers::CanBitrate::KBPS_500;
    can_cfg.channel  = 1u;

    auto& can = drivers::CanDriver::instance();
    Status s = can.init(can_cfg);
    if (s != Status::OK) {
        std::printf("[MAIN] CAN init failed!\n");
        return -1;
    }

    // Add hardware filters for known ADAS message IDs
    can.addFilter(0x100u, 0x7F0u);   // Speed / steering (0x100–0x10F)
    can.addFilter(0x200u, 0x7F0u);   // Sensor messages (0x200–0x20F)
    can.addFilter(0x400u, 0x7F0u);   // Driver inputs (0x400–0x40F)

    // ── 3. Register scheduler tasks ───────────────────────────────────────────
    auto& sched = rtos::Scheduler::instance();

    sched.registerTask("FastSensors",   Task_FastSensors,  10u);
    sched.registerTask("Control",       Task_Control,      20u);
    sched.registerTask("MediumCycle",   Task_MediumCycle,  50u);
    sched.registerTask("Diagnostics",   Task_Diagnostics, 100u);
    sched.registerTask("Background",    Task_Background, 1000u);

    sched.start();

    // ── 4. Main loop ──────────────────────────────────────────────────────────
    std::printf("[MAIN] Entering main loop\n\n");

#ifdef SIMULATION_BUILD
    // Run simulation for ~10 seconds then exit
    const TickType_t SIM_DURATION_MS = 10000u;
    TickType_t sim_start = hal::Timer::getTick();

    while (hal::Timer::elapsed(sim_start) < SIM_DURATION_MS) {
        // Inject test stimulus into CAN Rx buffer
        injectSimulationFrames();

        // Execute all due tasks
        sched.dispatch();

        // Yield to OS (prevent 100% CPU in simulation)
        hal::Timer::delayMs(1u);
    }
    std::printf("[MAIN] Simulation complete. Exiting.\n");
#else
    // Embedded: infinite loop — never returns
    while (true) {
        sched.dispatch();
        // WFI (Wait For Interrupt) — enters CPU sleep until next SysTick
        // __WFI();   // CMSIS instruction
    }
#endif

    return 0;
}
