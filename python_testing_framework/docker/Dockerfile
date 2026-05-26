# ============================================================
# docker/Dockerfile
# Enterprise ADAS Test Framework — Multi-stage container
# ============================================================

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libusb-1.0-0-dev \
        can-utils \
        libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements/requirements.txt /build/requirements.txt
RUN pip install --upgrade pip && \
    pip install --user --no-cache-dir -r /build/requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="ADAS Test Framework"
LABEL org.opencontainers.image.description="Enterprise pytest + Robot Framework ADAS validation"
LABEL org.opencontainers.image.version="1.0.0"

# Non-root user for security
RUN groupadd -r adas && useradd -r -g adas -d /app -s /sbin/nologin adas

# Runtime OS packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        can-utils \
        libusb-1.0-0 \
        libopencv-core4.5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /home/adas/.local

WORKDIR /app

# Copy framework source
COPY --chown=adas:adas . /app/python_testing_framework/

# Create output directories
RUN mkdir -p /app/reports /app/allure-results /app/logs && \
    chown -R adas:adas /app

USER adas

ENV PYTHONPATH=/app/python_testing_framework
ENV PATH=/home/adas/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Health check — verify pytest is importable
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -m pytest --version

# Default: run smoke tests
ENTRYPOINT ["python3", "-m", "pytest"]
CMD [ \
    "python_testing_framework/pytest_framework/test_suites/", \
    "-m", "smoke", \
    "--no-hardware", \
    "--env=ci", \
    "--tb=short", \
    "--alluredir=/app/allure-results", \
    "--junitxml=/app/reports/results.xml", \
    "-v" \
]
