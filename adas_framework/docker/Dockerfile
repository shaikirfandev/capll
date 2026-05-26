# adas_framework/docker/Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
# ADAS Test Framework — Containerised Test Environment
#
# Multi-stage build:
#   1. builder   — compile OpenCV + install all Python deps
#   2. runtime   — lean image for CI test execution
#
# Usage:
#   docker build -t adas-test-framework .
#   docker run --rm adas-test-framework pytest test_cases/ -m smoke --no-hardware
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Build ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# OS build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make cmake \
    libusb-1.0-0-dev \
    libpcan-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install Python dependencies
COPY requirements/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --user --no-warn-script-location -r requirements.txt


# ── Stage 2: Runtime ───────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="adas-test-team"
LABEL description="ADAS Enterprise Test Framework — CI/CD container"
LABEL version="1.0.0"

# Runtime OS libs (CAN, USB)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libusb-1.0-0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Create non-root user for security
RUN useradd -m -u 1000 testrunner && \
    mkdir -p /adas_framework /logs /reports && \
    chown -R testrunner:testrunner /adas_framework /logs /reports

USER testrunner
WORKDIR /adas_framework

# Copy framework source
COPY --chown=testrunner:testrunner . .

# Environment
ENV PYTHONPATH=/adas_framework
ENV ADAS_ENV=docker
ENV ADAS_LOG_DIR=/logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Default: run smoke suite
CMD ["pytest", "test_cases/", "-m", "smoke", "--no-hardware", \
     "-v", "--tb=short", "--html=/reports/smoke_report.html", \
     "--self-contained-html", "-q"]
