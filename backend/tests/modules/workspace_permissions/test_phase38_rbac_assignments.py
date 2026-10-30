import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.core.exceptions import ResourceNotFound, ValidationError
from app.modules.workspace_permissions.effective import MembershipAccess
from app.modules.workspace_rbac import service as service_module
from app.modules.workspace_rbac.assignment_repository import (
    MembershipRoleAssignmentRepository,
)
from app.modules.workspace_rbac.schemas import (
    WorkspaceMemberRoleUpdateRequest,
    WorkspaceRoleCreateRequest,
    WorkspaceRoleListResponse,
    WorkspaceRoleUpdateRequest,
)
from app.modules.workspace_rbac.service import WorkspaceRBACService


class RoleAssignmentServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.workspace_id = uuid.uuid4()
        self.user = SimpleNamespace(id=uuid.uuid4())
        self.actor = self.member("member", user_id=self.user.id)
        self.target = self.member("member")

        self.session = SimpleNamespace(
            commit=AsyncMock(),
            rollback=AsyncMock(),
            scalar=AsyncMock(return_value=None),
        )
        self.service = WorkspaceRBACService(self.session)

        self.service.repository = SimpleNamespace(
            get_membership=AsyncMock(return_value=self.target),
            get_moderation=AsyncMock(return_value=None),
            get_custom_role_by_key=AsyncMock(return_value=None),
            get_custom_role=AsyncMock(return_value=None),
            get_role_permissions=AsyncMock(
                return_value=frozenset({"employees.read"})
            ),
            create_custom_role=AsyncMock(),
            set_role_permissions=AsyncMock(),
            delete_custom_role=AsyncMock(),
            list_members=AsyncMock(return_value=[]),
        )

        self.service.assignment_repository = SimpleNamespace(
            normalize_role_key=(
                MembershipRoleAssignmentRepository.normalize_role_key
            ),
            add=AsyncMock(),
            remove=AsyncMock(return_value=True),
            list_for=AsyncMock(return_value=[]),
        )

        self.service._workspace = AsyncMock()
        self.service._actor_membership = AsyncMock(
            return_value=self.actor
        )

        self.actor_permissions = frozenset(
            {
                "roles.assign",
                "roles.read",
                "roles.manage",
                "members.read",
                "employees.read",
            }
        )

        async def access(member):
            if member.id == self.actor.id:
                return MembershipAccess(
                    ("member", "delegated_admin"),
                    self.actor_permissions,
                )

            return MembershipAccess(
                ("member", "reader"),
                frozenset({"employees.read"}),
            )

        self.service._access = AsyncMock(side_effect=access)

    def member(self, role_key, **overrides):
        values = dict(
            id=uuid.uuid4(),
            workspace_id=self.workspace_id,
            user_id=uuid.uuid4(),
            role_key=role_key,
            status="active",
            user=SimpleNamespace(
                email="member@example.com",
                username="member",
            ),
        )
        values.update(overrides)
        return SimpleNamespace(**values)

    def role(self, **overrides):
        values = dict(
            id=uuid.uuid4(),
            workspace_id=self.workspace_id,
            role_key="reader",
            is_active=True,
            display_name="Reader",
            description=None,
        )
        values.update(overrides)
        return SimpleNamespace(**values)

    async def grant(self, key="reader"):
        return await self.service.grant_member_role(
            workspace_id=self.workspace_id,
            membership_id=self.target.id,
            role_key=key,
            user=self.user,
        )

    async def test_require_uses_combined_permissions(self):
        result = await self.service._require(
            workspace_id=self.workspace_id,
            user=self.user,
            permission="roles.assign",
        )

        self.assertIs(result, self.actor)
        self.service._workspace.assert_awaited_once_with(
            self.workspace_id,
            lock=True,
        )

    async def test_missing_effective_permission_denies_mutation(self):
        self.actor_permissions = frozenset({"employees.read"})

        with self.assertRaises(HTTPException) as error:
            await self.grant()

        self.assertEqual(error.exception.status_code, 403)
        self.service.assignment_repository.add.assert_not_awaited()
        self.session.commit.assert_not_awaited()
        self.session.rollback.assert_awaited_once()

    async def test_grant_within_actor_permissions_commits(self):
        self.service.repository.get_custom_role_by_key.return_value = (
            self.role()
        )

        response = await self.grant()

        self.service.assignment_repository.add.assert_awaited_once_with(
            workspace_id=self.workspace_id,
            membership_id=self.target.id,
            role_key="reader",
            granted_by_user_id=self.user.id,
        )
        self.assertEqual(response.membership_id, self.target.id)
        self.session.commit.assert_awaited_once()

    async def test_grant_above_actor_permissions_is_denied(self):
        self.service.repository.get_custom_role_by_key.return_value = (
            self.role()
        )
        self.service.repository.get_role_permissions.return_value = (
            frozenset({"payroll.manage"})
        )

        with self.assertRaises(HTTPException) as error:
            await self.grant()

        self.assertEqual(error.exception.status_code, 403)
        self.service.assignment_repository.add.assert_not_awaited()
        self.session.commit.assert_not_awaited()

    async def test_additional_owner_role_is_denied(self):
        with self.assertRaises(ValidationError):
            await self.grant("owner")

        self.service.assignment_repository.add.assert_not_awaited()

    async def test_owner_target_is_protected(self):
        self.target.role_key = "owner"

        with self.assertRaises(ValidationError):
            await self.grant()

        self.service.assignment_repository.add.assert_not_awaited()

    async def test_inactive_target_is_denied(self):
        self.target.status = "removed"

        with self.assertRaises(ValidationError):
            await self.grant()

        self.service.assignment_repository.add.assert_not_awaited()

    async def test_banned_target_is_denied(self):
        self.service.repository.get_moderation.return_value = (
            SimpleNamespace(is_banned=True)
        )

        with self.assertRaises(ValidationError):
            await self.grant()

        self.service.assignment_repository.add.assert_not_awaited()

    async def test_foreign_target_is_not_found(self):
        self.target.workspace_id = uuid.uuid4()

        with self.assertRaises(ResourceNotFound):
            await self.grant()

        self.service.assignment_repository.add.assert_not_awaited()

    async def test_inactive_custom_role_is_denied(self):
        self.service.repository.get_custom_role_by_key.return_value = (
            self.role(is_active=False)
        )

        with self.assertRaises(ResourceNotFound):
            await self.grant()

        self.service.assignment_repository.add.assert_not_awaited()

    async def test_failed_storage_rolls_back_without_commit(self):
        self.service.repository.get_custom_role_by_key.return_value = (
            self.role()
        )
        self.service.assignment_repository.add.side_effect = RuntimeError(
            "storage unavailable"
        )

        with self.assertRaises(RuntimeError):
            await self.grant()

        self.session.commit.assert_not_awaited()
        self.session.rollback.assert_awaited_once()

    async def test_revoke_is_idempotent(self):
        self.service.repository.get_custom_role_by_key.return_value = (
            self.role()
        )
        self.service.assignment_repository.remove.return_value = False

        response = await self.service.revoke_member_role(
            workspace_id=self.workspace_id,
            membership_id=self.target.id,
            role_key="reader",
            user=self.user,
        )

        self.assertEqual(response.membership_id, self.target.id)
        self.session.commit.assert_awaited_once()

    async def test_revoke_cannot_change_primary_role(self):
        with self.assertRaises(ValidationError):
            await self.service.revoke_member_role(
                workspace_id=self.workspace_id,
                membership_id=self.target.id,
                role_key="member",
                user=self.user,
            )

        self.service.assignment_repository.remove.assert_not_awaited()

    async def test_member_cannot_read_another_members_roles_without_permission(
        self,
    ):
        self.actor_permissions = frozenset()

        with self.assertRaises(HTTPException) as error:
            await self.service.get_member_roles(
                workspace_id=self.workspace_id,
                membership_id=self.target.id,
                user=self.user,
            )

        self.assertEqual(error.exception.status_code, 403)
        self.service.repository.get_membership.assert_not_awaited()

    async def test_member_can_read_own_roles(self):
        self.actor_permissions = frozenset()
        self.service.repository.get_membership.return_value = self.actor

        response = await self.service.get_member_roles(
            workspace_id=self.workspace_id,
            membership_id=self.actor.id,
            user=self.user,
        )

        self.assertEqual(response.membership_id, self.actor.id)
        self.session.commit.assert_not_awaited()

    async def test_bootstrap_reports_combined_access(self):
        self.service.list_roles = AsyncMock(
            return_value=WorkspaceRoleListResponse(roles=[])
        )

        response = await self.service.bootstrap(
            workspace_id=self.workspace_id,
            user=self.user,
        )

        self.assertEqual(response.role_key, "member")
        self.assertEqual(
            response.role_keys,
            ["member", "delegated_admin"],
        )
        self.assertEqual(
            frozenset(response.permissions),
            self.actor_permissions,
        )

    async def test_custom_role_creation_cannot_escalate_actor(self):
        payload = WorkspaceRoleCreateRequest(
            role_key="powerful",
            display_name="Powerful",
            permissions=["payroll.manage"],
        )

        with self.assertRaises(HTTPException):
            await self.service.create_role(
                payload,
                workspace_id=self.workspace_id,
                user=self.user,
            )

        self.service.repository.create_custom_role.assert_not_awaited()
        self.session.commit.assert_not_awaited()

    async def test_role_reactivation_cannot_escalate_actor(self):
        role = self.role(is_active=False)
        self.service.repository.get_custom_role.return_value = role
        self.service.repository.get_role_permissions.return_value = (
            frozenset({"payroll.manage"})
        )

        with self.assertRaises(HTTPException):
            await self.service.update_role(
                WorkspaceRoleUpdateRequest(is_active=True),
                workspace_id=self.workspace_id,
                role_id=role.id,
                user=self.user,
            )

        self.assertFalse(role.is_active)
        self.session.commit.assert_not_awaited()

    async def test_assigned_custom_role_cannot_be_deleted(self):
        role = self.role()
        self.service.repository.get_custom_role.return_value = role
        self.session.scalar.return_value = self.target.id

        with self.assertRaises(ValidationError):
            await self.service.delete_role(
                workspace_id=self.workspace_id,
                role_id=role.id,
                user=self.user,
            )

        self.service.repository.delete_custom_role.assert_not_awaited()
        self.session.commit.assert_not_awaited()

    async def test_owner_demotion_is_blocked(self):
        self.target.role_key = "owner"
        self.service.repository.get_custom_role_by_key.return_value = (
            self.role()
        )

        with self.assertRaises(ValidationError):
            await self.service.update_member_role(
                WorkspaceMemberRoleUpdateRequest(role_key="reader"),
                workspace_id=self.workspace_id,
                membership_id=self.target.id,
                user=self.user,
            )

        self.assertEqual(self.target.role_key, "owner")
        self.session.commit.assert_not_awaited()

    async def test_primary_role_change_cannot_escalate_actor(self):
        self.service.repository.get_custom_role_by_key.return_value = (
            self.role()
        )
        self.service.repository.get_role_permissions.return_value = (
            frozenset({"payroll.manage"})
        )

        with self.assertRaises(HTTPException):
            await self.service.update_member_role(
                WorkspaceMemberRoleUpdateRequest(role_key="reader"),
                workspace_id=self.workspace_id,
                membership_id=self.target.id,
                user=self.user,
            )

        self.assertEqual(self.target.role_key, "member")
        self.session.commit.assert_not_awaited()

    async def test_access_uses_shared_tenant_permission_resolver(self):
        expected = MembershipAccess(
            ("member",),
            frozenset({"employees.read"}),
        )

        with patch.object(
            service_module,
            "resolve_membership_access",
            AsyncMock(return_value=expected),
        ) as resolver:
            result = await WorkspaceRBACService._access(
                self.service,
                self.actor,
            )

        self.assertIs(result, expected)
        resolver.assert_awaited_once_with(
            self.session,
            workspace_id=self.workspace_id,
            membership=self.actor,
        )

    async def test_workspace_inactive_or_wrong_scope_is_rejected(self):
        cases = [
            dict(
                id=self.workspace_id,
                is_active=False,
                status="ready",
            ),
            dict(
                id=self.workspace_id,
                is_active=True,
                status="provisioning",
            ),
            dict(
                id=uuid.uuid4(),
                is_active=True,
                status="ready",
            ),
        ]

        for values in cases:
            self.session.scalar.return_value = SimpleNamespace(**values)

            with self.assertRaises(ResourceNotFound):
                await WorkspaceRBACService._workspace(
                    self.service,
                    self.workspace_id,
                    lock=True,
                )

    async def test_primary_role_change_removes_duplicate_additional_role(
        self,
    ):
        self.service.repository.get_custom_role_by_key.return_value = (
            self.role()
        )

        response = await self.service.update_member_role(
            WorkspaceMemberRoleUpdateRequest(role_key="reader"),
            workspace_id=self.workspace_id,
            membership_id=self.target.id,
            user=self.user,
        )

        self.assertEqual(response.role_key, "reader")
        self.service.assignment_repository.remove.assert_awaited_once_with(
            workspace_id=self.workspace_id,
            membership_id=self.target.id,
            role_key="reader",
        )
        self.session.commit.assert_awaited_once()

    async def test_response_failure_rolls_back_grant(self):
        self.service.repository.get_custom_role_by_key.return_value = (
            self.role()
        )
        self.service._member_roles_response = AsyncMock(
            side_effect=RuntimeError("response failure")
        )

        with self.assertRaises(RuntimeError):
            await self.grant()

        self.service.assignment_repository.add.assert_awaited_once()
        self.session.commit.assert_not_awaited()
        self.session.rollback.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()