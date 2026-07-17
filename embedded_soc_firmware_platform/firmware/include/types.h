#ifndef FIRMWARE_TYPES_H
#define FIRMWARE_TYPES_H

#include <cstdint>
#include <chrono>
#include <string>
#include <map>
#include <vector>
#include <queue>

namespace firmware {

// Basic types
using uint8  = uint8_t;
using uint16 = uint16_t;
using uint32 = uint32_t;
using uint64 = uint64_t;
using int8   = int8_t;
using int16  = int16_t;
using int32  = int32_t;
using int64  = int64_t;

// Status codes
enum class Status {
    SUCCESS                    = 0x00,
    FAILURE                    = 0x01,
    TIMEOUT                    = 0x02,
    INVALID_PARAM              = 0x03,
    NOT_SUPPORTED              = 0x04,
    INSUFFICIENT_RESOURCES     = 0x05,
    DEVICE_ERROR               = 0x06,
    AUTHENTICATION_FAILURE     = 0x07,
    CRC_ERROR                  = 0x08,
    FIRMWARE_CORRUPTED         = 0x09,
};

// Boot states
enum class BootState {
    POWER_OFF = 0,
    POWER_ON,
    SEC_PHASE,              // Security phase
    PEI_PHASE,              // Pre-EFI Initialization
    DXE_PHASE,              // Driver Execution Environment
    BDS_PHASE,              // Boot Device Selection
    OS_LOADER,              // OS Loader
    RECOVERY_MODE,
    ERROR_STATE,
};

// Power states
enum class PowerState {
    S0 = 0,  // Working
    S1 = 1,  // Sleep with CPU running
    S3 = 3,  // Sleep
    S4 = 4,  // Hibernation
    S5 = 5,  // Soft Off
    S6 = 6,  // Hard Off
};

// PCIe generations
enum class PCIeGen {
    GEN1 = 1,  // 2.5 GT/s
    GEN2 = 2,  // 5.0 GT/s
    GEN3 = 3,  // 8.0 GT/s
    GEN4 = 4,  // 16.0 GT/s
};

// USB standards
enum class USBStandard {
    USB2 = 2,
    USB3 = 3,
};

// Temperature thresholds
struct TemperatureThresholds {
    int32 warning_temp_c;     // Warning threshold in Celsius
    int32 critical_temp_c;    // Critical threshold
    int32 shutdown_temp_c;    // Shutdown threshold
};

// Memory characteristics
struct MemoryInfo {
    uint64 total_size;
    uint64 available_size;
    uint32 ecc_enabled;
    uint32 ddr_type;         // DDR3, DDR4, DDR5
    uint32 ddr_speed_mhz;
};

// Event types for logging
enum class EventType {
    BOOT_START,
    BOOT_PHASE_ENTRY,
    BOOT_PHASE_EXIT,
    POWER_STATE_CHANGE,
    MEMORY_INIT,
    SECURITY_CHECK,
    DEVICE_ENUMERATION,
    ERROR_DETECTED,
    RECOVERY_START,
    SYSTEM_SHUTDOWN,
    HEALTH_STATUS,
};

// Timestamp
using Timestamp = std::chrono::high_resolution_clock::time_point;

// Device info
struct DeviceInfo {
    std::string vendor_id;
    std::string device_id;
    std::string name;
    uint32 bus;
    uint32 slot;
    uint32 function;
    PowerState power_state;
    Status status;
};

// Boot metrics
struct BootMetrics {
    Timestamp boot_start_time;
    Timestamp sec_phase_start;
    Timestamp pei_phase_start;
    Timestamp dxe_phase_start;
    Timestamp bds_phase_start;
    Timestamp os_load_start;
    uint32 total_boot_time_ms;
    uint32 sec_phase_time_ms;
    uint32 pei_phase_time_ms;
    uint32 dxe_phase_time_ms;
    uint32 bds_phase_time_ms;
    uint32 os_load_time_ms;
    bool boot_successful;
    std::string failure_reason;
};

// Power metrics
struct PowerMetrics {
    Timestamp state_change_time;
    PowerState previous_state;
    PowerState current_state;
    uint32 transition_time_ms;
    uint32 wake_latency_ms;
    bool transition_successful;
};

// Security event
struct SecurityEvent {
    std::string event_type;
    std::string description;
    Timestamp timestamp;
    Status result;
    std::string details;
};

// Health status
struct HealthStatus {
    int32 cpu_temp_c;
    uint32 memory_usage_percent;
    uint32 pcie_devices_healthy;
    uint32 usb_devices_healthy;
    uint32 security_status_ok;
    std::string overall_status;
};

} // namespace firmware

#endif // FIRMWARE_TYPES_H
