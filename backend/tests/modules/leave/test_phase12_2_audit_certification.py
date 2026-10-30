from __future__ import annotations

import inspect

from app.modules.audit_log.service import (
    AuditLogService,
)
import app.modules.leave.audit as leave_audit


def test_leave_audit_module_uses_canonical_audit_service():
    source = inspect.getsource(
        leave_audit
    )

    assert (
        "AuditLogService"
        in source
    )

    assert (
        "AuditEventCreate"
        in source
    )


def test_leave_audit_records_workspace_identity():
    source = inspect.getsource(
        leave_audit
    )

    assert (
        "workspace_id"
        in source
    )

    assert (
        "actor_user_id"
        in source
    )


def test_leave_audit_covers_sensitive_actions():
    source = (
        inspect
        .getsource(
            leave_audit
        )
        .lower()
    )

    required_words = {
        "approve",
        "reject",
        "cancel",
        "balance",
        "policy",
    }

    for word in required_words:
        assert word in source


def test_canonical_audit_service_is_append_oriented():
    source = inspect.getsource(
        AuditLogService.record
    )

    assert (
        "repository.create"
        in source
    )

    # Canonical audit service deliberately leaves
    # commit ownership with the caller.
    assert (
        ".commit("
        not in source
    )