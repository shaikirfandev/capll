load("@rules_cc//cc:defs.bzl", "cc_test")

cc_test(
    name = "sil_aeb_scenario",
    size = "medium",
    srcs = ["sil_test_harness.cpp"],
    copts = ["-std=c++17", "-O2"],
    linkopts = ["-lpthread", "-lrt"],
    deps = [
        "//src/adas/perception:perception",
        "//src/adas/control:planning",
        "//src/adas/control:control",
        "//src/hil_sil:hil_sil",
        "//src/diagnostics:diagnostics",
        "@com_google_googletest//:gtest_main",
    ],
)
