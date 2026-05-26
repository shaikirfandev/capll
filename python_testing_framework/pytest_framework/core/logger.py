"""
pytest_framework/core/logger.py

Enterprise ADAS Framework – Structured Logging
================================================
Dual-sink logger:
  • JSON formatter  → files / ELK / Kibana ingestion
  • Color formatter → terminal / developer visibility

Usage:
    from core.logger import get_logger
    log = get_logger("my_module")
    log.info("Signal received", extra={"signal": "ACC_Status", "value": 2})
"""
from __future__ import annotations

import json
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_REGISTRY: dict[str, logging.Logger] = {}
_LOCK = threading.Lock()

# ANSI colour codes
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_RED    = "\033[91m"
_YELLOW = "\033[93m"
_GREEN  = "\033[92m"
_CYAN   = "\033[96m"
_GREY   = "\033[90m"

_LEVEL_COLORS = {
    "DEBUG":    _GREY,
    "INFO":     _GREEN,
    "WARNING":  _YELLOW,
    "ERROR":    _RED,
    "CRITICAL": _BOLD + _RED,
}


class JSONFormatter(logging.Formatter):
    """ELK-compatible JSON log record."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts":      datetime.now(timezone.utc).isoformat(),
            "level":   record.levelname,
            "logger":  record.name,
            "message": record.getMessage(),
            "module":  record.module,
            "line":    record.lineno,
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Merge any extra keys (feature, asil, req_ids…)
        for k, v in record.__dict__.items():
            if k not in logging.LogRecord.__dict__ and not k.startswith("_"):
                payload[k] = v
        return json.dumps(payload, default=str)


class ColorConsoleFormatter(logging.Formatter):
    """Human-readable coloured terminal output."""

    FMT = "{color}{level:<8}{reset} {grey}{ts}{reset}  {bold}{logger:<20}{reset}  {msg}"

    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelname, _RESET)
        ts    = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line  = self.FMT.format(
            color=color, level=record.levelname, reset=_RESET,
            grey=_GREY, ts=ts, bold=_BOLD,
            logger=record.name[:20], msg=record.getMessage()
        )
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def _build_logger(
    name: str,
    level: int,
    log_dir: Optional[Path],
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Console sink
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(ColorConsoleFormatter())
    ch.setLevel(level)
    logger.addHandler(ch)

    # File sink (JSON)
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / f"{name.replace('.', '_')}.jsonl",
                                 encoding="utf-8")
        fh.setFormatter(JSONFormatter())
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)

    return logger


def get_logger(
    name: str,
    level: Optional[int] = None,
    log_dir: Optional[Path] = None,
) -> logging.Logger:
    """
    Return a named logger (created once, cached forever).

    Args:
        name:    Logger name (module / feature identifier).
        level:   Override log level; defaults to ADAS_LOG_LEVEL env var or INFO.
        log_dir: Directory for JSON log files; defaults to logs/<name>.
    """
    with _LOCK:
        if name in _REGISTRY:
            return _REGISTRY[name]

        _level = level or getattr(
            logging,
            os.environ.get("ADAS_LOG_LEVEL", "INFO").upper(),
            logging.INFO,
        )
        _dir = log_dir or (
            Path(os.environ.get("ADAS_LOG_DIR", "logs")) / name
            if os.environ.get("ADAS_LOG_FILE_ENABLED", "true").lower() != "false"
            else None
        )
        _REGISTRY[name] = _build_logger(name, _level, _dir)
        return _REGISTRY[name]


def set_global_level(level: int) -> None:
    """Adjust all existing loggers to a new level (e.g., DEBUG during fault injection)."""
    with _LOCK:
        for logger in _REGISTRY.values():
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)
