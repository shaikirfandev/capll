/**
 * @file SafetyTypes.hpp
 * @brief Safety-critical type definitions — DO-178C DAL-A/B
 */
#pragma once
#include <cstdint>
#include <array>

namespace fms::safety {

enum class FaultId : uint32_t {
    NONE               = 0x0000U,
    GPS_LOSS_OF_FIX    = 0x0001U,
    GPS_INTEGRITY_FAIL = 0x0002U,
    INS_ALIGN_FAIL     = 0x0010U,
    INS_EXCESSIVE_DRIFT = 0x0011U,
    ADC_PLAUSIBILITY   = 0x0020U,
    PITOT_HEAT_FAIL    = 0x0021U,
    NAV_RNP_EXCEEDED   = 0x0030U,
    FMS_NAV_DOWNGRADE  = 0x0031U,
    ARINC429_BUS_FAIL  = 0x0040U,
    ARINC429_PARITY    = 0x0041U,
    AFDX_LINK_FAIL     = 0x0050U,
    CAN_BUS_OFF        = 0x0060U,
    WATCHDOG_TIMEOUT   = 0x0070U,
    MEMORY_CHECKSUM    = 0x0080U,
    STACK_OVERFLOW     = 0x0081U,
    CPU_EXCEPTION      = 0x0082U,
    FUEL_IMBALANCE     = 0x0090U,
    FUEL_LOW           = 0x0091U,
    FP_INVALID         = 0x00A0U,
    VNAV_PATH_ERROR    = 0x00B0U,
};

enum class FaultSeverity : uint8_t {
    INFO     = 0U,
    ADVISORY = 1U,  // Log only
    CAUTION  = 2U,  // Alert crew, no immediate action
    WARNING  = 3U,  // Immediate crew action required
    CRITICAL = 4U,  // Shutdown affected function
};

enum class FaultState : uint8_t {
    INACTIVE = 0U,
    ACTIVE   = 1U,
    LATCHED  = 2U,   // Requires crew/maintenance reset
    INHIBITED = 3U,  // Ground test suppression
};

struct FaultRecord {
    FaultId      id{FaultId::NONE};
    FaultSeverity severity{FaultSeverity::INFO};
    FaultState   state{FaultState::INACTIVE};
    uint32_t     occurrence_count{0U};
    uint64_t     first_detected_us{0U};
    uint64_t     last_detected_us{0U};
    char         description[64]{};
};

static constexpr uint16_t MAX_FAULT_RECORDS = 64U;
static constexpr uint32_t WATCHDOG_TIMEOUT_MS = 500U;

}  // namespace fms::safety
