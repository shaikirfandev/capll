#!/usr/bin/env python3
"""
Main Test Execution Runner
Orchestrates test execution across all test suites
"""

import sys
import json
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from validation_framework import ValidationFramework
from boot.test_boot_suite import BootValidationSuite
from power.test_power_suite import PowerValidationSuite
from security.test_security_suite import SecurityValidationSuite
from memory.test_memory_suite import MemoryValidationSuite
from pcie.test_pcie_suite import PCIeValidationSuite
from usb.test_usb_suite import USBValidationSuite


def main():
    """Main test execution"""
    
    # Initialize framework
    framework = ValidationFramework(log_dir="validation_logs")
    
    # Register test suites
    framework.register_test_suite("Boot", BootValidationSuite)
    framework.register_test_suite("Power", PowerValidationSuite)
    framework.register_test_suite("Security", SecurityValidationSuite)
    framework.register_test_suite("Memory", MemoryValidationSuite)
    framework.register_test_suite("PCIe", PCIeValidationSuite)
    framework.register_test_suite("USB", USBValidationSuite)
    
    # Run all suites
    print("\n" + "="*60)
    print("EMBEDDED SOC FIRMWARE VALIDATION TEST RUN")
    print("="*60 + "\n")
    
    results = framework.run_all_suites()
    
    # Print summary
    framework.print_summary()
    
    # Save report
    report_file = framework.save_report("json")
    print(f"\nTest report saved to: {report_file}\n")
    
    # Print detailed results
    print("Detailed Results by Suite:")
    for suite_name, suite_results in results.items():
        print(f"\n{suite_name} Suite: {len(suite_results)} tests")
        for result in suite_results:
            status_symbol = "✓" if result.status.value == "PASSED" else "✗"
            print(f"  {status_symbol} {result.test_id}: {result.test_name}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
