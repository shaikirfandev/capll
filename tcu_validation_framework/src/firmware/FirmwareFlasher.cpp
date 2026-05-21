/**
 * @file FirmwareFlasher.cpp
 * @brief Dual-path firmware flashing: UDS 0x34/0x36/0x37 + Renesas RFP CLI.
 */

#include "firmware/FirmwareFlasher.h"
#include "firmware/CRCValidator.h"
#include "logging/Logger.h"

#include <fstream>
#include <iterator>
#include <sstream>
#include <cstdio>
#include <array>
#include <stdexcept>
#include <thread>
#include <chrono>

namespace tcu::firmware {

static auto s_log = tcu::logging::Logger::get("firmware");

// ============================================================
// Construction
// ============================================================

FirmwareFlasher::FirmwareFlasher(std::shared_ptr<tcu::diagnostics::UDSClient> uds,
                                 const UDSFlashConfig& uds_cfg,
                                 const RFPConfig& rfp_cfg)
    : m_uds(std::move(uds))
    , m_uds_cfg(uds_cfg)
    , m_rfp_cfg(rfp_cfg)
{}

// ============================================================
// Main flash entry
// ============================================================

FlashResult FirmwareFlasher::flash(const FirmwarePackage& pkg,
                                   ProgressCallback progress_cb) {
    s_log->info("Flash start: {} v{}", pkg.path, pkg.version);

    // 1. Load firmware file
    auto firmware_data = load_file(pkg.path);
    if (firmware_data.empty()) {
        return make_error("Failed to load firmware: " + pkg.path);
    }
    s_log->info("Firmware size: {} bytes", firmware_data.size());

    // 2. Validate CRC if provided
    if (pkg.crc32 != 0) {
        uint32_t actual = CRCValidator::crc32(firmware_data.data(), firmware_data.size());
        if (actual != pkg.crc32) {
            s_log->error("CRC mismatch: expected={:#010x} actual={:#010x}",
                         pkg.crc32, actual);
            return make_error("CRC32 mismatch");
        }
        s_log->info("CRC32 verified: {:#010x}", actual);
    }

    // 3. Choose flashing path
    FlashResult result;
    if (pkg.use_uds_path) {
        result = flash_via_uds(pkg, firmware_data, progress_cb);
    } else {
        result = flash_via_rfp(pkg, progress_cb);
    }

    if (result.success) {
        s_log->info("Flash complete: {} v{} in {:.1f}s",
                    pkg.path, pkg.version, result.elapsed_seconds);
    } else {
        s_log->error("Flash failed: {}", result.error_message);
    }
    return result;
}

// ============================================================
// UDS path: 0x34 (RequestDownload) / 0x36 (TransferData) / 0x37 (TransferExit)
// ============================================================

FlashResult FirmwareFlasher::flash_via_uds(const FirmwarePackage& pkg,
                                            const std::vector<uint8_t>& data,
                                            ProgressCallback progress_cb) {
    auto t_start = std::chrono::steady_clock::now();
    s_log->info("UDS flash path: addr={:#010x}", pkg.target_address);

    // Open programming session
    auto sess = m_uds->open_session(tcu::diagnostics::UDSSession::Programming);
    if (!sess.success) {
        return make_error("Failed to enter programming session");
    }

    // Security access if required
    if (m_uds_cfg.security_level != 0) {
        auto sa = m_uds->security_access(m_uds_cfg.security_level,
                                          m_uds_cfg.seed_key_algo);
        if (!sa.success) {
            return make_error("Security access failed");
        }
        s_log->info("Security access granted (level={})", m_uds_cfg.security_level);
    }

    // Erase memory via routine control if enabled
    if (m_uds_cfg.erase_routine != 0) {
        std::vector<uint8_t> erase_params = {
            static_cast<uint8_t>((pkg.target_address >> 24) & 0xFF),
            static_cast<uint8_t>((pkg.target_address >> 16) & 0xFF),
            static_cast<uint8_t>((pkg.target_address >>  8) & 0xFF),
            static_cast<uint8_t>( pkg.target_address        & 0xFF),
            static_cast<uint8_t>((data.size() >> 24) & 0xFF),
            static_cast<uint8_t>((data.size() >> 16) & 0xFF),
            static_cast<uint8_t>((data.size() >>  8) & 0xFF),
            static_cast<uint8_t>( data.size()        & 0xFF),
        };
        auto erase = m_uds->routine_control_start(m_uds_cfg.erase_routine, erase_params);
        if (!erase.success) {
            return make_error("Memory erase routine failed");
        }
        s_log->info("Memory erase complete");
    }

    // Request download
    auto max_block = m_uds->request_download(pkg.target_address,
                                              static_cast<uint32_t>(data.size()));
    if (!max_block) {
        return make_error("RequestDownload (0x34) failed");
    }
    size_t block_size = std::min(*max_block, static_cast<size_t>(m_uds_cfg.block_size));
    s_log->info("Max block size: {}", block_size);

    // Transfer data in blocks
    size_t offset = 0;
    uint8_t seq   = 1;
    size_t total  = data.size();

    while (offset < total) {
        size_t chunk_size = std::min(block_size, total - offset);
        std::vector<uint8_t> chunk(data.begin() + static_cast<ptrdiff_t>(offset),
                                   data.begin() + static_cast<ptrdiff_t>(offset + chunk_size));
        auto td = m_uds->transfer_data(seq, chunk);
        if (!td.success) {
            return make_error("TransferData failed at block " + std::to_string(seq));
        }
        offset += chunk_size;
        seq     = static_cast<uint8_t>((seq % 0xFF) + 1);

        float pct = 100.0f * static_cast<float>(offset) / static_cast<float>(total);
        if (progress_cb) { progress_cb(pct, offset, total); }
        s_log->trace("Transferred {}/{} bytes ({:.1f}%)", offset, total, pct);
    }

    // Transfer exit
    auto te = m_uds->request_transfer_exit();
    if (!te.success) {
        return make_error("RequestTransferExit (0x37) failed");
    }

    // Checksum routine if configured
    if (m_uds_cfg.checksum_routine != 0) {
        auto chk = m_uds->routine_control_start(m_uds_cfg.checksum_routine);
        if (!chk.success) {
            s_log->warn("Checksum routine failed — proceeding anyway");
        }
    }

    // Reset ECU
    m_uds->ecu_reset(tcu::diagnostics::ECUResetType::Hard);

    auto elapsed = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - t_start).count();

