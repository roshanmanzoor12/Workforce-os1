from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(".")


def read(
    path: str,
) -> str:
    target = ROOT / path

    if not target.exists():
        raise RuntimeError(
            f"Missing required file: {path}"
        )

    return target.read_text(
        encoding="utf-8"
    )


def write(
    path: str,
    source: str,
) -> None:
    target = ROOT / path

    backup = target.with_suffix(
        target.suffix
        + ".phase17_backup"
    )

    if not backup.exists():
        backup.write_text(
            target.read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )

    target.write_text(
        source,
        encoding="utf-8",
    )


def replace_once(
    source: str,
    old: str,
    new: str,
    *,
    label: str,
) -> str:
    if new in source:
        return source

    if old not in source:
        raise RuntimeError(
            f"Phase 17 anchor missing: {label}"
        )

    return source.replace(
        old,
        new,
        1,
    )


# =========================================================
# LIVE MONITORING MODELS
# =========================================================


def wire_models() -> None:
    path = (
        "app/modules/live_monitoring/"
        "models.py"
    )

    source = read(path)

    source = replace_once(
        source,
        (
            'SCREENSHOT_STATUS_EXPIRED = "expired"\n'
        ),
        (
            'SCREENSHOT_STATUS_EXPIRED = "expired"\n'
            'SCREENSHOT_STATUS_FAILED = "failed"\n'
        ),
        label=(
            "screenshot failed status"
        ),
    )

    source = replace_once(
        source,
        (
            '    "SCREENSHOT_STATUS_EXPIRED",\n'
        ),
        (
            '    "SCREENSHOT_STATUS_EXPIRED",\n'
            '    "SCREENSHOT_STATUS_FAILED",\n'
        ),
        label=(
            "screenshot failed export"
        ),
    )

    write(
        path,
        source,
    )


# =========================================================
# LIVE MONITORING SCHEMAS
# =========================================================


def wire_schemas() -> None:
    path = (
        "app/modules/live_monitoring/"
        "schemas.py"
    )

    source = read(path)

    deny_block = """class ScreenshotAgentDeny(
    LiveMonitoringSchema
):
    reason: str | None = Field(
        default=None,
        max_length=500,
    )
"""

    fail_block = deny_block + """

class ScreenshotAgentFail(
    LiveMonitoringSchema
):
    reason: str = Field(
        min_length=1,
        max_length=1000,
    )
"""

    source = replace_once(
        source,
        deny_block,
        fail_block,
        label="ScreenshotAgentFail schema",
    )

    # Browser-facing screenshot history must not expose
    # storage object keys or raw integrity hashes.
    source = re.sub(
        (
            r"\n    storage_object_key: \(\s*"
            r"str\s*\|\s*None\s*\)\s*"
            r"\n\s*sha256: \(\s*"
            r"str\s*\|\s*None\s*\)\s*"
        ),
        "\n",
        source,
        count=1,
    )

    list_anchor = """class ScreenshotListResponse(
    LiveMonitoringSchema
):
    items: list[
        ScreenshotResponse
    ] = Field(
        default_factory=list
    )

    total: int = Field(
        ge=0
    )
"""

    media_block = list_anchor + """

class ScreenshotMediaResponse(
    LiveMonitoringSchema
):
    request_id: uuid.UUID

    download_url: str = Field(
        min_length=1,
    )

    expires_in_seconds: int = Field(
        ge=1,
        le=3600,
    )
"""

    source = replace_once(
        source,
        list_anchor,
        media_block,
        label=(
            "ScreenshotMediaResponse schema"
        ),
    )

    source = replace_once(
        source,
        (
            '    "ScreenshotAgentDeny",\n'
        ),
        (
            '    "ScreenshotAgentDeny",\n'
            '    "ScreenshotAgentFail",\n'
        ),
        label="ScreenshotAgentFail export",
    )

    source = replace_once(
        source,
        (
            '    "ScreenshotListResponse",\n'
        ),
        (
            '    "ScreenshotListResponse",\n'
            '    "ScreenshotMediaResponse",\n'
        ),
        label=(
            "ScreenshotMediaResponse export"
        ),
    )

    write(
        path,
        source,
    )


# =========================================================
# REPOSITORY
# =========================================================


