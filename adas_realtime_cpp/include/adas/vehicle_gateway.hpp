#pragma once

#include "adas/interfaces.hpp"

#include <mutex>

namespace adas {

// Host-only adapter used for integration testing. Replace with generated AUTOSAR
// RTE ports or a QNX io-pkt/SOME-IP transport in the target integration layer.
class InMemoryVehicleGateway final : public IVehicleGateway {
public:
    void publish(SensorFrame frame) noexcept;
    std::optional<SensorFrame> read_frame() noexcept override;
    bool write_command(const ActuatorCommand& command) noexcept override;
    [[nodiscard]] std::optional<ActuatorCommand> last_command() const noexcept;

private:
    mutable std::mutex mutex_;
    std::optional<SensorFrame> frame_;
    std::optional<ActuatorCommand> command_;
};

}  // namespace adas
