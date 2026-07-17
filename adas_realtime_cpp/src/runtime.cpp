#include "adas/runtime.hpp"

namespace adas {

ControlRuntime::ControlRuntime(AdasSupervisor& supervisor, IVehicleGateway& gateway, std::chrono::microseconds deadline) noexcept
    : supervisor_(supervisor), gateway_(gateway), deadline_(deadline) {}

bool ControlRuntime::run_cycle(TimePoint now, double dt_s) noexcept {
    const auto start = TimePoint::clock::now();
    ++health_.cycle_count;
    const auto frame = gateway_.read_frame();
    if (!frame) {
        health_.faults |= Fault::FrameInvalid;
        return false;
    }

    auto command = supervisor_.step(*frame, now, dt_s);
    const auto end = TimePoint::clock::now();
    const auto execution = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    if (execution > health_.worst_execution_time) health_.worst_execution_time = execution;
    if (execution > deadline_) {
        ++health_.deadline_miss_count;
        health_.faults |= Fault::DeadlineMiss;
        command.faults |= Fault::DeadlineMiss;
        command.longitudinal_mode = ControlMode::Standby;
        command.lateral_mode = ControlMode::Standby;
    }
    health_.faults |= command.faults;
    if (!gateway_.write_command(command)) {
        health_.faults |= Fault::GatewayWriteFailure;
        return false;
    }
    return !has_fault(command.faults, Fault::ConfigurationInvalid);
}

}  // namespace adas
