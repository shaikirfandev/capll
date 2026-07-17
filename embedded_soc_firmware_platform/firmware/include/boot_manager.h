#ifndef FIRMWARE_BOOT_MANAGER_H
#define FIRMWARE_BOOT_MANAGER_H

#include "types.h"
#include <functional>
#include <map>

namespace firmware {

class BootManager {
public:
    BootManager();

    // Boot operations
    Status power_on_reset();
    Status cold_boot();
    Status warm_boot();
    Status recovery_boot();
    Status watchdog_reset();

    // Boot sequence phases
    Status run_sec_phase();
    Status run_pei_phase();
    Status run_dxe_phase();
    Status run_bds_phase();
    Status run_os_loader();

    // Current state
    BootState get_boot_state() const;
    BootMetrics get_boot_metrics() const;

    // Failure injection
    void inject_memory_training_failure();
    void inject_pcie_failure();
    void inject_usb_failure();
    void inject_firmware_corruption();
    void inject_boot_timeout();
    void clear_injected_failures();

    // Boot log
    std::vector<std::string> get_boot_log() const;

private:
    BootState current_state_;
    BootMetrics metrics_;
    std::vector<std::string> boot_log_;

    // Injected failures
    bool memory_training_failure_;
    bool pcie_failure_;
    bool usb_failure_;
    bool firmware_corrupted_;
    bool boot_timeout_;

    void update_boot_log(const std::string& message);
    void transition_to_state(BootState new_state);
};

} // namespace firmware

#endif // FIRMWARE_BOOT_MANAGER_H
