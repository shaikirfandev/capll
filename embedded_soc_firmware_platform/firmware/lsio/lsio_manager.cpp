#include "lsio_manager.h"
#include "logger.h"

namespace firmware {

// GPIO Implementation
Status GPIOManager::set_gpio(uint32 pin, uint8 value) {
    if (pin >= gpio_state_.size()) {
        gpio_state_.resize(pin + 1, 0);
    }
    gpio_state_[pin] = value;
    return Status::SUCCESS;
}

Status GPIOManager::get_gpio(uint32 pin, uint8& value) {
    if (pin >= gpio_state_.size()) {
        return Status::FAILURE;
    }
    value = gpio_state_[pin];
    return Status::SUCCESS;
}

Status GPIOManager::configure_interrupt(uint32 pin) {
    return Status::SUCCESS;
}

Status GPIOManager::handle_interrupt(uint32 pin) {
    return Status::SUCCESS;
}

// I2C Implementation
Status I2CManager::write_byte(uint8 addr, uint8 reg, uint8 value) {
    if (i2c_devices_.find(addr) == i2c_devices_.end()) {
        i2c_devices_[addr] = std::map<uint8, uint8>();
    }
    i2c_devices_[addr][reg] = value;
    return Status::SUCCESS;
}

Status I2CManager::read_byte(uint8 addr, uint8 reg, uint8& value) {
    if (i2c_devices_.find(addr) == i2c_devices_.end() ||
        i2c_devices_[addr].find(reg) == i2c_devices_[addr].end()) {
        return Status::FAILURE;
    }
    value = i2c_devices_[addr][reg];
    return Status::SUCCESS;
}

Status I2CManager::write_buffer(uint8 addr, const std::vector<uint8>& data) {
    for (size_t i = 0; i < data.size(); ++i) {
        write_byte(addr, i, data[i]);
    }
    return Status::SUCCESS;
}

Status I2CManager::read_buffer(uint8 addr, std::vector<uint8>& data, uint32 length) {
    data.clear();
    for (uint32 i = 0; i < length; ++i) {
        uint8 value = 0;
        read_byte(addr, i, value);
        data.push_back(value);
    }
    return Status::SUCCESS;
}

// SPI Implementation
Status SPIManager::transfer(const std::vector<uint8>& tx_data, std::vector<uint8>& rx_data) {
    rx_data = tx_data;  // Echo back for simulation
    return Status::SUCCESS;
}

Status SPIManager::configure_clock(uint32 clock_hz) {
    clock_rate_ = clock_hz;
    return Status::SUCCESS;
}

Status SPIManager::select_chip(uint32 chip_select) {
    current_chip_select_ = chip_select;
    return Status::SUCCESS;
}

// UART Implementation
Status UARTManager::configure(uint32 baud_rate, uint8 data_bits, uint8 stop_bits) {
    baud_rate_ = baud_rate;
    return Status::SUCCESS;
}

Status UARTManager::write_data(const std::vector<uint8>& data) {
    for (auto byte : data) {
        uart_buffer_ += static_cast<char>(byte);
    }
    return Status::SUCCESS;
}

Status UARTManager::read_data(std::vector<uint8>& data, uint32 length) {
    data.clear();
    for (uint32 i = 0; i < length && i < uart_buffer_.length(); ++i) {
        data.push_back(static_cast<uint8>(uart_buffer_[i]));
    }
    uart_buffer_.clear();
    return Status::SUCCESS;
}

Status UARTManager::send_string(const std::string& str) {
    uart_buffer_ = str;
    return Status::SUCCESS;
}

std::string UARTManager::read_string(uint32 max_length) {
    std::string result = uart_buffer_.substr(0, max_length);
    uart_buffer_.clear();
    return result;
}

// LSIOManager Implementation
LSIOManager::LSIOManager() {
}

Status LSIOManager::gpio_set(uint32 pin, uint8 value) {
    LOG_DEBUG("LSIOManager", "GPIO SET pin=" + std::to_string(pin) + " value=" + std::to_string(value));
    return gpio_.set_gpio(pin, value);
}

Status LSIOManager::gpio_get(uint32 pin, uint8& value) {
    LOG_DEBUG("LSIOManager", "GPIO GET pin=" + std::to_string(pin));
    return gpio_.get_gpio(pin, value);
}

Status LSIOManager::i2c_write(uint8 addr, uint8 reg, uint8 value) {
    LOG_DEBUG("LSIOManager", "I2C WRITE addr=0x" + std::to_string(addr) + 
              " reg=0x" + std::to_string(reg) + " value=0x" + std::to_string(value));
    
    if (protocol_errors_.find("i2c") != protocol_errors_.end() && protocol_errors_["i2c"]) {
        return Status::DEVICE_ERROR;
    }
    
    return i2c_.write_byte(addr, reg, value);
}

Status LSIOManager::i2c_read(uint8 addr, uint8 reg, uint8& value) {
    LOG_DEBUG("LSIOManager", "I2C READ addr=0x" + std::to_string(addr) + 
              " reg=0x" + std::to_string(reg));
    
    if (protocol_errors_.find("i2c") != protocol_errors_.end() && protocol_errors_["i2c"]) {
        return Status::DEVICE_ERROR;
    }
    
    return i2c_.read_byte(addr, reg, value);
}

Status LSIOManager::spi_transfer(const std::vector<uint8>& tx_data, std::vector<uint8>& rx_data) {
    LOG_DEBUG("LSIOManager", "SPI TRANSFER len=" + std::to_string(tx_data.size()));
    
    if (protocol_errors_.find("spi") != protocol_errors_.end() && protocol_errors_["spi"]) {
        return Status::DEVICE_ERROR;
    }
    
    return spi_.transfer(tx_data, rx_data);
}

Status LSIOManager::uart_configure(uint32 baud_rate) {
    LOG_DEBUG("LSIOManager", "UART CONFIGURE baud=" + std::to_string(baud_rate));
    return uart_.configure(baud_rate, 8, 1);
}

Status LSIOManager::uart_send(const std::string& data) {
    LOG_DEBUG("LSIOManager", "UART SEND data=" + data);
    
    if (timeouts_.find("uart") != timeouts_.end() && timeouts_["uart"]) {
        return Status::TIMEOUT;
    }
    
    std::vector<uint8> tx_data(data.begin(), data.end());
    return uart_.write_data(tx_data);
}

std::string LSIOManager::uart_receive() {
    LOG_DEBUG("LSIOManager", "UART RECEIVE");
    return uart_.read_string(256);
}

void LSIOManager::inject_protocol_error(const std::string& interface) {
    LOG_WARNING("LSIOManager", "Injecting protocol error on " + interface);
    protocol_errors_[interface] = true;
}

void LSIOManager::inject_timeout(const std::string& interface) {
    LOG_WARNING("LSIOManager", "Injecting timeout on " + interface);
    timeouts_[interface] = true;
}

void LSIOManager::clear_injected_errors() {
    LOG_INFO("LSIOManager", "Clearing all injected LSIO errors");
    protocol_errors_.clear();
    timeouts_.clear();
}

} // namespace firmware
