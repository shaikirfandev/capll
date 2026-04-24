cmake_minimum_required(VERSION 3.16)
project(ADAS_ECU VERSION 2.4.1 LANGUAGES CXX)

# ── Compiler Standards ─────────────────────────────────────────────────────────
set(CMAKE_CXX_STANDARD          17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS        OFF)

# ── Build Type ─────────────────────────────────────────────────────────────────
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# ── Target: embedded cross-compile vs host simulation ─────────────────────────
option(EMBEDDED_TARGET  "Build for embedded ARM target"         OFF)
option(BUILD_SIMULATION "Build host simulation (Linux/macOS)"   ON)
option(BUILD_TESTS      "Build unit tests"                      ON)

# ── Compiler Flags ─────────────────────────────────────────────────────────────
set(COMMON_FLAGS
    -Wall -Wextra -Wpedantic -Wshadow
    -Wno-unused-parameter
    -fno-exceptions              # Embedded: no exception overhead
    -fno-rtti                    # Embedded: no runtime type info
)

if(EMBEDDED_TARGET)
    set(CMAKE_CXX_COMPILER arm-none-eabi-g++)
    list(APPEND COMMON_FLAGS
        -mcpu=cortex-m4
        -mthumb
        -mfpu=fpv4-sp-d16
        -mfloat-abi=hard
        -specs=nosys.specs
        -nostdlib
        -Os
    )
else()
    list(APPEND COMMON_FLAGS -O2 -g)
endif()

add_compile_options(${COMMON_FLAGS})

# ── Definitions ────────────────────────────────────────────────────────────────
add_compile_definitions(
    ADAS_ECU_VERSION_MAJOR=${PROJECT_VERSION_MAJOR}
    ADAS_ECU_VERSION_MINOR=${PROJECT_VERSION_MINOR}
    ADAS_ECU_VERSION_PATCH=${PROJECT_VERSION_PATCH}
    $<$<BOOL:${BUILD_SIMULATION}>:SIMULATION_BUILD>
    $<$<BOOL:${EMBEDDED_TARGET}>:EMBEDDED_TARGET>
)

# ── Include Directories ────────────────────────────────────────────────────────
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/include/hal
    ${CMAKE_SOURCE_DIR}/include/drivers
    ${CMAKE_SOURCE_DIR}/include/rtos
    ${CMAKE_SOURCE_DIR}/include/features
    ${CMAKE_SOURCE_DIR}/include/diagnostics
    ${CMAKE_SOURCE_DIR}/include/utils
)

# ── Source Files ───────────────────────────────────────────────────────────────
file(GLOB_RECURSE ADAS_SOURCES
    "src/hal/*.cpp"
    "src/drivers/*.cpp"
    "src/rtos/*.cpp"
    "src/features/*.cpp"
    "src/diagnostics/*.cpp"
    "src/utils/*.cpp"
)

# ── Main Executable ────────────────────────────────────────────────────────────
add_executable(adas_ecu
    src/main.cpp
    ${ADAS_SOURCES}
)

target_include_directories(adas_ecu PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

# ── Unit Tests (Google Test) ───────────────────────────────────────────────────
if(BUILD_TESTS)
    enable_testing()
    find_package(GTest QUIET)

    if(GTest_FOUND)
        file(GLOB_RECURSE TEST_SOURCES "tests/*.cpp")
        add_executable(adas_tests ${TEST_SOURCES} ${ADAS_SOURCES})
        target_link_libraries(adas_tests GTest::GTest GTest::Main)
        add_test(NAME ADAS_Unit_Tests COMMAND adas_tests)
    else()
        message(STATUS "GTest not found — unit tests disabled")
    endif()
endif()

# ── Install ────────────────────────────────────────────────────────────────────
install(TARGETS adas_ecu DESTINATION bin)
