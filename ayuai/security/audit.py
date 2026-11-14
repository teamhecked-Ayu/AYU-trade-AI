"""Security-focused audit events.

Never include passwords, access tokens, API keys, or request bodies in audit events.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

logger = logging.getLogger("ayuai.audit")


@dataclass(frozen=True)
class AuditEvent:
    event: str
    user_id: str | None = None
    ip: str | None = None
    status: str = "ok"

    def write(self) -> None:
        logger.info(
            "audit event=%s user_id=%s ip=%s status=%s",
            self.event,
            self.user_id or "-",
            self.ip or "-",
            self.status,
        )
