/**
 * @file main.cpp
 * @brief FMS bootstrap — EGLL→KSFO flight scenario
 * @req SRS-PERF-001
 */
#include "common/Logger.hpp"
#include "sensors/AirDataSystem.hpp"
#include "sensors/InertialNavSystem.hpp"
#include "sensors/GpsReceiver.hpp"
#include "sensors/SensorFusion.hpp"
#include "fms/NavigationEngine.hpp"
#include "fms/GuidanceComputer.hpp"
#include "fms/FlightPlanManager.hpp"
#include "fms/FuelManagement.hpp"
#include "fms/PerformanceComputer.hpp"
#include "safety/FaultManager.hpp"
#include "safety/Watchdog.hpp"
#include "safety/HealthMonitor.hpp"
#include "comms/Arinc429Driver.hpp"
#include "fms/FmsTypes.hpp"

#include <cstdio>
#include <thread>
#include <chrono>

int main() {
    std::puts("=== Avionics FMS v3.2.1 — EGLL→KSFO ===");

    // ── Logger ───────────────────────────────────────────────────────────────
    fms::Logger::get().init("fms.log", fms::LogLevel::INFO);
    FMS_LOG_INFO("MAIN", "FMS boot sequence start");

    // ── Safety ───────────────────────────────────────────────────────────────
    fms::safety::FaultManager fault_mgr;
    fms::safety::Watchdog     watchdog;
    fms::safety::HealthMonitor health;
    fault_mgr.init();
    watchdog.init(500U);
    health.init();
    health.run_bite();

    fault_mgr.set_fault_callback([](const fms::safety::FaultRecord& r) {
        std::printf("[FAULT] id=0x%04X sev=%u desc='%s'\n",
                    static_cast<unsigned>(r.id),
                    static_cast<unsigned>(r.severity),
                    r.description);
    });

    // ── Sensors ──────────────────────────────────────────────────────────────
    const fms::LatLon egll{51.4775, -0.4614};
    const fms::Position3D egll_pos{51.4775, -0.4614, 0.0};
    fms::sensors::AirDataSystem     adc;
    fms::sensors::InertialNavSystem ins;
    fms::sensors::GpsReceiver       gps;
    fms::sensors::SensorFusion      fusion;
    adc.init();
    ins.init(egll_pos);
    gps.init();
    fusion.init();

    // ── Navigation ───────────────────────────────────────────────────────────
    fms::NavigationEngine nav_eng;
    nav_eng.init(egll);
    nav_eng.set_rnp_requirement(2.0f);

    // ── Communications ───────────────────────────────────────────────────────
    fms::comms::Arinc429Driver arinc429;
    arinc429.init(0U, 100U);
    double rx_alt = 0.0;
    arinc429.set_rx_callback(fms::comms::label::ALTITUDE_CORRECTED,
        [&](const fms::comms::Arinc429Frame& f) {
            rx_alt = fms::comms::Arinc429Driver::decode_bnr(f.data_bits, 1.0, 18U);
        });

    // ── Flight Plan ──────────────────────────────────────────────────────────
    fms::FlightPlanManager fpm;
    fpm.init(nullptr);
    fpm.set_origin("EGLL");
    fpm.set_destination("KSFO");
    {
        fms::Waypoint wpt{};
        const char* waypoints[] = {"WOBUN", "MALOT", "SUNOT", "MIMKU"};
        for (const char* id : waypoints) {
            if (fpm.find_waypoint(id, wpt)) {
                fpm.insert_waypoint(fpm.get_active_fp().wpt_count, wpt);
            }
        }
        fms::Waypoint dest{};
        if (fpm.find_waypoint("KSFO", dest)) {
            fpm.insert_waypoint(fpm.get_active_fp().wpt_count, dest);
        }
    }
    if (fpm.activate() == fms::FmsError::OK) {
        FMS_LOG_INFO("MAIN", "Flight plan EGLL→KSFO activated");
    }

    // ── Performance & Fuel ───────────────────────────────────────────────────
    fms::PerformanceComputer perf_comp;
    fms::FuelManagement      fuel_mgr;
    perf_comp.init();
    fuel_mgr.init();

    // ── Guidance ─────────────────────────────────────────────────────────────
    fms::GuidanceComputer guidance;
    guidance.init();
    guidance.set_lnav_mode(fms::LnavMode::LNAV);
    guidance.set_vnav_mode(fms::VnavMode::VNAV_PTH);

    // ── Main loop (50 cycles = 2.5 s simulated) ──────────────────────────────
    for (int cycle = 0; cycle < 50; ++cycle) {
        adc.update();
        ins.update();
        gps.update();
        fusion.update(gps.get_data(), ins.get_data(), adc.get_data());

        const auto& g = gps.get_data();
        if (g.valid) {
            nav_eng.update_gps(g.lat_deg, g.lon_deg, g.alt_wgs84_m,
                                g.vel_north_ms, g.vel_east_ms,
                                g.num_satellites, g.hdop);
        }
        const auto& a = adc.get_data();
        if (a.valid) {
            nav_eng.update_adc(a.tas_kt, a.cas_kt, a.mach,
                                a.pressure_alt_ft, a.isa_deviation_c);
        }

        const auto& nav = nav_eng.get_nav_state();
        perf_comp.update(nav, fuel_mgr.get_fuel_state(), fpm.get_active_fp());
        fuel_mgr.update(perf_comp.get_perf_data(), nav);
        guidance.update(nav, fpm.get_active_fp(), perf_comp.get_perf_data());

        // ARINC 429 transmit altitude every cycle
        const uint32_t alt_word = fms::comms::Arinc429Driver::encode_bnr(
            fms::comms::label::ALTITUDE_CORRECTED, 0U,
            nav.position.alt_ft, 1.0, 18U, fms::comms::Arinc429Ssm::NORMAL_OP);
        arinc429.transmit_raw(alt_word);

        watchdog.kick();
        health.update();

        if (!nav_eng.is_rnp_satisfied()) {
            fault_mgr.report_fault(
                fms::safety::FaultId::NAV_RNP_EXCEEDED,
                fms::safety::FaultSeverity::WARNING,
                "ANP exceeds RNP");
        }

        if (cycle % 10 == 0) {
            const auto& hr = health.get_health();
            std::printf("[CYCLE %3d] ALT=%.0f ft | GS=%.0f kt | ANP=%.3f nm | "
                        "CPU=%.1f%% | RX_ALT=%.0f\n",
                        cycle,
                        static_cast<double>(nav.position.alt_ft),
                        static_cast<double>(nav.ground_speed_kt),
                        static_cast<double>(nav.anp_nm),
                        static_cast<double>(hr.cpu_load_pct),
                        rx_alt);
        }
    }

    std::puts("=== FMS shutdown ===");
    return 0;
}
