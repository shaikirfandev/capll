# 04 — Bazel Build System

## Overview

This module documents the **Bazel build system** configuration used in `adas_rt_cpp_project`: workspace layout, BUILD file anatomy, configuration profiles, dependency management, testing, and useful Bazel commands for automotive C++ development.

---

## 1. Why Bazel for Automotive C++?

| Feature | Benefit in Automotive |
|---------|----------------------|
| **Hermetic builds** | No "works on my machine" — all builds use declared dependencies only |
| **Reproducibility** | SHA256 of every external dep is pinned in `WORKSPACE` |
| **Remote caching** | CI servers and developer machines share a build cache |
| **Multi-language** | C++, Python (test scripts), Shell, Starlark — one tool |
| **Cross-compilation** | First-class toolchain concept; trivial ARM Cortex-A target |
| **`bazel query`** | Dependency analysis without running builds |
| **Incremental builds** | Only recompiles what changed — critical for large codebases |

---

## 2. Workspace Structure

```
adas_rt_cpp_project/
├── WORKSPACE                ← Workspace root — external dependencies
├── BUILD                    ← Top-level filegroup targets
├── .bazelrc                 ← Default flags and named configs
└── src/
    ├── BUILD                ← cc_binary for adas_rt
    ├── adas/
    │   ├── perception/
    │   │   └── BUILD        ← cc_library: perception
    │   └── control/
    │       └── BUILD        ← cc_library: planning + control
    ├── realtime/
    │   └── BUILD            ← cc_library: realtime
    ├── hil_sil/
    │   └── BUILD            ← cc_library: hil_sil
    └── diagnostics/
        └── BUILD            ← cc_library: diagnostics
tests/
    ├── unit/
    │   └── BUILD            ← cc_test: 3 unit test targets
    └── sil/
        └── BUILD            ← cc_test: sil_aeb_scenario
```

---

## 3. WORKSPACE File Deep Dive

**File**: `WORKSPACE`

```python
workspace(name = "adas_rt_cpp")

# Bazel rules for C++
http_archive(
    name = "rules_cc",
    urls = ["https://github.com/bazelbuild/rules_cc/releases/download/0.0.9/rules_cc-0.0.9.tar.gz"],
    sha256 = "...",  # SHA256 pinned — build fails if file changes
)
load("@rules_cc//cc:repositories.bzl", "rules_cc_dependencies")
rules_cc_dependencies()

# Google Test
http_archive(
    name = "com_google_googletest",
    urls = ["https://github.com/google/googletest/archive/v1.14.0.tar.gz"],
    sha256 = "8ad598c73ad796e0d8280b082cebd82a630d73e73cd3c70057938a6501bba5d7",
    strip_prefix = "googletest-1.14.0",
)

# spdlog (fast logging)
http_archive(
    name = "com_github_gabime_spdlog",
    urls = ["https://github.com/gabime/spdlog/archive/v1.13.0.tar.gz"],
    sha256 = "...",
    strip_prefix = "spdlog-1.13.0",
    build_file = "@//:third_party/spdlog.BUILD",
)
```

**Key principle**: Every external dependency is an `http_archive` with a pinned `sha256`. If upstream changes the file, the build fails — preventing supply chain attacks.

---

## 4. BUILD File Anatomy

### 4.1 `cc_library` — Reusable Module

```python
load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "perception",

    # Implementation files
    srcs = [
        "object_detection.cpp",
        "sensor_fusion.cpp",
    ],

    # Public headers (exported to dependents)
    hdrs = [
        "object_detection.hpp",
        "sensor_fusion.hpp",
    ],

    # Compiler flags
    copts = [
        "-std=c++17",
        "-O2",
        "-Wall",
        "-Wextra",
    ],

    # Other libraries this depends on
    deps = [
        "//src/diagnostics:diagnostics",
        "@com_github_gabime_spdlog//:spdlog",
    ],

    # Who can depend on this target
    visibility = ["//visibility:public"],
)
```

### 4.2 `cc_binary` — Executable

```python
cc_binary(
    name = "adas_rt",
    srcs = ["main.cpp"],
    deps = [
        "//src/adas/perception:perception",
        "//src/adas/control:planning",
        "//src/adas/control:control",
        "//src/realtime:realtime",
        "//src/hil_sil:hil_sil",
        "//src/diagnostics:diagnostics",
    ],
    linkopts = [
        "-lpthread",
        "-lrt",          # POSIX RT: clock_nanosleep, mq_open
        "-lm",
    ],
)
```

### 4.3 `cc_test` — GTest Target

```python
cc_test(
    name = "test_sensor_fusion",
    srcs = ["test_sensor_fusion.cpp"],
    deps = [
        "//src/adas/perception:perception",
        "@com_google_googletest//:gtest_main",
    ],
    size = "small",  # < 1 min; enforces timeout
)
```

---

## 5. `.bazelrc` Configuration Profiles

