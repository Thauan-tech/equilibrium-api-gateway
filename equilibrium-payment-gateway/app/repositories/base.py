"""
Interfaces abstratas dos repositórios.

Cada repositório define o contrato que toda implementação
(in-memory, PostgreSQL, etc.) deve respeitar. Para adicionar
uma nova implementação basta criar uma subclasse e injetar
via deps.py — nenhum endpoint precisa ser alterado.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID
from datetime import datetime

from app.models.models import PaymentStatus, PaymentMethod


class AbstractMemberRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        name: str,
        email: str,
        cpf: str,
        phone: Optional[str],
        password_hash: str,
        is_admin: bool = False,
    ) -> Any: ...

    @abstractmethod
    async def has_any_admin(self) -> bool: ...

    @abstractmethod
    async def get_by_id(self, member_id: UUID) -> Optional[Any]: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Any]: ...

    @abstractmethod
    async def find_by_email_or_cpf(self, email: str, cpf: str) -> Optional[Any]: ...

    @abstractmethod
    async def list(self, offset: int = 0, limit: int = 20) -> list[Any]: ...

    @abstractmethod
    async def update(self, member_id: UUID, **fields) -> Optional[Any]: ...

    @abstractmethod
    async def delete(self, member_id: UUID) -> bool: ...


class AbstractPlanRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        name: str,
        description: Optional[str],
        plan_type: Any,
        price: float,
        duration_days: int,
    ) -> Any: ...

    @abstractmethod
    async def get_by_id(self, plan_id: UUID) -> Optional[Any]: ...

    @abstractmethod
    async def list(self, active_only: bool = True) -> list[Any]: ...

    @abstractmethod
    async def update(self, plan_id: UUID, **fields) -> Optional[Any]: ...

    @abstractmethod
    async def deactivate(self, plan_id: UUID) -> Optional[Any]: ...


class AbstractSubscriptionRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        member_id: UUID,
        plan_id: UUID,
        start_date: datetime,
        end_date: datetime,
        auto_renew: bool,
    ) -> Any: ...

    @abstractmethod
    async def get_by_id(self, subscription_id: UUID) -> Optional[Any]: ...

    @abstractmethod
    async def get_active_by_member(self, member_id: UUID) -> Optional[Any]: ...

    @abstractmethod
    async def list_by_member(self, member_id: UUID) -> list[Any]: ...

    @abstractmethod
    async def list_all(self) -> list[Any]: ...

    @abstractmethod
    async def cancel(self, subscription_id: UUID) -> Optional[Any]: ...


class AbstractPaymentRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        member_id: UUID,
        subscription_id: Optional[UUID],
        amount: float,
        method: PaymentMethod,
        status: PaymentStatus,
        provider: Optional[str],
        provider_transaction_id: Optional[str],
        provider_payment_url: Optional[str],
        description: Optional[str],
        paid_at: Optional[datetime],
    ) -> Any: ...

    @abstractmethod
    async def get_by_id(self, payment_id: UUID) -> Optional[Any]: ...

    @abstractmethod
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Any]: ...

    @abstractmethod
    async def list_by_member(self, member_id: UUID) -> list[Any]: ...

    @abstractmethod
    async def list_all(self) -> list[Any]: ...

    @abstractmethod
    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        paid_at: Optional[datetime] = None,
    ) -> Optional[Any]: ...
