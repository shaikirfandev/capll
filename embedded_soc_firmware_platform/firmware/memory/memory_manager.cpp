#include "memory_manager.h"
#include "logger.h"
#include <cstring>
#include <algorithm>

namespace firmware {

MemoryManager::MemoryManager()
    : ecc_errors_(0),
      training_failure_(false) {
    memory_info_.total_size = 16ULL * 1024 * 1024 * 1024;  // 16GB
    memory_info_.available_size = memory_info_.total_size;
    memory_info_.ecc_enabled = 1;
    memory_info_.ddr_type = 4;  // DDR4
    memory_info_.ddr_speed_mhz = 2666;
    
    memory_buffer_.resize(1024 * 1024);  // 1MB simulated buffer
}

Status MemoryManager::initialize_ddr() {
    LOG_INFO("MemoryManager", "Initializing DDR memory");
    
    test_results_.push_back("DDR4 initialization started");
    
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
    
    test_results_.push_back("DDR4 SPD reading completed");
    test_results_.push_back("Memory capacity detected: " + std::to_string(memory_info_.total_size / (1024*1024*1024)) + "GB");
    
    LOG_INFO("MemoryManager", "DDR initialization completed successfully");
    return Status::SUCCESS;
}

Status MemoryManager::run_ddr_training() {
    LOG_INFO("MemoryManager", "Running DDR training");
    
    if (training_failure_) {
        LOG_ERROR("MemoryManager", "DDR training failed");
        test_results_.push_back("FAILED: DDR training error");
        return Status::FAILURE;
    }
    
    test_results_.push_back("DDR training started");
    
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    
    test_results_.push_back("DDR training completed successfully");
    test_results_.push_back("Optimal timing parameters identified");
    
    LOG_INFO("MemoryManager", "DDR training completed");
    return Status::SUCCESS;
}

Status MemoryManager::enable_ecc() {
    LOG_INFO("MemoryManager", "Enabling ECC protection");
    
    memory_info_.ecc_enabled = 1;
    test_results_.push_back("ECC protection enabled");
    
    return Status::SUCCESS;
}

Status MemoryManager::write_memory(uint64 address, const uint8* data, uint64 size) {
    if (!data || size == 0 || size > memory_buffer_.size()) {
        return Status::INVALID_PARAM;
    }
    
    std::memcpy(memory_buffer_.data(), data, size);
    return Status::SUCCESS;
}

Status MemoryManager::read_memory(uint64 address, uint8* buffer, uint64 size) {
    if (!buffer || size == 0 || size > memory_buffer_.size()) {
        return Status::INVALID_PARAM;
    }
    
    std::memcpy(buffer, memory_buffer_.data(), size);
    return Status::SUCCESS;
}

Status MemoryManager::memory_stress_test() {
    LOG_INFO("MemoryManager", "Running memory stress test");
    
    test_results_.push_back("Memory stress test started");
    
    for (int iteration = 0; iteration < 10; ++iteration) {
        // Write pattern
        for (size_t i = 0; i < memory_buffer_.size(); ++i) {
            memory_buffer_[i] = static_cast<uint8>((i ^ iteration) & 0xFF);
        }
        
        // Read and verify pattern
        for (size_t i = 0; i < memory_buffer_.size(); ++i) {
            uint8 expected = static_cast<uint8>((i ^ iteration) & 0xFF);
            if (memory_buffer_[i] != expected) {
                test_results_.push_back("FAILED: Memory mismatch at iteration " + std::to_string(iteration));
                return Status::FAILURE;
            }
        }
    }
    
    test_results_.push_back("Memory stress test completed successfully");
    test_results_.push_back("All patterns verified correctly");
    
    LOG_INFO("MemoryManager", "Memory stress test passed");
    return Status::SUCCESS;
}

void MemoryManager::inject_single_bit_error(uint64 address) {
    LOG_WARNING("MemoryManager", "Injecting single-bit error at 0x" + std::to_string(address));
    single_bit_error_addresses_.push_back(address);
    ecc_errors_++;
}

void MemoryManager::inject_double_bit_error(uint64 address) {
    LOG_ERROR("MemoryManager", "Injecting double-bit error at 0x" + std::to_string(address));
    double_bit_error_addresses_.push_back(address);
    ecc_errors_++;
}

void MemoryManager::inject_training_failure() {
    LOG_WARNING("MemoryManager", "Injecting DDR training failure");
    training_failure_ = true;
}

void MemoryManager::clear_injected_errors() {
    LOG_INFO("MemoryManager", "Clearing all injected memory errors");
    single_bit_error_addresses_.clear();
    double_bit_error_addresses_.clear();
    training_failure_ = false;
    ecc_errors_ = 0;
}

MemoryInfo MemoryManager::get_memory_info() const {
    return memory_info_;
}

uint32 MemoryManager::get_ecc_error_count() const {
    return ecc_errors_;
}

std::vector<std::string> MemoryManager::get_test_results() const {
    return test_results_;
}

} // namespace firmware
