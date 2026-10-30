from dataclasses import dataclass
@dataclass(frozen=True)
class TenantContext:
    workspace_id: str
    tenant_database_name: str
    membership_id: str
    role_id: str
async def resolve_tenant_context(*, user_id: str, workspace_id: str) -> TenantContext:
    raise NotImplementedError("Resolve from authenticated membership + tenant_registry only.")
