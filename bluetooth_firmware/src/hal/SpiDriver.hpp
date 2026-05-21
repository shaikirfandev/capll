/**
 * @file SpiDriver.hpp
 */
#pragma once
#include "hal/ISpi.hpp"
#include <memory>
namespace bt::hal {
class SpiDriver final : public ISpi {
public:
    SpiDriver(); ~SpiDriver() override;
    bool    init(const SpiConfig &cfg) override;
    void    deinit()                   override;
    int32_t transfer(const uint8_t *tx, uint8_t *rx, uint16_t len) override;
    int32_t write(const uint8_t *data, uint16_t len)                override;
    int32_t read(uint8_t *buf, uint16_t len)                        override;
    bool    set_freq(uint32_t hz)                                   override;
private:
    struct Impl; std::unique_ptr<Impl> impl_;
};
}
