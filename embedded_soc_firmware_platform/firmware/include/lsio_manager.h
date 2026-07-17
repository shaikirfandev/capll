#ifndef FIRMWARE_LSIO_MANAGER_H
#define FIRMWARE_LSIO_MANAGER_H

#include "types.h"
#include <vector>

namespace firmware {

class GPIOManager {
public:
    Status set_gpio(uint32 pin, uint8 value);
    Status get_gpio(uint32 pin, uint8& value);
    Status configure_interrupt(uint32 pin);
    Status handle_interrupt(uint32 pin);
private:
    std::vector<uint8> gpio_state_;
};

class I2CManager {
public:
    Status write_byte(uint8 addr, uint8 reg, uint8 value);
    Status read_byte(uint8 addr, uint8 reg, uint8& value);
    Status write_buffer(uint8 addr, const std::vector<uint8>& data);
    Status read_buffer(uint8 addr, std::vector<uint8>& data, uint32 length);
private:
    std::map<uint8, std::map<uint8, uint8>> i2c_devices_;  // addr -> (reg -> value)
};

class SPIManager {
public:
    Status transfer(const std::vector<uint8>& tx_data, std::vector<uint8>& rx_data);
    Status configure_clock(uint32 clock_hz);
    Status select_chip(uint32 chip_select);
private:
    uint32 clock_rate_;
    uint32 current_chip_select_;
    std::vector<uint8> spi_buffer_;
};

class UARTManager {
public:
    Status configure(uint32 baud_rate, uint8 data_bits, uint8 stop_bits);
    Status write_data(const std::vector<uint8>& data);
    Status read_data(std::vector<uint8>& data, uint32 length);
    Status send_string(const std::string& str);
    std::string read_string(uint32 max_length);
private:
    uint32 baud_rate_;
    std::string uart_buffer_;
};

class LSIOManager {
public:
    LSIOManager();

    // GPIO operations
    Status gpio_set(uint32 pin, uint8 value);
    Status gpio_get(uint32 pin, uint8& value);

    // I2C operations
    Status i2c_write(uint8 addr, uint8 reg, uint8 value);
    Status i2c_read(uint8 addr, uint8 reg, uint8& value);

    // SPI operations
    Status spi_transfer(const std::vector<uint8>& tx_data, std::vector<uint8>& rx_data);

    // UART operations
    Status uart_configure(uint32 baud_rate);
    Status uart_send(const std::string& data);
    std::string uart_receive();

    // Error injection
    void inject_protocol_error(const std::string& interface);
    void inject_timeout(const std::string& interface);
    void clear_injected_errors();

private:
    GPIOManager gpio_;
    I2CManager i2c_;
    SPIManager spi_;
    UARTManager uart_;

    // Injected errors
    std::map<std::string, bool> protocol_errors_;
    std::map<std::string, bool> timeouts_;
};

} // namespace firmware

#endif // FIRMWARE_LSIO_MANAGER_H