def wire_repository() -> None:
    path = (
        "app/modules/live_monitoring/"
        "repository.py"
    )

    source = read(path)

    source = replace_once(
        source,
        "import uuid\n",
        (
            "import uuid\n"
            "from datetime import datetime\n"
        ),
        label="repository datetime import",
    )

    anchor = """    async def create_live_session(
        self,
        item: LiveScreenSession,
    ) -> LiveScreenSession:
"""

    method = """    async def list_screenshots_filtered(
        self,
        *,
        employee_ids: (
            frozenset[
                uuid.UUID
            ]
            | None
        ),
        employee_id: uuid.UUID | None,
        device_id: uuid.UUID | None,
        status: str | None,
        start_at: datetime | None,
        end_at: datetime | None,
        limit: int,
        offset: int,
    ) -> tuple[
        list[
            ScreenshotCaptureRequest
        ],
        int,
    ]:
        filters = []

        if employee_id is not None:
            if (
                employee_ids is not None
                and employee_id
                not in employee_ids
            ):
                return (
                    [],
                    0,
                )

            filters.append(
                ScreenshotCaptureRequest
                .employee_id
                == employee_id
            )

        elif employee_ids is not None:
            if not employee_ids:
                return (
                    [],
                    0,
                )

            filters.append(
                ScreenshotCaptureRequest
                .employee_id
                .in_(
                    tuple(
                        employee_ids
                    )
                )
            )

        if device_id is not None:
            filters.append(
                ScreenshotCaptureRequest
                .device_id
                == device_id
            )

        if status is not None:
            filters.append(
                ScreenshotCaptureRequest
                .status
                == status
            )

        if start_at is not None:
            filters.append(
                ScreenshotCaptureRequest
                .requested_at
                >= start_at
            )

        if end_at is not None:
            filters.append(
                ScreenshotCaptureRequest
                .requested_at
                < end_at
            )

        count_statement = (
            select(
                func.count(
                    ScreenshotCaptureRequest.id
                )
            )
        )

        if filters:
            count_statement = (
                count_statement.where(
                    *filters
                )
            )

        total_result = await (
            self.session.execute(
                count_statement
            )
        )

        total = int(
            total_result.scalar_one()
            or 0
        )

        statement = (
            select(
                ScreenshotCaptureRequest
            )
            .order_by(
                ScreenshotCaptureRequest
                .requested_at
                .desc(),
                ScreenshotCaptureRequest
                .id
                .desc(),
            )
            .limit(
                limit
            )
            .offset(
                offset
            )
        )

        if filters:
            statement = statement.where(
                *filters
            )

        result = await (
            self.session.execute(
                statement
            )
        )

        return (
            list(
                result.scalars().all()
            ),
            total,
        )

""" + anchor

    source = replace_once(
        source,
        anchor,
        method,
        label=(
            "filtered screenshot repository"
        ),
    )

    write(
        path,
        source,
    )


# =========================================================
# SERVICE
# =========================================================


