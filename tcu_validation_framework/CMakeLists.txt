cmake_minimum_required(VERSION 3.18)

project(TCU_Validation_Framework
    VERSION 2.0.0
    DESCRIPTION "Automotive Telematics TCU Validation & Integration Framework"
    LANGUAGES C CXX
)

# ============================================================
# Global C/C++ Standards
# ============================================================
set(CMAKE_C_STANDARD   11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ============================================================
# Build type default
# ============================================================
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "RelWithDebInfo" CACHE STRING "Build type" FORCE)
endif()

message(STATUS "Build type : ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ standard: C++${CMAKE_CXX_STANDARD}")

# ============================================================
# Compile options (MISRA-inspired + safety)
# ============================================================
add_compile_options(
    -Wall -Wextra -Wpedantic
    -Wshadow -Wconversion -Wsign-conversion
    -Wnull-dereference -Wformat=2
    -fstack-protector-strong
    -D_FORTIFY_SOURCE=2
    $<$<CONFIG:Debug>:-g3 -O0 -fsanitize=address,undefined>
    $<$<CONFIG:Release>:-O2 -DNDEBUG>
    $<$<CONFIG:RelWithDebInfo>:-O2 -g -DNDEBUG>
)

add_link_options(
    $<$<CONFIG:Debug>:-fsanitize=address,undefined>
)

# ============================================================
# Output directories
# ============================================================
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# ============================================================
# Dependencies — find_package
# ============================================================
find_package(Threads REQUIRED)

# spdlog (logging)
find_package(spdlog QUIET)
if(NOT spdlog_FOUND)
    message(STATUS "spdlog not found via find_package — fetching via FetchContent")
    include(FetchContent)
    FetchContent_Declare(spdlog
        GIT_REPOSITORY https://github.com/gabime/spdlog.git
        GIT_TAG        v1.13.0
    )
    FetchContent_MakeAvailable(spdlog)
endif()

# nlohmann/json
find_package(nlohmann_json QUIET)
if(NOT nlohmann_json_FOUND)
    include(FetchContent)
    FetchContent_Declare(nlohmann_json
        GIT_REPOSITORY https://github.com/nlohmann/json.git
        GIT_TAG        v3.11.3
    )
    FetchContent_MakeAvailable(nlohmann_json)
endif()

# GoogleTest
include(FetchContent)
FetchContent_Declare(googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG        v1.14.0
)
FetchContent_MakeAvailable(googletest)

# ============================================================
# Global include path
# ============================================================
include_directories(${CMAKE_SOURCE_DIR}/include)

# ============================================================
# Sub-project libraries
# ============================================================
add_subdirectory(src)
add_subdirectory(tests)

# ============================================================
# Main executable
# ============================================================
add_executable(tcu_validator
    src/main.cpp
)

target_link_libraries(tcu_validator
    PRIVATE
        tcu_core
        tcu_can
        tcu_telematics
        tcu_diagnostics
        tcu_firmware
        tcu_validation
        tcu_logging
        tcu_reporting
        tcu_config
        Threads::Threads
        spdlog::spdlog
        nlohmann_json::nlohmann_json
)

# ============================================================
# Installation
# ============================================================
install(TARGETS tcu_validator
    RUNTIME DESTINATION bin
)
install(DIRECTORY configs/ DESTINATION etc/tcu_validator)
install(DIRECTORY include/  DESTINATION include/tcu_validator)

# ============================================================
# Static Analysis targets (optional)
# ============================================================
find_program(CPPCHECK cppcheck)
if(CPPCHECK)
    add_custom_target(cppcheck
        COMMAND ${CPPCHECK}
            --enable=all
            --std=c++17
            --suppress=missingIncludeSystem
            --error-exitcode=1
            -I ${CMAKE_SOURCE_DIR}/include
            ${CMAKE_SOURCE_DIR}/src
        COMMENT "Running cppcheck static analysis"
    )
endif()

find_program(CLANG_TIDY clang-tidy)
if(CLANG_TIDY)
    set(CMAKE_CXX_CLANG_TIDY
        clang-tidy;
        --config-file=${CMAKE_SOURCE_DIR}/.clang-tidy
    )
endif()

# ============================================================
# Package generation (CPack)
# ============================================================
include(CPack)
set(CPACK_PACKAGE_NAME            "tcu-validation-framework")
set(CPACK_PACKAGE_VERSION         ${PROJECT_VERSION})
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY ${PROJECT_DESCRIPTION})
set(CPACK_GENERATOR               "DEB;TGZ")
set(CPACK_DEBIAN_PACKAGE_MAINTAINER "TCU Test Team <tcu-test@company.com>")
