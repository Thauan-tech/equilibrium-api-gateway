from typing import Optional
from uuid import UUID
from datetime import datetime

from app.repositories.base import AbstractSubscriptionRepository
from app.repositories.memory.entities import SubscriptionEntity
from app.repositories.base import AbstractPlanRepository


class InMemorySubscriptionRepository(AbstractSubscriptionRepository):
    """
    O repositório recebe o plan_repo para resolver o relacionamento
    plan → subscription no momento da criação, espelhando o comportamento
    do SQLAlchemy com eager/lazy loading.
    """

    def __init__(self, plan_repo: AbstractPlanRepository) -> None:
        self._store: dict[UUID, SubscriptionEntity] = {}
        self._plan_repo = plan_repo

    async def create(
        self, *, member_id, plan_id, start_date, end_date, auto_renew
    ) -> SubscriptionEntity:
        plan = await self._plan_repo.get_by_id(plan_id)
        entity = SubscriptionEntity(
            member_id=member_id,
            plan_id=plan_id,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            auto_renew=auto_renew,
        )
        self._store[entity.id] = entity
        return entity

    async def get_by_id(self, subscription_id: UUID) -> Optional[SubscriptionEntity]:
        return self._store.get(subscription_id)

    async def get_active_by_member(self, member_id: UUID) -> Optional[SubscriptionEntity]:
        return next(
            (
                s for s in self._store.values()
                if str(s.member_id) == str(member_id) and s.is_active
            ),
            None,
        )

    async def list_by_member(self, member_id: UUID) -> list[SubscriptionEntity]:
        return [
            s for s in self._store.values()
            if str(s.member_id) == str(member_id)
        ]

    async def list_all(self) -> list[SubscriptionEntity]:
        return list(self._store.values())

    async def cancel(self, subscription_id: UUID) -> Optional[SubscriptionEntity]:
        entity = self._store.get(subscription_id)
        if not entity:
            return None
        entity.is_active = False
        entity.auto_renew = False
        return entity
