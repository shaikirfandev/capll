#include "firmware_application.h"
#include <iostream>
#include <cstring>

using namespace firmware;

void print_usage() {
    std::cout << "Embedded SoC Firmware Simulator\n";
    std::cout << "Usage: firmware_simulator [command] [options]\n";
    std::cout << "\nCommands:\n";
    std::cout << "  boot              - Execute boot sequence\n";
    std::cout << "  power             - Perform power state transitions\n";
    std::cout << "  memory            - Test memory subsystem\n";
    std::cout << "  security          - Test security features\n";
    std::cout << "  pcie              - Test PCIe subsystem\n";
    std::cout << "  usb               - Test USB subsystem\n";
    std::cout << "  health            - Display system health\n";
    std::cout << "  simulate [sec]    - Run simulation for N seconds (default 60)\n";
    std::cout << "  help              - Show this help message\n";
}

int main(int argc, char* argv[]) {
    FirmwareApplication& fw = FirmwareApplication::getInstance();
    
    std::cout << "========================================\n";
    std::cout << "Embedded SoC Firmware Simulation Platform\n";
    std::cout << "========================================\n\n";
    
    // Initialize firmware
    if (fw.initialize() != Status::SUCCESS) {
        std::cerr << "ERROR: Failed to initialize firmware\n";
        return 1;
    }
    
    // Default command or from arguments
    std::string command = (argc > 1) ? argv[1] : "boot";
    
    try {
        if (command == "boot") {
            std::cout << "Executing Boot Sequence...\n\n";
            if (fw.start_boot_sequence() == Status::SUCCESS) {
                std::cout << "Boot completed successfully\n";
                
                auto metrics = fw.get_boot_manager().get_boot_metrics();
                std::cout << "Total Boot Time: " << metrics.total_boot_time_ms << " ms\n";
                std::cout << "SEC Phase: " << metrics.sec_phase_time_ms << " ms\n";
                std::cout << "PEI Phase: " << metrics.pei_phase_time_ms << " ms\n";
                std::cout << "DXE Phase: " << metrics.dxe_phase_time_ms << " ms\n";
                std::cout << "BDS Phase: " << metrics.bds_phase_time_ms << " ms\n";
                std::cout << "OS Load: " << metrics.os_load_time_ms << " ms\n";
            } else {
                std::cerr << "Boot failed\n";
            }
        }
        else if (command == "power") {
            std::cout << "Testing Power State Transitions...\n\n";
            
            fw.change_power_state(PowerState::S0);
            std::cout << "Current State: S0 (Working)\n";
            
            fw.change_power_state(PowerState::S3);
            std::cout << "Transitioned to S3 (Sleep)\n";
            
            fw.change_power_state(PowerState::S0);
            std::cout << "Resumed to S0\n";
            
            auto metrics = fw.get_power_manager().get_power_metrics();
            std::cout << "Transition Time: " << metrics.transition_time_ms << " ms\n";
        }
        else if (command == "memory") {
            std::cout << "Testing Memory Subsystem...\n\n";
            
            auto& mem_mgr = fw.get_memory_manager();
            mem_mgr.initialize_ddr();
            mem_mgr.run_ddr_training();
            mem_mgr.memory_stress_test();
            
            auto info = mem_mgr.get_memory_info();
            std::cout << "Memory Capacity: " << (info.total_size / (1024*1024*1024)) << " GB\n";
            std::cout << "DDR Type: DDR" << info.ddr_type << "\n";
            std::cout << "DDR Speed: " << info.ddr_speed_mhz << " MHz\n";
            std::cout << "ECC Enabled: " << (info.ecc_enabled ? "Yes" : "No") << "\n";
            std::cout << "ECC Errors: " << mem_mgr.get_ecc_error_count() << "\n";
            
            std::cout << "\nTest Results:\n";
            for (const auto& result : mem_mgr.get_test_results()) {
                std::cout << "  " << result << "\n";
            }
        }
        else if (command == "security") {
            std::cout << "Testing Security Subsystem...\n\n";
            
            auto& sec_mgr = fw.get_security_manager();
            sec_mgr.initialize_tpm();
            sec_mgr.enable_secure_boot();
            sec_mgr.start_measured_boot();
            
            std::cout << "Secure Boot: " << (sec_mgr.is_secure_boot_enabled() ? "Enabled" : "Disabled") << "\n";
            std::cout << "TPM Initialized: Yes\n";
            
            std::cout << "\nSecurity Events:\n";
            auto events = sec_mgr.get_security_events();
            for (const auto& event : events) {
                std::cout << "  - " << event.event_type << ": " << event.description << "\n";
            }
        }
        else if (command == "pcie") {
            std::cout << "Testing PCIe Subsystem...\n\n";
            
            auto& pcie_mgr = fw.get_pcie_manager();
            
            // Add some test devices
            PCIeDevice device1;
            device1.bus = 0;
            device1.slot = 0;
            device1.function = 0;
            device1.vendor_id = "1022";  // AMD
            device1.device_id = "1234";
            device1.device_name = "Test PCIe Device 1";
            device1.generation = PCIeGen::GEN4;
            device1.hot_pluggable = true;
            
            pcie_mgr.add_device(device1);
            pcie_mgr.enumerate_devices();
            
            auto metrics = pcie_mgr.get_metrics();
            std::cout << "Total Devices: " << metrics.total_devices << "\n";
            std::cout << "Enumerated Devices: " << metrics.enumerated_devices << "\n";
            std::cout << "Link Trained Devices: " << metrics.link_trained_devices << "\n";
        }
        else if (command == "usb") {
            std::cout << "Testing USB Subsystem...\n\n";
            
            auto& usb_mgr = fw.get_usb_manager();
            
            USBDevice device;
            device.port = 1;
            device.standard = USBStandard::USB3;
            device.vendor_id = "1234";
            device.product_id = "5678";
            device.device_name = "Test USB Device";
            device.device_class = "MassStorage";
            
            usb_mgr.connect_device(device);
            usb_mgr.perform_data_transfer(1, 1024);
            
            auto metrics = usb_mgr.get_metrics();
            std::cout << "Connected Devices: " << metrics.connected_devices << "\n";
            std::cout << "Enumerated Devices: " << metrics.enumerated_devices << "\n";
            std::cout << "Total Data Transferred: " << metrics.total_data_transferred << " bytes\n";
        }
        else if (command == "health") {
            std::cout << "System Health Status:\n\n";
            std::cout << fw.get_health_monitor().generate_health_report();
            
            auto warnings = fw.get_health_monitor().get_warnings();
            if (!warnings.empty()) {
                std::cout << "Warnings:\n";
                for (const auto& warning : warnings) {
                    std::cout << "  - " << warning << "\n";
                }
            }
        }
        else if (command == "simulate") {
            uint32 duration = 60;
            if (argc > 2) {
                duration = std::stoi(argv[2]);
            }
            
            std::cout << "Running simulation for " << duration << " seconds...\n";
            fw.run_simulation(duration);
            std::cout << "Simulation completed\n";
        }
        else if (command == "help") {
            print_usage();
        }
        else {
            std::cerr << "Unknown command: " << command << "\n";
            print_usage();
            return 1;
        }
    }
    catch (const std::exception& e) {
        std::cerr << "ERROR: " << e.what() << "\n";
        return 1;
    }
    
    // Shutdown
    fw.shutdown();
    
    std::cout << "\n========================================\n";
    std::cout << "Firmware Simulator Completed\n";
    std::cout << "========================================\n";
    
    return 0;
}
