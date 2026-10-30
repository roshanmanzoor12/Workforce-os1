import asyncio

from app.modules.health.service import (
    get_health,
    get_readiness,
)


async def main():
    print("READINESS")
    readiness = await get_readiness()
    print(readiness.model_dump())

    print("\nHEALTH")
    health = await get_health()
    print(health.model_dump())


if __name__ == "__main__":
    asyncio.run(main())