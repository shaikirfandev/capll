load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "diagnostics",
    srcs = [
        "logger.cpp",
        "fault_manager.cpp",
    ],
    hdrs = [
        "logger.hpp",
        "fault_manager.hpp",
    ],
    copts = ["-std=c++17", "-O2"],
    linkopts = ["-lpthread"],
    visibility = ["//visibility:public"],
)
