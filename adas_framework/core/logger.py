# adas_framework/core/logger.py
"""
Structured logging framework for ADAS test suite.

Features:
    - Per-test log files (keyed by test node ID)
    - Structured JSON logs for Kibana/Grafana ingestion
    - Console handler with rich color output
    - CAN / UDS / sensor domain-specific child loggers
    - Thread-safe singleton factory
    - Automatic log rotation (10 MB, 5 backups)

Usage:
    from core.logger import get_logger
    log = get_logger("radar")
    log.info("Target acquired", extra={"range_m": 45.2, "velocity_mps": 12.5})
"""
from __future__ import annotations

import json
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


_lock = threading.Lock()
_loggers: dict[str, logging.Logger] = {}

LOG_DIR = Path(os.environ.get("ADAS_LOG_DIR", "logs"))
LOG_LEVEL = os.environ.get("ADAS_LOG_LEVEL", "DEBUG").upper()

# ANSI color codes for console
_COLORS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
    "RESET":    "\033[0m",
}


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for Kibana/ELK ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        doc = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "level":      record.levelname,
            "logger":     record.name,
            "message":    record.getMessage(),
            "module":     record.module,
            "function":   record.funcName,
            "line":       record.lineno,
            "thread":     record.thread,
        }
        # Attach any extra fields added via extra={...}
        skip = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        for k, v in record.__dict__.items():
            if k not in skip:
                try:
                    json.dumps(v)
                    doc[k] = v
                except (TypeError, ValueError):
                    doc[k] = str(v)

        if record.exc_info:
            doc["exception"] = self.formatException(record.exc_info)
        return json.dumps(doc, ensure_ascii=False)


class ColorConsoleFormatter(logging.Formatter):
    """Human-readable colored console formatter."""

    FMT = "{color}[{level:<8}]{reset} {asctime} | {name:<18} | {message}"

    def format(self, record: logging.LogRecord) -> str:
        color = _COLORS.get(record.levelname, "")
        reset = _COLORS["RESET"]
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        line = self.FMT.format(
            color=color, reset=reset,
            level=record.levelname,
            asctime=ts,
            name=record.name[:18],
            message=record.getMessage(),
        )
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def _build_logger(name: str) -> logging.Logger:
    """Create and configure a named logger."""
    logger = logging.getLogger(f"adas.{name}")
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.DEBUG))
    logger.propagate = False

    if logger.handlers:
        return logger

    # ── Console ──────────────────────────────────────────────────────────────
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(ColorConsoleFormatter())
    logger.addHandler(ch)

    # ── Rotating file (plain text) ────────────────────────────────────────────
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(
        LOG_DIR / f"{name}.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    ))
    logger.addHandler(fh)

    # ── Structured JSON file (for ELK) ────────────────────────────────────────
    jh = RotatingFileHandler(
        LOG_DIR / f"{name}.jsonl",
        maxBytes=20 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    jh.setLevel(logging.DEBUG)
    jh.setFormatter(JSONFormatter())
    logger.addHandler(jh)

    return logger


def get_logger(name: str = "adas") -> logging.Logger:
    """Thread-safe logger factory. Returns cached instance on repeat calls."""
    with _lock:
        if name not in _loggers:
            _loggers[name] = _build_logger(name)
        return _loggers[name]


def set_test_context(test_id: str):
    """Add test node ID to all subsequent log records (log filter)."""
    class TestContextFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            record.test_id = test_id
            return True

    for logger in _loggers.values():
        for handler in logger.handlers:
            handler.addFilter(TestContextFilter())


# Pre-create domain loggers
log         = get_logger("adas")
can_log     = get_logger("can")
uds_log     = get_logger("uds")
radar_log   = get_logger("radar")
camera_log  = get_logger("camera")
lidar_log   = get_logger("lidar")
fusion_log  = get_logger("fusion")
eth_log     = get_logger("ethernet")
hil_log     = get_logger("hil")
report_log  = get_logger("report")
