# Getting Started Guide - Embedded SoC Firmware Platform

## Quick Start

### 5-Minute Setup

#### 1. Build the Firmware Simulator

```bash
cd embedded_soc_firmware_platform
mkdir build
cd build
cmake ..
make
```

#### 2. Run a Boot Test

```bash
./firmware_simulator boot
```

You should see output:
```
========================================
Embedded SoC Firmware Simulation Platform
========================================

Executing Boot Sequence...

Boot completed successfully
Total Boot Time: 335 ms
SEC Phase: 50 ms
PEI Phase: 75 ms
DXE Phase: 100 ms
BDS Phase: 60 ms
OS Load: 50 ms
```

#### 3. Try Other Commands

```bash
# Test power state transitions
./firmware_simulator power

# Test memory subsystem
./firmware_simulator memory

# Test security features
./firmware_simulator security

# Test PCIe subsystem
./firmware_simulator pcie

# Test USB subsystem
./firmware_simulator usb

# Check system health
./firmware_simulator health

# Run 60-second simulation
./firmware_simulator simulate 60
```

### 10-Minute Test Run

```bash
cd embedded_soc_firmware_platform/tests

# Run all validation tests
python3 run_all_tests.py
```

Expected output:
```
============================================================
EMBEDDED SOC FIRMWARE VALIDATION TEST RUN
============================================================

Running test suite: Boot
Running test suite: Power
Running test suite: Security
Running test suite: Memory
Running test suite: PCIe
Running test suite: USB

============================================================
VALIDATION TEST EXECUTION SUMMARY
============================================================
Total Tests: 350
Passed: 343
Failed: 7
Blocked: 0
Errors: 0
Pass Rate: 98.00%
============================================================

Test report saved to: validation_logs/validation_report_20260601_123456.json
```

## Detailed Usage

### Firmware Simulator Commands

#### Boot Command
Tests the complete boot sequence through all phases:
- SEC Phase (Security initialization)
- PEI Phase (Pre-EFI initialization)
- DXE Phase (Driver execution environment)
- BDS Phase (Boot device selection)
- OS Loader phase

```bash
./firmware_simulator boot
```

#### Power Command
Tests power state transitions:
```bash
./firmware_simulator power
```

Tests S0→S3→S0 transitions and measures wake latency

#### Memory Command
Tests memory subsystem:
```bash
./firmware_simulator memory
```

Initializes DDR, runs training, stress tests, and checks ECC

#### Security Command
Tests security features:
```bash
./firmware_simulator security
```

Tests Secure Boot, TPM, measured boot, certificates, and signatures

#### PCIe Command
Tests PCIe subsystem:
```bash
./firmware_simulator pcie
```

Enumerates devices, trains links, tests bandwidth

#### USB Command
Tests USB subsystem:
```bash
./firmware_simulator usb
```

Enumerates devices, transfers data, tests hot-plug

#### Health Command
Displays system health:
```bash
./firmware_simulator health
```

Shows temperature, memory usage, device health

#### Simulate Command
Runs extended simulation:
```bash
./firmware_simulator simulate 300
```

Runs simulation for 300 seconds with periodic monitoring

## Test Execution

### Running All Tests

```bash
cd tests
python3 run_all_tests.py
```

### Running Specific Test Suite

```bash
python3 -m pytest boot/test_boot_suite.py -v
python3 -m pytest power/test_power_suite.py -v
python3 -m pytest security/test_security_suite.py -v
python3 -m pytest memory/test_memory_suite.py -v
python3 -m pytest pcie/test_pcie_suite.py -v
python3 -m pytest usb/test_usb_suite.py -v
```

### Running Individual Test

```bash
python3 -m pytest boot/test_boot_suite.py::BootValidationSuite::test_BOOT_001_cold_boot_success -v
```

### Running Tests with Output

```bash
# Verbose output
python3 run_all_tests.py 2>&1 | tee test_run.log

# With specific logging level
python3 -m pytest boot/test_boot_suite.py -v -s
```

## Understanding the Output

### Boot Test Output

```
[INFO] BootManager: Executing Power-On Reset (POR)
[INFO] BootManager: Running SEC (Security) Phase
[INFO] BootManager: SEC phase: Starting security initialization
[INFO] BootManager: SEC phase completed successfully
[INFO] BootManager: Running PEI (Pre-EFI Initialization) Phase
...
[INFO] BootManager: Boot completed successfully in 335ms
```

**What to look for:**
- No [ERROR] lines during normal operation
- All phases complete in sequence
- Boot time is reasonable (300-400ms typical)

### Power Test Output

```
[INFO] PowerManager: Setting power state to S3
[INFO] PowerManager: System in S3 sleep state
[INFO] PowerManager: Resuming from suspend state
[INFO] PowerManager: Transitioned to S0
[INFO] PowerManager: Wake latency measured: 25ms
```

**What to look for:**
- Successful state transitions
- Wake latency < 100ms
- No failures during transitions

### Memory Test Output

```
[INFO] MemoryManager: Initializing DDR memory
[INFO] MemoryManager: DDR initialization completed successfully
[INFO] MemoryManager: Running DDR training
[INFO] MemoryManager: DDR training completed
[INFO] MemoryManager: Memory Capacity: 16 GB
Memory capacity: 16GB, DDR4 @ 2666MHz, ECC enabled
```

