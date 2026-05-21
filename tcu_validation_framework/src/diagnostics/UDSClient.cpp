/**
 * @file UDSClient.cpp
 * @brief ISO 14229 UDS Client over ISO-TP (software framing on raw SocketCAN).
 *
 * ISO-TP framing (ISO 15765-2):
 *   Single Frame (SF): DLC[0] bits 7:4 = 0x0, bits 3:0 = length
 *   First Frame (FF):  DLC[0] bits 7:4 = 0x1, DLC[1] = lower length
 *   Consecutive Frame: DLC[0] bits 7:4 = 0x2, bits 3:0 = seq. number
 *   Flow Control (FC): DLC[0] bits 7:4 = 0x3
 */

#include "diagnostics/UDSClient.h"
#include "can/CANManager.h"
#include "logging/Logger.h"

#include <algorithm>
#include <chrono>
#include <cstring>
#include <thread>
#include <sstream>
#include <iomanip>

namespace tcu::diagnostics {

static auto s_log = tcu::logging::Logger::get("uds");

// ============================================================
// Helpers
// ============================================================

static std::string hex_dump(const std::vector<uint8_t>& data) {
    std::ostringstream oss;
    for (auto b : data) {
        oss << std::hex << std::uppercase << std::setw(2) << std::setfill('0')
            << static_cast<int>(b) << " ";
    }
    return oss.str();
}

static bool is_positive_response(const std::vector<uint8_t>& resp, uint8_t service_id) {
    return !resp.empty() && resp[0] == (service_id | 0x40U);
}

static bool is_negative_response(const std::vector<uint8_t>& resp) {
    return resp.size() >= 3 && resp[0] == 0x7F;
}

// ============================================================
// Construction
// ============================================================

UDSClient::UDSClient(std::shared_ptr<tcu::can::CANManager> can_mgr,
                     const ISOTPConfig& istp_cfg)
    : m_can(std::move(can_mgr))
    , m_istp(istp_cfg)
{
    // Register Rx callback to capture ECU responses
    m_rx_callback_handle = m_can->register_rx_callback(
        [this](const tcu::can::CANFrame& frame) {
            if (frame.id == m_istp.rx_id && frame.dlc > 0) {
                std::lock_guard<std::mutex> lock(m_rx_mutex);
                // Append raw CAN data to Rx buffer
                for (uint8_t i = 0; i < frame.dlc; ++i) {
                    m_rx_buffer.push_back(frame.data[i]);
                }
            }
        }
    );
}

UDSClient::~UDSClient() {
    if (m_session_open) { close_session(); }
    if (m_can) { m_can->unregister_callback(m_rx_callback_handle); }
}

// ============================================================
// Session management
// ============================================================

UDSResult UDSClient::open_session(UDSSession session) {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::DiagnosticSessionControl),
        static_cast<uint8_t>(session)
    };
    auto result = send_and_receive(req);
    if (result.success) {
        m_session_open     = true;
        m_current_session  = session;
        s_log->info("UDS session opened: {}", static_cast<int>(session));
    } else {
        s_log->error("Failed to open session {}: {}", static_cast<int>(session),
                     result.error_message);
    }
    return result;
}

void UDSClient::close_session() {
    tester_present(false);  // Send final TesterPresent without suppress
    open_session(UDSSession::Default);
    m_session_open = false;
}

UDSResult UDSClient::tester_present(bool suppress_response) {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::TesterPresent),
        static_cast<uint8_t>(suppress_response ? 0x80 : 0x00)
    };
    if (suppress_response) {
        // Send without waiting for response
        send_isotp(req);
        return {true};
    }
    return send_and_receive(req);
}

// ============================================================
// Core services
// ============================================================

UDSResult UDSClient::ecu_reset(ECUResetType type) {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::ECUReset),
        static_cast<uint8_t>(type)
    };
    auto result = send_and_receive(req);
    if (result.success) {
        s_log->info("ECU reset sent (type={:#04x})", static_cast<int>(type));
        // Wait for ECU to restart
        std::this_thread::sleep_for(std::chrono::milliseconds(2000));
    }
    return result;
}

UDSResult UDSClient::read_data_by_id(uint16_t did) {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::ReadDataById),
        static_cast<uint8_t>((did >> 8) & 0xFF),
        static_cast<uint8_t>(did & 0xFF)
    };
    auto result = send_and_receive(req);
    if (result.success) {
        s_log->debug("ReadDataById DID={:#06x}: {}", did, hex_dump(result.payload));
    }
    return result;
}

