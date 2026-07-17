#ifndef FIRMWARE_APPLICATION_H
#define FIRMWARE_APPLICATION_H

#include "types.h"
#include "boot_manager.h"
#include "power_manager.h"
#include "memory_manager.h"
#include "security_manager.h"
#include "pcie_manager.h"
#include "usb_manager.h"
#include "bmc_manager.h"
#include "lsio_manager.h"
#include "health_monitor.h"
#include "logger.h"

namespace firmware {

class FirmwareApplication {
public:
    static FirmwareApplication& getInstance();

    // Initialize all subsystems
    Status initialize();
    Status shutdown();

    // Main firmware operations
    Status start_boot_sequence();
    Status change_power_state(PowerState state);

    // Subsystem access
    BootManager& get_boot_manager();
    PowerManager& get_power_manager();
    MemoryManager& get_memory_manager();
    SecurityManager& get_security_manager();
    PCIeManager& get_pcie_manager();
    USBManager& get_usb_manager();
    BMCManager& get_bmc_manager();
    LSIOManager& get_lsio_manager();
    HealthMonitor& get_health_monitor();
    Logger& get_logger();

    // Get system status
    std::string get_system_status() const;
    HealthStatus get_system_health() const;
    std::vector<std::string> get_all_logs() const;

    // Simulation control
    void run_simulation(uint32 duration_seconds = 60);
    void simulate_periodic_monitoring();

private:
    FirmwareApplication();
    FirmwareApplication(const FirmwareApplication&) = delete;
    FirmwareApplication& operator=(const FirmwareApplication&) = delete;

    BootManager boot_manager_;
    PowerManager power_manager_;
    MemoryManager memory_manager_;
    SecurityManager security_manager_;
    PCIeManager pcie_manager_;
    USBManager usb_manager_;
    BMCManager bmc_manager_;
    LSIOManager lsio_manager_;
    HealthMonitor health_monitor_;
    Logger& logger_;

    bool initialized_;
};

} // namespace firmware

#endif // FIRMWARE_APPLICATION_H
