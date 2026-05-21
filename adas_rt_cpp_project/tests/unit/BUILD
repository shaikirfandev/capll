load("@rules_cc//cc:defs.bzl", "cc_test")

# ── Object detection unit tests ───────────────────────────────────────────────
cc_test(
    name = "test_object_detection",
    size = "small",
    srcs = ["test_object_detection.cpp"],
    deps = [
        "//src/adas/perception:perception",
        "@com_google_googletest//:gtest_main",
    ],
    copts = ["-std=c++17"],
)

# ── Sensor fusion unit tests ──────────────────────────────────────────────────
cc_test(
    name = "test_sensor_fusion",
    size = "small",
    srcs = ["test_sensor_fusion.cpp"],
    deps = [
        "//src/adas/perception:perception",
        "@com_google_googletest//:gtest_main",
    ],
    copts = ["-std=c++17"],
)

# ── CAN signal unit tests ─────────────────────────────────────────────────────
cc_test(
    name = "test_can_signals",
    size = "small",
    srcs = ["test_can_signals.cpp"],
    deps = [
        "//src/hil_sil:hil_sil",
        "@com_google_googletest//:gtest_main",
    ],
    copts = ["-std=c++17"],
    linkopts = ["-lpthread"],
)