**What to look for:**
- DDR training completes
- Memory capacity correctly detected
- ECC status correct

### Test Report Output

```json
{
  "timestamp": "2026-06-01T12:34:56",
  "total_tests": 350,
  "passed": 343,
  "failed": 7,
  "blocked": 0,
  "pass_rate": 98.0,
  "test_suites": {
    "Boot": {
      "total": 80,
      "passed": 78,
      "failed": 2,
      "results": [
        {
          "test_id": "BOOT_001",
          "test_name": "Cold Boot Sequence Success",
          "status": "PASSED",
          "duration_ms": 335
        }
      ]
    }
  }
}
```

## Log Files

Logs are saved in the project directory:

- `firmware_sim.log` - Firmware simulator log (JSON format)
- `validation_logs/` - Validation test logs
- `validation_logs/validation_report_*.json` - Test reports

## Root Cause Analysis

If tests fail, analyze the logs:

```bash
python3 tools/rca_engine/rca_engine.py firmware_sim.log
```

This generates:
- Failure detection
- Signature matching against known issues
- Root cause analysis
- Recommended actions

Example RCA output:
```
ROOT CAUSE ANALYSIS REPORT
====================================
Analysis Time: 2026-06-01T12:34:56

Failure #1
  Severity: CRITICAL
  Matching Signatures:
    - Memory Training Failure
      Likely Cause: Memory initialization error
      Recommended Action: Check memory module compatibility
```

## Common Scenarios

### Scenario 1: Normal Boot Flow

```bash
$ ./firmware_simulator boot

Expected:
- Boot progresses through all phases
- No errors
- ~335ms total time
- "Boot completed successfully" message

Pass: ✓
```

### Scenario 2: Test Power Transitions

```bash
$ ./firmware_simulator power

Expected:
- Transitions S0 → S3 → S0
- Wake latency < 100ms
- All transitions successful

Pass: ✓
```

### Scenario 3: Validate Security

```bash
$ ./firmware_simulator security

Expected:
- Secure Boot enabled
- TPM initialized
- Certificates validated
- No security events

Pass: ✓
```

### Scenario 4: Complete Validation Run

```bash
$ cd tests && python3 run_all_tests.py

Expected:
- 1000+ tests execute
- > 95% pass rate
- Report generated
- No critical failures

Pass: ✓
```

## Troubleshooting

### Firmware Won't Build

**Problem:** CMake errors
```
CMake Error: JSON library not found
```

**Solution:**
```bash
# Install nlohmann/json-dev package
# Ubuntu/Debian:
sudo apt-get install nlohmann-json3-dev

# macOS:
brew install nlohmann-json

# Then retry cmake/make
```

### Tests Won't Run

**Problem:** Python ImportError
```
ModuleNotFoundError: No module named 'validation_framework'
```

**Solution:**
```bash
# Ensure you're in the tests directory
cd tests

# Make sure Python path includes current directory
export PYTHONPATH="${PYTHONPATH}:."

# Then run tests
python3 run_all_tests.py
```

### Firmware Crashes

**Problem:** Segmentation fault
```
Segmentation fault (core dumped)
```

**Solution:**
1. Check if all dependencies are installed
2. Rebuild with debug symbols: `cmake -DCMAKE_BUILD_TYPE=Debug`
3. Check memory for corruption
4. Review error log

### Tests Fail

**Problem:** Tests showing failures
```
Pass Rate: 85.00%
Failed: 150 tests
```

**Solution:**
1. Run RCA: `python3 tools/rca_engine/rca_engine.py firmware_sim.log`
2. Check specific test logs
3. Verify firmware binary is up-to-date
4. Run individual failing tests with `-s` flag for details

## Performance Expectations

### Build Time
- Initial build: 30-60 seconds
- Incremental build: 5-10 seconds

### Execution Time
- Single firmware command: 1-5 seconds
- Full test suite: 5-15 minutes
- Extended simulation (1 hour): 60+ minutes
- RCA analysis: < 1 second

### Output Size
- Firmware simulator log: 1-10 MB per run
- Test report JSON: 500 KB - 2 MB
- Validation logs: 10-50 MB per full run

## Next Steps

1. **Read Architecture Guide**: `docs/architecture/ARCHITECTURE.md`
2. **Review Test Strategy**: `docs/test_strategies/TEST_STRATEGY.md`
3. **Run Example Tests**: See scenario examples above
4. **Modify Test Cases**: Add your own tests based on requirements
5. **Integrate to CI/CD**: Use test runner in automated pipelines

## Additional Resources

- **Project README**: Full project overview
- **Architecture Document**: System design and components
- **Test Strategy**: Comprehensive testing methodology
- **Code Comments**: Inline documentation in C++ source
- **Docstrings**: Python function documentation

## Support

For detailed information:
1. Check the `docs/` directory
2. Review inline code comments
3. Check test case examples
4. Run with `-v` or `--verbose` flags
5. Generate and analyze logs

## Summary

The Embedded SoC Firmware Simulation Platform provides:
- ✓ Realistic firmware simulation
- ✓ Comprehensive test automation
- ✓ Professional validation framework
- ✓ Root cause analysis tools
- ✓ Production-quality documentation

You're now ready to validate firmware at the post-silicon stage!