UDSResult UDSClient::write_data_by_id(uint16_t did, const std::vector<uint8_t>& data) {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::WriteDataById),
        static_cast<uint8_t>((did >> 8) & 0xFF),
        static_cast<uint8_t>(did & 0xFF)
    };
    req.insert(req.end(), data.begin(), data.end());
    return send_and_receive(req);
}

// ============================================================
// Security access
// ============================================================

UDSResult UDSClient::security_access(uint8_t level, SeedKeyAlgorithm algorithm) {
    // Step 1: Request seed (odd level)
    uint8_t seed_level = (level % 2 == 0) ? (level - 1) : level;
    std::vector<uint8_t> seed_req = {
        static_cast<uint8_t>(UDSService::SecurityAccess),
        seed_level
    };
    auto seed_result = send_and_receive(seed_req);
    if (!seed_result.success) {
        s_log->error("SecurityAccess: seed request failed");
        return seed_result;
    }

    // Extract seed from response (skip service ID + sub-function byte)
    std::vector<uint8_t> seed(seed_result.payload.begin() + 2,
                               seed_result.payload.end());
    s_log->debug("SecurityAccess seed: {}", hex_dump(seed));

    // Step 2: Calculate key
    auto key = algorithm(seed);
    s_log->debug("SecurityAccess key:  {}", hex_dump(key));

    // Step 3: Send key (even level)
    uint8_t key_level = (seed_level % 2 == 0) ? seed_level : (seed_level + 1);
    std::vector<uint8_t> key_req = {
        static_cast<uint8_t>(UDSService::SecurityAccess),
        key_level
    };
    key_req.insert(key_req.end(), key.begin(), key.end());

    return send_and_receive(key_req);
}

// ============================================================
// DTC services
// ============================================================

std::vector<DTCRecord> UDSClient::read_dtcs() {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::ReadDTC),
        0x02,   // reportDTCByStatusMask sub-function
        0xFF    // all status bits
    };
    auto result = send_and_receive(req);
    std::vector<DTCRecord> dtcs;

    if (!result.success || result.payload.size() < 3) {
        return dtcs;
    }

    // payload[0] = 0x59 (positive response), [1] = sub-function, [2] = status mask
    // Each DTC record = 3 bytes DTC + 1 byte status
    size_t idx = 3;
    while (idx + 3 < result.payload.size()) {
        DTCRecord rec;
        rec.dtc_id = (static_cast<uint32_t>(result.payload[idx])     << 16)
                   | (static_cast<uint32_t>(result.payload[idx + 1]) <<  8)
                   |  static_cast<uint32_t>(result.payload[idx + 2]);
        rec.status_byte = result.payload[idx + 3];

        // Decode status bits
        std::string status;
        if (rec.status_byte & 0x01) status += "TestFailed|";
        if (rec.status_byte & 0x08) status += "ConfirmedDTC|";
        if (rec.status_byte & 0x20) status += "PendingDTC|";
        if (!status.empty()) status.pop_back();
        rec.status_text = status;

        dtcs.push_back(rec);
        idx += 4;
    }

    s_log->info("ReadDTCs: found {} records", dtcs.size());
    return dtcs;
}

UDSResult UDSClient::clear_dtcs() {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::ClearDTC),
        0xFF, 0xFF, 0xFF  // clearAll group
    };
    return send_and_receive(req);
}

UDSResult UDSClient::control_dtc_setting(bool enable) {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::ControlDTCSetting),
        static_cast<uint8_t>(enable ? 0x01 : 0x02)
    };
    return send_and_receive(req);
}

// ============================================================
// Routine control
// ============================================================

UDSResult UDSClient::routine_control_start(uint16_t routine_id,
                                            const std::vector<uint8_t>& params) {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::RoutineControl),
        0x01,  // startRoutine
        static_cast<uint8_t>((routine_id >> 8) & 0xFF),
        static_cast<uint8_t>(routine_id & 0xFF)
    };
    req.insert(req.end(), params.begin(), params.end());
    return send_and_receive(req);
}

UDSResult UDSClient::routine_control_stop(uint16_t routine_id) {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::RoutineControl),
        0x02,  // stopRoutine
        static_cast<uint8_t>((routine_id >> 8) & 0xFF),
        static_cast<uint8_t>(routine_id & 0xFF)
    };
    return send_and_receive(req);
}

UDSResult UDSClient::routine_control_result(uint16_t routine_id) {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::RoutineControl),
        0x03,  // requestRoutineResults
        static_cast<uint8_t>((routine_id >> 8) & 0xFF),
        static_cast<uint8_t>(routine_id & 0xFF)
    };
    return send_and_receive(req);
}

// ============================================================
// Download services
// ============================================================

