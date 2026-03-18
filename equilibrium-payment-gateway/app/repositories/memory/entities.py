"""
Entidades em memória que espelham os campos dos modelos SQLAlchemy.

Os nomes dos campos são idênticos aos das colunas ORM para que os
Pydantic schemas (model_config = {"from_attributes": True}) funcionem
sem qualquer alteração — basta passar a entidade no lugar do objeto ORM.
"""
from dataclasses import dataclass, field
from typing import Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from app.models.models import MemberStatus, PlanType, PaymentStatus, PaymentMethod


@dataclass
class MemberEntity:
    name: str
    email: str
    cpf: str
    password_hash: str
    id: UUID = field(default_factory=uuid4)
    phone: Optional[str] = None
    status: MemberStatus = MemberStatus.ACTIVE
    is_admin: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PlanEntity:
    name: str
    plan_type: PlanType
    price: float
    duration_days: int
    id: UUID = field(default_factory=uuid4)
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SubscriptionEntity:
    member_id: UUID
    plan_id: UUID
    plan: Any          # PlanEntity — resolvido no momento da criação
    start_date: datetime
    end_date: datetime
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    auto_renew: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PaymentEntity:
    member_id: UUID
    amount: float
    method: PaymentMethod
    status: PaymentStatus
    id: UUID = field(default_factory=uuid4)
    subscription_id: Optional[UUID] = None
    provider: Optional[str] = None
    provider_transaction_id: Optional[str] = None
    provider_payment_url: Optional[str] = None
    description: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
