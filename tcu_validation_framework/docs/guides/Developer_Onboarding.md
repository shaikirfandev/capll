# Developer Onboarding Guide
## TCU Validation Framework v2.0.0

Welcome to the TCU Validation Framework project. This guide gets you from zero to a running build in under 15 minutes.

---

## 1. Environment Setup

### 1.1 Run the setup script
```bash
scripts/setup.sh          # Installs all system dependencies
scripts/setup_vcan.sh     # Creates vcan0 virtual CAN interface
```

### 1.2 Manual setup (Ubuntu 22.04)
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential cmake ninja-build git \
    cppcheck clang clang-tidy clang-format \
    can-utils iproute2 lcov gcovr \
    libssl-dev python3 python3-pip

pip3 install python-can cantools
```

---

## 2. First Build

```bash
git clone <repo-url>
cd tcu_validation_framework

scripts/setup_vcan.sh
scripts/build.sh          # Debug build with tests

# Verify
build/Debug/bin/tcu_validator --help
```

---

## 3. Project Structure

```
tcu_validation_framework/
├── CMakeLists.txt             ← Root build configuration
├── include/                   ← Public headers (9 modules)
│   ├── core/Framework.h
│   ├── can/CANManager.h
│   ├── diagnostics/UDSClient.h
│   ├── validation/TestEngine.h
│   ├── validation/FaultInjector.h
│   ├── firmware/FirmwareFlasher.h
│   ├── firmware/CRCValidator.h
│   ├── telematics/TelematicsSDKAdapter.h
│   ├── logging/Logger.h
│   ├── reporting/ReportGenerator.h
│   └── config/ConfigManager.h
├── src/                       ← Implementation files
│   ├── CMakeLists.txt
│   ├── main.cpp
│   ├── core/         can/    diagnostics/    firmware/
│   ├── telematics/   validation/    logging/
│   ├── reporting/    config/
├── tests/
│   ├── unit/                  ← GoogleTest unit tests
│   ├── integration/           ← Integration tests (needs vcan0)
│   └── stress/                ← Throughput & concurrency tests
├── configs/
│   ├── default.json           ← Base configuration
│   ├── production.json        ← Production overlay
│   └── test.json              ← Test overlay
├── scripts/                   ← Shell utilities
├── tools/                     ← Python helper tools
├── docs/                      ← Documentation (you are here)
├── Dockerfile
├── docker-compose.yml
├── .github/workflows/ci.yml
├── Jenkinsfile
├── .clang-tidy
├── .clang-format
└── sonar-project.properties
```

---

## 4. Code Conventions

### 4.1 Naming
| Construct | Style | Example |
|-----------|-------|---------|
| Namespace | `lower_case` | `tcu` |
| Class | `CamelCase` | `CANManager` |
| Method | `lower_case` | `send_frame()` |
| Member variable | `m_` prefix | `m_socket` |
| Static member | `s_` prefix | `s_instance` |
| Constant | `UPPER_CASE` | `CAN_MAX_DLC` |
| Enum value | `UPPER_CASE` | `TestVerdict::PASS` |
| Template param | `T`, `U` | `template<typename T>` |

### 4.2 Formatting
Run `clang-format` before committing:
```bash
find src/ include/ tests/ -name '*.cpp' -o -name '*.h' | \
    xargs clang-format -i
```

The `.clang-format` in the project root is based on LLVM style with:
- 4-space indentation
- 100-character column limit
- Allman brace style

### 4.3 Error handling
- Return `bool` or `UDSResult`/`TestResult` structs — do not throw from library code
- Use `log->error(...)` and return false for recoverable errors
- RAII for all resource ownership (sockets, threads, fault guards)

### 4.4 Thread safety
- Protect shared mutable state with `std::mutex`
- Use `std::shared_mutex` + `std::shared_lock` for read-heavy data (e.g., ConfigManager)
- Prefer `std::atomic<bool>` for stop flags over mutexed booleans
- Never call user callbacks while holding a lock

---

## 5. Adding a New Module

1. **Header** in `include/<module>/MyModule.h`:
```cpp
#pragma once
#include <string>

namespace tcu {

class MyModule {
public:
    explicit MyModule(const std::string& param);
    bool start();
    void stop();
    std::string health() const;

private:
    std::string m_param;
};

} // namespace tcu
```

2. **Implementation** in `src/<module>/MyModule.cpp`:
```cpp
#include "<module>/MyModule.h"
#include "logging/Logger.h"

namespace tcu {

MyModule::MyModule(const std::string& param) : m_param(param) {}

bool MyModule::start() {
    auto log = Logger::get("my_module");
    log->info("Starting MyModule with param={}", m_param);
    return true;
}

void MyModule::stop() {}

std::string MyModule::health() const { return "OK"; }

} // namespace tcu
```

3. **Add to `src/CMakeLists.txt`**:
```cmake
add_library(tcu_mymodule STATIC src/<module>/MyModule.cpp)
target_include_directories(tcu_mymodule PUBLIC include)
target_link_libraries(tcu_mymodule PRIVATE tcu_logging spdlog::spdlog)
```

4. **Register in `main.cpp`**:
```cpp
auto my_mod = std::make_shared<tcu::MyModule>("param");
framework.register_module(
    "MyModule",
    [&]() { return my_mod->start(); },
    [&]() { my_mod->stop(); },
    [&]() { return my_mod->health(); }
);
```

---

## 6. Adding a Test Case

Add to `tests/unit/test_my_module.cpp`:
```cpp
#include <gtest/gtest.h>
#include "<module>/MyModule.h"

class MyModuleTest : public ::testing::Test {
protected:
    tcu::MyModule mod{"test_param"};
};

TEST_F(MyModuleTest, StartsSuccessfully) {
    EXPECT_TRUE(mod.start());
}

TEST_F(MyModuleTest, StopsCleanly) {
    mod.start();
    EXPECT_NO_FATAL_FAILURE(mod.stop());
}
```

Add to `tests/unit/CMakeLists.txt`:
```cmake
target_sources(unit_tests PRIVATE
    test_my_module.cpp
    # ... existing files ...
)
```

---

## 7. Running Static Analysis Locally

```bash
# cppcheck
cppcheck --enable=all --suppress=missingInclude src/ 2>&1 | grep -v "^$"

# clang-tidy (needs compile_commands.json)
scripts/build.sh   # generates compile_commands.json
run-clang-tidy -p build/Debug/compile_commands.json src/
```

---

## 8. Git Workflow

```
main      ← stable, CI must pass
develop   ← integration branch
feature/* ← feature branches, merge via PR
release/* ← release preparation branches
```

Commit message format:
```
feat(can): add CAN-FD payload validation
fix(uds): handle NRC 0x78 loop timeout
docs: update API reference for FaultInjector
test: add CANManager loopback stress test
```

---

## 9. Key Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| spdlog | 1.13.0 | Async logging |
| nlohmann/json | 3.11.3 | JSON config + reports |
| GoogleTest | 1.14.0 | Unit + integration tests |
| Linux kernel headers | ≥5.4 | SocketCAN (CAN-FD) |

All fetched automatically by CMake FetchContent — no manual download needed.
