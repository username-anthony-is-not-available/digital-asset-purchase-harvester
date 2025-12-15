"""Structured logging utilities."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

ISO_TIMESTAMP = "%Y-%m-%dT%H:%M:%S.%fZ"


class JsonFormatter(logging.Formatter):
    """Format log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - thin wrapper
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).strftime(ISO_TIMESTAMP),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Include any extra fields set on the record
        payload.update({k: v for k, v in record.__dict__.items() if k.startswith("extra_")})
        return json.dumps(payload)


@dataclass
class StructuredLoggerFactory:
    """Factory for creating structured logger adapters."""

    json_output: bool = False

    def build(self, name: str, *, default_fields: Optional[Dict[str, Any]] = None) -> "StructuredLoggerAdapter":
        logger = logging.getLogger(name)
        if self.json_output:
            # ensure handler has JSON formatter once
            if not any(isinstance(handler.formatter, JsonFormatter) for handler in logger.handlers):
                handler = logging.StreamHandler()
                handler.setFormatter(JsonFormatter())
                logger.addHandler(handler)
        return StructuredLoggerAdapter(logger, default_fields or {})


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that merges structured data for every message."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        extra = kwargs.setdefault("extra", {})
        # Merge adapter context
        extra_fields = {f"extra_{k}": v for k, v in self.extra.items()}
        extra.update(extra_fields)
        return msg, kwargs

    def bind(self, **fields: Any) -> "StructuredLoggerAdapter":
        merged = dict(self.extra)
        merged.update(fields)
        return StructuredLoggerAdapter(self.logger, merged)


def log_event(logger: StructuredLoggerAdapter, event: str, **fields: Any) -> None:
    """Emit a structured info-level event."""

    logger.info(event, extra={f"extra_{k}": v for k, v in fields.items()})
