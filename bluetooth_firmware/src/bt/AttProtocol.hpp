/**
 * @file AttProtocol.hpp
 */
#pragma once
#include "bt/BluetoothTypes.hpp"
namespace bt {
class AttProtocol {
public:
    struct DecodedPdu {
        uint8_t  opcode{0};
        AttHandle handle{INVALID_ATT_HANDLE};
        uint16_t mtu{0};
        uint8_t  error_code{0};
        std::vector<uint8_t> value;
        bool valid{false};
    };
    static std::vector<uint8_t> encode_mtu_request(uint16_t client_mtu);
    static std::vector<uint8_t> encode_mtu_response(uint16_t server_mtu);
    static std::vector<uint8_t> encode_read_request(AttHandle handle);
    static std::vector<uint8_t> encode_write_request(AttHandle handle, const uint8_t *value, uint16_t len);
    static std::vector<uint8_t> encode_notification(AttHandle handle, const uint8_t *value, uint16_t len);
    static DecodedPdu           decode(const uint8_t *data, uint16_t len);
};
}
