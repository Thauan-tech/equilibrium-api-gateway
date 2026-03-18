from typing import Optional
from uuid import UUID

from app.repositories.base import AbstractPlanRepository
from app.repositories.memory.entities import PlanEntity


class InMemoryPlanRepository(AbstractPlanRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, PlanEntity] = {}

    async def create(self, *, name, description, plan_type, price, duration_days) -> PlanEntity:
        entity = PlanEntity(
            name=name,
            description=description,
            plan_type=plan_type,
            price=price,
            duration_days=duration_days,
        )
        self._store[entity.id] = entity
        return entity

    async def get_by_id(self, plan_id: UUID) -> Optional[PlanEntity]:
        return self._store.get(plan_id)

    async def list(self, active_only: bool = True) -> list[PlanEntity]:
        plans = self._store.values()
        if active_only:
            plans = [p for p in plans if p.is_active]
        return sorted(plans, key=lambda p: p.created_at)

    async def update(self, plan_id: UUID, **fields) -> Optional[PlanEntity]:
        entity = self._store.get(plan_id)
        if not entity:
            return None
        for key, value in fields.items():
            setattr(entity, key, value)
        return entity

    async def deactivate(self, plan_id: UUID) -> Optional[PlanEntity]:
        entity = self._store.get(plan_id)
        if not entity:
            return None
        entity.is_active = False
        return entity
