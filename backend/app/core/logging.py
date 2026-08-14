"""
Structured logging setup for the application.
Provides JSON formatted logs enriched with request correlation IDs, user IDs, and duration metrics.
"""

import json
import logging
import logging.handlers
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """
    JSON structured log formatter for enterprise observability.
    Enriches log records with request correlation ID, user ID, interview ID, and duration.
    """

    def format(self, record: logging.LogRecord) -> str:
        from app.core.request_context import get_interview_id, get_request_id, get_user_id

        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "InterviewSageAI",
            "request_id": get_request_id(),
            "user_id": get_user_id(),
            "interview_id": get_interview_id(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add duration_ms if explicitly passed in log call
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        if hasattr(record, "workflow_stage"):
            log_data["workflow_stage"] = record.workflow_stage

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)

        return json.dumps(log_data)


def setup_logging() -> None:
    """
    Configure application logging with structured output.
    """
    log_file = Path(settings.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    if settings.debug:
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_format)
    else:
        console_handler.setFormatter(StructuredFormatter())

    root_logger.addHandler(console_handler)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    """
    return logging.getLogger(name)
