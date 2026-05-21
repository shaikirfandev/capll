/**
 * @file IUart.hpp
 * @brief Pure abstract UART interface for the HAL layer
 */
#pragma once
#include <cstdint>
#include <functional>

namespace bt::hal {

using UartRxCb = std::function<void(const uint8_t *data, uint16_t len)>;

enum class UartParity  : uint8_t { NONE, EVEN, ODD };
enum class UartStopBit : uint8_t { ONE, ONE_HALF, TWO };

struct UartConfig {
    uint32_t   baud_rate{115200U};
    uint8_t    data_bits{8U};
    UartParity parity{UartParity::NONE};
    UartStopBit stop_bits{UartStopBit::ONE};
    bool       flow_control{true};  // HW RTS/CTS for HCI H4
};

class IUart {
public:
    virtual ~IUart() = default;
    virtual bool    init(const UartConfig &cfg) = 0;
    virtual void    deinit() = 0;
    virtual int32_t send(const uint8_t *data, uint16_t len) = 0;
    virtual int32_t receive(uint8_t *buf, uint16_t max_len, uint32_t timeout_ms) = 0;
    virtual void    set_rx_callback(UartRxCb cb) = 0;
    virtual bool    set_baud_rate(uint32_t baud) = 0;
    virtual void    flush() = 0;
};

}  // namespace bt::hal
