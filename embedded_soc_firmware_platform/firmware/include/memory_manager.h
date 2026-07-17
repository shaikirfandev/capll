#ifndef FIRMWARE_MEMORY_MANAGER_H
#define FIRMWARE_MEMORY_MANAGER_H

#include "types.h"
#include <vector>

namespace firmware {

class MemoryManager {
public:
    MemoryManager();

    // Initialization and training
    Status initialize_ddr();
    Status run_ddr_training();
    Status enable_ecc();

    // Memory operations
    Status write_memory(uint64 address, const uint8* data, uint64 size);
    Status read_memory(uint64 address, uint8* buffer, uint64 size);
    Status memory_stress_test();

    // Fault injection
    void inject_single_bit_error(uint64 address);
    void inject_double_bit_error(uint64 address);
    void inject_training_failure();
    void clear_injected_errors();

    // Memory info
    MemoryInfo get_memory_info() const;
    uint32 get_ecc_error_count() const;

    // Memory test results
    std::vector<std::string> get_test_results() const;

private:
    MemoryInfo memory_info_;
    std::vector<uint8> memory_buffer_;
    uint32 ecc_errors_;
    std::vector<std::string> test_results_;

    // Injected faults
    bool training_failure_;
    std::vector<uint64> single_bit_error_addresses_;
    std::vector<uint64> double_bit_error_addresses_;
};

} // namespace firmware

#endif // FIRMWARE_MEMORY_MANAGER_H
