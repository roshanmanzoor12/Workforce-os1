from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


AUDIT_OUTCOME_SUCCESS = "success"
AUDIT_OUTCOME_FAILURE = "failure"


AUDIT_OUTCOMES = frozenset(
    {
        AUDIT_OUTCOME_SUCCESS,
        AUDIT_OUTCOME_FAILURE,
    }
)


AUDIT_SEVERITY_INFO = "info"
AUDIT_SEVERITY_WARNING = "warning"
AUDIT_SEVERITY_ERROR = "error"


AUDIT_SEVERITIES = frozenset(
    {
        AUDIT_SEVERITY_INFO,
        AUDIT_SEVERITY_WARNING,
        AUDIT_SEVERITY_ERROR,
    }
)


class WorkspaceAuditEvent(Base):
    __tablename__ = (
        "workspace_audit_events"
    )

    __table_args__ = (
        Index(
            "ix_wsa_workspace_time",
            "workspace_id",
            "occurred_at",
        ),
        Index(
            "ix_wsa_actor_time",
            "actor_user_id",
            "occurred_at",
        ),
        Index(
            "ix_wsa_action",
            "workspace_id",
            "action",
        ),
        Index(
            "ix_wsa_target",
            "workspace_id",
            "target_type",
            "target_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Logical reference only.
    #
    # Audit history must survive workspace deletion /
    # archival and must not be cascade-deleted.
    workspace_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Logical global-user reference.
    #
    # No FK so history survives account/member removal.
    actor_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    outcome: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AUDIT_OUTCOME_SUCCESS,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AUDIT_SEVERITY_INFO,
    )

    target_type: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    target_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    target_label: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
    )

    message: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    request_id: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    ip_address: Mapped[
        str | None
    ] = mapped_column(
        String(64),
        nullable=True,
    )

    user_agent: Mapped[
        str | None
    ] = mapped_column(
        String(1000),
        nullable=True,
    )

    # Do not name this ORM attribute "metadata".
    # SQLAlchemy Declarative reserves that name.
    event_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    occurred_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        server_default=func.now(),
    )


__all__ = [
    "AUDIT_OUTCOME_SUCCESS",
    "AUDIT_OUTCOME_FAILURE",
    "AUDIT_OUTCOMES",

    "AUDIT_SEVERITY_INFO",
    "AUDIT_SEVERITY_WARNING",
    "AUDIT_SEVERITY_ERROR",
    "AUDIT_SEVERITIES",

    "WorkspaceAuditEvent",
]