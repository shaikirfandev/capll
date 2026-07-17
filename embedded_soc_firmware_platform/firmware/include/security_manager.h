#ifndef FIRMWARE_SECURITY_MANAGER_H
#define FIRMWARE_SECURITY_MANAGER_H

#include "types.h"
#include <vector>
#include <map>

namespace firmware {

struct Certificate {
    std::string subject;
    std::string issuer;
    std::string serial_number;
    bool expired;
    bool valid;
};

struct FirmwareSignature {
    std::string signature_hex;
    std::string public_key;
    bool valid;
    bool revoked;
};

class SecurityManager {
public:
    SecurityManager();

    // Secure Boot operations
    Status enable_secure_boot();
    Status disable_secure_boot();
    bool is_secure_boot_enabled() const;

    // TPM simulation
    Status initialize_tpm();
    Status extend_pcr(uint32 pcr_index, const std::string& data);
    std::string read_pcr(uint32 pcr_index) const;

    // Certificate validation
    Status validate_certificate(const Certificate& cert);
    Status validate_firmware_signature(const FirmwareSignature& sig);

    // Measured boot
    Status start_measured_boot();
    std::vector<std::string> get_pcr_values() const;

    // Anti-rollback protection
    Status check_firmware_version(uint32 current_version, uint32 stored_version);
    Status update_firmware_version(uint32 version);

    // Security events
    std::vector<SecurityEvent> get_security_events() const;

    // Failure simulation
    void inject_invalid_certificate();
    void inject_expired_certificate();
    void inject_tampered_firmware();
    void inject_unauthorized_bootloader();
    void clear_security_failures();

private:
    bool secure_boot_enabled_;
    bool tpm_initialized_;
    std::map<uint32, std::string> pcr_values_;  // PCR registers
    std::vector<Certificate> loaded_certificates_;
    uint32 current_firmware_version_;
    std::vector<SecurityEvent> security_events_;

    // Injected failures
    bool invalid_cert_;
    bool expired_cert_;
    bool tampered_fw_;
    bool unauthorized_bootloader_;

    void log_security_event(const std::string& event_type, const std::string& description, Status result);
};

} // namespace firmware

#endif // FIRMWARE_SECURITY_MANAGER_H