```ini
# Default flags applied to all builds
build --cxxopt='-std=c++17'
build --cxxopt='-Wall'
build --cxxopt='-Wextra'
build --cxxopt='-Wno-unused-parameter'

# ─── Real-Time build ────────────────────────────────────────────────────────
build:rt --cxxopt='-D_GNU_SOURCE'
build:rt --cxxopt='-DADAS_RT_ENABLED'
build:rt --linkopt='-lrt'
build:rt --linkopt='-lpthread'

# ─── Release build ──────────────────────────────────────────────────────────
build:release --compilation_mode=opt
build:release --cxxopt='-O2'
build:release --cxxopt='-DNDEBUG'
build:release --linkopt='-flto'

# ─── AddressSanitizer ────────────────────────────────────────────────────────
build:asan --compilation_mode=dbg
build:asan --cxxopt='-fsanitize=address'
build:asan --cxxopt='-fno-omit-frame-pointer'
build:asan --linkopt='-fsanitize=address'

# ─── ThreadSanitizer ─────────────────────────────────────────────────────────
build:tsan --compilation_mode=dbg
build:tsan --cxxopt='-fsanitize=thread'
build:tsan --linkopt='-fsanitize=thread'

# ─── Embedded cross-compile (ARM Cortex-A) ───────────────────────────────────
build:embedded --crosstool_top=//toolchains:arm_linux_toolchain
build:embedded --cpu=aarch64
build:embedded --cxxopt='-mcpu=cortex-a53'
build:embedded --cxxopt='-mfpu=neon-fp-armv8'
```

---

## 6. Useful Bazel Commands

### 6.1 Build Commands

```bash
# Build everything
bazel build //...

# Build only the main binary (real-time config)
bazel build //src:adas_rt --config=rt

# Release build (optimised)
bazel build //src:adas_rt --config=release

# Debug build (symbols, no optimisation)
bazel build //src:adas_rt -c dbg

# Cross-compile for ARM embedded target
bazel build //src:adas_rt --config=embedded
```

### 6.2 Test Commands

```bash
# Run all tests
bazel test //...

# Run specific test suite
bazel test //tests/unit:test_sensor_fusion --test_output=all

# Run all unit tests in parallel (default)
bazel test //tests/unit/...

# Run SIL scenario with verbose output
bazel test //tests/sil:sil_aeb_scenario --test_output=all

# Run with test filtering (GTest --gtest_filter)
bazel test //tests/unit:test_sensor_fusion \
  --test_arg='--gtest_filter=SensorFusion*'

# Code coverage (LCOV format)
bazel coverage //tests/unit/... \
  --combined_report=lcov \
  --coverage_report_generator=@bazel_tools//tools/test/LcovMerger/java/com/google/devtools/lcov:LcovMerger
```

### 6.3 Query Commands

```bash
# List all targets in the project
bazel query '//...'

# Show all deps of the main binary
bazel query 'deps(//src:adas_rt)'

# Show only direct deps
bazel query 'deps(//src:adas_rt, 1)'

# Find all targets that depend on perception
bazel query 'rdeps(//..., //src/adas/perception:perception)'

# Generate dependency graph (requires dot/graphviz)
bazel query 'deps(//src:adas_rt)' \
  --output=graph | dot -Tsvg -o deps.svg
```

### 6.4 Maintenance Commands

```bash
# Clean build artifacts
bazel clean

# Clean including cached downloads
bazel clean --expunge

# Show build output path for a target
bazel info bazel-bin

# Show effective flags for a build
bazel build //src:adas_rt --config=rt --announce_rc
```

---

## 7. Dependency Management

### 7.1 Third-Party Libraries Used

| Library | Role | Bazel Label |
|---------|------|-------------|
| Google Test 1.14 | Unit testing | `@com_google_googletest//:gtest_main` |
| Google Benchmark | Micro-benchmarks | `@com_github_google_benchmark//:benchmark` |
| Abseil-cpp | String utilities, status | `@com_google_absl//...` |
| spdlog | Structured logging backend | `@com_github_gabime_spdlog//:spdlog` |
| nlohmann/json | JSON config parsing | `@com_github_nlohmann_json//:json` |

### 7.2 Pinning Dependencies Securely

Every `http_archive` has a `sha256` field. This prevents:
- Supply chain attacks (upstream file replaced silently)
- Build non-reproducibility (different developers get different content)

To update a dependency:
```bash
# Get new sha256
curl -L https://github.com/.../archive/v2.0.tar.gz | sha256sum
# Update WORKSPACE sha256 and urls fields
```

### 7.3 External BUILD Files

For libraries without Bazel support (e.g., spdlog), a custom `BUILD` file in `third_party/` exposes the library:

```python
# third_party/spdlog.BUILD
cc_library(
    name = "spdlog",
    hdrs = glob(["include/**/*.h"]),
    includes = ["include"],
    visibility = ["//visibility:public"],
)
```

Referenced in WORKSPACE as:
```python
build_file = "@//:third_party/spdlog.BUILD",
```

---

## 8. Remote Caching Setup

For a team, configure a remote cache to share build artifacts:

```ini
# .bazelrc additions for remote caching
build --remote_cache=grpc://my-build-cache:9090
build --remote_upload_local_results=true
```

With a Bazel Remote Cache (Buildbarn, Buildbuddy, or self-hosted):
- First build: ~3 min
- CI builds (cache hit): ~10 s for incremental changes

---

*See also*: [07_Multithreading_Realtime.md](07_Multithreading_Realtime.md) for the `--config=rt` motivation.  
*See also*: [05_Embedded_Linux.md](05_Embedded_Linux.md) for the `--config=embedded` cross-compilation setup.
