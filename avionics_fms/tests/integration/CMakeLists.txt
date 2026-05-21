cmake_minimum_required(VERSION 3.20)

add_executable(fms_integration_tests
    test_fms_integration.cpp
    test_navigation_integration.cpp
    test_comms_integration.cpp
)

target_include_directories(fms_integration_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
)

target_link_libraries(fms_integration_tests PRIVATE
    fms_core
    GTest::gtest_main
    GTest::gmock
)

include(GoogleTest)
gtest_discover_tests(fms_integration_tests)
