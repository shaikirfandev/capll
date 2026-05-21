cmake_minimum_required(VERSION 3.18)
project(TCU_Tests)

enable_testing()

add_subdirectory(unit)
add_subdirectory(integration)
add_subdirectory(stress)
