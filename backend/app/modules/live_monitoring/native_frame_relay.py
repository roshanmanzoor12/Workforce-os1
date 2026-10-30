"""Bounded in-process native-screen frame relay state.

No API route is exposed here. Endpoints MUST authenticate employee/device and owner,
check workspace isolation, confirm visible employee consent, then mint role tickets.
Never use ticket roles as a replacement for authenticated issuance.
"""
from __future__ import annotations

import asyncio
import secrets
import time
from dataclasses import dataclass, field

MAX_JPEG_BYTES = 900_000
MAX_SESSION_SECONDS = 900
MIN_JPEG_BYTES = 4


class RelayError(Exception):
    pass


@dataclass
class _Lease:
    workspace_id: str
    session_id: str
    employee_id: str
    device_id: str
    expiry: float
    approved: bool = False
    revoked: bool = False
    publisher_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    viewer_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    latest_frame: bytes | None = None
    sequence: int = 0
    changed: asyncio.Event = field(default_factory=asyncio.Event)


class NativeFrameRelay:
    """Single-worker, in-memory media buffer. No capture and no persistent storage.

    Not suitable for multi-worker deployment without shared state and pub/sub.
    """

    def __init__(self):
        self._leases: dict[str, _Lease] = {}
        self._lock = asyncio.Lock()

    async def issue(self, *, workspace_id: str, session_id: str,
                    employee_id: str, device_id: str, expires_in: int = 300) -> tuple[str, str]:
        if not all((workspace_id, session_id, employee_id, device_id)):
            raise RelayError("All ownership bindings are required")
        if not 1 <= expires_in <= MAX_SESSION_SECONDS:
            raise RelayError("Invalid lease duration")
        async with self._lock:
            existing = self._leases.get(session_id)
            if existing and not existing.revoked and existing.expiry > time.monotonic():
                raise RelayError("Active session already exists")
            lease = _Lease(workspace_id, session_id, employee_id, device_id,
                           time.monotonic() + expires_in)
            # Preserve the monotonic sequence across a media-ticket renewal.
            # The browser sends ?after=<last sequence>; resetting to zero makes
            # the browser discard every new frame until it catches up.
            if existing is not None:
                lease.sequence = existing.sequence
            self._leases[session_id] = lease
            return lease.publisher_token, lease.viewer_token

    def _valid(self, session_id: str, token: str, role: str, workspace_id: str) -> _Lease:
        lease = self._leases.get(session_id)
        if (lease is None or lease.revoked or time.monotonic() >= lease.expiry
                or lease.workspace_id != workspace_id):
            raise RelayError("Session unavailable")
        expected = lease.publisher_token if role == "publisher" else lease.viewer_token
        if not token or not secrets.compare_digest(token, expected):
            raise RelayError("Invalid session credential")
        return lease

    async def approve(self, *, session_id: str, workspace_id: str,
                      publisher_token: str) -> None:
        async with self._lock:
            lease = self._valid(session_id, publisher_token, "publisher", workspace_id)
            lease.approved = True

    async def publish(self, *, session_id: str, workspace_id: str,
                      publisher_token: str, jpeg: bytes) -> int:
        if (not MIN_JPEG_BYTES <= len(jpeg) <= MAX_JPEG_BYTES or
                not jpeg.startswith(b"\xff\xd8") or not jpeg.endswith(b"\xff\xd9")):
            raise RelayError("Invalid JPEG frame")
        async with self._lock:
            lease = self._valid(session_id, publisher_token, "publisher", workspace_id)
            if not lease.approved:
                raise RelayError("Employee consent required")
            lease.latest_frame = bytes(jpeg)
            lease.sequence += 1
            previous = lease.changed
            lease.changed = asyncio.Event()
            previous.set()
            return lease.sequence

    async def snapshot(self, *, session_id: str, workspace_id: str,
                       viewer_token: str, after: int = 0) -> tuple[int, bytes | None]:
        async with self._lock:
            lease = self._valid(session_id, viewer_token, "viewer", workspace_id)
            if not lease.approved or lease.sequence <= after:
                return lease.sequence, None
            return lease.sequence, lease.latest_frame

    async def revoke(self, *, session_id: str, workspace_id: str) -> None:
        async with self._lock:
            lease = self._leases.get(session_id)
            if lease and lease.workspace_id == workspace_id:
                lease.revoked = True
                lease.latest_frame = None
                lease.changed.set()
                lease.publisher_token = ""
                lease.viewer_token = ""

    async def purge(self) -> None:
        async with self._lock:
            for session_id, lease in list(self._leases.items()):
                if lease.revoked or lease.expiry <= time.monotonic():
                    lease.latest_frame = None
                    lease.changed.set()
                    del self._leases[session_id]
