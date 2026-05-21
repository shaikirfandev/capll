/**
 * @file main.cpp
 * @brief ADAS Real-Time C++ System — Entry Point
 *
 * STARTUP SEQUENCE
 * ────────────────
 * 1. Lock all process memory (mlockall) → prevents page faults in RT threads
 * 2. Initialise HAL (SimHal for SIL, SocketCanHal for HIL)
 * 3. Start logger and fault manager
 * 4. Configure ADAS pipeline (detector → fusion → planner → controller)
 * 5. Register RT tasks in RtScheduler
 * 6. Start scheduler
 * 7. Block on SIGINT/SIGTERM
 * 8. Graceful shutdown
 *
 * RUNTIME LOOP (executed by RT tasks)
 * ─────────────────────────────────────
 *   50 Hz  → camera sensor frame processing + EKF fusion
 *   20 Hz  → radar sensor frame processing
 *   20 Hz  → path planning + control output (CAN Tx)
 *   10 Hz  → diagnostic reporting + fault check
 *
 * COMPILE
 * ───────
 *   bazel build //src:adas_rt --config=rt       # Release RT build
 *   bazel build //src:adas_rt --config=asan      # AddressSanitizer
 */

#include "adas/perception/object_detection.hpp"
#include "adas/perception/sensor_fusion.hpp"
#include "adas/planning/path_planner.hpp"
#include "adas/control/vehicle_controller.hpp"
#include "hil_sil/can_bus_sim.hpp"
#include "realtime/rt_scheduler.hpp"
#include "realtime/lock_free_queue.hpp"
#include "diagnostics/logger.hpp"
#include "diagnostics/fault_manager.hpp"

#include <atomic>
#include <csignal>
#include <iostream>
#include <chrono>
#include <thread>

// ─── Global signal flag ───────────────────────────────────────────────────────

static std::atomic<bool> g_running{true};

static void signalHandler(int sig) {
    (void)sig;
    g_running.store(false);
}

// ─── Shared data (protected by lock-free queues between RT threads) ───────────

using DetectionQueue = adas::realtime::SpscQueue<
    std::vector<adas::perception::DetectedObject>, 8>;

using TrackQueue = adas::realtime::SpscQueue<
    std::vector<adas::perception::TrackedObject>, 8>;

// ─── ADAS pipeline globals ────────────────────────────────────────────────────

adas::perception::ObjectDetector  g_detector;
adas::perception::SensorFusion    g_fusion;
adas::planning::PathPlanner       g_planner;
adas::control::VehicleController  g_controller;
adas::hil::SimHal                 g_hal;

// Ego state updated from CAN RX callback
static adas::planning::EgoState g_ego{};
static std::mutex               g_ego_mutex;

// ─── Task implementations ─────────────────────────────────────────────────────

static uint64_t taskSensorFusion() {
    static uint64_t ts = 0;
    ts += 20'000;  // 50 Hz simulation

    // Simulate a camera detection for demonstration
    adas::perception::SensorFrame frame{};
    frame.type         = adas::perception::SensorType::CAMERA;
    frame.timestamp_us = ts;

    adas::perception::CameraDetection cd{};
    cd.u = 320.f;  cd.v = 240.f;
    cd.width = 80.f; cd.height = 60.f;
    cd.depth_m = 30.f;
    cd.confidence = 0.90f;
    cd.cls = adas::perception::ObjectClass::VEHICLE;
    frame.camera_dets.push_back(cd);

    auto detections = g_detector.process(frame);
    auto tracks     = g_fusion.update(detections, ts);

    if (!tracks.empty()) {
        ADAS_LOG_DEBUG("FUSION", "Tracks: %zu  Lead: (%.1f,%.1f) v=%.1f m/s",
                        tracks.size(),
                        tracks[0].px, tracks[0].py, tracks[0].vx);
    }
    return ts;
}

static void taskPlanControl(uint64_t timestamp_us) {
    adas::planning::EgoState ego;
    {
        std::lock_guard<std::mutex> lock(g_ego_mutex);
        ego = g_ego;
    }

    // Get latest tracks from fusion (simplified: re-run fusion get)
    auto tracks  = g_fusion.getTracks();
    auto traj    = g_planner.plan(ego, tracks, 0.05f);
    auto cmd     = g_controller.compute(ego, traj, timestamp_us);

    // Publish control command on CAN (ID 0x200)
    adas::hil::CanFrame frame{};
    frame.id  = 0x200;
    adas::hil::encodeSignal(frame, adas::hil::signals::THROTTLE,    cmd.throttle);
    adas::hil::encodeSignal(frame, adas::hil::signals::BRAKE,       cmd.brake);
    adas::hil::encodeSignal(frame, adas::hil::signals::STEER_ANGLE, cmd.steer_rad);
    g_hal.txCan(frame);

    ADAS_LOG_TRACE("CTRL", "CMD thr=%.2f brk=%.2f steer=%.3f rad",
                   cmd.throttle, cmd.brake, cmd.steer_rad);
}

static void taskDiagnostics() {
    auto& fm = adas::diag::FaultManager::instance();
    if (fm.hasActiveFaults()) {
        fm.dump();
    }

    // Report RT deadline stats every 10 s (simplified)
    static uint32_t tick = 0;
    if (++tick % 100 == 0) {
        ADAS_LOG_INFO("DIAG", "System nominal. Uptime ticks: %u", tick);
    }
}

