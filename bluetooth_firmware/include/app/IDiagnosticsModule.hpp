/**
 * @file IDiagnosticsModule.hpp
 * @brief Diagnostics and health monitoring interface
 */
#pragma once
#include "../bt/BluetoothTypes.hpp"
#include <string>
namespace bt::app {
struct BtHealthStats {
    uint64_t tx_bytes{0};
    uint64_t rx_bytes{0};
    uint32_t conn_count{0};
    uint32_t disconn_count{0};
    uint32_t pairing_failures{0};
    uint32_t hci_errors{0};
    uint32_t ota_attempts{0};
    uint32_t ota_success{0};
    int8_t   last_rssi{0};
    float    avg_conn_interval_ms{0.0F};
};

class IDiagnosticsModule {
public:
    virtual ~IDiagnosticsModule() = default;
    virtual const BtHealthStats &get_stats() const = 0;
    virtual void reset_stats() = 0;
    virtual std::string generate_report() const = 0;
    virtual void record_event(std::string_view component, std::string_view event) = 0;
};
}
