"""Structured-ish logging setup shared by the API and scripts."""

from __future__ import annotations

import logging
import sys

from app.core.config import get_settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging(level: str | None = None) -> None:
    settings = get_settings()
    resolved = (level or settings.log_level).upper()
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(resolved)
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(handler)
    root.setLevel(resolved)
    logging.getLogger("uvicorn.access").setLevel("WARNING")
    logging.getLogger("sqlalchemy.engine").setLevel("WARNING")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"mindscribe.{name}")
