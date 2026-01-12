"""Centralized logging utility for SRL4C.

Usage:
    from srl4c.core.logger import Logger

    Logger.info("attack", "Starting attack", entity_type="attack", entity_id="abc123")
    Logger.warning("score", "Low agreement between judges", entity_type="score", entity_id="def456")
    Logger.error("guardrails", "Failed to generate rules", entity_type="guardrail_set", entity_id="ghi789")
"""

from datetime import datetime

from srl4c.db.models import Log
from srl4c.db.repository import LogRepository, generate_id


class Logger:
    """Simple logging utility that writes to the database."""

    @staticmethod
    def _log(
        level: str,
        source: str,
        message: str,
        entity_type: str = None,
        entity_id: str = None,
        metadata: dict = None,
    ) -> Log:
        """Internal method to create a log entry."""
        log = Log(
            id=generate_id(),
            timestamp=datetime.now().isoformat(),
            level=level,
            source=source,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata,
        )
        return LogRepository.create(log)

    @staticmethod
    def info(
        source: str,
        message: str,
        entity_type: str = None,
        entity_id: str = None,
        metadata: dict = None,
    ) -> Log:
        """Log an info message."""
        return Logger._log("info", source, message, entity_type, entity_id, metadata)

    @staticmethod
    def warning(
        source: str,
        message: str,
        entity_type: str = None,
        entity_id: str = None,
        metadata: dict = None,
    ) -> Log:
        """Log a warning message."""
        return Logger._log("warning", source, message, entity_type, entity_id, metadata)

    @staticmethod
    def error(
        source: str,
        message: str,
        entity_type: str = None,
        entity_id: str = None,
        metadata: dict = None,
    ) -> Log:
        """Log an error message."""
        return Logger._log("error", source, message, entity_type, entity_id, metadata)