std::optional<size_t> UDSClient::request_download(uint32_t address, uint32_t size,
                                                    uint8_t compression_method,
                                                    uint8_t encrypting_method) {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::RequestDownload),
        static_cast<uint8_t>((compression_method << 4) | encrypting_method),
        0x44,  // addressAndLengthFormat: 4 bytes address, 4 bytes size
        // Memory address (big-endian 4 bytes)
        static_cast<uint8_t>((address >> 24) & 0xFF),
        static_cast<uint8_t>((address >> 16) & 0xFF),
        static_cast<uint8_t>((address >>  8) & 0xFF),
        static_cast<uint8_t>( address        & 0xFF),
        // Memory size (big-endian 4 bytes)
        static_cast<uint8_t>((size >> 24) & 0xFF),
        static_cast<uint8_t>((size >> 16) & 0xFF),
        static_cast<uint8_t>((size >>  8) & 0xFF),
        static_cast<uint8_t>( size        & 0xFF),
    };

    auto result = send_and_receive(req);
    if (!result.success || result.payload.size() < 3) {
        return std::nullopt;
    }

    // Extract maxBlockLen from response payload
    // Byte[0]=0x74, Byte[1]=lengthFormatIdentifier, Bytes[2..n]=maxBlockLen
    uint8_t len_format = result.payload[1];
    uint8_t block_len_size = (len_format >> 4) & 0x0F;
    size_t max_block_len = 0;
    for (uint8_t i = 0; i < block_len_size && (2 + i) < result.payload.size(); ++i) {
        max_block_len = (max_block_len << 8) | result.payload[2 + i];
    }

    s_log->info("RequestDownload: address={:#010x} size={} maxBlockLen={}",
                address, size, max_block_len);
    return max_block_len;
}

UDSResult UDSClient::transfer_data(uint8_t block_seq,
                                    const std::vector<uint8_t>& data) {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::TransferData),
        block_seq
    };
    req.insert(req.end(), data.begin(), data.end());
    return send_and_receive(req);
}

UDSResult UDSClient::request_transfer_exit() {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::RequestTransferExit)
    };
    return send_and_receive(req);
}

// ============================================================
// Communication control
// ============================================================

UDSResult UDSClient::communication_control(uint8_t control_type, uint8_t comm_type) {
    std::vector<uint8_t> req = {
        static_cast<uint8_t>(UDSService::CommunicationControl),
        control_type,
        comm_type
    };
    return send_and_receive(req);
}

// ============================================================
// Raw service
// ============================================================

UDSResult UDSClient::send_raw(const std::vector<uint8_t>& request) {
    return send_and_receive(request);
}

// ============================================================
// Internal: send/receive with ISO-TP + P2/P2* timer handling
// ============================================================

UDSResult UDSClient::send_and_receive(const std::vector<uint8_t>& request) {
    {
        std::lock_guard<std::mutex> lock(m_rx_mutex);
        m_rx_buffer.clear();
    }

    s_log->trace("UDS Tx: {}", hex_dump(request));

    if (!send_isotp(request)) {
        return {false, request[0], NRC::ServiceNotSupported, {}, "ISO-TP send failed"};
    }

    // Wait for response with P2 timer
    auto response = receive_isotp(m_istp.p2_timeout_ms);

    // Handle NRC 0x78 (responsePending) — extend to P2*
    while (response && response->size() >= 3 &&
           (*response)[0] == 0x7F && (*response)[2] == 0x78) {
        s_log->debug("NRC 0x78 (responsePending) — waiting P2* = {} ms",
                     m_istp.p2_star_ms);
        response = receive_isotp(m_istp.p2_star_ms);
    }

    if (!response || response->empty()) {
        s_log->warn("UDS timeout waiting for response to service {:#04x}", request[0]);
        return {false, request[0], NRC::ServiceNotSupported, {}, "Timeout"};
    }

    s_log->trace("UDS Rx: {}", hex_dump(*response));

    UDSResult result;
    result.service_id = request[0];
    result.payload    = *response;

    if (is_positive_response(*response, request[0])) {
        result.success = true;
    } else if (is_negative_response(*response)) {
        result.success        = false;
        result.nrc            = static_cast<NRC>((*response)[2]);
        result.error_message  = "NRC: " + std::to_string(static_cast<int>((*response)[2]));
        s_log->warn("UDS NRC {:#04x} for service {:#04x}",
                    static_cast<int>((*response)[2]), request[0]);
    } else {
        result.success = false;
        result.error_message = "Unexpected response";
    }

    return result;
}

// ============================================================
// ISO-TP framing (simplified — single/multi frame)
// ============================================================

