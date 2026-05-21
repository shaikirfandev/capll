/**
 * @file RfcommSimulator.hpp
 */
#pragma once
#include "bt/BluetoothTypes.hpp"
#include <memory>
#include <optional>
#include <vector>
namespace bt {
class RfcommSimulator {
public:
    RfcommSimulator();
    ~RfcommSimulator();
    BtError open_mux(ConnHandle conn);
    BtError open_dlci(uint8_t dlci);
    BtError send(uint8_t dlci, const uint8_t *data, uint16_t len);
    void    inject_rx(const uint8_t *data, uint16_t len);  // Test hook
    std::optional<std::vector<uint8_t>> receive();
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
