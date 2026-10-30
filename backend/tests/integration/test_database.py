import pytest
from app.core.database import check_control_database
@pytest.mark.asyncio
async def test_database(): assert await check_control_database() is True
