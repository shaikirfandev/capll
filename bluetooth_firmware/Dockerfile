# syntax=docker/dockerfile:1.4
# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — Builder
# Production-grade multi-stage Docker build for Bluetooth Firmware
# Target: Ubuntu 22.04, CMake 3.26, GCC-12, Clang-15
# ─────────────────────────────────────────────────────────────────────────────
FROM ubuntu:22.04 AS builder

LABEL maintainer="automotive-bt-team@company.com"
LABEL description="Bluetooth Firmware Build Environment"
LABEL version="2.1.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV CMAKE_VERSION=3.26.4
ENV NINJA_VERSION=1.11.1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc-12 \
    g++-12 \
    clang-15 \
    cmake \
    ninja-build \
    git \
    curl \
    wget \
    ca-certificates \
    libssl-dev \
    valgrind \
    lcov \
    gcovr \
    cppcheck \
    clang-tidy-15 \
    clang-format-15 \
    python3 \
    python3-pip \
    doxygen \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Set GCC-12 as default
RUN update-alternatives --install /usr/bin/gcc    gcc    /usr/bin/gcc-12    120 \
 && update-alternatives --install /usr/bin/g++    g++    /usr/bin/g++-12    120 \
 && update-alternatives --install /usr/bin/clang  clang  /usr/bin/clang-15  120 \
 && update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-15 120

WORKDIR /workspace

# Copy source
COPY . /workspace/

# Build (Release by default; override with --build-arg)
ARG BUILD_TYPE=Release
ARG ENABLE_TESTS=ON
ARG ENABLE_COVERAGE=OFF

RUN cmake -B build \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
    -DBT_ENABLE_TESTS=${ENABLE_TESTS} \
    -DBT_COVERAGE=${ENABLE_COVERAGE} \
    -DCMAKE_CXX_COMPILER=g++ \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    && cmake --build build --parallel $(nproc)

# Run tests inside builder
RUN cd build && ctest --output-on-failure --timeout 60

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Static analysis (separate layer, doesn't block build)
# ─────────────────────────────────────────────────────────────────────────────
FROM builder AS analyzer

RUN cppcheck \
    --enable=all \
    --std=c++17 \
    --suppress=missingIncludeSystem \
    --error-exitcode=0 \
    --xml \
    /workspace/src/ 2>/workspace/build/cppcheck_report.xml \
    && echo "cppcheck complete"

RUN cd /workspace && clang-tidy-15 \
    -p build/compile_commands.json \
    $(find src -name "*.cpp") \
    2>&1 | tee build/clang_tidy_report.txt || true

# ─────────────────────────────────────────────────────────────────────────────
# Stage 3 — Runtime image (minimal)
# ─────────────────────────────────────────────────────────────────────────────
FROM ubuntu:22.04 AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libstdc++6 \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r btapp && useradd -r -g btapp btapp

WORKDIR /app
COPY --from=builder /workspace/build/bt_firmware /app/bt_firmware
COPY --from=builder /workspace/config/            /app/config/

# Set ownership
RUN chown -R btapp:btapp /app
USER btapp

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep bt_firmware || exit 1

ENTRYPOINT ["/app/bt_firmware"]
CMD ["--config", "/app/config/bt_config.json"]
