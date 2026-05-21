add_executable(unit_tests
    test_can_manager.cpp
    test_uds_client.cpp
    test_config_manager.cpp
    test_report_generator.cpp
    test_test_engine.cpp
)

target_include_directories(unit_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(unit_tests PRIVATE
    tcu_can
    tcu_diagnostics
    tcu_validation
    tcu_config
    tcu_reporting
    tcu_logging
    GTest::gtest_main
    GTest::gmock
)

target_compile_features(unit_tests PRIVATE cxx_std_17)

include(GoogleTest)
gtest_discover_tests(unit_tests
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    PROPERTIES TIMEOUT 60
)
