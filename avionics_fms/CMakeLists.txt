cmake_minimum_required(VERSION 3.20)
project(AvionicsFMS VERSION 3.2.1 LANGUAGES C CXX)

# ── Standards ──────────────────────────────────────────────────────────────────
set(CMAKE_C_STANDARD   11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ── Build Options ──────────────────────────────────────────────────────────────
option(FMS_ENABLE_TESTS      "Build unit and integration tests"   ON)
option(FMS_ENABLE_COVERAGE   "Enable gcov coverage instrumentation" OFF)
option(FMS_ENABLE_ASAN       "Enable AddressSanitizer"            OFF)
option(FMS_ENABLE_UBSAN      "Enable UndefinedBehaviorSanitizer"  OFF)
option(FMS_TARGET_FREERTOS   "Build for FreeRTOS target"          OFF)
option(FMS_TARGET_VXWORKS    "Build for VxWorks target"           OFF)
option(FMS_ENABLE_ARINC429   "Enable ARINC 429 driver"            ON)
option(FMS_ENABLE_ARINC664   "Enable ARINC 664/AFDX driver"       ON)
option(FMS_ENABLE_CAN_AERO   "Enable CAN Aerospace driver"        ON)
option(FMS_STRICT_WARNINGS   "Enable all compiler warnings"       ON)

# ── Compiler Flags ─────────────────────────────────────────────────────────────
if(FMS_STRICT_WARNINGS)
    add_compile_options(
        -Wall -Wextra -Wpedantic
        -Wconversion -Wshadow -Wcast-align
        -Wdouble-promotion -Wformat=2
        -Wnull-dereference -Wundef
        $<$<COMPILE_LANGUAGE:CXX>:-Wnon-virtual-dtor>
        $<$<COMPILE_LANGUAGE:CXX>:-Woverloaded-virtual>
    )
endif()

if(FMS_ENABLE_ASAN)
    add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address)
endif()

if(FMS_ENABLE_UBSAN)
    add_compile_options(-fsanitize=undefined)
    add_link_options(-fsanitize=undefined)
endif()

if(FMS_ENABLE_COVERAGE)
    add_compile_options(--coverage -fprofile-arcs -ftest-coverage)
    add_link_options(--coverage)
endif()

# ── Dependencies via FetchContent ──────────────────────────────────────────────
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

if(FMS_ENABLE_TESTS)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG        v1.14.0
    )
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)
endif()

FetchContent_MakeAvailable(spdlog nlohmann_json)

# ── Include Directories ────────────────────────────────────────────────────────
set(FMS_INCLUDE_DIRS
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_SOURCE_DIR}/config
)

# ── Core Library Sources ───────────────────────────────────────────────────────
set(FMS_COMMON_SOURCES
    src/common/Logger.cpp
    src/common/FixedPoint.cpp
    src/common/RingBuffer.cpp
)

set(FMS_RTOS_SOURCES
    src/rtos/FreeRtosTask.cpp
    src/rtos/FreeRtosMutex.cpp
    src/rtos/FreeRtosQueue.cpp
    src/rtos/FreeRtosTimer.cpp
)

set(FMS_SENSOR_SOURCES
    src/sensors/AirDataSystem.cpp
    src/sensors/InertialNavSystem.cpp
    src/sensors/GpsReceiver.cpp
    src/sensors/SensorFusion.cpp
)

set(FMS_COMMS_SOURCES
    src/comms/Arinc429Driver.cpp
    src/comms/DataBusMonitor.cpp
)

if(FMS_ENABLE_ARINC664)
    list(APPEND FMS_COMMS_SOURCES src/comms/Arinc664Driver.cpp)
endif()

if(FMS_ENABLE_CAN_AERO)
    list(APPEND FMS_COMMS_SOURCES src/comms/CanAerospaceDriver.cpp)
endif()

set(FMS_SAFETY_SOURCES
    src/safety/FaultManager.cpp
    src/safety/Watchdog.cpp
    src/safety/HealthMonitor.cpp
)

set(FMS_CORE_SOURCES
    src/fms/NavigationEngine.cpp
    src/fms/GuidanceComputer.cpp
    src/fms/FlightPlanManager.cpp
    src/fms/FuelManagement.cpp
    src/fms/PerformanceComputer.cpp
)

# ── fms_core static library ────────────────────────────────────────────────────
add_library(fms_core STATIC
    ${FMS_COMMON_SOURCES}
    ${FMS_RTOS_SOURCES}
    ${FMS_SENSOR_SOURCES}
    ${FMS_COMMS_SOURCES}
    ${FMS_SAFETY_SOURCES}
    ${FMS_CORE_SOURCES}
)

target_include_directories(fms_core PUBLIC ${FMS_INCLUDE_DIRS})
target_link_libraries(fms_core PUBLIC spdlog::spdlog nlohmann_json::nlohmann_json)
target_compile_features(fms_core PUBLIC cxx_std_17)

# Preprocessor defines
target_compile_definitions(fms_core PUBLIC
    $<$<BOOL:${FMS_ENABLE_ARINC429}>:FMS_ARINC429_ENABLED>
    $<$<BOOL:${FMS_ENABLE_ARINC664}>:FMS_ARINC664_ENABLED>
    $<$<BOOL:${FMS_ENABLE_CAN_AERO}>:FMS_CAN_AERO_ENABLED>
    $<$<BOOL:${FMS_TARGET_FREERTOS}>:FMS_FREERTOS_TARGET>
    FMS_VERSION_MAJOR=3
    FMS_VERSION_MINOR=2
    FMS_VERSION_PATCH=1
)

# ── Executable ─────────────────────────────────────────────────────────────────
add_executable(fms_app src/main.cpp)
target_link_libraries(fms_app PRIVATE fms_core)
target_include_directories(fms_app PRIVATE ${FMS_INCLUDE_DIRS})

# ── Tests ──────────────────────────────────────────────────────────────────────
if(FMS_ENABLE_TESTS)
    enable_testing()
    add_subdirectory(tests/unit)
    add_subdirectory(tests/integration)
endif()

# ── Install ────────────────────────────────────────────────────────────────────
install(TARGETS fms_app DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)
install(FILES config/fms_config.json DESTINATION etc/fms)

# ── Summary ────────────────────────────────────────────────────────────────────
message(STATUS "======================================================")
message(STATUS "  Avionics FMS v${PROJECT_VERSION}")
message(STATUS "  Build type   : ${CMAKE_BUILD_TYPE}")
message(STATUS "  Tests        : ${FMS_ENABLE_TESTS}")
message(STATUS "  ARINC 429    : ${FMS_ENABLE_ARINC429}")
message(STATUS "  ARINC 664    : ${FMS_ENABLE_ARINC664}")
message(STATUS "  CAN Aerospace: ${FMS_ENABLE_CAN_AERO}")
message(STATUS "  ASan         : ${FMS_ENABLE_ASAN}")
message(STATUS "======================================================")
