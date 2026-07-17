#include "adas/vehicle_gateway.hpp"

namespace adas {

void InMemoryVehicleGateway::publish(SensorFrame frame) noexcept {
    const std::scoped_lock lock(mutex_);
    frame_ = frame;
}

std::optional<SensorFrame> InMemoryVehicleGateway::read_frame() noexcept {
    const std::scoped_lock lock(mutex_);
    return frame_;
}

bool InMemoryVehicleGateway::write_command(const ActuatorCommand& command) noexcept {
    const std::scoped_lock lock(mutex_);
    command_ = command;
    return true;
}

std::optional<ActuatorCommand> InMemoryVehicleGateway::last_command() const noexcept {
    const std::scoped_lock lock(mutex_);
    return command_;
}

}  // namespace adas
