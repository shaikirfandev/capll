#ifndef FIRMWARE_BMC_MANAGER_H
#define FIRMWARE_BMC_MANAGER_H

#include "types.h"
#include <vector>

namespace firmware {

struct Sensor {
    std::string name;
    float value;
    std::string unit;
    float threshold_warning;
    float threshold_critical;
};

class BMCManager {
public:
    BMCManager();

    // Remote operations
    Status remote_power_on();
    Status remote_power_off();
    Status remote_reset();
    Status remote_power_cycle();

    // Sensor monitoring
    Status read_sensors();
    std::vector<Sensor> get_sensor_readings() const;

    // Firmware update
    Status start_firmware_update(const std::string& firmware_image);
    Status verify_firmware_update();
    Status abort_firmware_update();

    // Health monitoring
    Status get_system_health();
    std::string get_health_summary() const;

    // IPMI simulation
    Status ipmi_command(uint8 netfn, uint8 cmd, const std::vector<uint8>& data);

    // Redfish simulation
    std::string get_redfish_info() const;

private:
    std::vector<Sensor> sensors_;
    std::string health_status_;
    bool firmware_update_in_progress_;
};

} // namespace firmware

#endif // FIRMWARE_BMC_MANAGER_H
