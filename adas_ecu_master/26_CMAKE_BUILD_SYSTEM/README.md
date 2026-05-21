# 26 — CMake Build System for Automotive ECU

> **Tool:** CMake 3.16+ (industry standard for C/C++ automotive projects)  
> **Target:** Host build (x86_64 for unit tests) + Cross-compile (arm-none-eabi for ECU)

---

## 26.1 Build Commands

```bash
# Navigate to adas_ecu_master/ root
cd /Users/macbook/Documents/capl/adas_ecu_master

# Copy top-level CMakeLists.txt from this folder to root
cp 26_CMAKE_BUILD_SYSTEM/CMakeLists.txt .

# Create build directory
mkdir -p build && cd build

# Configure — Debug with sanitizers
cmake .. -DCMAKE_BUILD_TYPE=Debug

# Build all targets
make -j4

# Run all unit tests
make run_tests

# OR via CTest:
ctest --verbose

# Build + generate coverage report (Coverage mode):
cmake .. -DCMAKE_BUILD_TYPE=Coverage
make -j4
make coverage
open coverage_html/index.html
```

---

## 26.2 Cross-Compilation for ARM ECU

```bash
# Create toolchain file: cmake/arm_ecu.cmake
cat > cmake/arm_ecu.cmake << 'EOF'
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

set(CMAKE_C_COMPILER   arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER arm-none-eabi-g++)
set(CMAKE_ASM_COMPILER arm-none-eabi-as)
set(CMAKE_AR           arm-none-eabi-ar)
set(CMAKE_OBJCOPY      arm-none-eabi-objcopy)
set(CMAKE_SIZE         arm-none-eabi-size)

# ECU-specific flags
set(CPU_FLAGS "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")
set(ECU_FLAGS "-fno-exceptions -fno-rtti -fno-use-cxa-atexit -ffunction-sections -fdata-sections")

set(CMAKE_C_FLAGS_INIT   "${CPU_FLAGS} ${ECU_FLAGS}")
set(CMAKE_CXX_FLAGS_INIT "${CPU_FLAGS} ${ECU_FLAGS} -std=c++17")
set(CMAKE_EXE_LINKER_FLAGS_INIT "--specs=nano.specs -Wl,--gc-sections -Wl,-Map=output.map")

# Don't try to run test binaries on host
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
EOF

# Configure for ARM target
cmake .. -DCMAKE_TOOLCHAIN_FILE=../cmake/arm_ecu.cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF
make -j4

# Check binary size
arm-none-eabi-size lka_ecu
# Expected: text ~8KB, data ~0.5KB, bss ~2KB
```

---

## 26.3 CMake Target Structure

```
adas_ecu_master/
├── CMakeLists.txt          ← copied from 26_CMAKE_BUILD_SYSTEM/
├── cmake/
│   └── arm_ecu.cmake       ← toolchain file
├── build/                  ← out-of-source build
│   ├── ecu_cpp_patterns    ← host executable
│   ├── can_parser
│   ├── sensor_fusion
│   ├── lka_ecu
│   ├── acc_ecu
│   ├── automotive_hsm
│   ├── test_adas_ecu       ← GTest binary
│   └── coverage_html/      ← coverage report (Coverage mode)
└── ...
```

---

## 26.4 Static Analysis Integration

```bash
# cppcheck (free, cross-platform):
brew install cppcheck  # macOS
make static_analysis   # Runs cppcheck on all source files

# clang-tidy (LLVM):
# Add to CMakeLists.txt:
# set(CMAKE_CXX_CLANG_TIDY clang-tidy;-checks=clang-analyzer-*,cppcoreguidelines-*)

# Polyspace (commercial):
polyspace-bug-finder \
  -sources $(find . -name "*.cpp" -not -path "*/build/*") \
  -I include \
  -compiler g++ \
  -misra-cpp 2008 \
  -autosar-cpp14 \
  -results-dir polyspace_results/
```

---

## 26.5 CI/CD Integration (GitHub Actions)

```yaml
# .github/workflows/adas_ecu.yml
name: ADAS ECU Build & Test

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build-and-test:
    runs-on: ubuntu-22.04
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y cmake g++ libgtest-dev lcov cppcheck
    
    - name: Configure (Debug + Coverage)
      run: |
        cmake -S . -B build \
          -DCMAKE_BUILD_TYPE=Coverage \
          -DBUILD_TESTS=ON
    
    - name: Build
      run: cmake --build build -j4
    
    - name: Run unit tests
      run: ctest --test-dir build --verbose
    
    - name: Generate coverage
      run: cmake --build build --target coverage
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: build/coverage_filtered.info
    
    - name: Static analysis
      run: cmake --build build --target static_analysis
```
