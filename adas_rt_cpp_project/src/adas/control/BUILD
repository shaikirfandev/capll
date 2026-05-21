load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "planning",
    srcs = ["path_planner.cpp"],
    hdrs = ["path_planner.hpp"],
    deps = ["//src/adas/perception:perception"],
    copts = ["-std=c++17", "-O2"],
    visibility = ["//visibility:public"],
)

cc_library(
    name = "control",
    srcs = ["vehicle_controller.cpp"],
    hdrs = ["vehicle_controller.hpp"],
    deps = [":planning"],
    copts = ["-std=c++17", "-O2"],
    visibility = ["//visibility:public"],
)
