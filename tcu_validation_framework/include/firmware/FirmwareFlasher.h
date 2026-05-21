/**
 * @file FirmwareFlasher.h
 * @brief Firmware flashing module — Renesas RFP CLI integration + UDS-based flash.
 *
 * Supports two flash paths:
 *   1. Renesas Flash Programmer (RFP) CLI — external tool invocation
 *   2. UDS-based firmware download (ISO 14229 services 0x34/0x36/0x37)
 *
 * Safety features:
 *   - CRC-32 verification before and after flash
 *   - A/B partition support for rollback
 *   - Power-cut safe: atomic partition flag updates
 *   - Dry-run mode for testing without actual flash
 */

#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#include <optional>

namespace tcu::diagnostics { class UDSClient; }

namespace tcu::firmware {

/**
 * @brief Firmware package metadata.
 */
struct FirmwarePackage {
    std::string  path;               ///< Absolute path to firmware binary
    std::string  version;            ///< Version string (e.g. "2.5.3")
    std::string  target_ecu;         ///< Target ECU name
    uint32_t     target_address{0};  ///< Flash start address
    uint32_t     size{0};            ///< Expected binary size (bytes)
    uint32_t     expected_crc32{0};  ///< CRC-32 of the binary
    bool         use_uds_path{true}; ///< true = UDS, false = Renesas RFP CLI
};

/**
 * @brief Flash operation result.
 */
struct FlashResult {
    bool        success{false};
    std::string error_message;
    std::string installed_version;   ///< Read back from ECU post-flash
    uint32_t    actual_crc32{0};     ///< CRC-32 read from ECU post-flash
    uint32_t    duration_ms{0};
    uint32_t    bytes_written{0};
};

/**
 * @brief Progress callback: (bytes_written, total_bytes) → called per block.
 */
using ProgressCallback = std::function<void(uint32_t written, uint32_t total)>;

/**
 * @brief Renesas RFP CLI configuration.
 */
struct RFPConfig {
    std::string rfp_cli_path{"/opt/renesas/rfp/rfp-cli"}; ///< Path to rfp-cli binary
    std::string device_type{"RX65N"};                     ///< Target device type
    std::string connection_type{"TCPIP"};                 ///< "TCPIP" or "USB"
    std::string host{"192.168.10.10"};                    ///< TCU IP (TCPIP mode)
    uint16_t    port{9090};                               ///< RFP server port
    uint32_t    baud_rate{115200};                        ///< UART baud (USB mode)
    uint32_t    timeout_s{300};                           ///< Overall flash timeout (s)
};

/**
 * @brief UDS flash configuration.
 */
struct UDSFlashConfig {
    uint8_t  security_level{0x03};    ///< Security access level for programming session
    uint32_t block_size{0x0400};      ///< Transfer block size (bytes)
    bool     erase_before_write{true};///< Erase flash region before writing
    uint16_t erase_routine_id{0xFF00};///< UDS routine ID for erase
    uint16_t checksum_routine_id{0xFF01}; ///< UDS routine ID for CRC check
    uint16_t sw_version_did{0xF189};  ///< DID to read SW version post-flash
};

/**
 * @brief Firmware Flashing Module.
 *
 * Usage (UDS path):
 * @code
 *   FirmwareFlasher flasher(uds_client, uds_cfg, rfp_cfg);
 *   flasher.set_progress_callback([](uint32_t w, uint32_t t) {
 *       printf("[%u%%] Writing...\n", 100 * w / t);
 *   });
 *   auto result = flasher.flash(pkg);
 * @endcode
 */
class FirmwareFlasher {
public:
    explicit FirmwareFlasher(std::shared_ptr<tcu::diagnostics::UDSClient> uds,
                             const UDSFlashConfig& uds_cfg = {},
                             const RFPConfig&      rfp_cfg = {});
    ~FirmwareFlasher() = default;

    FirmwareFlasher(const FirmwareFlasher&)            = delete;
    FirmwareFlasher& operator=(const FirmwareFlasher&) = delete;

    /**
     * @brief Flash firmware using the path specified in the package.
     * @param pkg     Firmware package descriptor
     * @param dry_run If true, validate only — do not write to flash
     */
    FlashResult flash(const FirmwarePackage& pkg, bool dry_run = false);

    /**
     * @brief Read currently installed firmware version from ECU.
     */
    std::optional<std::string> read_installed_version();

    /**
     * @brief Verify installed firmware CRC matches expected value.
     * @param expected_crc32  Expected CRC from package metadata
     */
    bool verify_crc(uint32_t expected_crc32);

    /**
     * @brief Check if new version is valid (anti-rollback: new > current).
     */
    bool is_version_upgrade(const std::string& new_version,
                             const std::string& current_version);

    /**
     * @brief Set progress callback for flash progress reporting.
     */
    void set_progress_callback(ProgressCallback cb);

    /**
     * @brief Enable/disable dry-run globally.
     */
    void set_dry_run(bool enabled) noexcept;

private:
    // UDS flash path
    FlashResult flash_via_uds(const FirmwarePackage& pkg, bool dry_run);
    bool        erase_flash_region(uint32_t address, uint32_t size);
    bool        write_blocks(const std::vector<uint8_t>& data, uint32_t total_size);
    bool        verify_post_flash(uint32_t expected_crc);

    // Renesas RFP flash path
    FlashResult flash_via_rfp(const FirmwarePackage& pkg, bool dry_run);
    bool        invoke_rfp_cli(const std::string& command, std::string& output);

    // Utility
    std::vector<uint8_t> load_binary(const std::string& path);
    uint32_t             calculate_crc32(const std::vector<uint8_t>& data);

    std::shared_ptr<tcu::diagnostics::UDSClient> m_uds;
    UDSFlashConfig  m_uds_cfg;
    RFPConfig       m_rfp_cfg;
    ProgressCallback m_progress_cb;
    bool             m_dry_run{false};
};

} // namespace tcu::firmware
