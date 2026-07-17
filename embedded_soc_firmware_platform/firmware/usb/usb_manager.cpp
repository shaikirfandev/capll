#include "usb_manager.h"
#include "logger.h"
#include <thread>

namespace firmware {

USBManager::USBManager() {
    metrics_.total_ports = 10;
    metrics_.connected_devices = 0;
    metrics_.enumerated_devices = 0;
    metrics_.active_transfers = 0;
    metrics_.total_data_transferred = 0;
    metrics_.transfer_errors = 0;
}

Status USBManager::enumerate_devices() {
    LOG_INFO("USBManager", "Starting USB device enumeration");
    
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
    
    metrics_.enumerated_devices = devices_.size();
    
    for (auto& device : devices_) {
        device.enumerated = true;
        device.active = true;
    }
    
    LOG_INFO("USBManager", "USB enumeration completed: " + std::to_string(metrics_.enumerated_devices) + " devices");
    return Status::SUCCESS;
}

std::vector<USBDevice> USBManager::get_enumerated_devices() const {
    return devices_;
}

Status USBManager::connect_device(const USBDevice& device) {
    LOG_INFO("USBManager", "Connecting USB device: " + device.device_name + " on port " + std::to_string(device.port));
    
    if (enumeration_failures_.size() > 0 && 
        std::find(enumeration_failures_.begin(), enumeration_failures_.end(), device.port) != enumeration_failures_.end()) {
        LOG_ERROR("USBManager", "Failed to enumerate device on port " + std::to_string(device.port));
        metrics_.transfer_errors++;
        return Status::FAILURE;
    }
    
    devices_.push_back(device);
    metrics_.connected_devices++;
    
    return enumerate_devices();
}

Status USBManager::disconnect_device(uint32 port) {
    LOG_INFO("USBManager", "Disconnecting USB device on port " + std::to_string(port));
    
    auto it = std::find_if(devices_.begin(), devices_.end(),
        [port](const USBDevice& d) { return d.port == port; });
    
    if (it == devices_.end()) {
        return Status::FAILURE;
    }
    
    devices_.erase(it);
    metrics_.connected_devices--;
    
    return Status::SUCCESS;
}

Status USBManager::perform_data_transfer(uint32 port, uint64 size) {
    if (std::find(transfer_failures_.begin(), transfer_failures_.end(), port) != transfer_failures_.end()) {
        LOG_ERROR("USBManager", "Data transfer failed on port " + std::to_string(port));
        metrics_.transfer_errors++;
        return Status::FAILURE;
    }
    
    metrics_.active_transfers++;
    
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    
    metrics_.total_data_transferred += size;
    metrics_.active_transfers--;
    
    LOG_DEBUG("USBManager", "Data transfer completed: " + std::to_string(size) + " bytes");
    return Status::SUCCESS;
}

Status USBManager::perform_stress_transfer(uint32 port) {
    LOG_INFO("USBManager", "Starting USB stress transfer on port " + std::to_string(port));
    
    for (int i = 0; i < 100; ++i) {
        Status result = perform_data_transfer(port, 1024);
        if (result != Status::SUCCESS) {
            return result;
        }
    }
    
    LOG_INFO("USBManager", "USB stress transfer completed on port " + std::to_string(port));
    return Status::SUCCESS;
}

Status USBManager::hot_plug_device(const USBDevice& device) {
    LOG_INFO("USBManager", "Hot-plugging USB device on port " + std::to_string(device.port));
    return connect_device(device);
}

Status USBManager::hot_remove_device(uint32 port) {
    LOG_INFO("USBManager", "Hot-removing USB device on port " + std::to_string(port));
    return disconnect_device(port);
}

USBMetrics USBManager::get_metrics() const {
    return metrics_;
}

void USBManager::inject_enumeration_failure(uint32 port) {
    LOG_WARNING("USBManager", "Injecting enumeration failure on port " + std::to_string(port));
    enumeration_failures_.push_back(port);
}

void USBManager::inject_transfer_failure(uint32 port) {
    LOG_WARNING("USBManager", "Injecting transfer failure on port " + std::to_string(port));
    transfer_failures_.push_back(port);
}

void USBManager::inject_power_failure(uint32 port) {
    LOG_WARNING("USBManager", "Injecting power failure on port " + std::to_string(port));
    power_failures_.push_back(port);
}

void USBManager::clear_injected_failures() {
    LOG_INFO("USBManager", "Clearing all injected USB failures");
    enumeration_failures_.clear();
    transfer_failures_.clear();
    power_failures_.clear();
}

} // namespace firmware
