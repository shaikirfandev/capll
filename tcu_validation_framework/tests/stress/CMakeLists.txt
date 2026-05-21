add_executable(stress_tests
    test_stress.cpp
)

target_include_directories(stress_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(stress_tests PRIVATE
    tcu_telematics
    tcu_validation
    tcu_config
    tcu_reporting
    tcu_logging
    GTest::gtest_main
)

target_compile_features(stress_tests PRIVATE cxx_std_17)

include(GoogleTest)
gtest_discover_tests(stress_tests
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    PROPERTIES
        TIMEOUT 600
        LABELS  "stress"
)
