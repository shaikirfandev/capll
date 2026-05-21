cmake_minimum_required(VERSION 3.20)

add_executable(fms_unit_tests
    test_navigation_engine.cpp
    test_arinc429.cpp
    test_fault_manager.cpp
    test_flight_plan_manager.cpp
    test_guidance_computer.cpp
)

target_include_directories(fms_unit_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
)

target_link_libraries(fms_unit_tests PRIVATE
    fms_core
    GTest::gtest_main
    GTest::gmock
)

include(GoogleTest)
gtest_discover_tests(fms_unit_tests)