def wire_service() -> None:
    path = (
        "app/modules/live_monitoring/"
        "service.py"
    )

    source = read(path)

    source = replace_once(
        source,
        (
            "    SCREENSHOT_STATUS_EXPIRED,\n"
            "    SCREENSHOT_STATUS_PENDING,\n"
        ),
        (
            "    SCREENSHOT_STATUS_EXPIRED,\n"
            "    SCREENSHOT_STATUS_FAILED,\n"
            "    SCREENSHOT_STATUS_PENDING,\n"
        ),
        label="failed model import",
    )

    source = replace_once(
        source,
        (
            "    ScreenshotAgentDeny,\n"
        ),
        (
            "    ScreenshotAgentDeny,\n"
            "    ScreenshotAgentFail,\n"
        ),
        label="fail schema import",
    )

    live_anchor = """    # =====================================================
    # LIVE SCREEN
    # =====================================================
"""

    methods = """    async def fail_screenshot(
        self,
        *,
        access: LiveMonitoringAccess,
        request_id: uuid.UUID,
        payload: ScreenshotAgentFail,
    ) -> ScreenshotResponse:
        item = await (
            self.repository
            .get_screenshot(
                request_id=request_id
            )
        )

        if item is None:
            raise LiveMonitoringNotFoundError(
                "Screenshot request not found."
            )

        device = await self.devices.get(
            device_id=item.device_id
        )

        if device is None:
            raise LiveMonitoringNotFoundError(
                "Desktop agent device not found."
            )

        try:
            require_device_owner(
                access=access,
                device=device,
            )

        except ValidationError as exc:
            raise (
                LiveMonitoringPermissionError(
                    str(exc)
                )
            ) from exc

        if (
            item.status
            != SCREENSHOT_STATUS_PENDING
        ):
            raise ValidationError(
                "Screenshot request is no longer "
                "pending."
            )

        item.status = (
            SCREENSHOT_STATUS_FAILED
        )

        item.completed_at = (
            self._now()
        )

        item.metadata_json = {
            **(
                item.metadata_json
                or {}
            ),
            "failure_reason": (
                payload.reason
            ),
        }

        return self._screenshot_response(
            await (
                self.repository
                .refresh_screenshot(
                    item
                )
            )
        )

    async def list_screenshots_history(
        self,
        *,
        access: LiveMonitoringAccess,
        employee_id: uuid.UUID | None,
        device_id: uuid.UUID | None,
        status: str | None,
        start_at: datetime | None,
        end_at: datetime | None,
        limit: int,
        offset: int,
    ) -> ScreenshotListResponse:
        if (
            not access
            .can_request_screenshot
        ):
            raise LiveMonitoringPermissionError(
                "Live monitoring view permission "
                "required."
            )

        if (
            start_at is not None
            and end_at is not None
            and start_at >= end_at
        ):
            raise ValidationError(
                "start_at must be earlier "
                "than end_at."
            )

        items, total = await (
            self.repository
            .list_screenshots_filtered(
                employee_ids=(
                    access
                    .visible_employee_ids
                ),
                employee_id=employee_id,
                device_id=device_id,
                status=status,
                start_at=start_at,
                end_at=end_at,
                limit=limit,
                offset=offset,
            )
        )

        return ScreenshotListResponse(
            items=[
                self._screenshot_response(
                    item
                )
                for item
                in items
            ],
            total=total,
        )

    async def get_screenshot_media_object_key(
        self,
        *,
        access: LiveMonitoringAccess,
        request_id: uuid.UUID,
    ) -> str:
        if (
            not access
            .can_request_screenshot
        ):
            raise LiveMonitoringPermissionError(
                "Live monitoring view permission "
                "required."
            )

        item = await (
            self.repository
            .get_screenshot(
                request_id=request_id
            )
        )

        if item is None:
            raise LiveMonitoringNotFoundError(
                "Screenshot request not found."
            )

        if not can_access_employee(
            access=access,
            employee_id=(
                item.employee_id
            ),
        ):
            raise LiveMonitoringPermissionError(
                "Screenshot is outside your "
                "permitted employee scope."
            )

        if (
            item.status
            != SCREENSHOT_STATUS_COMPLETED
        ):
            raise ValidationError(
                "Screenshot media is available "
                "only after successful completion."
            )

        if not item.storage_object_key:
            raise ValidationError(
                "Screenshot media is unavailable."
            )

        return item.storage_object_key

""" + live_anchor

    source = replace_once(
        source,
        live_anchor,
        methods,
        label="Phase 17 screenshot service",
    )

    write(
        path,
        source,
    )


# =========================================================
# ROUTER
# =========================================================


