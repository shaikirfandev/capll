cmake_minimum_required(VERSION 3.21)
project(image_sensor_platform VERSION 2.0.0 LANGUAGES C CXX)

# ─────────────────────────────────────────────────────────────────────────────
# Build options
# ─────────────────────────────────────────────────────────────────────────────
option(ISF_TARGET_BARE_METAL  "Build for bare-metal embedded target"      OFF)
option(ISF_TARGET_LINUX       "Build Linux kernel module targets"          OFF)
option(ISF_TARGET_HOST        "Build host-side library and tests"          ON)
option(ISF_BUILD_TESTS        "Build unit and integration tests"           ON)
option(ISF_ENABLE_SANITIZERS  "Enable ASan + UBSan (host builds)"         OFF)
option(ISF_ENABLE_COVERAGE    "Enable code coverage (GCC/Clang)"          OFF)
option(ISF_RTOS_FREERTOS      "Use FreeRTOS RTOS abstraction"              OFF)
option(ISF_OS_POSIX           "Use POSIX (Linux/macOS) OS abstraction"     ON)

# ─────────────────────────────────────────────────────────────────────────────
# Language standards
# ─────────────────────────────────────────────────────────────────────────────
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ─────────────────────────────────────────────────────────────────────────────
# Platform detection and toolchain selection
# ─────────────────────────────────────────────────────────────────────────────
if(ISF_TARGET_BARE_METAL)
    message(STATUS "Building for bare-metal (ARM)")
    set(CMAKE_SYSTEM_NAME Generic)
    set(CMAKE_SYSTEM_PROCESSOR arm)
    # Toolchain file: cmake/toolchains/arm-none-eabi.cmake
endif()

# ─────────────────────────────────────────────────────────────────────────────
# Core firmware library (platform-agnostic)
# ─────────────────────────────────────────────────────────────────────────────
add_library(isf_core STATIC
    firmware/hal/src/hal_i2c.c
    firmware/hal/src/hal_dma.c
    firmware/hal/src/hal_gpio.c
    firmware/hal/src/hal_spi.c
    firmware/hal/src/hal_uart.c
    firmware/drivers/mipi_csi2/src/mipi_csi2.c
    firmware/sensor/src/sensor_manager.c
    firmware/sensor/src/imx477_driver.c
    firmware/sensor/src/ov5640_driver.c
    firmware/sensor/src/ar0820_driver.c
    firmware/streaming/src/streaming_engine.c
    firmware/diagnostics/src/isf_logger.c
    firmware/diagnostics/src/health_monitor.c
    firmware/middleware/src/memory_pool.c
    firmware/middleware/src/sync_manager.c
)

target_include_directories(isf_core PUBLIC
    firmware/hal/include
    firmware/drivers/mipi_csi2/include
    firmware/sensor/include
    firmware/streaming/include
    firmware/diagnostics/include
    firmware/middleware/include
)

target_compile_features(isf_core PUBLIC c_std_11)

target_compile_options(isf_core PRIVATE
    $<$<C_COMPILER_ID:GNU,Clang>:
        -Wall -Wextra -Wpedantic -Werror
        -Wshadow -Wformat=2 -Wconversion
        -Wmissing-prototypes -Wstrict-prototypes
    >
)

# RTOS selection
if(ISF_RTOS_FREERTOS)
    target_compile_definitions(isf_core PUBLIC ISF_RTOS_FREERTOS=1)
elseif(ISF_OS_POSIX)
    target_compile_definitions(isf_core PUBLIC ISF_OS_POSIX=1)
    target_link_libraries(isf_core PUBLIC pthread)
endif()

# ─────────────────────────────────────────────────────────────────────────────
# Sanitizers
# ─────────────────────────────────────────────────────────────────────────────
if(ISF_ENABLE_SANITIZERS AND CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(isf_core PUBLIC -fsanitize=address,undefined -fno-omit-frame-pointer)
    target_link_options(isf_core PUBLIC -fsanitize=address,undefined)
endif()

# ─────────────────────────────────────────────────────────────────────────────
# Coverage
# ─────────────────────────────────────────────────────────────────────────────
if(ISF_ENABLE_COVERAGE AND CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(isf_core PUBLIC --coverage -fprofile-arcs -ftest-coverage)
    target_link_options(isf_core PUBLIC --coverage)
endif()

# ─────────────────────────────────────────────────────────────────────────────
# Firmware demo executable (bare-metal simulation on host)
# ─────────────────────────────────────────────────────────────────────────────
if(ISF_TARGET_HOST)
    add_executable(isf_demo firmware/app/main.c)
    target_link_libraries(isf_demo PRIVATE isf_core)
endif()

# ─────────────────────────────────────────────────────────────────────────────
# Google Test unit tests
# ─────────────────────────────────────────────────────────────────────────────
if(ISF_BUILD_TESTS)
    enable_testing()
    find_package(GTest QUIET)

    if(GTest_FOUND)
        add_executable(isf_unit_tests
            tests/unit/test_hal_i2c.cpp
            tests/unit/test_sensor_manager.cpp
            tests/unit/test_streaming_engine.cpp
            tests/unit/test_diagnostics.cpp
            tests/unit/test_memory_pool.cpp
            tests/unit/test_crc.cpp
        )
        target_link_libraries(isf_unit_tests PRIVATE isf_core GTest::gtest_main GTest::gmock)
        add_test(NAME isf_unit_tests COMMAND isf_unit_tests --gtest_output=xml:reports/unit_results.xml)
    else()
        message(WARNING "GTest not found — skipping C++ unit tests")
    endif()
endif()

# ─────────────────────────────────────────────────────────────────────────────
# Static analysis targets
# ─────────────────────────────────────────────────────────────────────────────
find_program(CPPCHECK cppcheck)
if(CPPCHECK)
    add_custom_target(cppcheck
        COMMAND ${CPPCHECK}
            --enable=all --error-exitcode=1
            --suppress=missingIncludeSystem
            --std=c11
            --quiet
            ${CMAKE_SOURCE_DIR}/firmware
        COMMENT "Running cppcheck static analysis"
    )
endif()

find_program(CLANG_TIDY clang-tidy)
if(CLANG_TIDY)
    set_target_properties(isf_core PROPERTIES C_CLANG_TIDY
        "${CLANG_TIDY};-p;${CMAKE_BINARY_DIR};--config-file=${CMAKE_SOURCE_DIR}/.clang-tidy"
    )
endif()
