from __future__ import annotations


SCOPE_API_PREFIX = (
    "/workspaces/{workspace_id}"
    "/members/{membership_id}/scopes"
)

SCOPE_DELETE_SUFFIX = "/{scope_type}/{resource_id}"

SCOPE_API_CONTRACT = (
    ("GET", SCOPE_API_PREFIX),
    ("POST", SCOPE_API_PREFIX),
    ("DELETE", SCOPE_API_PREFIX + SCOPE_DELETE_SUFFIX),
)


__all__ = [
    "SCOPE_API_PREFIX",
    "SCOPE_DELETE_SUFFIX",
    "SCOPE_API_CONTRACT",
]