/**
 * @file UDSClient.h
 * @brief ISO 14229 UDS (Unified Diagnostic Services) client over SocketCAN.
 *
 * Implements the full UDS service set:
 *   - 0x10 DiagnosticSessionControl
 *   - 0x11 ECUReset
 *   - 0x14 ClearDiagnosticInformation
 *   - 0x19 ReadDTCInformation
 *   - 0x22 ReadDataByIdentifier
 *   - 0x27 SecurityAccess (seed-key)
 *   - 0x28 CommunicationControl
 *   - 0x2E WriteDataByIdentifier
 *   - 0x31 RoutineControl
 *   - 0x34 RequestDownload
 *   - 0x36 TransferData
 *   - 0x37 RequestTransferExit
 *   - 0x3E TesterPresent
 *   - 0x85 ControlDTCSetting
 *
 * Transport: ISO 15765-2 (CAN ISO-TP) via raw SocketCAN with software ISO-TP framing.
 *
 * Thread-safety: Each UDSClient instance is single-threaded (one session).
 *                Multiple parallel sessions require separate instances.
 */

#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#include <optional>

namespace tcu::can { class CANManager; }

namespace tcu::diagnostics {

/** @brief UDS service IDs */
enum class UDSService : uint8_t {
    DiagnosticSessionControl  = 0x10,
    ECUReset                  = 0x11,
    ClearDTC                  = 0x14,
    ReadDTC                   = 0x19,
    ReadDataById              = 0x22,
    SecurityAccess            = 0x27,
    CommunicationControl      = 0x28,
    WriteDataById             = 0x2E,
    RoutineControl            = 0x31,
    RequestDownload           = 0x34,
    TransferData              = 0x36,
    RequestTransferExit       = 0x37,
    TesterPresent             = 0x3E,
    ControlDTCSetting         = 0x85,
};

/** @brief UDS session types */
enum class UDSSession : uint8_t {
    Default          = 0x01,
    Programming      = 0x02,
    Extended         = 0x03,
};

/** @brief ECU reset types */
enum class ECUResetType : uint8_t {
    HardReset         = 0x01,
    KeyOffOnReset     = 0x02,
    SoftReset         = 0x03,
};

/** @brief UDS Negative Response Codes */
enum class NRC : uint8_t {
    SubFunctionNotSupported        = 0x12,
    IncorrectMsgLenOrFormat        = 0x13,
    ResponseTooLong                = 0x14,
    BusyRepeatRequest              = 0x21,
    ConditionsNotCorrect           = 0x22,
    RequestSequenceError           = 0x24,
    RequestOutOfRange              = 0x31,
    SecurityAccessDenied           = 0x33,
    InvalidKey                     = 0x35,
    ExceededAttempts               = 0x36,
    RequiredTimeDelayNotExpired    = 0x37,
    UploadDownloadNotAccepted      = 0x70,
    TransferDataSuspended          = 0x71,
    GeneralProgrammingFailure      = 0x72,
    WrongBlockSequenceCounter      = 0x73,
    ResponsePending                = 0x78,
    ServiceNotSupportedInSession   = 0x7E,
    ServiceNotSupported            = 0x7F,
};

/**
 * @brief Result of a UDS service call.
 */
struct UDSResult {
    bool    success{false};
    uint8_t service_id{0};
    NRC     nrc{NRC::ServiceNotSupported};
    std::vector<uint8_t> payload;
    std::string error_message;
};

/**
 * @brief Decoded DTC record.
 */
struct DTCRecord {
    uint32_t dtc_id{0};          ///< 3-byte DTC (e.g. 0x123456)
    uint8_t  status_byte{0};     ///< DTC status mask
    std::string status_text;     ///< Human-readable status
};

/**
 * @brief ISO-TP configuration for UDS transport.
 */
struct ISOTPConfig {
    uint32_t tx_id{0x7E0};       ///< Tester physical request CAN ID
    uint32_t rx_id{0x7E8};       ///< ECU response CAN ID
    uint8_t  block_size{0};      ///< FC block size (0 = no flow control limit)
    uint8_t  st_min_ms{0};       ///< Separation time minimum (ms)
    uint32_t p2_timeout_ms{50};  ///< P2 timer (ECU response timeout, ms)
    uint32_t p2_star_ms{5000};   ///< P2* timer (after NRC 0x78, ms)
    uint32_t p3_timeout_ms{5000};///< P3 timer (between tester requests, ms)
};

/**
 * @brief Seed-key algorithm callback.
 * @param seed   Seed bytes from ECU
 * @return Calculated key bytes
 */
using SeedKeyAlgorithm = std::function<std::vector<uint8_t>(const std::vector<uint8_t>& seed)>;

/**
 * @brief Full ISO 14229 UDS client.
 */
class UDSClient {
public:
    explicit UDSClient(std::shared_ptr<tcu::can::CANManager> can_mgr,
                       const ISOTPConfig& istp_cfg = {});
    ~UDSClient();