def wire_router() -> None:
    path = (
        "app/modules/live_monitoring/"
        "router.py"
    )

    source = read(path)

    source = replace_once(
        source,
        "import uuid\n",
        (
            "import uuid\n"
            "from datetime import datetime\n"
        ),
        label="router datetime import",
    )

    source = replace_once(
        source,
        (
            "    ScreenshotAgentDeny,\n"
        ),
        (
            "    ScreenshotAgentDeny,\n"
            "    ScreenshotAgentFail,\n"
        ),
        label="router fail schema import",
    )

    source = replace_once(
        source,
        (
            "    ScreenshotListResponse,\n"
        ),
        (
            "    ScreenshotListResponse,\n"
            "    ScreenshotMediaResponse,\n"
        ),
        label="router media schema import",
    )

    service_import = """from app.modules.live_monitoring.service import (
"""

    phase_import = """from app.modules.live_monitoring.phase17 import (
    SCREENSHOT_ALLOWED_STATUSES,
    create_screenshot_download_url,
    effective_retention_start,
    record_screenshot_audit,
)
from app.modules.monitoring_admin.service import (
    MonitoringAdminService,
)
"""

    if phase_import not in source:
        source = source.replace(
            service_import,
            phase_import
            + service_import,
            1,
        )

    pattern = re.compile(
        r'@router\.get\(\n'
        r'    "/screenshots",\n'
        r'    response_model=ScreenshotListResponse,\n'
        r'\)\n'
        r'async def list_screenshots\([\s\S]*?'
        r'(?=\n@router\.post\(\n'
        r'    "/screenshots/\{request_id\}/complete")'
    )

    replacement = '''@router.get(
    "/screenshots",
    response_model=ScreenshotListResponse,
)
async def list_screenshots(
    workspace_id: uuid.UUID,
    context: TenantContext,

    employee_id: uuid.UUID | None = Query(
        default=None,
    ),

    device_id: uuid.UUID | None = Query(
        default=None,
    ),

    status_filter: str | None = Query(
        default=None,
        alias="status",
        max_length=32,
    ),

    start_at: datetime | None = Query(
        default=None,
    ),

    end_at: datetime | None = Query(
        default=None,
    ),

    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),

    offset: int = Query(
        default=0,
        ge=0,
    ),
) -> ScreenshotListResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    if status_filter is not None:
        status_filter = (
            status_filter
            .strip()
            .lower()
        )

        if (
            status_filter
            not in SCREENSHOT_ALLOWED_STATUSES
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Invalid screenshot status."
                ),
            )

    policy = await (
        MonitoringAdminService(
            tenant_session=(
                context.tenant_session
            ),
            workspace_id=workspace_id,
        )
        .policy()
    )

    effective_start = (
        effective_retention_start(
            requested_start=start_at,
            retention_days=(
                policy
                .screenshot_retention_days
            ),
        )
    )

    try:
        result = await (
            _service(
                context
            )
            .list_screenshots_history(
                access=access,
                employee_id=employee_id,
                device_id=device_id,
                status=status_filter,
                start_at=effective_start,
                end_at=end_at,
                limit=limit,
                offset=offset,
            )
        )

        await record_screenshot_audit(
            control_session=(
                context.control_session
            ),
            workspace_id=workspace_id,
            actor_user_id=(
                access.actor_user_id
            ),
            action=(
                "screenshot.history.view"
            ),
            event_data={
                "employee_id": employee_id,
                "device_id": device_id,
                "status": status_filter,
                "start_at": effective_start,
                "end_at": end_at,
                "result_count": len(
                    result.items
                ),
            },
        )

        return result

    except (
        ValidationError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc

'''

    source, count = pattern.subn(
        replacement,
        source,
        count=1,
    )

    if count != 1:
        if (
            ".list_screenshots_history("
            not in source
        ):
            raise RuntimeError(
                "Could not replace screenshot "
                "history route."
            )

    live_anchor = '''@router.post(
    "/live-sessions",
'''

    extra_routes = '''@router.post(
    "/screenshots/{request_id}/fail",
    response_model=ScreenshotResponse,
)
async def fail_screenshot(
    workspace_id: uuid.UUID,
    request_id: uuid.UUID,
    payload: ScreenshotAgentFail,
    context: TenantContext,
) -> ScreenshotResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .fail_screenshot(
                access=access,
                request_id=request_id,
                payload=payload,
            )
        )

    except (
        ValidationError,
        LiveMonitoringNotFoundError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


@router.post(
    "/screenshots/{request_id}/media",
    response_model=ScreenshotMediaResponse,
)
async def screenshot_media(
    workspace_id: uuid.UUID,
    request_id: uuid.UUID,
    context: TenantContext,
) -> ScreenshotMediaResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        object_key = await (
            _service(
                context
            )
            .get_screenshot_media_object_key(
                access=access,
                request_id=request_id,
            )
        )

        (
            download_url,
            expires_in_seconds,
        ) = create_screenshot_download_url(
            object_key=object_key
        )

        await record_screenshot_audit(
            control_session=(
                context.control_session
            ),
            workspace_id=workspace_id,
            actor_user_id=(
                access.actor_user_id
            ),
            action=(
                "screenshot.media.view"
            ),
            target_id=request_id,
        )

        return ScreenshotMediaResponse(
            request_id=request_id,
            download_url=download_url,
            expires_in_seconds=(
                expires_in_seconds
            ),
        )

    except (
        ValidationError,
        LiveMonitoringNotFoundError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


''' + live_anchor

    source = replace_once(
        source,
        live_anchor,
        extra_routes,
        label="Phase 17 screenshot routes",
    )

    write(
        path,
        source,
    )


# =========================================================
# TIMELINE ENUMS
# =========================================================


