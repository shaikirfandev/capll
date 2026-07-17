cmake_minimum_required(VERSION 3.21)
project(adas_realtime_cpp VERSION 2.0.0 LANGUAGES CXX)

# ──────────────────────────────────────────────────────────────────────────────
# Toolchain settings
# ──────────────────────────────────────────────────────────────────────────────
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ──────────────────────────────────────────────────────────────────────────────
# Build options
# ──────────────────────────────────────────────────────────────────────────────
option(ADAS_BUILD_TESTS       "Build unit tests"                         ON)
option(ADAS_ENABLE_SANITIZERS "Enable address + UB sanitizers (dev only)" OFF)
option(ADAS_ENABLE_COVERAGE   "Enable gcov line coverage (GCC/Clang)"     OFF)

# ──────────────────────────────────────────────────────────────────────────────
# Core library: no OS, no socket, no dynamic allocation
# ──────────────────────────────────────────────────────────────────────────────
add_library(adas_core
    # Control algorithms
    src/estimation.cpp
    src/controllers.cpp
    src/supervisor.cpp
    src/vehicle_dynamics.cpp
    # Sensor fusion
    src/sensor_fusion.cpp
    # Runtime shell
    src/runtime.cpp
    # Protocol / transport
    src/can_codec.cpp
    src/someip_stub.cpp
    # Diagnostics
    src/diagnostics.cpp
    # Gateway
    src/vehicle_gateway.cpp
    # OS integration helpers
    src/qnx_integration.cpp)

target_include_directories(adas_core PUBLIC include)
target_compile_features(adas_core PUBLIC cxx_std_20)
target_compile_options(adas_core PRIVATE
    $<$<CXX_COMPILER_ID:Clang,GNU>:-Wall -Wextra -Wpedantic -Werror>
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /WX>)
set_target_properties(adas_core PROPERTIES
    CXX_VISIBILITY_PRESET  hidden
    VISIBILITY_INLINES_HIDDEN YES)

if(ADAS_ENABLE_SANITIZERS AND CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(adas_core PRIVATE
        -fsanitize=address,undefined -fno-omit-frame-pointer)
    target_link_options(adas_core INTERFACE -fsanitize=address,undefined)
endif()

if(ADAS_ENABLE_COVERAGE AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(adas_core PUBLIC --coverage -fprofile-arcs -ftest-coverage)
    target_link_options(adas_core PUBLIC --coverage)
endif()

# ──────────────────────────────────────────────────────────────────────────────
# Demo executable (50 Hz control loop)
# ──────────────────────────────────────────────────────────────────────────────
add_executable(adas_demo app/main.cpp)
target_link_libraries(adas_demo PRIVATE adas_core)

# ──────────────────────────────────────────────────────────────────────────────
# Test executables
# ──────────────────────────────────────────────────────────────────────────────
if(ADAS_BUILD_TESTS)
    enable_testing()

    # Core algorithm tests
    add_executable(adas_tests tests/adas_tests.cpp)
    target_link_libraries(adas_tests PRIVATE adas_core)
    add_test(NAME adas_core_tests COMMAND adas_tests)

    # Extended module tests
    add_executable(adas_extended_tests tests/extended_tests.cpp)
    target_link_libraries(adas_extended_tests PRIVATE adas_core)
    add_test(NAME adas_extended_tests COMMAND adas_extended_tests)
endif()
