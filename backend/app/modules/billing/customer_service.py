from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .enums import BillingProvider
from .models import BillingCustomer
from .repository import BillingRepository


class BillingCustomerService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        repository: BillingRepository | None = None,
    ) -> None:
        self.session = session

        self.repository = (
            repository
            or BillingRepository()
        )

    async def ensure_customer(
        self,
        *,
        user_id: uuid.UUID,
    ) -> BillingCustomer:
        return await self.repository.ensure_customer(
            self.session,
            user_id=user_id,
        )

    async def apply_provider_customer(
        self,
        *,
        user_id: uuid.UUID,
        provider: BillingProvider,
        provider_customer_id: str,
    ) -> BillingCustomer:
        if provider == BillingProvider.NONE:
            raise ValueError(
                "Provider customer cannot use "
                "BillingProvider.NONE."
            )

        normalized_id = (
            provider_customer_id.strip()
        )

        if not normalized_id:
            raise ValueError(
                "provider_customer_id is required."
            )

        if len(normalized_id) > 255:
            raise ValueError(
                "provider_customer_id is too long."
            )

        customer = (
            await self.repository
            .ensure_customer(
                self.session,
                user_id=user_id,
            )
        )

        if (
            customer.provider
            not in (
                BillingProvider.NONE,
                provider,
            )
        ):
            raise ValueError(
                "Billing customer is already linked "
                "to another provider."
            )

        if (
            customer.provider_customer_id
            is not None
            and customer.provider_customer_id
            != normalized_id
        ):
            raise ValueError(
                "Billing customer already has a "
                "different provider customer ID."
            )

        customer.provider = provider

        customer.provider_customer_id = (
            normalized_id
        )

        await self.session.flush()

        return customer


__all__ = [
    "BillingCustomerService",
]