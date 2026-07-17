#include "pcie_manager.h"
#include "logger.h"
#include <thread>

namespace firmware {

PCIeManager::PCIeManager()
    : enumeration_failure_(false),
      timeout_injected_(false) {
    metrics_.total_devices = 0;
    metrics_.enumerated_devices = 0;
    metrics_.link_trained_devices = 0;
    metrics_.total_bandwidth_mbps = 0;
    metrics_.link_failures = 0;
    metrics_.enumeration_failures = 0;
}

Status PCIeManager::enumerate_devices() {
    LOG_INFO("PCIeManager", "Starting PCIe device enumeration");
    
    if (enumeration_failure_) {
        LOG_ERROR("PCIeManager", "PCIe enumeration failed");
        metrics_.enumeration_failures++;
        return Status::FAILURE;
    }
    
    std::this_thread::sleep_for(std::chrono::milliseconds(30));
    
    metrics_.total_devices = devices_.size();
    metrics_.enumerated_devices = devices_.size();
    
    for (auto& device : devices_) {
        device.enumerated = true;
        perform_link_training(device);
    }
    
    LOG_INFO("PCIeManager", "Enumeration completed: " + std::to_string(metrics_.enumerated_devices) + " devices");
    return Status::SUCCESS;
}

std::vector<PCIeDevice> PCIeManager::get_enumerated_devices() const {
    return devices_;
}

Status PCIeManager::train_link(uint32 bus, uint32 slot, uint32 func) {
    auto key = std::make_tuple(bus, slot, func);
    
    if (link_failures_.find(key) != link_failures_.end() && link_failures_.at(key)) {
        LOG_ERROR("PCIeManager", "Link training failed for device at B:S:F " + 
                  std::to_string(bus) + ":" + std::to_string(slot) + ":" + std::to_string(func));
        metrics_.link_failures++;
        return Status::FAILURE;
    }
    
    for (auto& device : devices_) {
        if (device.bus == bus && device.slot == slot && device.function == func) {
            device.link_trained = true;
            metrics_.link_trained_devices++;
            return Status::SUCCESS;
        }
    }
    
    return Status::FAILURE;
}

Status PCIeManager::upgrade_to_generation(uint32 bus, uint32 slot, uint32 func, PCIeGen gen) {
    LOG_INFO("PCIeManager", "Attempting to upgrade to Gen" + std::to_string(static_cast<int>(gen)));
    
    for (auto& device : devices_) {
        if (device.bus == bus && device.slot == slot && device.function == func) {
            device.generation = gen;
            return Status::SUCCESS;
        }
    }
    
    return Status::FAILURE;
}

Status PCIeManager::hot_plug_device(const PCIeDevice& device) {
    if (!device.hot_pluggable) {
        return Status::NOT_SUPPORTED;
    }
    
    LOG_INFO("PCIeManager", "Hot-plugging device: " + device.device_name);
    
    devices_.push_back(device);
    metrics_.total_devices++;
    
    return enumerate_devices();
}

Status PCIeManager::hot_remove_device(uint32 bus, uint32 slot, uint32 func) {
    LOG_INFO("PCIeManager", "Hot-removing device at B:S:F " + 
             std::to_string(bus) + ":" + std::to_string(slot) + ":" + std::to_string(func));
    
    auto it = std::find_if(devices_.begin(), devices_.end(),
        [bus, slot, func](const PCIeDevice& d) {
            return d.bus == bus && d.slot == slot && d.function == func && d.hot_pluggable;
        });
    
    if (it == devices_.end()) {
        return Status::FAILURE;
    }
    
    devices_.erase(it);
    metrics_.total_devices--;
    
    return Status::SUCCESS;
}

PCIeMetrics PCIeManager::get_metrics() const {
    return metrics_;
}

uint64 PCIeManager::get_device_bandwidth(uint32 bus, uint32 slot, uint32 func) const {
    for (const auto& device : devices_) {
        if (device.bus == bus && device.slot == slot && device.function == func) {
            // Gen1: 250MB/s, Gen2: 500MB/s, Gen3: 1000MB/s, Gen4: 2000MB/s
            uint64 base_bandwidth = 250;
            return base_bandwidth * static_cast<uint64>(device.generation) * device.link_width;
        }
    }
    return 0;
}

void PCIeManager::inject_link_failure(uint32 bus, uint32 slot, uint32 func) {
    LOG_WARNING("PCIeManager", "Injecting link failure for device at B:S:F " + 
                std::to_string(bus) + ":" + std::to_string(slot) + ":" + std::to_string(func));
    link_failures_[std::make_tuple(bus, slot, func)] = true;
}

void PCIeManager::inject_enumeration_failure() {
    LOG_WARNING("PCIeManager", "Injecting PCIe enumeration failure");
    enumeration_failure_ = true;
}

void PCIeManager::inject_timeout() {
    LOG_WARNING("PCIeManager", "Injecting PCIe timeout");
    timeout_injected_ = true;
}

void PCIeManager::clear_injected_failures() {
    LOG_INFO("PCIeManager", "Clearing all injected PCIe failures");
    enumeration_failure_ = false;
    timeout_injected_ = false;
    link_failures_.clear();
}

Status PCIeManager::add_device(const PCIeDevice& device) {
    devices_.push_back(device);
    metrics_.total_devices++;
    return Status::SUCCESS;
}

Status PCIeManager::remove_device(uint32 bus, uint32 slot, uint32 func) {
    auto it = std::find_if(devices_.begin(), devices_.end(),
        [bus, slot, func](const PCIeDevice& d) {
            return d.bus == bus && d.slot == slot && d.function == func;
        });
    
    if (it == devices_.end()) {
        return Status::FAILURE;
    }
    
    devices_.erase(it);
    metrics_.total_devices--;
    
    return Status::SUCCESS;
}

Status PCIeManager::perform_enumeration() {
    return enumerate_devices();
}

Status PCIeManager::perform_link_training(PCIeDevice& device) {
    return train_link(device.bus, device.slot, device.function);
}

} // namespace firmware
