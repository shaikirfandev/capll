load("@rules_cc//cc:defs.bzl", "cc_binary")

cc_binary(
    name = "adas_rt",
    srcs = ["main.cpp"],
    copts = [
        "-std=c++17",
        "-O2",
        "-D_GNU_SOURCE",
        "-Wall",
        "-Wextra",
    ],
    linkopts = [
        "-lpthread",
        "-lrt",
    ],
    deps = [
        "//src/adas/perception:perception",
        "//src/adas/control:planning",
        "//src/adas/control:control",
        "//src/realtime:realtime",
        "//src/hil_sil:hil_sil",
        "//src/diagnostics:diagnostics",
    ],
)