bool UDSClient::send_isotp(const std::vector<uint8_t>& data) {
    if (data.empty()) { return false; }

    if (data.size() <= 7) {
        // Single Frame
        tcu::can::CANFrame frame;
        frame.id  = m_istp.tx_id;
        frame.dlc = static_cast<uint8_t>(data.size() + 1);
        frame.data[0] = static_cast<uint8_t>(data.size() & 0x0F);  // PCI: SF, length
        for (size_t i = 0; i < data.size(); ++i) {
            frame.data[i + 1] = data[i];
        }
        return m_can->transmit(frame);
    }

    // Multi-frame: First Frame
    tcu::can::CANFrame ff;
    ff.id    = m_istp.tx_id;
    ff.dlc   = 8;
    ff.data[0] = static_cast<uint8_t>(0x10 | ((data.size() >> 8) & 0x0F));
    ff.data[1] = static_cast<uint8_t>(data.size() & 0xFF);
    for (int i = 0; i < 6; ++i) {
        ff.data[2 + i] = data[static_cast<size_t>(i)];
    }
    if (!m_can->transmit(ff)) { return false; }

    // Wait for Flow Control
    auto fc = receive_isotp(m_istp.p2_timeout_ms);
    if (!fc || fc->empty()) {
        s_log->error("No Flow Control received");
        return false;
    }

    // Consecutive Frames
    size_t sent = 6;
    uint8_t seq = 1;
    while (sent < data.size()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(m_istp.st_min_ms));
        tcu::can::CANFrame cf;
        cf.id    = m_istp.tx_id;
        cf.dlc   = 8;
        cf.data[0] = static_cast<uint8_t>(0x20 | (seq & 0x0F));
        for (int i = 0; i < 7 && sent < data.size(); ++i, ++sent) {
            cf.data[1 + i] = data[sent];
        }
        if (!m_can->transmit(cf)) { return false; }
        seq = (seq + 1) & 0x0F;
    }
    return true;
}

std::optional<std::vector<uint8_t>> UDSClient::receive_isotp(uint32_t timeout_ms) {
    auto deadline = std::chrono::steady_clock::now() +
                    std::chrono::milliseconds(timeout_ms);

    while (std::chrono::steady_clock::now() < deadline) {
        {
            std::lock_guard<std::mutex> lock(m_rx_mutex);
            if (!m_rx_buffer.empty()) {
                uint8_t pci = m_rx_buffer[0];
                uint8_t frame_type = (pci >> 4) & 0x0F;

                if (frame_type == 0x00) {
                    // Single Frame
                    uint8_t len = pci & 0x0F;
                    if (m_rx_buffer.size() >= static_cast<size_t>(len + 1)) {
                        std::vector<uint8_t> payload(m_rx_buffer.begin() + 1,
                                                      m_rx_buffer.begin() + 1 + len);
                        m_rx_buffer.clear();
                        return payload;
                    }
                } else if (frame_type == 0x01) {
                    // First Frame — multi-frame response
                    uint16_t total_len = static_cast<uint16_t>(((pci & 0x0F) << 8) | m_rx_buffer[1]);
                    // Send FC
                    send_flow_control(0x00, 0, m_istp.st_min_ms);
                    // Accumulate all data until total_len bytes collected
                    std::vector<uint8_t> payload(m_rx_buffer.begin() + 2,
                                                  m_rx_buffer.end());
                    m_rx_buffer.clear();

                    // Wait for consecutive frames
                    auto cf_deadline = std::chrono::steady_clock::now() +
                                       std::chrono::milliseconds(timeout_ms);
                    while (payload.size() < total_len &&
                           std::chrono::steady_clock::now() < cf_deadline) {
                        std::this_thread::sleep_for(std::chrono::milliseconds(1));
                        std::lock_guard<std::mutex> cl(m_rx_mutex);
                        if (!m_rx_buffer.empty()) {
                            // Consecutive frame: skip PCI byte (0x2x)
                            payload.insert(payload.end(),
                                           m_rx_buffer.begin() + 1,
                                           m_rx_buffer.end());
                            m_rx_buffer.clear();
                        }
                    }
                    payload.resize(total_len);
                    return payload;
                }
            }
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    return std::nullopt;
}

void UDSClient::send_flow_control(uint8_t flow_status,
                                   uint8_t block_size,
                                   uint8_t st_min) {
    tcu::can::CANFrame fc;
    fc.id    = m_istp.tx_id;
    fc.dlc   = 3;
    fc.data[0] = static_cast<uint8_t>(0x30 | (flow_status & 0x0F));
    fc.data[1] = block_size;
    fc.data[2] = st_min;
    m_can->transmit(fc);
}

void UDSClient::set_istp_config(const ISOTPConfig& cfg) { m_istp = cfg; }
const ISOTPConfig& UDSClient::istp_config() const noexcept { return m_istp; }

} // namespace tcu::diagnostics
