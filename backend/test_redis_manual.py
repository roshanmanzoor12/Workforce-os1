import asyncio

from app.core.redis import (
    check_redis,
    redis_delete,
    redis_get,
    redis_set,
)


async def main():
    print("1. Checking Redis health...")

    healthy = await check_redis()
    print("Redis health:", healthy)

    if not healthy:
        print("Redis is not reachable.")
        return

    print("\n2. Writing test value...")

    result = await redis_set(
        "test:foundation",
        "working",
        expire_seconds=60,
    )

    print("SET result:", result)

    print("\n3. Reading test value...")

    value = await redis_get(
        "test:foundation"
    )

    print("GET value:", value)

    print("\n4. Deleting test value...")

    deleted = await redis_delete(
        "test:foundation"
    )

    print("Deleted keys:", deleted)

    print("\n5. Test complete.")


if __name__ == "__main__":
    asyncio.run(main())