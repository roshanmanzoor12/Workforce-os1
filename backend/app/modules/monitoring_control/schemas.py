from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class MonitoringControlSchema(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )


class MonitoringCapabilityResponse(
    MonitoringControlSchema
):
    monitoring_view: bool
    monitoring_manage: bool
    live_screen_view: bool
    settings_manage: bool


class MonitoringControlSummaryResponse(
    MonitoringControlSchema
):
    role_key: str

    capabilities: (
        MonitoringCapabilityResponse
    )

    permissions: list[
        str
    ] = Field(
        default_factory=list
    )


class MonitoringAccessResponse(
    MonitoringControlSchema
):
    permission: str
    allowed: bool


__all__ = [
    "MonitoringCapabilityResponse",
    "MonitoringControlSummaryResponse",
    "MonitoringAccessResponse",
]