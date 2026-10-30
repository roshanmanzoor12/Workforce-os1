from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.modules.realtime_bridge.redis_transport import (
    get_realtime_transport,
)

from .chat_redis import (
    get_chat_redis,
    ping_chat_redis,
)
from .realtime_subscriber import ChatRealtimeSubscriber


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChatRealtimeRuntime:
    subscriber: ChatRealtimeSubscriber
    task: asyncio.Task[None]


_runtime: ChatRealtimeRuntime | None = None
_runtime_lock = asyncio.Lock()


def _report_task_completion(
    task: asyncio.Task[None],
) -> None:
    if task.cancelled():
        return

    error = task.exception()

    if error is not None:
        logger.error(
            "Chat realtime worker failed",
            exc_info=(
                type(error),
                error,
                error.__traceback__,
            ),
        )


async def start_chat_realtime_runtime(
    *,
    session_factory: async_sessionmaker[AsyncSession],
) -> ChatRealtimeRuntime:
    global _runtime

    async with _runtime_lock:
        if (
            _runtime is not None
            and not _runtime.task.done()
        ):
            return _runtime

        if not await ping_chat_redis():
            raise RuntimeError(
                "Chat realtime Redis health check failed."
            )

        subscriber = ChatRealtimeSubscriber(
            redis_client=get_chat_redis(),
            session_factory=session_factory,
            bridge_channel=get_realtime_transport().channel,
        )

        task = asyncio.create_task(
            subscriber.run(),
            name="workforceos-chat-realtime",
        )

        task.add_done_callback(
            _report_task_completion
        )

        runtime = ChatRealtimeRuntime(
            subscriber=subscriber,
            task=task,
        )

        _runtime = runtime

        # Give the worker an opportunity to start and detect an
        # immediate failure. This is not a subscription-ready
        # acknowledgement.
        await asyncio.sleep(0)

        if task.done():
            _runtime = None

            await task

            raise RuntimeError(
                "Chat realtime worker stopped during startup."
            )

        return runtime


async def stop_chat_realtime_runtime() -> None:
    global _runtime

    async with _runtime_lock:
        runtime = _runtime
        _runtime = None

        if runtime is None:
            return

        try:
            await runtime.subscriber.stop()

            await asyncio.wait_for(
                asyncio.shield(runtime.task),
                timeout=15.0,
            )

        except asyncio.TimeoutError:
            runtime.task.cancel()

            try:
                await runtime.task

            except asyncio.CancelledError:
                pass

            except Exception:
                logger.exception(
                    "Chat realtime worker failed during cancellation"
                )

        except asyncio.CancelledError:
            # Propagate cancellation of the shutdown caller.
            # An already-cancelled worker alone should not
            # prevent the remaining application cleanup.
            if asyncio.current_task().cancelling():
                runtime.task.cancel()

                try:
                    await runtime.task

                except asyncio.CancelledError:
                    pass

                except Exception:
                    logger.exception(
                        "Chat realtime worker cancellation cleanup failed"
                    )

                raise

        except Exception:
            logger.exception(
                "Chat realtime worker failed during shutdown"
            )

            if not runtime.task.done():
                runtime.task.cancel()

                try:
                    await runtime.task

                except asyncio.CancelledError:
                    pass

                except Exception:
                    logger.exception(
                        "Chat realtime worker cleanup failed"
                    )


def get_chat_realtime_runtime() -> ChatRealtimeRuntime | None:
    return _runtime


__all__ = [
    "ChatRealtimeRuntime",
    "get_chat_realtime_runtime",
    "start_chat_realtime_runtime",
    "stop_chat_realtime_runtime",
]