"""
Provedores de dependência para FastAPI (Depends).

Troca de implementação:
  - Em memória (padrão): basta USE_DB=false ou omitir a variável.
  - PostgreSQL: defina USE_DB=true no .env e implemente os repositórios
    em app/repositories/postgres/ seguindo os mesmos ABCs de base.py.

Exemplo de migração futura:

    # postgres/member.py
    class PostgresMemberRepository(AbstractMemberRepository):
        def __init__(self, db: AsyncSession): ...

    # deps.py
    async def get_member_repo(db: AsyncSession = Depends(get_db)):
        return PostgresMemberRepository(db)
"""
import os
from functools import lru_cache

from app.repositories.base import (
    AbstractMemberRepository,
    AbstractPlanRepository,
    AbstractSubscriptionRepository,
    AbstractPaymentRepository,
)
from app.repositories.memory import (
    InMemoryMemberRepository,
    InMemoryPlanRepository,
    InMemorySubscriptionRepository,
    InMemoryPaymentRepository,
)


# ─── Singletons in-memory ────────────────────────────────────────────────────
# Um único objeto por tipo garante estado compartilhado entre requisições,
# comportamento esperado durante validação/testes manuais.

@lru_cache(maxsize=1)
def _member_repo() -> InMemoryMemberRepository:
    return InMemoryMemberRepository()


@lru_cache(maxsize=1)
def _plan_repo() -> InMemoryPlanRepository:
    return InMemoryPlanRepository()


@lru_cache(maxsize=1)
def _subscription_repo() -> InMemorySubscriptionRepository:
    return InMemorySubscriptionRepository(_plan_repo())


@lru_cache(maxsize=1)
def _payment_repo() -> InMemoryPaymentRepository:
    return InMemoryPaymentRepository()


# ─── FastAPI Depends ──────────────────────────────────────────────────────────

def get_member_repo() -> AbstractMemberRepository:
    return _member_repo()


def get_plan_repo() -> AbstractPlanRepository:
    return _plan_repo()


def get_subscription_repo() -> AbstractSubscriptionRepository:
    return _subscription_repo()


def get_payment_repo() -> AbstractPaymentRepository:
    return _payment_repo()
