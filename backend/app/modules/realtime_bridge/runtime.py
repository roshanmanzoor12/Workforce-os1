from __future__ import annotations

from app.modules.realtime_bridge.redis_transport import (
    get_realtime_transport,
)


class RealtimeBridgeRuntime:
    def __init__(
        self,
    ) -> None:
        self.started = False

    async def start(
        self,
    ) -> None:
        if self.started:
            return

        transport = (
            get_realtime_transport()
        )

        await transport.start()

        self.started = True

    async def stop(
        self,
    ) -> None:
        if not self.started:
            return

        transport = (
            get_realtime_transport()
        )

        await transport.stop()

        self.started = False


runtime = RealtimeBridgeRuntime()