    UDSClient(const UDSClient&)            = delete;
    UDSClient& operator=(const UDSClient&) = delete;

    // --------------------------------------------------------
    // Session management
    // --------------------------------------------------------

    /** @brief Open a diagnostic session (0x10). */
    UDSResult open_session(UDSSession session);

    /** @brief Close session — send default session request. */
    void      close_session();

    /** @brief Send TesterPresent (0x3E) to keep session alive. */
    UDSResult tester_present(bool suppress_response = true);

    // --------------------------------------------------------
    // Core services
    // --------------------------------------------------------

    /** @brief ECU Reset (0x11). */
    UDSResult ecu_reset(ECUResetType type = ECUResetType::HardReset);

    /** @brief Read Data By Identifier (0x22). */
    UDSResult read_data_by_id(uint16_t did);

    /** @brief Write Data By Identifier (0x2E). */
    UDSResult write_data_by_id(uint16_t did, const std::vector<uint8_t>& data);

    // --------------------------------------------------------
    // Security access
    // --------------------------------------------------------

    /**
     * @brief Perform full security access sequence (0x27 request seed + send key).
     * @param level     Security level (odd = request seed, even = send key)
     * @param algorithm Seed-key calculation function
     */
    UDSResult security_access(uint8_t level, SeedKeyAlgorithm algorithm);

    // --------------------------------------------------------
    // DTC services
    // --------------------------------------------------------

    /** @brief Read all confirmed DTCs (0x19 sub 0x02). */
    std::vector<DTCRecord> read_dtcs();

    /** @brief Clear all DTCs (0x14 0xFF 0xFF 0xFF). */
    UDSResult clear_dtcs();

    /** @brief Control DTC setting (0x85). */
    UDSResult control_dtc_setting(bool enable);

    // --------------------------------------------------------
    // Routine control
    // --------------------------------------------------------

    /** @brief Start routine (0x31 0x01). */
    UDSResult routine_control_start(uint16_t routine_id,
                                    const std::vector<uint8_t>& params = {});

    /** @brief Stop routine (0x31 0x02). */
    UDSResult routine_control_stop(uint16_t routine_id);

    /** @brief Request routine result (0x31 0x03). */
    UDSResult routine_control_result(uint16_t routine_id);

    // --------------------------------------------------------
    // Download / flashing services
    // --------------------------------------------------------

    /** @brief Request Download (0x34). Returns maxBlockLen. */
    std::optional<size_t> request_download(uint32_t address, uint32_t size,
                                           uint8_t compression_method = 0x00,
                                           uint8_t encrypting_method  = 0x00);

    /** @brief Transfer Data block (0x36). */
    UDSResult transfer_data(uint8_t block_seq, const std::vector<uint8_t>& data);

    /** @brief Request Transfer Exit (0x37). */
    UDSResult request_transfer_exit();

    // --------------------------------------------------------
    // Communication control
    // --------------------------------------------------------

    /** @brief Communication control (0x28). */
    UDSResult communication_control(uint8_t control_type, uint8_t comm_type);

    // --------------------------------------------------------
    // Raw service
    // --------------------------------------------------------

    /**
     * @brief Send a raw UDS request and return the response.
     * @param request  Full request PDU (service ID + parameters)
     */
    UDSResult send_raw(const std::vector<uint8_t>& request);

    // --------------------------------------------------------
    // Configuration
    // --------------------------------------------------------

    void set_istp_config(const ISOTPConfig& cfg);
    const ISOTPConfig& istp_config() const noexcept;

private:
    UDSResult send_and_receive(const std::vector<uint8_t>& request);
    bool      send_isotp(const std::vector<uint8_t>& data);
    std::optional<std::vector<uint8_t>> receive_isotp(uint32_t timeout_ms);
    void      send_flow_control(uint8_t flow_status, uint8_t block_size, uint8_t st_min);
    NRC       parse_nrc(const std::vector<uint8_t>& response);

    std::shared_ptr<tcu::can::CANManager> m_can;
    ISOTPConfig                           m_istp;
    bool                                  m_session_open{false};
    UDSSession                            m_current_session{UDSSession::Default};
    uint32_t                              m_rx_callback_handle{0};
    std::vector<uint8_t>                  m_rx_buffer;
    mutable std::mutex                    m_rx_mutex;
};

} // namespace tcu::diagnostics
