cmake_minimum_required(VERSION 3.18)
project(BluetoothFirmware
    VERSION 2.1.0
    DESCRIPTION "Production-Grade Automotive Bluetooth Firmware Stack — C++17"
    LANGUAGES CXX C
)

# ─── Language standard ──────────────────────────────────────────────────────
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# ─── Build options ───────────────────────────────────────────────────────────
option(BT_ENABLE_BLE          "Enable BLE subsystem"                 ON)
option(BT_ENABLE_CLASSIC      "Enable Classic Bluetooth subsystem"   ON)
option(BT_ENABLE_A2DP         "Enable A2DP audio streaming"          ON)
option(BT_ENABLE_HFP          "Enable HFP hands-free profile"        ON)
option(BT_ENABLE_HID          "Enable HID device profile"            ON)
option(BT_ENABLE_OTA          "Enable OTA firmware update"           ON)
option(BT_ENABLE_DIAGNOSTICS  "Enable diagnostics module"            ON)
option(BT_ENABLE_TESTS        "Build unit and integration tests"      ON)
option(BT_ASAN                "Enable AddressSanitizer (debug only)"  OFF)
option(BT_TSAN                "Enable ThreadSanitizer (debug only)"   OFF)
option(BT_COVERAGE            "Enable coverage instrumentation"       OFF)
option(BT_RTOS_FREERTOS       "Use FreeRTOS abstraction (else std)"  OFF)
option(BT_LOG_LEVEL_VERBOSE   "Enable verbose logging"               ON)

# ─── Compiler flags ──────────────────────────────────────────────────────────
set(BT_COMPILE_OPTIONS
    -Wall
    -Wextra
    -Wpedantic
    -Wconversion
    -Wshadow
    -Wno-unused-parameter
    -ffunction-sections
    -fdata-sections
)

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    list(APPEND BT_COMPILE_OPTIONS -g3 -O0)
    if(BT_ASAN)
        list(APPEND BT_COMPILE_OPTIONS -fsanitize=address,undefined)
        add_link_options(-fsanitize=address,undefined)
    endif()
    if(BT_TSAN)
        list(APPEND BT_COMPILE_OPTIONS -fsanitize=thread)
        add_link_options(-fsanitize=thread)
    endif()
    if(BT_COVERAGE)
        list(APPEND BT_COMPILE_OPTIONS --coverage -fprofile-arcs -ftest-coverage)
        add_link_options(--coverage)
    endif()
else()
    list(APPEND BT_COMPILE_OPTIONS -O2 -DNDEBUG)
endif()

# ─── Dependencies (FetchContent) ─────────────────────────────────────────────
include(FetchContent)

FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG        v1.13.0
)
FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG        v3.11.3
)
if(BT_ENABLE_TESTS)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG        v1.14.0
    )
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)
endif()

FetchContent_MakeAvailable(spdlog nlohmann_json)

# ─── Core library ────────────────────────────────────────────────────────────
add_library(bt_core STATIC
    # Common utilities
    src/common/Logger.cpp
    src/common/RingBuffer.cpp

    # HAL simulation layer
    src/hal/UartDriver.cpp
    src/hal/SpiDriver.cpp
    src/hal/PowerManager.cpp
    src/hal/GpioDriver.cpp

    # RTOS abstraction
    src/rtos/StdThreadTask.cpp
    src/rtos/StdMutex.cpp
    src/rtos/StdQueue.cpp
    src/rtos/StdSemaphore.cpp

    # Bluetooth stack
    src/bt/BluetoothController.cpp
    src/bt/BleAdvertiser.cpp
    src/bt/BleScanner.cpp
    src/bt/GattServer.cpp
    src/bt/GattClient.cpp
    src/bt/AttProtocol.cpp
    src/bt/L2capManager.cpp
    src/bt/PairingManager.cpp
    src/bt/SecurityManager.cpp
    src/bt/RfcommSimulator.cpp
    src/bt/ConnectionStateMachine.cpp
    src/bt/EventBus.cpp

    # Profiles
    src/bt/profiles/A2dpSimulator.cpp
    src/bt/profiles/HfpSimulator.cpp
    src/bt/profiles/HidDevice.cpp

    # Application layer
    src/app/ConnectionManager.cpp
    src/app/DiagnosticsModule.cpp
)

if(BT_ENABLE_OTA)
    target_sources(bt_core PRIVATE src/app/OtaManager.cpp)
endif()

target_include_directories(bt_core
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_compile_options(bt_core PRIVATE ${BT_COMPILE_OPTIONS})

target_link_libraries(bt_core
    PUBLIC
        spdlog::spdlog
        nlohmann_json::nlohmann_json
    PRIVATE
        pthread
)

# ─── Compile definitions ─────────────────────────────────────────────────────
if(BT_ENABLE_BLE)
    target_compile_definitions(bt_core PUBLIC BT_BLE_ENABLED=1)
endif()
if(BT_ENABLE_CLASSIC)
    target_compile_definitions(bt_core PUBLIC BT_CLASSIC_ENABLED=1)
endif()
if(BT_ENABLE_A2DP)
    target_compile_definitions(bt_core PUBLIC BT_A2DP_ENABLED=1)
endif()
if(BT_ENABLE_HFP)
    target_compile_definitions(bt_core PUBLIC BT_HFP_ENABLED=1)
endif()
if(BT_ENABLE_OTA)
    target_compile_definitions(bt_core PUBLIC BT_OTA_ENABLED=1)
endif()
if(BT_LOG_LEVEL_VERBOSE)
    target_compile_definitions(bt_core PUBLIC BT_LOG_VERBOSE=1)
endif()

# ─── Main executable ─────────────────────────────────────────────────────────
add_executable(bt_firmware src/main.cpp)
target_link_libraries(bt_firmware PRIVATE bt_core)
target_compile_options(bt_firmware PRIVATE ${BT_COMPILE_OPTIONS})

# ─── Tests ───────────────────────────────────────────────────────────────────
if(BT_ENABLE_TESTS)
    enable_testing()
    add_subdirectory(tests/unit)
    add_subdirectory(tests/integration)
endif()

# ─── Install ─────────────────────────────────────────────────────────────────
install(TARGETS bt_firmware DESTINATION bin)
install(TARGETS bt_core     DESTINATION lib)
install(DIRECTORY include/  DESTINATION include)

# ─── Summary ─────────────────────────────────────────────────────────────────
message(STATUS "=== Bluetooth Firmware Build Configuration ===")
message(STATUS "  Version     : ${PROJECT_VERSION}")
message(STATUS "  Build type  : ${CMAKE_BUILD_TYPE}")
message(STATUS "  BLE         : ${BT_ENABLE_BLE}")
message(STATUS "  Classic BT  : ${BT_ENABLE_CLASSIC}")
message(STATUS "  A2DP        : ${BT_ENABLE_A2DP}")
message(STATUS "  HFP         : ${BT_ENABLE_HFP}")
message(STATUS "  HID         : ${BT_ENABLE_HID}")
message(STATUS "  OTA         : ${BT_ENABLE_OTA}")
message(STATUS "  Tests       : ${BT_ENABLE_TESTS}")
message(STATUS "  ASan        : ${BT_ASAN}")
message(STATUS "  TSan        : ${BT_TSAN}")
message(STATUS "==============================================")
