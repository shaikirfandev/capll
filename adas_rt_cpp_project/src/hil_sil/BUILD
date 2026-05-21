load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "hil_sil",
    srcs = ["can_bus_sim.cpp"],
    hdrs = [
        "hal.hpp",
        "can_bus_sim.hpp",
    ],
    copts = [
        "-std=c++17",
        "-O2",
        "-D_GNU_SOURCE",
    ],
    linkopts = ["-lpthread"],
    visibility = ["//visibility:public"],
)

# SocketCAN variant (Linux only, requires vcan kernel module)
cc_library(
    name = "hil_sil_socketcan",
    srcs = ["can_bus_sim.cpp"],
    hdrs = [
        "hal.hpp",
        "can_bus_sim.hpp",
    ],
    copts = [
        "-std=c++17",
        "-O2",
        "-D_GNU_SOURCE",
        "-DADAS_USE_SOCKETCAN",
    ],
    linkopts = ["-lpthread"],
    visibility = ["//visibility:public"],
)
