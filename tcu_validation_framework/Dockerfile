# syntax=docker/dockerfile:1
# =============================================================================
# Dockerfile — TCU Validation Framework
# Multi-stage build: builder → runtime image
# =============================================================================

# -------------------------------------------------------
# Stage 1: Builder
# -------------------------------------------------------
FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV BUILD_TYPE=Release

RUN apt-get update -q && \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        ninja-build \
        git \
        pkg-config \
        libssl-dev \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy source
COPY . .

# Configure and build (Release, no tests for production image)
RUN cmake -S . -B build/release \
        -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_TESTS=OFF && \
    cmake --build build/release --parallel "$(nproc)"

# -------------------------------------------------------
# Stage 2: Runtime image
# -------------------------------------------------------
FROM ubuntu:22.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -q && \
    apt-get install -y --no-install-recommends \
        iproute2 \
        can-utils \
        libssl3 \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python CAN tools for can_replay.py
RUN pip3 install --no-cache-dir python-can cantools

# Create non-root user
RUN useradd -m -s /bin/bash tcu
USER tcu
WORKDIR /app

# Copy compiled binary
COPY --from=builder --chown=tcu:tcu \
    /build/build/release/bin/tcu_validator \
    /app/tcu_validator

# Copy configs and tools
COPY --chown=tcu:tcu configs/      /app/configs/
COPY --chown=tcu:tcu tools/        /app/tools/
COPY --chown=tcu:tcu scripts/      /app/scripts/

# Create runtime directories
RUN mkdir -p /app/logs /app/reports /app/firmware

EXPOSE 9090

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD test -f /app/tcu_validator || exit 1

ENTRYPOINT ["/app/tcu_validator"]
CMD ["--config", "/app/configs/default.json", "--simulate"]

# -------------------------------------------------------
# Stage 3: Test image (includes test binaries)
# -------------------------------------------------------
FROM builder AS test

RUN cmake -S . -B build/test \
        -G Ninja \
        -DCMAKE_BUILD_TYPE=Debug \
        -DBUILD_TESTS=ON && \
    cmake --build build/test --parallel "$(nproc)"

WORKDIR /build
ENTRYPOINT ["bash", "-c"]
CMD ["build/test/bin/unit_tests && build/test/bin/integration_tests"]
