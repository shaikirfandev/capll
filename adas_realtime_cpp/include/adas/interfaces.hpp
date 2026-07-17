#pragma once

#include "adas/types.hpp"

#include <cstddef>
#include <optional>

namespace adas {

class IVehicleGateway {
public:
    virtual ~IVehicleGateway() = default;
    virtual std::optional<SensorFrame> read_frame() noexcept = 0;
    virtual bool write_command(const ActuatorCommand& command) noexcept = 0;
};

// Boundary for CAN/CAN-FD, Automotive Ethernet or SOME/IP adapters.
// Keep decoding, endianness and transport retries out of control algorithms.
class ITransport {
public:
    virtual ~ITransport() = default;
    virtual bool send(const std::byte* payload, std::size_t size) noexcept = 0;
};

}  // namespace adas
