cmake_minimum_required(VERSION 3.18)

# ============================================================
# Core Framework library
# ============================================================
add_library(tcu_core STATIC
    core/Framework.cpp
    core/Watchdog.cpp
)
target_include_directories(tcu_core PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(tcu_core PUBLIC spdlog::spdlog Threads::Threads)

# ============================================================
# CAN Communication library
# ============================================================
add_library(tcu_can STATIC
    can/CANManager.cpp
    can/CANFilter.cpp
    can/DBCParser.cpp
)
target_include_directories(tcu_can PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(tcu_can PUBLIC tcu_core Threads::Threads)

# ============================================================
# Telematics SDK Adapter library
# ============================================================
add_library(tcu_telematics STATIC
    telematics/TelematicsSDKAdapter.cpp
    telematics/NetworkMonitor.cpp
)
target_include_directories(tcu_telematics PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(tcu_telematics PUBLIC tcu_core tcu_can nlohmann_json::nlohmann_json)

# ============================================================
# Diagnostics library
# ============================================================
add_library(tcu_diagnostics STATIC
    diagnostics/UDSClient.cpp
    diagnostics/DTCManager.cpp
)
target_include_directories(tcu_diagnostics PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(tcu_diagnostics PUBLIC tcu_core tcu_can)

# ============================================================
# Firmware Flashing library
# ============================================================
add_library(tcu_firmware STATIC
    firmware/FirmwareFlasher.cpp
    firmware/CRCValidator.cpp
)
target_include_directories(tcu_firmware PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(tcu_firmware PUBLIC tcu_core tcu_diagnostics)

# ============================================================
# Validation/Test Engine library
# ============================================================
add_library(tcu_validation STATIC
    validation/TestEngine.cpp
    validation/TestCase.cpp
    validation/FaultInjector.cpp
)
target_include_directories(tcu_validation PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(tcu_validation PUBLIC tcu_core tcu_can tcu_diagnostics nlohmann_json::nlohmann_json)

# ============================================================
# Logging library
# ============================================================
add_library(tcu_logging STATIC
    logging/Logger.cpp
    logging/BinaryLogger.cpp
)
target_include_directories(tcu_logging PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(tcu_logging PUBLIC tcu_core spdlog::spdlog Threads::Threads)

# ============================================================
# Reporting library
# ============================================================
add_library(tcu_reporting STATIC
    reporting/ReportGenerator.cpp
)
target_include_directories(tcu_reporting PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(tcu_reporting PUBLIC tcu_core nlohmann_json::nlohmann_json)

# ============================================================
# Configuration library
# ============================================================
add_library(tcu_config STATIC
    config/ConfigManager.cpp
)
target_include_directories(tcu_config PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(tcu_config PUBLIC tcu_core nlohmann_json::nlohmann_json)
