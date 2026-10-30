from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .enums import (
    BillingProvider,
    SubscriptionStatus,
)
from .plans import PlanCode


def enum_values(
    enum_class,
) -> list[str]:
    return [
        member.value
        for member in enum_class
    ]


class BillingCustomer(Base):
    __tablename__ = "billing_customers"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_billing_customers_user_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    provider: Mapped[BillingProvider] = mapped_column(
        Enum(
            BillingProvider,
            name="billing_provider",
            native_enum=False,
            values_callable=enum_values,
        ),
        nullable=False,
        default=BillingProvider.NONE,
    )

    provider_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class BillingSubscription(Base):
    __tablename__ = "billing_subscriptions"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_billing_subscription_user",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    plan_code: Mapped[PlanCode] = mapped_column(
        Enum(
            PlanCode,
            name="billing_plan_code",
            native_enum=False,
            values_callable=enum_values,
        ),
        nullable=False,
        default=PlanCode.FREE,
    )

    provider: Mapped[BillingProvider] = mapped_column(
        Enum(
            BillingProvider,
            name="billing_subscription_provider",
            native_enum=False,
            values_callable=enum_values,
        ),
        nullable=False,
        default=BillingProvider.NONE,
    )

    provider_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(
            SubscriptionStatus,
            name="billing_subscription_status",
            native_enum=False,
            values_callable=enum_values,
        ),
        nullable=False,
        default=SubscriptionStatus.NONE,
    )

    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )