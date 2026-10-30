from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.models import (
    Employee,
)
from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.knowledge.enums import (
    KnowledgeStatus,
)
from app.modules.knowledge.models import (
    KnowledgeEntry,
)
from app.modules.knowledge.repository import (
    KnowledgeRepository,
)
from app.modules.knowledge.schemas import (
    KnowledgeCreateRequest,
    KnowledgeListResponse,
    KnowledgePublic,
    KnowledgeUpdateRequest,
)


class KnowledgeNotFoundError(
    LookupError
):
    pass


class KnowledgeValidationError(
    ValueError
):
    pass


class KnowledgeActorEmployeeNotFoundError(
    LookupError
):
    pass


class KnowledgeService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            KnowledgeRepository(
                session
            )
        )

        self.employees = (
            EmployeeRepository(
                session
            )
        )

    async def resolve_actor_employee(
        self,
        actor_user_id: uuid.UUID,
    ) -> Employee:
        result = await self.session.execute(
            select(
                Employee
            ).where(
                Employee.user_id
                == actor_user_id,
                Employee.is_active.is_(
                    True
                ),
            )
        )

        employee = (
            result.scalar_one_or_none()
        )

        if employee is None:
            raise (
                KnowledgeActorEmployeeNotFoundError(
                    "Active employee profile "
                    "for current user was not found."
                )
            )

        return employee

    async def create_entry(
        self,
        request: KnowledgeCreateRequest,
    ) -> KnowledgePublic:
        employee = await (
            self.employees
            .get_employee_by_id(
                request.owner_employee_id
            )
        )

        if employee is None:
            raise KnowledgeValidationError(
                "Employee not found."
            )

        if not employee.is_active:
            raise KnowledgeValidationError(
                "Employee is not active."
            )

        entry = KnowledgeEntry(
            owner_employee_id=(
                request.owner_employee_id
            ),
            title=request.title,
            content=request.content,
            category=request.category.value,
            status=(
                KnowledgeStatus.DRAFT.value
            ),
            visibility=(
                request.visibility.value
            ),
        )

        try:
            await self.repository.create(
                entry
            )

            await self.session.commit()

            await self.session.refresh(
                entry
            )
        except Exception:
            await self.session.rollback()
            raise

        return self._to_public(
            entry
        )

    async def create_my_entry(
        self,
        actor_user_id: uuid.UUID,
        request: KnowledgeCreateRequest,
    ) -> KnowledgePublic:
        employee = await (
            self.resolve_actor_employee(
                actor_user_id
            )
        )

        trusted = KnowledgeCreateRequest(
            owner_employee_id=employee.id,
            title=request.title,
            content=request.content,
            category=request.category,
            visibility=request.visibility,
        )

        return await self.create_entry(
            trusted
        )

    async def get_entry(
        self,
        entry_id: uuid.UUID,
    ) -> KnowledgePublic:
        entry = await (
            self._require_entry(
                entry_id
            )
        )

        return self._to_public(
            entry
        )

    async def get_my_entry(
        self,
        actor_user_id: uuid.UUID,
        entry_id: uuid.UUID,
    ) -> KnowledgePublic:
        employee = await (
            self.resolve_actor_employee(
                actor_user_id
            )
        )

        entry = await (
            self._require_entry(
                entry_id
            )
        )

        if (
            entry.owner_employee_id
            != employee.id
        ):
            raise KnowledgeNotFoundError(
                "Knowledge entry not found."
            )

        return self._to_public(
            entry
        )

    async def list_my_entries(
        self,
        actor_user_id: uuid.UUID,
        include_archived: bool = False,
    ) -> KnowledgeListResponse:
        employee = await (
            self.resolve_actor_employee(
                actor_user_id
            )
        )

        entries = await (
            self.repository
            .list_for_employee(
                employee.id,
                include_archived,
            )
        )

        return self._to_list(
            entries
        )

    async def list_workspace_entries(
        self,
        actor_user_id: uuid.UUID,
    ) -> KnowledgeListResponse:
        employee = await (
            self.resolve_actor_employee(
                actor_user_id
            )
        )

        entries = await (
            self.repository
            .list_workspace_visible(
                employee.id
            )
        )

        return self._to_list(
            entries
        )

    async def update_entry(
        self,
        entry_id: uuid.UUID,
        request: KnowledgeUpdateRequest,
    ) -> KnowledgePublic:
        entry = await (
            self._require_entry(
                entry_id
            )
        )

        values = request.model_dump(
            exclude_unset=True
        )

        for field in (
            "category",
            "status",
            "visibility",
        ):
            value = values.get(
                field
            )

            if value is not None:
                values[field] = (
                    value.value
                )

        for key, value in values.items():
            setattr(
                entry,
                key,
                value,
            )

        try:
            await self.session.commit()

            await self.session.refresh(
                entry
            )
        except Exception:
            await self.session.rollback()
            raise

        return self._to_public(
            entry
        )

    async def update_my_entry(
        self,
        actor_user_id: uuid.UUID,
        entry_id: uuid.UUID,
        request: KnowledgeUpdateRequest,
    ) -> KnowledgePublic:
        await self.get_my_entry(
            actor_user_id,
            entry_id,
        )

        return await self.update_entry(
            entry_id,
            request,
        )

    async def delete_entry(
        self,
        entry_id: uuid.UUID,
    ) -> None:
        entry = await (
            self._require_entry(
                entry_id
            )
        )

        try:
            await self.repository.delete(
                entry
            )

            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def delete_my_entry(
        self,
        actor_user_id: uuid.UUID,
        entry_id: uuid.UUID,
    ) -> None:
        await self.get_my_entry(
            actor_user_id,
            entry_id,
        )

        await self.delete_entry(
            entry_id
        )

    async def _require_entry(
        self,
        entry_id: uuid.UUID,
    ) -> KnowledgeEntry:
        entry = await (
            self.repository
            .get_by_id(
                entry_id
            )
        )

        if entry is None:
            raise KnowledgeNotFoundError(
                "Knowledge entry not found."
            )

        return entry

    @staticmethod
    def _to_public(
        entry: KnowledgeEntry,
    ) -> KnowledgePublic:
        return KnowledgePublic.model_validate(
            entry
        )

    @classmethod
    def _to_list(
        cls,
        entries: list[KnowledgeEntry],
    ) -> KnowledgeListResponse:
        items = [
            cls._to_public(
                entry
            )
            for entry in entries
        ]

        return KnowledgeListResponse(
            items=items,
            total=len(items),
        )


__all__ = [
    "KnowledgeService",
    "KnowledgeNotFoundError",
    "KnowledgeValidationError",
    "KnowledgeActorEmployeeNotFoundError",
]