def wire_timeline_enums() -> None:
    path = (
        "app/modules/timeline/enums.py"
    )

    source = read(path)

    source = replace_once(
        source,
        (
            '    ATTENDANCE_BREAK_END = (\n'
            '        "attendance.break_end"\n'
            '    )\n'
        ),
        (
            '    ATTENDANCE_BREAK_END = (\n'
            '        "attendance.break_end"\n'
            '    )\n'
            '\n'
            '    SCREENSHOT_REQUESTED = (\n'
            '        "screenshot.requested"\n'
            '    )\n'
            '\n'
            '    SCREENSHOT_COMPLETED = (\n'
            '        "screenshot.completed"\n'
            '    )\n'
            '\n'
            '    SCREENSHOT_DENIED = (\n'
            '        "screenshot.denied"\n'
            '    )\n'
            '\n'
            '    SCREENSHOT_EXPIRED = (\n'
            '        "screenshot.expired"\n'
            '    )\n'
            '\n'
            '    SCREENSHOT_FAILED = (\n'
            '        "screenshot.failed"\n'
            '    )\n'
        ),
        label="timeline screenshot events",
    )

    source = replace_once(
        source,
        (
            '    ATTENDANCE_EVENT = (\n'
            '        "attendance_event"\n'
            '    )\n'
        ),
        (
            '    ATTENDANCE_EVENT = (\n'
            '        "attendance_event"\n'
            '    )\n'
            '\n'
            '    SCREENSHOT_CAPTURE = (\n'
            '        "screenshot_capture"\n'
            '    )\n'
        ),
        label="timeline screenshot entity",
    )

    source = replace_once(
        source,
        (
            '    ATTENDANCE = "attendance"\n'
        ),
        (
            '    ATTENDANCE = "attendance"\n'
            '\n'
            '    SCREENSHOTS = "screenshots"\n'
        ),
        label="timeline screenshot source",
    )

    write(
        path,
        source,
    )


# =========================================================
# TIMELINE SOURCE
# =========================================================


