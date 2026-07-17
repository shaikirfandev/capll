#ifndef FIRMWARE_USB_MANAGER_H
#define FIRMWARE_USB_MANAGER_H

#include "types.h"
#include <vector>

namespace firmware {

struct USBDevice {
    uint32 port;
    USBStandard standard;
    std::string vendor_id;
    std::string product_id;
    std::string device_name;
    std::string device_class;  // MassStorage, Keyboard, Mouse, etc.
    bool enumerated;
    bool active;
    uint32 data_rate_mbps;
};

struct USBMetrics {
    uint32 total_ports;
    uint32 connected_devices;
    uint32 enumerated_devices;
    uint32 active_transfers;
    uint64 total_data_transferred;
    uint32 transfer_errors;
};

class USBManager {
public:
    USBManager();

    // Device enumeration
    Status enumerate_devices();
    std::vector<USBDevice> get_enumerated_devices() const;

    // Device operations
    Status connect_device(const USBDevice& device);
    Status disconnect_device(uint32 port);

    // Data transfer
    Status perform_data_transfer(uint32 port, uint64 size);
    Status perform_stress_transfer(uint32 port);

    // Hot plug/removal
    Status hot_plug_device(const USBDevice& device);
    Status hot_remove_device(uint32 port);

    // Metrics
    USBMetrics get_metrics() const;

    // Failure injection
    void inject_enumeration_failure(uint32 port);
    void inject_transfer_failure(uint32 port);
    void inject_power_failure(uint32 port);
    void clear_injected_failures();

private:
    std::vector<USBDevice> devices_;
    USBMetrics metrics_;

    // Injected failures
    std::vector<uint32> enumeration_failures_;
    std::vector<uint32> transfer_failures_;
    std::vector<uint32> power_failures_;
};

} // namespace firmware

#endif // FIRMWARE_USB_MANAGER_H
