load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "realtime",
    srcs = [
        "rt_scheduler.cpp",
        "thread_pool.cpp",
    ],
    hdrs = [
        "lock_free_queue.hpp",
        "rt_scheduler.hpp",
        "thread_pool.hpp",
    ],
    copts = [
        "-std=c++17",
        "-O2",
        "-D_GNU_SOURCE",
    ],
    linkopts = [
        "-lpthread",
        "-lrt",
    ],
    visibility = ["//visibility:public"],
)
