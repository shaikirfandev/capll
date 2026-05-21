/**
 * @file AttProtocol.cpp
 * @brief ATT Protocol PDU encoder/decoder
 * Handles ATT_MTU_REQ/RSP, ATT_READ_BY_TYPE_REQ/RSP, ATT_WRITE_REQ/RSP
 */

#include "bt/AttProtocol.hpp"
#include "common/Logger.hpp"
#include <cstring>

static constexpr const char *TAG = "ATT";

// ATT opcodes
static constexpr uint8_t ATT_ERROR_RSP           = 0x01U;
static constexpr uint8_t ATT_EXCHANGE_MTU_REQ    = 0x02U;
static constexpr uint8_t ATT_EXCHANGE_MTU_RSP    = 0x03U;
static constexpr uint8_t ATT_FIND_INFO_REQ       = 0x04U;
static constexpr uint8_t ATT_READ_BY_TYPE_REQ    = 0x08U;
static constexpr uint8_t ATT_READ_REQ            = 0x0AU;
static constexpr uint8_t ATT_READ_RSP            = 0x0BU;
static constexpr uint8_t ATT_WRITE_REQ           = 0x12U;
static constexpr uint8_t ATT_WRITE_RSP           = 0x13U;
static constexpr uint8_t ATT_HANDLE_VALUE_NTF    = 0x1BU;
static constexpr uint8_t ATT_HANDLE_VALUE_IND    = 0x1DU;
static constexpr uint8_t ATT_HANDLE_VALUE_CONF   = 0x1EU;

namespace bt {

std::vector<uint8_t> AttProtocol::encode_mtu_request(uint16_t client_mtu) {
    return {ATT_EXCHANGE_MTU_REQ,
            static_cast<uint8_t>(client_mtu & 0xFFU),
            static_cast<uint8_t>((client_mtu >> 8U) & 0xFFU)};
}

std::vector<uint8_t> AttProtocol::encode_mtu_response(uint16_t server_mtu) {
    return {ATT_EXCHANGE_MTU_RSP,
            static_cast<uint8_t>(server_mtu & 0xFFU),
            static_cast<uint8_t>((server_mtu >> 8U) & 0xFFU)};
}

std::vector<uint8_t> AttProtocol::encode_read_request(AttHandle handle) {
    return {ATT_READ_REQ,
            static_cast<uint8_t>(handle & 0xFFU),
            static_cast<uint8_t>((handle >> 8U) & 0xFFU)};
}

std::vector<uint8_t> AttProtocol::encode_write_request(AttHandle handle,
                                                          const uint8_t *value,
                                                          uint16_t len) {
    std::vector<uint8_t> pdu;
    pdu.reserve(3U + len);
    pdu.push_back(ATT_WRITE_REQ);
    pdu.push_back(static_cast<uint8_t>(handle & 0xFFU));
    pdu.push_back(static_cast<uint8_t>((handle >> 8U) & 0xFFU));
    pdu.insert(pdu.end(), value, value + len);
    return pdu;
}

std::vector<uint8_t> AttProtocol::encode_notification(AttHandle handle,
                                                         const uint8_t *value,
                                                         uint16_t len) {
    std::vector<uint8_t> pdu;
    pdu.reserve(3U + len);
    pdu.push_back(ATT_HANDLE_VALUE_NTF);
    pdu.push_back(static_cast<uint8_t>(handle & 0xFFU));
    pdu.push_back(static_cast<uint8_t>((handle >> 8U) & 0xFFU));
    pdu.insert(pdu.end(), value, value + len);
    return pdu;
}

AttProtocol::DecodedPdu AttProtocol::decode(const uint8_t *data, uint16_t len) {
    DecodedPdu result{};
    if (len < 1U) { result.valid = false; return result; }
    result.opcode = data[0];
    result.valid  = true;

    switch (result.opcode) {
        case ATT_EXCHANGE_MTU_REQ:
        case ATT_EXCHANGE_MTU_RSP:
            if (len >= 3U) {
                result.mtu = static_cast<uint16_t>(data[1] | (static_cast<uint16_t>(data[2]) << 8U));
            }
            break;
        case ATT_READ_REQ:
        case ATT_WRITE_REQ:
            if (len >= 3U) {
                result.handle = static_cast<uint16_t>(data[1] | (static_cast<uint16_t>(data[2]) << 8U));
                result.value.assign(data + 3U, data + len);
            }
            break;
        case ATT_HANDLE_VALUE_NTF:
        case ATT_HANDLE_VALUE_IND:
            if (len >= 3U) {
                result.handle = static_cast<uint16_t>(data[1] | (static_cast<uint16_t>(data[2]) << 8U));
                result.value.assign(data + 3U, data + len);
            }
            break;
        case ATT_ERROR_RSP:
            if (len >= 5U) {
                result.error_code = data[4];
            }
            break;
        default:
            BT_LOG_WARN(TAG, "Unknown ATT opcode: 0x{:02X}", result.opcode);
            break;
    }
    return result;
}

}  // namespace bt
