from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
import re

from app.models.models import MemberStatus, PlanType, PaymentStatus, PaymentMethod


# ─── Auth ────────────────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ─── Member ──────────────────────────────────────────────────────────────────


class MemberCreate(BaseModel):
    name: str
    email: EmailStr
    cpf: str
    phone: Optional[str] = None
    password: str

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) != 11:
            raise ValueError("CPF inválido")
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres")
        return v


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[MemberStatus] = None


class MemberResponse(BaseModel):
    id: UUID
    name: str
    email: str
    cpf: str
    phone: Optional[str]
    status: MemberStatus
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminSetupRequest(BaseModel):
    name: str
    email: EmailStr
    cpf: str
    phone: Optional[str] = None
    password: str

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) != 11:
            raise ValueError("CPF inválido")
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres")
        return v


class PromoteRequest(BaseModel):
    is_admin: bool


# ─── Plan ────────────────────────────────────────────────────────────────────


class PlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    plan_type: PlanType
    price: float
    duration_days: int

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Preço deve ser maior que zero")
        return round(v, 2)


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None


class PlanResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    plan_type: PlanType
    price: float
    duration_days: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Subscription ────────────────────────────────────────────────────────────


class SubscriptionCreate(BaseModel):
    plan_id: UUID
    auto_renew: bool = False


class SubscriptionResponse(BaseModel):
    id: UUID
    member_id: UUID
    plan: PlanResponse
    start_date: datetime
    end_date: datetime
    is_active: bool
    auto_renew: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Payment ─────────────────────────────────────────────────────────────────


class PaymentCreate(BaseModel):
    subscription_id: UUID
    method: PaymentMethod


class PaymentResponse(BaseModel):
    id: UUID
    member_id: UUID
    subscription_id: Optional[UUID]
    amount: float
    status: PaymentStatus
    method: PaymentMethod
    provider: Optional[str]
    provider_transaction_id: Optional[str]
    provider_payment_url: Optional[str]
    description: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Webhook ─────────────────────────────────────────────────────────────────


class WebhookPayload(BaseModel):
    provider: str
    event: str
    transaction_id: str
    status: str
    amount: Optional[float] = None
    metadata: Optional[dict] = None


# ─── Generic ─────────────────────────────────────────────────────────────────


class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list