def wire_timeline_sources() -> None:
    path = (
        "app/modules/timeline/sources.py"
    )

    source = read(path)

    monitoring_import = """from app.modules.live_monitoring.models import (
    SCREENSHOT_STATUS_COMPLETED,
    SCREENSHOT_STATUS_DENIED,
    SCREENSHOT_STATUS_EXPIRED,
    SCREENSHOT_STATUS_FAILED,
    SCREENSHOT_STATUS_PENDING,
    ScreenshotCaptureRequest,
)
"""

    employee_import = (
        "from app.modules.meetings.models import (\n"
    )

    if monitoring_import not in source:
        source = source.replace(
            employee_import,
            monitoring_import
            + employee_import,
            1,
        )

    build_anchor = """def build_default_timeline_sources(
    session: AsyncSession,
) -> list[
    TimelineSource
]:
"""

    screenshot_source = """class ScreenshotTimelineSource:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    @staticmethod
    def _event_type(
        status: str,
    ) -> TimelineEventType:
        mapping = {
            SCREENSHOT_STATUS_PENDING: (
                TimelineEventType
                .SCREENSHOT_REQUESTED
            ),
            SCREENSHOT_STATUS_COMPLETED: (
                TimelineEventType
                .SCREENSHOT_COMPLETED
            ),
            SCREENSHOT_STATUS_DENIED: (
                TimelineEventType
                .SCREENSHOT_DENIED
            ),
            SCREENSHOT_STATUS_EXPIRED: (
                TimelineEventType
                .SCREENSHOT_EXPIRED
            ),
            SCREENSHOT_STATUS_FAILED: (
                TimelineEventType
                .SCREENSHOT_FAILED
            ),
        }

        return mapping.get(
            status,
            TimelineEventType
            .SCREENSHOT_REQUESTED,
        )

    @staticmethod
    def _title(
        status: str,
    ) -> str:
        titles = {
            SCREENSHOT_STATUS_PENDING: (
                "Screenshot requested"
            ),
            SCREENSHOT_STATUS_COMPLETED: (
                "Screenshot completed"
            ),
            SCREENSHOT_STATUS_DENIED: (
                "Screenshot denied"
            ),
            SCREENSHOT_STATUS_EXPIRED: (
                "Screenshot expired"
            ),
            SCREENSHOT_STATUS_FAILED: (
                "Screenshot failed"
            ),
        }

        return titles.get(
            status,
            "Screenshot event",
        )

    async def list_events(
        self,
        *,
        employee_id: uuid.UUID,
        before: datetime | None,
        after: datetime | None,
        limit: int,
    ) -> list[
        TimelineEvent
    ]:
        statement = (
            select(
                ScreenshotCaptureRequest
            )
            .where(
                ScreenshotCaptureRequest
                .employee_id
                == employee_id
            )
        )

        if before is not None:
            statement = (
                statement.where(
                    ScreenshotCaptureRequest
                    .requested_at
                    < before
                )
            )

        if after is not None:
            statement = (
                statement.where(
                    ScreenshotCaptureRequest
                    .requested_at
                    >= after
                )
            )

        statement = (
            statement
            .order_by(
                ScreenshotCaptureRequest
                .requested_at
                .desc(),
                ScreenshotCaptureRequest
                .id
                .desc(),
            )
            .limit(
                limit
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        screenshots = list(
            result.scalars().all()
        )

        items: list[
            TimelineEvent
        ] = []

        for screenshot in screenshots:
            occurred_at = (
                screenshot.completed_at
                if (
                    screenshot.completed_at
                    is not None
                    and screenshot.status
                    != SCREENSHOT_STATUS_PENDING
                )
                else screenshot.requested_at
            )

            items.append(
                TimelineEvent(
                    event_id=(
                        "screenshot:"
                        f"{screenshot.status}:"
                        f"{screenshot.id}"
                    ),
                    event_type=(
                        self._event_type(
                            screenshot.status
                        )
                    ),
                    source=(
                        TimelineSourceKey
                        .SCREENSHOTS
                    ),
                    entity_type=(
                        TimelineEntityType
                        .SCREENSHOT_CAPTURE
                    ),
                    entity_id=(
                        screenshot.id
                    ),
                    employee_id=(
                        employee_id
                    ),
                    occurred_at=(
                        occurred_at
                    ),
                    title=(
                        self._title(
                            screenshot.status
                        )
                    ),
                    summary=(
                        screenshot.reason
                    ),
                    metadata={
                        "device_id": (
                            screenshot
                            .device_id
                        ),
                        "status": (
                            screenshot.status
                        ),
                        "width": (
                            screenshot.width
                        ),
                        "height": (
                            screenshot.height
                        ),
                        "consent_required": (
                            screenshot
                            .consent_required
                        ),
                        "visible_indicator_required": (
                            screenshot
                            .visible_indicator_required
                        ),
                    },
                )
            )

        return items


""" + build_anchor

    source = replace_once(
        source,
        build_anchor,
        screenshot_source,
        label="ScreenshotTimelineSource",
    )

    source = replace_once(
        source,
        """        AttendanceTimelineSource(
            session
        ),
""",
        """        AttendanceTimelineSource(
            session
        ),
        ScreenshotTimelineSource(
            session
        ),
""",
        label=(
            "default screenshot timeline source"
        ),
    )

    source = replace_once(
        source,
        (
            '    "AttendanceTimelineSource",\n'
        ),
        (
            '    "AttendanceTimelineSource",\n'
            '    "ScreenshotTimelineSource",\n'
        ),
        label=(
            "screenshot timeline export"
        ),
    )

    write(
        path,
        source,
    )


# =========================================================
# TIMELINE REGISTRY
# =========================================================


def wire_timeline_registry() -> None:
    path = (
        "app/modules/timeline/registry.py"
    )

    source = read(path)

    source = replace_once(
        source,
        (
            "    NoteTimelineSource,\n"
            "    TimelineSource,\n"
        ),
        (
            "    NoteTimelineSource,\n"
            "    ScreenshotTimelineSource,\n"
            "    TimelineSource,\n"
        ),
        label="registry screenshot import",
    )

    attendance_block = """            RegisteredTimelineSource(
                key=(
                    TimelineSourceKey
                    .ATTENDANCE
                ),
                source=(
                    AttendanceTimelineSource(
                        session
                    )
                ),
            ),
"""

    screenshot_block = attendance_block + """            RegisteredTimelineSource(
                key=(
                    TimelineSourceKey
                    .SCREENSHOTS
                ),
                source=(
                    ScreenshotTimelineSource(
                        session
                    )
                ),
            ),
"""

    source = replace_once(
        source,
        attendance_block,
        screenshot_block,
        label="registry screenshot entry",
    )

    write(
        path,
        source,
    )


def main() -> None:
    wire_models()
    wire_schemas()
    wire_repository()
    wire_service()
    wire_router()

    wire_timeline_enums()
    wire_timeline_sources()
    wire_timeline_registry()

    print(
        "PASS Phase 17 screenshot/timeline "
        "wiring complete"
    )


if __name__ == "__main__":
    main()