// ─── CAN RX handler (called from HAL, not an RT task) ─────────────────────────

static void onCanRx(const adas::hil::CanFrame& frame) {
    if (frame.id == 0x100) {
        const float speed = adas::hil::decodeSignal(frame, adas::hil::signals::EGO_SPEED);
        std::lock_guard<std::mutex> lock(g_ego_mutex);
        g_ego.speed_mps = speed;
    } else if (frame.id == 0x101) {
        const float accel = adas::hil::decodeSignal(frame, adas::hil::signals::EGO_ACCEL);
        std::lock_guard<std::mutex> lock(g_ego_mutex);
        g_ego.accel_mps2 = accel;
    }
}

// ─── main() ───────────────────────────────────────────────────────────────────

int main() {
    std::signal(SIGINT,  signalHandler);
    std::signal(SIGTERM, signalHandler);

    // ── 1. Logging ────────────────────────────────────────────────────────────
    auto& logger = adas::diag::Logger::instance();
    logger.setLevel(adas::diag::LogLevel::DEBUG);
    logger.start();
    ADAS_LOG_INFO("MAIN", "ADAS Real-Time System starting...");

    // ── 2. Fault manager ──────────────────────────────────────────────────────
    auto& fm = adas::diag::FaultManager::instance();
    fm.registerSafeStateCallback([](adas::diag::FaultCode code) {
        ADAS_LOG_FATAL("SAFE", "Safe state triggered by DTC %04X",
                       static_cast<unsigned>(code));
        g_running.store(false);
    });

    // ── 3. HAL (SIL) ──────────────────────────────────────────────────────────
    g_hal.open();
    g_hal.registerCanRxCallback(onCanRx);

    // ── 4. Configure ADAS pipeline ────────────────────────────────────────────
    adas::perception::CameraIntrinsics   cam_intr{ 718.8f, 718.8f, 607.5f, 185.2f };
    adas::perception::ExtrinsicTransform cam_ext { 1.5f, 0.f, 1.2f, 0.f, 0.f, 0.f };
    adas::perception::ExtrinsicTransform rad_ext { 2.5f, 0.f, 0.5f, 0.f, 0.f, 0.f };

    g_detector.configure(cam_intr, cam_ext, rad_ext);
    g_fusion.setNoiseParams(0.5f, 0.3f, 1.0f);
    g_planner.configure(33.33f);   // 120 km/h cruise
    g_controller.configure(1.0f, 0.05f, 0.1f, 0.5f);

    g_ego.speed_mps    = 20.0f;   // initial speed 72 km/h
    g_ego.heading_rad  = 0.0f;

    ADAS_LOG_INFO("MAIN", "Pipeline configured. Starting RT scheduler...");

    // ── 5. RT Scheduler ───────────────────────────────────────────────────────
    adas::realtime::RtScheduler scheduler;

    // Memory lock (best-effort: may fail without root/CAP_IPC_LOCK)
    scheduler.lockMemory();

    // Task: Sensor fusion @ 50 Hz, priority 70, CPU core 2
    scheduler.addTask({
        "sensor_fusion",
        70,
        2,
        std::chrono::microseconds(20'000),
        []() {
            taskSensorFusion();
        }
    });

    // Task: Planning + control @ 20 Hz, priority 60, CPU core 2
    scheduler.addTask({
        "plan_control",
        60,
        2,
        std::chrono::microseconds(50'000),
        []() {
            const uint64_t ts = static_cast<uint64_t>(
                std::chrono::duration_cast<std::chrono::microseconds>(
                    std::chrono::steady_clock::now().time_since_epoch()).count());
            taskPlanControl(ts);
        }
    });

    // Task: Diagnostics @ 10 Hz, priority 40, any CPU
    scheduler.addTask({
        "diagnostics",
        40,
        -1,
        std::chrono::microseconds(100'000),
        []() {
            taskDiagnostics();
        }
    });

    scheduler.start();
    ADAS_LOG_INFO("MAIN", "All RT tasks running. Press Ctrl+C to stop.");

    // ── 6. Simulate ego CAN frames every 100 ms ───────────────────────────────
    std::thread can_sim([&]() {
        uint64_t t = 0;
        while (g_running.load()) {
            adas::hil::CanFrame spd_frame{};
            spd_frame.id = 0x100;
            adas::hil::encodeSignal(spd_frame, adas::hil::signals::EGO_SPEED, 20.0f);
            g_hal.injectFrame(spd_frame);
            t += 100'000;
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    });

    // ── 7. Main loop ──────────────────────────────────────────────────────────
    while (g_running.load()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    // ── 8. Graceful shutdown ──────────────────────────────────────────────────
    ADAS_LOG_INFO("MAIN", "Shutdown requested.");
    scheduler.stop();
    can_sim.join();
    g_hal.close();
    logger.stop();

    // Print final RT stats
    const auto stats = scheduler.getStats();
    std::cout << "\n=== RT Task Statistics ===\n";
    for (const auto& s : stats) {
        std::printf("%-20s  executions=%llu  deadline_misses=%llu  max_jitter=%lld µs  avg_jitter=%lld µs\n",
                    s.name.c_str(),
                    static_cast<unsigned long long>(s.executions),
                    static_cast<unsigned long long>(s.deadline_misses),
                    static_cast<long long>(s.max_jitter_us),
                    static_cast<long long>(s.avg_jitter_us));
    }

    std::cout << "\n=== Active Faults ===\n";
    fm.dump();

    return 0;
}
