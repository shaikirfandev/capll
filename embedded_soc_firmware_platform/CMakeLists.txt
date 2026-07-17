cmake_minimum_required(VERSION 3.20)
project(EmbeddedSoCFirmwarePlatform)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -O2")

# Include directories
include_directories(${CMAKE_SOURCE_DIR}/firmware/include)

# Find required packages
find_package(Threads REQUIRED)

# Firmware library
file(GLOB_RECURSE FIRMWARE_SOURCES 
    "firmware/src/*.cpp"
    "firmware/boot/*.cpp"
    "firmware/power/*.cpp"
    "firmware/memory/*.cpp"
    "firmware/security/*.cpp"
    "firmware/pcie/*.cpp"
    "firmware/usb/*.cpp"
    "firmware/bmc/*.cpp"
    "firmware/lsio/*.cpp"
    "firmware/health/*.cpp"
    "firmware/logging/*.cpp"
)

add_library(firmware ${FIRMWARE_SOURCES})
target_link_libraries(firmware Threads::Threads)

# Main firmware executable
add_executable(firmware_simulator firmware/src/main.cpp)
target_link_libraries(firmware_simulator firmware)

# Enable testing
enable_testing()

# Add test executables (optional - can be integrated with Python tests)
add_executable(test_firmware_core firmware/src/test_firmware.cpp)
target_link_libraries(test_firmware_core firmware)
add_test(NAME FirmwareCoreTest COMMAND test_firmware_core)
