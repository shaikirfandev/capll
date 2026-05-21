cmake_minimum_required(VERSION 3.18)

add_executable(bt_unit_tests
    test_ring_buffer.cpp
    test_connection_statemachine.cpp
    test_ble_advertiser.cpp
    test_gatt_server.cpp
    test_pairing_manager.cpp
    test_security_manager.cpp
    test_event_bus.cpp
)

target_include_directories(bt_unit_tests PRIVATE
    ${PROJECT_SOURCE_DIR}/include
    ${PROJECT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/mocks
)

target_link_libraries(bt_unit_tests PRIVATE
    bt_core
    GTest::gtest_main
    GTest::gmock
)

target_compile_features(bt_unit_tests PRIVATE cxx_std_17)
include(GoogleTest)
gtest_discover_tests(bt_unit_tests)
