add_executable(integration_tests
    test_tcu_integration.cpp
)

target_include_directories(integration_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(integration_tests PRIVATE
    tcu_can
    tcu_diagnostics
    tcu_validation
    tcu_telematics
    tcu_firmware
    tcu_config
    tcu_reporting
    tcu_logging
    tcu_core
    GTest::gtest_main
)

target_compile_features(integration_tests PRIVATE cxx_std_17)

include(GoogleTest)
gtest_discover_tests(integration_tests
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    PROPERTIES
        TIMEOUT 120
        LABELS  "integration"
)
