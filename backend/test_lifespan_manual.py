import asyncio

from app.core.logging import configure_logging
from app.lifespan import (
    shutdown_services,
    startup_services,
)


async def main():
    configure_logging()

    print("1. Starting WorkforceOS core services...")

    await startup_services()

    print("2. All core services are ready.")

    print("3. Shutting services down...")

    await shutdown_services()

    print("4. Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())