    FlashResult res;
    res.success          = true;
    res.bytes_written    = total;
    res.elapsed_seconds  = elapsed;
    res.method_used      = "UDS-0x34/0x36/0x37";
    res.firmware_version = pkg.version;
    return res;
}

// ============================================================
// RFP CLI path
// ============================================================

FlashResult FirmwareFlasher::flash_via_rfp(const FirmwarePackage& pkg,
                                            ProgressCallback progress_cb) {
    auto t_start = std::chrono::steady_clock::now();
    s_log->info("RFP CLI flash path: {}", m_rfp_cfg.rfp_cli_path);

    // Build rfp-cli command
    std::string cmd = build_rfp_command(pkg);
    s_log->info("RFP command: {}", cmd);

    // Execute command capturing output
    std::array<char, 512> buffer{};
    std::string output;

    // NOLINT(cert-env33-c): rfp_cli_path is from trusted config, not user input
    std::unique_ptr<FILE, decltype(&pclose)> pipe(
        ::popen(cmd.c_str(), "r"), &pclose);

    if (!pipe) {
        return make_error("popen() failed for rfp-cli");
    }

    float progress = 0.0f;
    while (::fgets(buffer.data(), static_cast<int>(buffer.size()), pipe.get()) != nullptr) {
        std::string line(buffer.data());
        output += line;
        // Parse simple progress lines like "Progress: 45%"
        if (line.find("Progress:") != std::string::npos ||
            line.find("percent") != std::string::npos) {
            progress = std::min(progress + 10.0f, 100.0f);
            if (progress_cb) { progress_cb(progress, 0, 0); }
        }
    }

    int exit_code = pclose(pipe.release());
    if (exit_code != 0) {
        s_log->error("rfp-cli exited with code {}", exit_code);
        s_log->error("Output:\n{}", output);
        return make_error("rfp-cli flash failed (exit code " +
                          std::to_string(exit_code) + ")");
    }

    if (progress_cb) { progress_cb(100.0f, 0, 0); }

    auto elapsed = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - t_start).count();

    FlashResult res;
    res.success          = true;
    res.elapsed_seconds  = elapsed;
    res.method_used      = "Renesas-RFP-CLI";
    res.firmware_version = pkg.version;
    return res;
}

std::string FirmwareFlasher::build_rfp_command(const FirmwarePackage& pkg) const {
    std::ostringstream oss;
    oss << m_rfp_cfg.rfp_cli_path;

    if (m_rfp_cfg.use_tcpip) {
        oss << " -device " << m_rfp_cfg.device_type
            << " -port TCPIP:"  << m_rfp_cfg.host
            << ":" << m_rfp_cfg.port;
    } else {
        oss << " -device " << m_rfp_cfg.device_type
            << " -port USB";
    }

    oss << " -file " << pkg.path
        << " -output None"
        << " -erase";

    if (!m_rfp_cfg.extra_args.empty()) {
        oss << " " << m_rfp_cfg.extra_args;
    }

    return oss.str();
}

// ============================================================
// Helpers
// ============================================================

std::vector<uint8_t> FirmwareFlasher::load_file(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file.is_open()) {
        s_log->error("Cannot open firmware file: {}", path);
        return {};
    }
    return std::vector<uint8_t>(std::istreambuf_iterator<char>(file),
                                 std::istreambuf_iterator<char>());
}

FlashResult FirmwareFlasher::make_error(const std::string& msg) {
    FlashResult r;
    r.success       = false;
    r.error_message = msg;
    s_log->error("FlashResult error: {}", msg);
    return r;
}

} // namespace tcu::firmware
