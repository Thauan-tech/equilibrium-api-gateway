from typing import Optional
from uuid import UUID
from datetime import datetime

from app.repositories.base import AbstractMemberRepository
from app.repositories.memory.entities import MemberEntity
from app.models.models import MemberStatus


class InMemoryMemberRepository(AbstractMemberRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, MemberEntity] = {}

    async def create(self, *, name, email, cpf, phone, password_hash) -> MemberEntity:
        entity = MemberEntity(
            name=name,
            email=email,
            cpf=cpf,
            phone=phone,
            password_hash=password_hash,
        )
        self._store[entity.id] = entity
        return entity

    async def get_by_id(self, member_id: UUID) -> Optional[MemberEntity]:
        return self._store.get(member_id)

    async def get_by_email(self, email: str) -> Optional[MemberEntity]:
        return next((m for m in self._store.values() if m.email == email), None)

    async def find_by_email_or_cpf(self, email: str, cpf: str) -> Optional[MemberEntity]:
        return next(
            (m for m in self._store.values() if m.email == email or m.cpf == cpf),
            None,
        )

    async def list(self, offset: int = 0, limit: int = 20) -> list[MemberEntity]:
        members = sorted(self._store.values(), key=lambda m: m.created_at)
        return members[offset : offset + limit]

    async def update(self, member_id: UUID, **fields) -> Optional[MemberEntity]:
        entity = self._store.get(member_id)
        if not entity:
            return None
        for key, value in fields.items():
            setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()
        return entity

    async def delete(self, member_id: UUID) -> bool:
        return self._store.pop(member_id, None) is not None
