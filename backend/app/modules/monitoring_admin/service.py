from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.exceptions import (
    ValidationError,
)
from app.modules.live_monitoring.screenshot_retention import (
    ScreenshotRetentionService,
)
from app.modules.monitoring_admin.access import (
    MonitoringAdminAccess,
    require_monitoring_settings_manager,
    require_monitoring_view,
)
from app.modules.monitoring_admin.repository import (
    MonitoringAdminRepository,
)
from app.modules.monitoring_admin.schemas import (
    MonitoringAdminPolicyPublic,
    MonitoringAdminPolicyUpdate,
    MonitoringAdminSummaryResponse,
    MonitoringPolicyAccessResponse,
    MonitoringPolicyCapabilities,
    MonitoringScreenshotRetentionCleanupResponse,
)


class MonitoringPolicyDisabledError(
    PermissionError
):
    pass


class MonitoringAdminService:
    def __init__(
        self,
        *,
        tenant_session: AsyncSession,
        workspace_id: uuid.UUID,
    ) -> None:
        self.tenant_session = (
            tenant_session
        )

        self.workspace_id = (
            workspace_id
        )

        self.repository = (
            MonitoringAdminRepository(
                tenant_session
            )
        )

    async def policy(
        self,
    ):
        return await (
            self.repository
            .get_or_create_policy()
        )

    @staticmethod
    def public_policy(
        policy,
    ) -> MonitoringAdminPolicyPublic:
        return (
            MonitoringAdminPolicyPublic(
                id=policy.id,

                monitoring_enabled=(
                    policy.monitoring_enabled
                ),

                screenshots_enabled=(
                    policy.screenshots_enabled
                ),

                live_screen_enabled=(
                    policy.live_screen_enabled
                ),

                screen_share_enabled=(
                    policy.screen_share_enabled
                ),

                disclosure_required=(
                    policy.disclosure_required
                ),

                explicit_live_consent_required=(
                    policy
                    .explicit_live_consent_required
                ),

                visible_live_indicator_required=(
                    policy
                    .visible_live_indicator_required
                ),

                screenshot_interval_seconds=(
                    policy
                    .screenshot_interval_seconds
                ),

                screenshot_retention_days=(
                    policy
                    .screenshot_retention_days
                ),

                live_session_max_minutes=(
                    policy
                    .live_session_max_minutes
                ),

                policy_version=(
                    policy.policy_version
                ),

                policy_notice=(
                    policy.policy_notice
                ),

                updated_by_user_id=(
                    policy
                    .updated_by_user_id
                ),

                created_at=(
                    policy.created_at
                ),

                updated_at=(
                    policy.updated_at
                ),
            )
        )

    @staticmethod
    def capabilities_from_policy(
        policy,
    ) -> MonitoringPolicyCapabilities:
        monitoring_allowed = bool(
            policy.monitoring_enabled
        )

        return (
            MonitoringPolicyCapabilities(
                monitoring_allowed=(
                    monitoring_allowed
                ),

                screenshots_allowed=(
                    monitoring_allowed
                    and (
                        policy
                        .screenshots_enabled
                    )
                ),

                live_screen_allowed=(
                    monitoring_allowed
                    and (
                        policy
                        .live_screen_enabled
                    )
                ),

                screen_share_allowed=(
                    monitoring_allowed
                    and (
                        policy
                        .screen_share_enabled
                    )
                ),

                disclosure_required=(
                    policy.disclosure_required
                ),

                explicit_live_consent_required=(
                    policy
                    .explicit_live_consent_required
                ),

                visible_live_indicator_required=(
                    policy
                    .visible_live_indicator_required
                ),

                screenshot_interval_seconds=(
                    policy
                    .screenshot_interval_seconds
                ),

                screenshot_retention_days=(
                    policy
                    .screenshot_retention_days
                ),

                live_session_max_minutes=(
                    policy
                    .live_session_max_minutes
                ),

                policy_version=(
                    policy.policy_version
                ),
            )
        )

    async def summary(
        self,
        *,
        access: MonitoringAdminAccess,
    ) -> MonitoringAdminSummaryResponse:
        require_monitoring_view(
            access
        )

        policy = await self.policy()

        return (
            MonitoringAdminSummaryResponse(
                workspace_id=(
                    self.workspace_id
                ),

                policy=self.public_policy(
                    policy
                ),

                capabilities=(
                    self
                    .capabilities_from_policy(
                        policy
                    )
                ),

                access=(
                    MonitoringPolicyAccessResponse(
                        can_view=(
                            access.can_view
                        ),

                        can_manage=(
                            access.can_manage
                        ),

                        can_live_view=(
                            access
                            .can_live_view
                        ),

                        can_live_screen=(
                            access
                            .can_live_screen
                        ),

                        can_manage_settings=(
                            access
                            .can_manage_settings
                        ),
                    )
                ),
            )
        )

    async def update_policy(
        self,
        *,
        access: MonitoringAdminAccess,
        payload: MonitoringAdminPolicyUpdate,
    ) -> MonitoringAdminPolicyPublic:
        require_monitoring_settings_manager(
            access
        )

        policy = await self.policy()

        changes = (
            payload.model_dump(
                exclude_unset=True
            )
        )

        if not changes:
            raise ValidationError(
                "At least one monitoring "
                "policy field is required."
            )

        # Sensitive monitoring protections
        # must never be weakened.

        if (
            "explicit_live_consent_required"
            in changes
            and (
                changes[
                    "explicit_live_consent_required"
                ]
                is False
            )
        ):
            raise ValidationError(
                "Explicit live-screen consent "
                "cannot be disabled."
            )

        if (
            "visible_live_indicator_required"
            in changes
            and (
                changes[
                    "visible_live_indicator_required"
                ]
                is False
            )
        ):
            raise ValidationError(
                "Visible live-screen indicator "
                "cannot be disabled."
            )

        if (
            "disclosure_required"
            in changes
            and (
                changes[
                    "disclosure_required"
                ]
                is False
            )
        ):
            raise ValidationError(
                "Monitoring disclosure "
                "cannot be disabled."
            )

        for (
            field_name,
            value,
        ) in changes.items():
            setattr(
                policy,
                field_name,
                value,
            )

        policy.policy_version += 1

        policy.updated_by_user_id = (
            access.actor_user_id
        )

        policy = await (
            self.repository.refresh(
                policy
            )
        )

        return self.public_policy(
            policy
        )

    async def cleanup_screenshot_retention(
        self,
        *,
        access: MonitoringAdminAccess,
        limit: int = 500,
    ) -> (
        MonitoringScreenshotRetentionCleanupResponse
    ):
        require_monitoring_settings_manager(
            access
        )

        policy = await self.policy()

        cleanup = (
            ScreenshotRetentionService(
                self.tenant_session
            )
        )

        result = await cleanup.cleanup(
            retention_days=(
                policy
                .screenshot_retention_days
            ),
            limit=limit,
        )

        return (
            MonitoringScreenshotRetentionCleanupResponse(
                retention_days=(
                    policy
                    .screenshot_retention_days
                ),

                cutoff_at=(
                    result.cutoff_at
                ),

                scanned=(
                    result.scanned
                ),

                deleted=(
                    result.deleted
                ),

                storage_failures=(
                    result.storage_failures
                ),

                database_failures=(
                    result.database_failures
                ),

                has_more=(
                    result.has_more
                ),
            )
        )

    async def require_screenshot_allowed(
        self,
    ) -> None:
        policy = await self.policy()

        if not policy.monitoring_enabled:
            raise (
                MonitoringPolicyDisabledError(
                    "Workspace monitoring "
                    "is disabled."
                )
            )

        if not policy.screenshots_enabled:
            raise (
                MonitoringPolicyDisabledError(
                    "Screenshot capture is "
                    "disabled by workspace policy."
                )
            )

    async def require_live_screen_allowed(
        self,
    ) -> None:
        policy = await self.policy()

        if not policy.monitoring_enabled:
            raise (
                MonitoringPolicyDisabledError(
                    "Workspace monitoring "
                    "is disabled."
                )
            )

        if not policy.live_screen_enabled:
            raise (
                MonitoringPolicyDisabledError(
                    "Live screen is disabled "
                    "by workspace policy."
                )
            )

        if not (
            policy
            .explicit_live_consent_required
        ):
            raise (
                MonitoringPolicyDisabledError(
                    "Invalid live-screen policy: "
                    "explicit consent is required."
                )
            )

        if not (
            policy
            .visible_live_indicator_required
        ):
            raise (
                MonitoringPolicyDisabledError(
                    "Invalid live-screen policy: "
                    "visible indicator is required."
                )
            )


__all__ = [
    "MonitoringPolicyDisabledError",
    "MonitoringAdminService",
]