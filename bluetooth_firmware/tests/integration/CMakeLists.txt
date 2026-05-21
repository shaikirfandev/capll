cmake_minimum_required(VERSION 3.18)

add_executable(bt_integration_tests
    test_bt_stack_integration.cpp
    test_ota_integration.cpp
    test_pairing_flow.cpp
)

target_include_directories(bt_integration_tests PRIVATE
    ${PROJECT_SOURCE_DIR}/include
    ${PROJECT_SOURCE_DIR}/src
)

target_link_libraries(bt_integration_tests PRIVATE
    bt_core
    GTest::gtest_main
)

target_compile_features(bt_integration_tests PRIVATE cxx_std_17)
include(GoogleTest)
gtest_discover_tests(bt_integration_tests)
