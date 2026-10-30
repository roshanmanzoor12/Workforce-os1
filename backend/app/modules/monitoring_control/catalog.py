from __future__ import annotations

from app.modules.monitoring_control.permissions import (
    MONITORING_LIVE_VIEW_PERMISSION,
    MONITORING_MANAGE_PERMISSION,
    MONITORING_SETTINGS_MANAGE_PERMISSION,
    MONITORING_VIEW_PERMISSION,
)


MONITORING_CAPABILITY_CATALOG = {
    "overview": {
        "permission": (
            MONITORING_VIEW_PERMISSION
        ),
        "implemented": True,
        "data_collection": False,
    },
    "management": {
        "permission": (
            MONITORING_MANAGE_PERMISSION
        ),
        "implemented": True,
        "data_collection": False,
    },
    "live_screen": {
        "permission": (
            MONITORING_LIVE_VIEW_PERMISSION
        ),
        "implemented": False,
        "data_collection": False,
    },
    "settings": {
        "permission": (
            MONITORING_SETTINGS_MANAGE_PERMISSION
        ),
        "implemented": True,
        "data_collection": False,
    },
}


__all__ = [
    "MONITORING_CAPABILITY_CATALOG",
]