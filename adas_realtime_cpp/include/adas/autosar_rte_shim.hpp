#pragma once

// ============================================================
// adas/autosar_rte_shim.hpp — AUTOSAR RTE compatibility shim
//
// PURPOSE:
//   Allow the ADAS core library to be compiled and tested without
//   the real AUTOSAR RTE headers (which are tool-generated and
//   proprietary to the target ECU toolchain).
//
//   In a real AUTOSAR Classic integration:
//     - Remove this file.
//     - Include the generated Rte_ADAS_Supervisor.h.
//     - Map Rte_Read_* / Rte_Write_* to your SW-C's ports.
//
//   In a real AUTOSAR Adaptive integration:
//     - Remove this file.
//     - Use ara::com Find/Offer, proxy/skeleton, and ara::exec.
//
// CLASSIC AUTOSAR MAPPING (summary):
//   SensorFrame       ← Rte_Read_ppi_SensorFrame_value(&sensorFrame)
//   ActuatorCommand   → Rte_Write_ppo_ActuatorCommand_value(&command)
//   CycleHealth       → Rte_Write_ppo_CycleHealth_value(&health)
//   20 ms RUNNABLE    ← TIMING_EVENT on ADAS_Supervisor_Runnable
//
// ADAPTIVE AUTOSAR MAPPING (summary):
//   SensorFrame       ← proxy->SensorFrameField.Get().get()
//   ActuatorCommand   → skeleton->ActuatorCommandEvent.Send(command)
//   ara::exec         → ExecutionClient.ReportExecutionState(kRunning)
// ============================================================

#include "adas/types.hpp"

namespace adas {
namespace autosar {

// ──────────────────────────────────────────────────────────────────────────────
// Classic RTE port stubs — replace with generated RTE headers on target
// ──────────────────────────────────────────────────────────────────────────────
inline bool rte_read_sensor_frame(SensorFrame& out) noexcept {
    // In production: return Rte_Read_ppi_SensorFrame_value(&out) == RTE_E_OK;
    (void)out;
    return false;  // Not connected in host build
}

inline bool rte_write_actuator_command(const ActuatorCommand& cmd) noexcept {
    // In production: return Rte_Write_ppo_ActuatorCommand_value(&cmd) == RTE_E_OK;
    (void)cmd;
    return false;
}

inline bool rte_write_cycle_health(const CycleHealth& h) noexcept {
    // In production: return Rte_Write_ppo_CycleHealth_value(&h) == RTE_E_OK;
    (void)h;
    return false;
}

// ──────────────────────────────────────────────────────────────────────────────
// Adaptive RTE port stubs
// ──────────────────────────────────────────────────────────────────────────────
inline void ara_exec_report_running() noexcept {
    // In production: ara::exec::ExecutionClient{}.ReportExecutionState(
    //     ara::exec::ExecutionState::kRunning);
}

inline void ara_exec_report_terminating() noexcept {
    // In production: ara::exec::ExecutionClient{}.ReportExecutionState(
    //     ara::exec::ExecutionState::kTerminating);
}

}  // namespace autosar
}  // namespace adas
