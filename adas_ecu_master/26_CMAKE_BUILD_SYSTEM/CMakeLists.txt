cmake_minimum_required(VERSION 3.16)
project(adas_ecu_master CXX C)

# ============================================================================
# GLOBAL SETTINGS
# ============================================================================

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)           # -std=c++17 not -std=gnu++17

# Export compile_commands.json for clangd / static analysis
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ============================================================================
# BUILD TYPES
# ============================================================================
# cmake -DCMAKE_BUILD_TYPE=Debug   → debug symbols, sanitisers
# cmake -DCMAKE_BUILD_TYPE=Release → optimised for ECU target
# cmake -DCMAKE_BUILD_TYPE=Coverage → gcov profiling

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug)
endif()

# ============================================================================
# COMPILER FLAGS — Host build (x86_64)
# ============================================================================

add_compile_options(
    -Wall
    -Wextra
    -Wpedantic
    -Wshadow
    -Wno-unused-parameter
    -Wconversion
    -Wdouble-promotion
)

# ECU-compatible flags (no STL heap, no exceptions, no RTTI)
# Uncomment for ECU build:
# add_compile_options(-fno-exceptions -fno-rtti -fno-use-cxa-atexit)

# Debug: AddressSanitizer catches memory bugs
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_options(-g -O0 -fsanitize=address -fsanitize=undefined)
    add_link_options(-fsanitize=address -fsanitize=undefined)
endif()

# Coverage
if(CMAKE_BUILD_TYPE STREQUAL "Coverage")
    add_compile_options(-O0 --coverage -fprofile-arcs -ftest-coverage)
    add_link_options(--coverage)
endif()

# Release: optimise + strip debug info
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_compile_options(-O2 -DNDEBUG)
endif()

# ============================================================================
# CROSS-COMPILATION TOOLCHAIN (ARM ECU target)
# ============================================================================
# Usage: cmake -DCMAKE_TOOLCHAIN_FILE=cmake/arm_ecu.cmake
# File: cmake/arm_ecu.cmake
#   set(CMAKE_SYSTEM_NAME Generic)
#   set(CMAKE_C_COMPILER   arm-none-eabi-gcc)
#   set(CMAKE_CXX_COMPILER arm-none-eabi-g++)
#   set(CMAKE_EXE_LINKER_FLAGS "--specs=nosys.specs -Wl,--gc-sections")

# ============================================================================
# INCLUDE DIRECTORIES
# ============================================================================

include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/01_CPP_FOR_ECU
    ${CMAKE_SOURCE_DIR}/07_LKA_MODULE
    ${CMAKE_SOURCE_DIR}/09_ACC_MODULE
)

# ============================================================================
# EXECUTABLES — Each module builds a standalone demo
# ============================================================================

# 01 — C++ ECU Patterns demo
add_executable(ecu_cpp_patterns
    01_CPP_FOR_ECU/ecu_cpp_patterns.cpp
)
target_compile_features(ecu_cpp_patterns PRIVATE cxx_std_17)

# 04 — CAN Parser demo
add_executable(can_parser
    04_CAN_PROTOCOL/can_parser.cpp
)

# 06 — Sensor Fusion / Kalman Filter demo
add_executable(sensor_fusion
    06_SENSOR_FUSION/sensor_fusion.cpp
)

# 07 — LKA ECU demo
add_executable(lka_ecu
    07_LKA_MODULE/lka_ecu.cpp
)

# 09 — ACC ECU demo
add_executable(acc_ecu
    09_ACC_MODULE/acc_ecu.cpp
)

# 10 — Automotive HSM demo
add_executable(automotive_hsm
    10_STATE_MACHINES/automotive_state_machine.cpp
)

# ============================================================================
# UNIT TESTS (Google Test)
# ============================================================================
# Prerequisites: brew install googletest (macOS) OR apt-get install libgtest-dev (Linux)

option(BUILD_TESTS "Build unit tests (requires Google Test)" ON)

if(BUILD_TESTS)
    find_package(GTest QUIET)

    if(GTest_FOUND)
        enable_testing()

        add_executable(test_adas_ecu
            15_UNIT_TESTING/test_adas_ecu.cpp
        )
        target_link_libraries(test_adas_ecu
            PRIVATE GTest::GTest GTest::Main
        )
        target_compile_options(test_adas_ecu PRIVATE -O0)

        # Register with CTest
        include(GoogleTest)
        gtest_discover_tests(test_adas_ecu)

        # Custom target: run tests + print results
        add_custom_target(run_tests
            COMMAND test_adas_ecu --gtest_color=yes
            DEPENDS test_adas_ecu
            COMMENT "Running ADAS ECU unit tests"
        )
    else()
        message(WARNING "Google Test not found — unit tests disabled. Install with: brew install googletest")
    endif()
endif()

# ============================================================================
# STATIC ANALYSIS TARGET
# ============================================================================
# Requires: cppcheck (brew install cppcheck)

find_program(CPPCHECK cppcheck)
if(CPPCHECK)
    add_custom_target(static_analysis
        COMMAND ${CPPCHECK}
            --enable=all
            --std=c++17
            --suppress=missingIncludeSystem
            --error-exitcode=1
            ${CMAKE_SOURCE_DIR}/01_CPP_FOR_ECU
            ${CMAKE_SOURCE_DIR}/04_CAN_PROTOCOL
            ${CMAKE_SOURCE_DIR}/06_SENSOR_FUSION
            ${CMAKE_SOURCE_DIR}/07_LKA_MODULE
            ${CMAKE_SOURCE_DIR}/09_ACC_MODULE
            ${CMAKE_SOURCE_DIR}/10_STATE_MACHINES
        COMMENT "Running cppcheck static analysis"
    )
endif()

# ============================================================================
# COVERAGE REPORT TARGET
# ============================================================================
# cmake -DCMAKE_BUILD_TYPE=Coverage && make && make coverage

find_program(LCOV lcov)
find_program(GENHTML genhtml)

if(LCOV AND GENHTML AND BUILD_TESTS AND GTest_FOUND)
    add_custom_target(coverage
        # Run tests first
        COMMAND ${CMAKE_CTEST_COMMAND} --verbose
        # Collect coverage
        COMMAND ${LCOV} --capture --directory ${CMAKE_BINARY_DIR} --output-file coverage.info
        # Remove system headers
        COMMAND ${LCOV} --remove coverage.info '/usr/*' --output-file coverage_filtered.info
        # Generate HTML report
        COMMAND ${GENHTML} coverage_filtered.info --output-directory coverage_html
        DEPENDS test_adas_ecu
        COMMENT "Generating code coverage report in coverage_html/"
    )
endif()

# ============================================================================
# PRINT BUILD SUMMARY
# ============================================================================

message(STATUS "=== ADAS ECU Master Build Configuration ===")
message(STATUS "Build type:     ${CMAKE_BUILD_TYPE}")
message(STATUS "CXX standard:   ${CMAKE_CXX_STANDARD}")
message(STATUS "Compiler:       ${CMAKE_CXX_COMPILER}")
message(STATUS "Unit tests:     ${BUILD_TESTS}")
message(STATUS "Source dir:     ${CMAKE_SOURCE_DIR}")
message(STATUS "Binary dir:     ${CMAKE_BINARY_DIR}")
message(STATUS "============================================")
