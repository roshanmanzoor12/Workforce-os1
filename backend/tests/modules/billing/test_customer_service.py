from __future__ import annotations

import uuid

import pytest

from app.modules.billing.customer_service import (
    BillingCustomerService,
)
from app.modules.billing.enums import (
    BillingProvider,
)


class FakeCustomer:
    def __init__(
        self,
    ) -> None:
        self.provider = (
            BillingProvider.NONE
        )

        self.provider_customer_id = None


class FakeRepository:
    def __init__(
        self,
    ) -> None:
        self.customer = FakeCustomer()

    async def ensure_customer(
        self,
        session,
        *,
        user_id,
        provider=BillingProvider.NONE,
        provider_customer_id=None,
    ):
        return self.customer


class FakeSession:
    def __init__(
        self,
    ) -> None:
        self.flushed = False

    async def flush(
        self,
    ) -> None:
        self.flushed = True


@pytest.mark.asyncio
async def test_provider_customer_is_linked():
    session = FakeSession()

    repository = FakeRepository()

    service = BillingCustomerService(
        session,
        repository=repository,
    )

    result = (
        await service.apply_provider_customer(
            user_id=uuid.uuid4(),
            provider=BillingProvider.STRIPE,
            provider_customer_id="cus_123",
        )
    )

    assert (
        result.provider
        == BillingProvider.STRIPE
    )

    assert (
        result.provider_customer_id
        == "cus_123"
    )

    assert session.flushed is True


@pytest.mark.asyncio
async def test_customer_id_is_trimmed():
    service = BillingCustomerService(
        FakeSession(),
        repository=FakeRepository(),
    )

    result = (
        await service.apply_provider_customer(
            user_id=uuid.uuid4(),
            provider=BillingProvider.STRIPE,
            provider_customer_id=(
                "   cus_abc   "
            ),
        )
    )

    assert (
        result.provider_customer_id
        == "cus_abc"
    )


@pytest.mark.asyncio
async def test_provider_none_rejected():
    service = BillingCustomerService(
        FakeSession(),
        repository=FakeRepository(),
    )

    with pytest.raises(
        ValueError,
        match="BillingProvider.NONE",
    ):
        await service.apply_provider_customer(
            user_id=uuid.uuid4(),
            provider=BillingProvider.NONE,
            provider_customer_id="invalid",
        )


@pytest.mark.asyncio
async def test_existing_different_customer_id_rejected():
    repository = FakeRepository()

    repository.customer.provider = (
        BillingProvider.STRIPE
    )

    repository.customer.provider_customer_id = (
        "cus_existing"
    )

    service = BillingCustomerService(
        FakeSession(),
        repository=repository,
    )

    with pytest.raises(
        ValueError,
        match="different provider customer ID",
    ):
        await service.apply_provider_customer(
            user_id=uuid.uuid4(),
            provider=BillingProvider.STRIPE,
            provider_customer_id="cus_other",
        )