/**
 * @file ISpi.hpp
 * @brief Pure abstract SPI interface
 */
#pragma once
#include <cstdint>
namespace bt::hal {
enum class SpiMode : uint8_t { MODE_0=0, MODE_1=1, MODE_2=2, MODE_3=3 };
struct SpiConfig { uint32_t freq_hz{4'000'000U}; SpiMode mode{SpiMode::MODE_0}; uint8_t bits_per_word{8U}; bool lsb_first{false}; };
class ISpi {
public:
    virtual ~ISpi() = default;
    virtual bool    init(const SpiConfig &cfg) = 0;
    virtual void    deinit() = 0;
    virtual int32_t transfer(const uint8_t *tx, uint8_t *rx, uint16_t len) = 0;
    virtual int32_t write(const uint8_t *data, uint16_t len) = 0;
    virtual int32_t read(uint8_t *buf, uint16_t len) = 0;
    virtual bool    set_freq(uint32_t hz) = 0;
};
}
