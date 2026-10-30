from __future__ import annotations


PHASE_11_8_MEETINGS_CONTRACT = {
    "tenant_revision": (
        "d3e4f5a6b7c8"
    ),
    "tenant_down_revision": (
        "c2d3e4f5a6b7"
    ),
    "tables": [
        "meetings",
        "meeting_participants",
    ],
    "meeting_lifecycle": [
        "scheduled",
        "active",
        "completed",
        "cancelled",
    ],
    "participant_status": [
        "invited",
        "accepted",
        "declined",
    ],
    "permissions": [
        "meetings.view",
        "meetings.create",
        "meetings.manage",
    ],
    "self_service": {
        "list_invitations": True,
        "accept": True,
        "decline": True,
        "employee_identity_from_backend": True,
    },
    "tenant_isolation": {
        "workspace_id_column": False,
        "physical_tenant_database": True,
    },
}


__all__ = [
    "PHASE_11_8_MEETINGS_CONTRACT",
]