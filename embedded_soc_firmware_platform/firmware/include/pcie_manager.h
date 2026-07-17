#ifndef FIRMWARE_PCIE_MANAGER_H
#define FIRMWARE_PCIE_MANAGER_H

#include "types.h"
#include <vector>
#include <map>

namespace firmware {

struct PCIeDevice {
    uint32 bus;
    uint32 slot;
    uint32 function;
    std::string vendor_id;
    std::string device_id;
    std::string device_name;
    PCIeGen generation;
    bool enumerated;
    bool link_trained;
    uint32 link_width;
    bool hot_pluggable;
};

struct PCIeMetrics {
    uint32 total_devices;
    uint32 enumerated_devices;
    uint32 link_trained_devices;
    uint64 total_bandwidth_mbps;
    uint32 link_failures;
    uint32 enumeration_failures;
};

class PCIeManager {
public:
    PCIeManager();

    // Device enumeration
    Status enumerate_devices();
    std::vector<PCIeDevice> get_enumerated_devices() const;

    // Link training
    Status train_link(uint32 bus, uint32 slot, uint32 func);
    Status upgrade_to_generation(uint32 bus, uint32 slot, uint32 func, PCIeGen gen);

    // Hot plug/removal
    Status hot_plug_device(const PCIeDevice& device);
    Status hot_remove_device(uint32 bus, uint32 slot, uint32 func);

    // Bandwidth monitoring
    PCIeMetrics get_metrics() const;
    uint64 get_device_bandwidth(uint32 bus, uint32 slot, uint32 func) const;

    // Failure injection
    void inject_link_failure(uint32 bus, uint32 slot, uint32 func);
    void inject_enumeration_failure();
    void inject_timeout();
    void clear_injected_failures();

    // Device operations
    Status add_device(const PCIeDevice& device);
    Status remove_device(uint32 bus, uint32 slot, uint32 func);

private:
    std::vector<PCIeDevice> devices_;
    PCIeMetrics metrics_;

    // Injected failures
    bool enumeration_failure_;
    bool timeout_injected_;
    std::map<std::tuple<uint32,uint32,uint32>, bool> link_failures_;

    Status perform_enumeration();
    Status perform_link_training(PCIeDevice& device);
};

} // namespace firmware

#endif // FIRMWARE_PCIE_MANAGER_H
