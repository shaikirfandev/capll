# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM ubuntu:22.04 AS builder
LABEL maintainer="avionics-fms@example.com"

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . .

RUN cmake -B build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DFMS_ENABLE_TESTS=OFF \
    -DFMS_STRICT_WARNINGS=ON \
    && cmake --build build --parallel

# ── Stage 2: Test runner ──────────────────────────────────────────────────────
FROM builder AS tester
RUN cmake -B build_test -G Ninja \
    -DCMAKE_BUILD_TYPE=Debug \
    -DFMS_ENABLE_TESTS=ON \
    -DFMS_ENABLE_ASAN=ON \
    && cmake --build build_test --parallel \
    && cd build_test && ctest --output-on-failure

# ── Stage 3: Runtime ──────────────────────────────────────────────────────────
FROM ubuntu:22.04 AS runtime
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/fms
COPY --from=builder /src/build/fms_app ./fms_app
COPY --from=builder /src/config/ ./config/
EXPOSE 8080
ENTRYPOINT ["/opt/fms/fms_app"]
