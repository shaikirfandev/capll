# Build and Deployment Guide
## TCU Validation Framework v2.0.0

---

## 1. Prerequisites

### 1.1 Ubuntu / Debian (recommended)
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential cmake ninja-build git \
    pkg-config libssl-dev \
    cppcheck clang clang-tidy \
    can-utils iproute2 \
    lcov gcovr python3 python3-pip

pip3 install python-can cantools
```

Verify CMake version (3.18+ required):
```bash
cmake --version   # Must be >= 3.18
```

### 1.2 macOS (development only — no SocketCAN)
```bash
brew install cmake ninja git llvm
```
SocketCAN tests will be skipped on macOS. All other modules compile normally.

---

## 2. Building the Project

### 2.1 Debug build (with sanitizers, tests)
```bash
scripts/build.sh
# BUILD_TYPE defaults to Debug
# Equivalent to:
cmake -S . -B build/Debug -G Ninja -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTS=ON
cmake --build build/Debug --parallel $(nproc)
```

### 2.2 Release build
```bash
BUILD_TYPE=Release scripts/build.sh
```

### 2.3 Manual CMake options
| Option | Default | Description |
|--------|---------|-------------|
| `CMAKE_BUILD_TYPE` | `Debug` | `Debug`, `Release`, `RelWithDebInfo` |
| `BUILD_TESTS` | `ON` | Build GoogleTest suite |
| `ENABLE_SANITIZERS` | Auto (Debug) | ASan + UBSan in Debug builds |
| `CMAKE_EXPORT_COMPILE_COMMANDS` | `ON` | Required by clang-tidy |

---

## 3. Running Tests

### 3.1 All tests (unit + integration)
```bash
scripts/run_tests.sh
```

### 3.2 Individual test binaries
```bash
build/Debug/bin/unit_tests
build/Debug/bin/integration_tests
build/Debug/bin/stress_tests           # Long-running
```

### 3.3 With coverage
```bash
COVERAGE=1 scripts/run_tests.sh
# Generates reports/coverage.html
```

### 3.4 Filtering tests
```bash
FILTER="*CAN*" scripts/run_tests.sh
# Equivalent to --gtest_filter=*CAN*
```

---

## 4. CMake Build Targets

| Target | Description |
|--------|-------------|
| `tcu_validator` | Main executable |
| `unit_tests` | Unit test binary |
| `integration_tests` | Integration test binary |
| `stress_tests` | Stress test binary |
| `cppcheck` | Run cppcheck static analysis |
| `clang-tidy` | Run clang-tidy (requires compile_commands.json) |
| `install` | Install to `CMAKE_INSTALL_PREFIX` |

```bash
cmake --build build/Debug --target cppcheck
cmake --build build/Debug --target clang-tidy
```

---

## 5. CPack Packaging

### 5.1 DEB package (Ubuntu/Debian)
```bash
cd build/Release
cpack -G DEB
# Produces: TCU_Validation_Framework-2.0.0-Linux.deb
```

### 5.2 TGZ tarball
```bash
cpack -G TGZ
# Produces: TCU_Validation_Framework-2.0.0-Linux.tar.gz
```

### 5.3 Install DEB
```bash
sudo dpkg -i TCU_Validation_Framework-2.0.0-Linux.deb
tcu_validator --help
```

---

## 6. Docker Deployment

### 6.1 Build runtime image
```bash
docker build --target runtime -t tcu-validation-framework:latest .
```

### 6.2 Build test image
```bash
docker build --target test -t tcu-validation-framework:test .
```

### 6.3 Run validator
```bash
docker run --rm \
    --cap-add=NET_ADMIN \
    -v $(pwd)/configs:/app/configs:ro \
    -v $(pwd)/reports:/app/reports \
    tcu-validation-framework:latest \
    --config /app/configs/default.json --simulate
```

### 6.4 Run full stack with docker-compose
```bash
docker-compose up tcu-validator mqtt-broker
```

### 6.5 Run tests in Docker
```bash
docker-compose --profile test up tcu-test
```

---

## 7. CI/CD Integration

### 7.1 GitHub Actions
The workflow file is at `.github/workflows/ci.yml`.  
See `docs/guides/CICD_Setup.md` for configuration details.

### 7.2 Jenkins
The `Jenkinsfile` in the project root defines a declarative pipeline.  
See `docs/guides/CICD_Setup.md` for Jenkins agent requirements.

---

## 8. Installation

```bash
# Install to /usr/local (default)
cmake --install build/Release

# Custom prefix
cmake --install build/Release --prefix /opt/tcu-framework
```

Installed layout:
```
{prefix}/
├── bin/
│   └── tcu_validator
├── lib/
│   ├── libtcu_core.a
│   ├── libtcu_can.a
│   └── ...
├── include/
│   └── tcu/
│       └── ...
└── share/
    └── tcu_validation_framework/
        └── TCU_Validation_FrameworkConfig.cmake
```

### Using as a CMake package
```cmake
find_package(TCU_Validation_Framework REQUIRED)
target_link_libraries(my_target PRIVATE tcu::tcu_core tcu::tcu_can)
```

---

## 9. Build Troubleshooting

### CMake can't find Ninja
```bash
apt-get install ninja-build   # Ubuntu
brew install ninja             # macOS
```

### FetchContent fails (no internet)
Pre-download dependencies and point CMake to local archives:
```bash
# Place spdlog, nlohmann-json, googletest zips in deps/
cmake -S . -B build \
    -DFETCHCONTENT_SOURCE_DIR_SPDLOG=/path/to/spdlog \
    -DFETCHCONTENT_SOURCE_DIR_JSON=/path/to/json \
    -DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=/path/to/googletest
```

### SocketCAN headers not found (non-Linux)
SocketCAN sources conditionally compile only on Linux. The build will succeed on macOS but `CANManager::open()` will return false at runtime.

### ASan library not found (Ubuntu packaging)
```bash
sudo apt-get install libasan6   # Ubuntu 22.04
```
