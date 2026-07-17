#include "security_manager.h"
#include "logger.h"

namespace firmware {

SecurityManager::SecurityManager()
    : secure_boot_enabled_(false),
      tpm_initialized_(false),
      current_firmware_version_(100),
      invalid_cert_(false),
      expired_cert_(false),
      tampered_fw_(false),
      unauthorized_bootloader_(false) {
}

Status SecurityManager::enable_secure_boot() {
    LOG_INFO("SecurityManager", "Enabling Secure Boot");
    secure_boot_enabled_ = true;
    log_security_event("SECURE_BOOT_ENABLED", "Secure Boot has been enabled", Status::SUCCESS);
    return Status::SUCCESS;
}

Status SecurityManager::disable_secure_boot() {
    LOG_INFO("SecurityManager", "Disabling Secure Boot");
    secure_boot_enabled_ = false;
    log_security_event("SECURE_BOOT_DISABLED", "Secure Boot has been disabled", Status::SUCCESS);
    return Status::SUCCESS;
}

bool SecurityManager::is_secure_boot_enabled() const {
    return secure_boot_enabled_;
}

Status SecurityManager::initialize_tpm() {
    LOG_INFO("SecurityManager", "Initializing TPM");
    tpm_initialized_ = true;
    
    // Initialize PCR values
    for (uint32 i = 0; i < 24; ++i) {
        pcr_values_[i] = "0000000000000000000000000000000000000000";  // SHA-1 zeros
    }
    
    log_security_event("TPM_INIT", "TPM initialized and PCRs cleared", Status::SUCCESS);
    return Status::SUCCESS;
}

Status SecurityManager::extend_pcr(uint32 pcr_index, const std::string& data) {
    if (!tpm_initialized_) {
        return Status::FAILURE;
    }
    
    if (pcr_index >= 24) {
        return Status::INVALID_PARAM;
    }
    
    // Simulate PCR extension (hash of previous value + new data)
    pcr_values_[pcr_index] = "extended_" + data.substr(0, 30);
    
    LOG_DEBUG("SecurityManager", "PCR[" + std::to_string(pcr_index) + "] extended with data");
    return Status::SUCCESS;
}

std::string SecurityManager::read_pcr(uint32 pcr_index) const {
    if (pcr_index >= 24 || pcr_values_.find(pcr_index) == pcr_values_.end()) {
        return "";
    }
    return pcr_values_.at(pcr_index);
}

Status SecurityManager::validate_certificate(const Certificate& cert) {
    LOG_INFO("SecurityManager", "Validating certificate: " + cert.subject);
    
    if (invalid_cert_) {
        log_security_event("CERTIFICATE_VALIDATION_FAILED", "Invalid certificate detected", Status::AUTHENTICATION_FAILURE);
        return Status::AUTHENTICATION_FAILURE;
    }
    
    if (expired_cert_ || cert.expired) {
        log_security_event("CERTIFICATE_EXPIRED", "Certificate has expired", Status::AUTHENTICATION_FAILURE);
        return Status::AUTHENTICATION_FAILURE;
    }
    
    if (!cert.valid) {
        log_security_event("INVALID_CERTIFICATE", "Certificate validation failed", Status::AUTHENTICATION_FAILURE);
        return Status::AUTHENTICATION_FAILURE;
    }
    
    log_security_event("CERTIFICATE_VALIDATED", "Certificate validation passed", Status::SUCCESS);
    loaded_certificates_.push_back(cert);
    
    return Status::SUCCESS;
}

Status SecurityManager::validate_firmware_signature(const FirmwareSignature& sig) {
    LOG_INFO("SecurityManager", "Validating firmware signature");
    
    if (tampered_fw_) {
        log_security_event("FIRMWARE_TAMPER_DETECTED", "Firmware tampering detected", Status::AUTHENTICATION_FAILURE);
        return Status::AUTHENTICATION_FAILURE;
    }
    
    if (!sig.valid) {
        log_security_event("INVALID_SIGNATURE", "Firmware signature is invalid", Status::AUTHENTICATION_FAILURE);
        return Status::AUTHENTICATION_FAILURE;
    }
    
    if (sig.revoked) {
        log_security_event("REVOKED_SIGNATURE", "Firmware signature has been revoked", Status::AUTHENTICATION_FAILURE);
        return Status::AUTHENTICATION_FAILURE;
    }
    
    log_security_event("FIRMWARE_SIGNATURE_VALID", "Firmware signature validation passed", Status::SUCCESS);
    return Status::SUCCESS;
}

Status SecurityManager::start_measured_boot() {
    LOG_INFO("SecurityManager", "Starting measured boot sequence");
    
    if (!tpm_initialized_) {
        initialize_tpm();
    }
    
    log_security_event("MEASURED_BOOT_START", "Measured boot sequence started", Status::SUCCESS);
    return Status::SUCCESS;
}

std::vector<std::string> SecurityManager::get_pcr_values() const {
    std::vector<std::string> values;
    for (uint32 i = 0; i < 24; ++i) {
        if (pcr_values_.find(i) != pcr_values_.end()) {
            values.push_back("PCR[" + std::to_string(i) + "]: " + pcr_values_.at(i));
        }
    }
    return values;
}

Status SecurityManager::check_firmware_version(uint32 current_version, uint32 stored_version) {
    LOG_INFO("SecurityManager", "Checking firmware version. Current: " + std::to_string(current_version) + 
             ", Stored: " + std::to_string(stored_version));
    
    if (current_version < stored_version) {
        log_security_event("ROLLBACK_DETECTED", "Firmware rollback attempt detected", Status::FAILURE);
        return Status::FAILURE;
    }
    
    return Status::SUCCESS;
}

Status SecurityManager::update_firmware_version(uint32 version) {
    LOG_INFO("SecurityManager", "Updating firmware version to " + std::to_string(version));
    current_firmware_version_ = version;
    log_security_event("FIRMWARE_VERSION_UPDATED", "Firmware version updated to " + std::to_string(version), Status::SUCCESS);
    return Status::SUCCESS;
}

std::vector<SecurityEvent> SecurityManager::get_security_events() const {
    return security_events_;
}

void SecurityManager::inject_invalid_certificate() {
    LOG_WARNING("SecurityManager", "Injecting invalid certificate failure");
    invalid_cert_ = true;
}

void SecurityManager::inject_expired_certificate() {
    LOG_WARNING("SecurityManager", "Injecting expired certificate failure");
    expired_cert_ = true;
}

void SecurityManager::inject_tampered_firmware() {
    LOG_WARNING("SecurityManager", "Injecting tampered firmware failure");
    tampered_fw_ = true;
}

void SecurityManager::inject_unauthorized_bootloader() {
    LOG_WARNING("SecurityManager", "Injecting unauthorized bootloader failure");
    unauthorized_bootloader_ = true;
}

void SecurityManager::clear_security_failures() {
    LOG_INFO("SecurityManager", "Clearing all security failures");
    invalid_cert_ = false;
    expired_cert_ = false;
    tampered_fw_ = false;
    unauthorized_bootloader_ = false;
}

void SecurityManager::log_security_event(const std::string& event_type, const std::string& description, Status result) {
    SecurityEvent event;
    event.event_type = event_type;
    event.description = description;
    event.timestamp = std::chrono::high_resolution_clock::now();
    event.result = result;
    security_events_.push_back(event);
}

} // namespace firmware
