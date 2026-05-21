# Deployment Guide
## Avionics FMS v3.2.1

## 1. Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| CMake | 4.0+ | Build system |
| GCC 12+ / Clang 14+ | — | C++17 compiler |
| Python 3.8+ | — | FetchContent / scripts |
| gcovr 7+ | — | Coverage reports |
| cppcheck 2+ | — | Static analysis |
| clang-tidy 14+ | — | Static analysis |

## 2. Build (Development)

```bash
git clone <repo> && cd avionics_fms

# Debug build with tests and sanitizers
cmake -B build_debug \
  -DCMAKE_BUILD_TYPE=Debug \
  -DFMS_ENABLE_TESTS=ON \
  -DFMS_ENABLE_ASAN=ON \
  -DFMS_ENABLE_UBSAN=ON
cmake --build build_debug --parallel $(nproc)

# Release build
cmake -B build_release -DCMAKE_BUILD_TYPE=Release
cmake --build build_release --parallel $(nproc)
```

Or use the convenience script:
```bash
./scripts/build.sh Debug    # Debug build
./scripts/build.sh Release  # Release build
```

## 3. Run Unit Tests

```bash
cd build_debug
ctest --output-on-failure
# Or filter:
ctest -R test_navigation -V
```

Via script: `./scripts/run_tests.sh`

## 4. Coverage Report

```bash
./scripts/generate_coverage.sh
# Opens: build/coverage/index.html
```

Targets: 100% statement, 100% decision (DO-178C DAL-B)

## 5. Static Analysis

```bash
./scripts/static_analysis.sh
# cppcheck + clang-tidy output in build/analysis/
```

## 6. Docker Build

```bash
docker build --target builder -t fms-builder .
docker run --rm fms-builder ctest --output-on-failure

# Full test pipeline:
docker build --target tester -t fms-tester .
docker run --rm fms-tester
```

## 7. CI/CD (GitHub Actions)

`.github/workflows/ci.yml` runs automatically on push/PR:
- Linux (ubuntu-22.04) + macOS-13
- Debug + Release matrix
- ASAN + UBSAN enabled
- Coverage gate (gcovr)
- Static analysis (cppcheck)

## 8. Runtime Configuration

Edit `config/fms_config.json`:
```json
{
  "log_level": "INFO",
  "cycle_time_ms": 50,
  "rnp_nm": 2.0,
  "initial_fuel_kg": 18000,
  "watchdog_period_ms": 500
}
```

## 9. Embedded Target Build

For FreeRTOS target:
```bash
cmake -B build_freertos \
  -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake \
  -DFMS_TARGET_FREERTOS=ON \
  -DFMS_ENABLE_TESTS=OFF \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build_freertos --parallel 4
```
