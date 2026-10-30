from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest
from pydantic import ValidationError

from app.modules.activity.schemas import (
    ActivityStateRequest,
    ActivityStateResponse,
    ActivityStatusResponse,
)


def test_activity_request_accepts_active_state() -> None:
    now = datetime.now(
        timezone.utc
    )

    payload = ActivityStateRequest(
        state="active",
        idle_seconds=5,
        last_input_at=(
            now
            - timedelta(
                seconds=5
            )
        ),
        observed_at=now,
    )

    assert payload.state == "active"
    assert payload.idle_seconds == 5


def test_activity_request_accepts_idle_state() -> None:
    now = datetime.now(
        timezone.utc
    )

    payload = ActivityStateRequest(
        state="idle",
        idle_seconds=600,
        last_input_at=(
            now
            - timedelta(
                seconds=600
            )
        ),
        observed_at=now,
    )

    assert payload.state == "idle"
    assert payload.idle_seconds == 600


def test_activity_request_normalizes_state() -> None:
    now = datetime.now(
        timezone.utc
    )

    payload = ActivityStateRequest(
        state="  ACTIVE  ",
        idle_seconds=0,
        last_input_at=now,
        observed_at=now,
    )

    assert payload.state == "active"


@pytest.mark.parametrize(
    "state",
    [
        "working",
        "away",
        "offline",
        "unknown",
    ],
)
def test_activity_request_rejects_unknown_state(
    state: str,
) -> None:
    now = datetime.now(
        timezone.utc
    )

    with pytest.raises(
        ValidationError
    ):
        ActivityStateRequest(
            state=state,
            idle_seconds=0,
            observed_at=now,
        )


def test_activity_request_rejects_negative_idle_seconds() -> None:
    with pytest.raises(
        ValidationError
    ):
        ActivityStateRequest(
            state="active",
            idle_seconds=-1,
            observed_at=datetime.now(
                timezone.utc
            ),
        )


def test_activity_request_rejects_excessive_idle_seconds() -> None:
    with pytest.raises(
        ValidationError
    ):
        ActivityStateRequest(
            state="idle",
            idle_seconds=86_401,
            observed_at=datetime.now(
                timezone.utc
            ),
        )


def test_activity_request_rejects_future_last_input() -> None:
    now = datetime.now(
        timezone.utc
    )

    with pytest.raises(
        ValidationError
    ):
        ActivityStateRequest(
            state="active",
            idle_seconds=0,
            last_input_at=(
                now
                + timedelta(
                    seconds=10
                )
            ),
            observed_at=now,
        )


def test_activity_request_rejects_identity_fields() -> None:
    now = datetime.now(
        timezone.utc
    )

    with pytest.raises(
        ValidationError
    ):
        ActivityStateRequest.model_validate(
            {
                "state": "active",
                "idle_seconds": 0,
                "observed_at": now.isoformat(),
                "device_uuid": str(
                    uuid.uuid4()
                ),
                "workspace_id": str(
                    uuid.uuid4()
                ),
            }
        )


def test_activity_state_response_accepts_valid_data() -> None:
    now = datetime.now(
        timezone.utc
    )

    response = ActivityStateResponse(
        event_id=uuid.uuid4(),
        device_uuid=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        state="active",
        idle_seconds=4,
        last_input_at=(
            now
            - timedelta(
                seconds=4
            )
        ),
        observed_at=now,
        received_at=now,
    )

    assert response.state == "active"
    assert response.idle_seconds == 4


def test_activity_status_supports_no_previous_event() -> None:
    response = ActivityStatusResponse(
        device_uuid=uuid.uuid4(),
        employee_id=None,
        state="idle",
        idle_seconds=0,
        last_input_at=None,
        observed_at=None,
        received_at=None,
    )

    assert response.observed_at is None
    assert response.received_at is None