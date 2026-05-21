load("@rules_cc//cc:defs.bzl", "cc_library")

# ── Perception library ────────────────────────────────────────────────────────
cc_library(
    name = "perception",
    srcs = [
        "object_detection.cpp",
        "sensor_fusion.cpp",
    ],
    hdrs = [
        "object_detection.hpp",
        "sensor_fusion.hpp",
    ],
    copts = [
        "-std=c++17",
        "-O2",
        "-Wall",
        "-Wextra",
    ],
    visibility = ["//visibility:public"],
)
