from __future__ import annotations

import uuid

import pytest
from sqlalchemy import (
    Column,
    MetaData,
    Table,
    Uuid,
    create_engine,
    event,
    insert,
    select,
)
from sqlalchemy.exc import IntegrityError

from app.modules.workspace_rbac.scope_models import (
    SAVED_RESOURCE_SCOPE_TYPES,
    WorkspaceMembershipScopeGrant,
)


@pytest.fixture
def storage():
    metadata = MetaData()

    users = Table(
        "users",
        metadata,
        Column(
            "id",
            Uuid(as_uuid=True),
            primary_key=True,
        ),
    )

    memberships = Table(
        "workspace_memberships",
        metadata,
        Column(
            "id",
            Uuid(as_uuid=True),
            primary_key=True,
        ),
    )

    grants = WorkspaceMembershipScopeGrant.__table__.to_metadata(
        metadata,
    )

    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    metadata.create_all(engine)

    membership_id = uuid.uuid4()
    grantor_id = uuid.uuid4()

    try:
        with engine.begin() as connection:
            connection.execute(
                insert(users),
                {"id": grantor_id},
            )
            connection.execute(
                insert(memberships),
                {"id": membership_id},
            )

            yield {
                "connection": connection,
                "users": users,
                "memberships": memberships,
                "grants": grants,
                "membership_id": membership_id,
                "grantor_id": grantor_id,
            }
    finally:
        engine.dispose()


def grant_values(storage, **overrides):
    values = {
        "membership_id": storage["membership_id"],
        "scope_type": "team",
        "resource_id": uuid.uuid4(),
        "granted_by_user_id": storage["grantor_id"],
    }

    values.update(overrides)
    return values


def test_supported_scope_types_are_explicit():
    assert SAVED_RESOURCE_SCOPE_TYPES == {
        "department",
        "team",
    }


@pytest.mark.parametrize("scope_type", ["department", "team"])
def test_supported_grant_is_stored(storage, scope_type):
    connection = storage["connection"]
    grants = storage["grants"]
    values = grant_values(storage, scope_type=scope_type)

    connection.execute(insert(grants), values)

    row = connection.execute(select(grants)).mappings().one()

    assert row["membership_id"] == values["membership_id"]
    assert row["scope_type"] == scope_type
    assert row["resource_id"] == values["resource_id"]
    assert row["granted_by_user_id"] == values["granted_by_user_id"]
    assert row["created_at"] is not None


@pytest.mark.parametrize(
    "scope_type",
    ["workspace", "self", "company", "shared", "TEAM", ""],
)
def test_unsupported_scope_type_is_rejected(storage, scope_type):
    with pytest.raises(IntegrityError):
        storage["connection"].execute(
            insert(storage["grants"]),
            grant_values(storage, scope_type=scope_type),
        )


def test_duplicate_grant_is_rejected(storage):
    connection = storage["connection"]
    statement = insert(storage["grants"])
    values = grant_values(storage)

    connection.execute(statement, values)

    with pytest.raises(IntegrityError):
        connection.execute(statement, values)


def test_same_resource_can_be_granted_to_different_members(storage):
    connection = storage["connection"]
    second_membership_id = uuid.uuid4()
    resource_id = uuid.uuid4()

    connection.execute(
        insert(storage["memberships"]),
        {"id": second_membership_id},
    )

    connection.execute(
        insert(storage["grants"]),
        [
            grant_values(storage, resource_id=resource_id),
            grant_values(
                storage,
                membership_id=second_membership_id,
                resource_id=resource_id,
            ),
        ],
    )

    rows = connection.execute(
        select(storage["grants"]),
    ).mappings().all()

    assert len(rows) == 2


def test_missing_membership_is_rejected(storage):
    with pytest.raises(IntegrityError):
        storage["connection"].execute(
            insert(storage["grants"]),
            grant_values(
                storage,
                membership_id=uuid.uuid4(),
            ),
        )


def test_missing_grantor_is_rejected(storage):
    with pytest.raises(IntegrityError):
        storage["connection"].execute(
            insert(storage["grants"]),
            grant_values(
                storage,
                granted_by_user_id=uuid.uuid4(),
            ),
        )


def test_null_resource_id_is_rejected(storage):
    with pytest.raises(IntegrityError):
        storage["connection"].execute(
            insert(storage["grants"]),
            grant_values(storage, resource_id=None),
        )


def test_deleting_membership_removes_its_grants(storage):
    connection = storage["connection"]
    grants = storage["grants"]
    memberships = storage["memberships"]

    connection.execute(
        insert(grants),
        grant_values(storage),
    )

    connection.execute(
        memberships.delete().where(
            memberships.c.id == storage["membership_id"],
        ),
    )

    assert connection.execute(select(grants)).all() == []


def test_grantor_with_existing_grants_cannot_be_deleted(storage):
    connection = storage["connection"]
    users = storage["users"]

    connection.execute(
        insert(storage["grants"]),
        grant_values(storage),
    )

    with pytest.raises(IntegrityError):
        connection.execute(
            users.delete().where(
                users.c.id == storage["grantor_id"],
            ),
        )