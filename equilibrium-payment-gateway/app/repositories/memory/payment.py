from typing import Optional
from uuid import UUID
from datetime import datetime

from app.repositories.base import AbstractPaymentRepository
from app.repositories.memory.entities import PaymentEntity
from app.models.models import PaymentStatus


class InMemoryPaymentRepository(AbstractPaymentRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, PaymentEntity] = {}

    async def create(
        self,
        *,
        member_id,
        subscription_id,
        amount,
        method,
        status,
        provider,
        provider_transaction_id,
        provider_payment_url,
        description,
        paid_at,
    ) -> PaymentEntity:
        entity = PaymentEntity(
            member_id=member_id,
            subscription_id=subscription_id,
            amount=amount,
            method=method,
            status=status,
            provider=provider,
            provider_transaction_id=provider_transaction_id,
            provider_payment_url=provider_payment_url,
            description=description,
            paid_at=paid_at,
        )
        self._store[entity.id] = entity
        return entity

    async def get_by_id(self, payment_id: UUID) -> Optional[PaymentEntity]:
        return self._store.get(payment_id)

    async def get_by_transaction_id(
        self, transaction_id: str
    ) -> Optional[PaymentEntity]:
        return next(
            (
                p
                for p in self._store.values()
                if p.provider_transaction_id == transaction_id
            ),
            None,
        )

    async def list_by_member(self, member_id: UUID) -> list[PaymentEntity]:
        return sorted(
            [p for p in self._store.values() if str(p.member_id) == str(member_id)],
            key=lambda p: p.created_at,
            reverse=True,
        )

    async def list_all(self) -> list[PaymentEntity]:
        return sorted(self._store.values(), key=lambda p: p.created_at, reverse=True)

    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        paid_at: Optional[datetime] = None,
    ) -> Optional[PaymentEntity]:
        entity = self._store.get(payment_id)
        if not entity:
            return None
        entity.status = status
        entity.updated_at = datetime.utcnow()
        if paid_at:
            entity.paid_at = paid_at
        return entity
