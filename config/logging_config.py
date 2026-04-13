from __future__ import annotations

import logging
import sys
from typing import Any

structlog: Any = None

try:
    import structlog as structlog_module
except ImportError:  # pragma: no cover - dependency-free test/runtime fallback
    pass
else:
    structlog = structlog_module


def configure_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging for application and libraries."""

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )
    if structlog is None:
        return

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class _StdlibCompatLogger:
    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def info(self, message: str, **kwargs: Any) -> None:
        self._logger.info("%s %s", message, kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning("%s %s", message, kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        self._logger.exception("%s %s", message, kwargs)


def get_logger(name: str) -> Any:
    if structlog is None:
        return _StdlibCompatLogger(name)
    return structlog.get_logger(name)
