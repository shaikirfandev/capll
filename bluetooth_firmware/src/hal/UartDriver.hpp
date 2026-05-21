/**
 * @file UartDriver.hpp
 */
#pragma once
#include "hal/IUart.hpp"
#include <memory>
namespace bt::hal {
class UartDriver final : public IUart {
public:
    UartDriver();
    ~UartDriver() override;
    bool    init(const UartConfig &cfg)                                    override;
    void    deinit()                                                       override;
    int32_t send(const uint8_t *data, uint16_t len)                        override;
    int32_t receive(uint8_t *buf, uint16_t max_len, uint32_t timeout_ms)   override;
    void    set_rx_callback(UartRxCb cb)                                   override;
    bool    set_baud_rate(uint32_t baud)                                   override;
    void    flush()                                                        override;
    void    inject_rx(const uint8_t *data, uint16_t len);  // Test hook
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
