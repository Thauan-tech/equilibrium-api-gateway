from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.models import Subscription, Plan, Member
from app.schemas.schemas import SubscriptionCreate, SubscriptionResponse, MessageResponse

router = APIRouter()


@router.post("/", response_model=SubscriptionResponse, status_code=201, summary="Assinar um plano")
async def create_subscription(
    payload: SubscriptionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch plan
    plan_result = await db.execute(select(Plan).where(Plan.id == payload.plan_id, Plan.is_active == True))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado ou inativo")

    # Check for existing active subscription
    existing = await db.execute(
        select(Subscription).where(
            Subscription.member_id == current_user["user_id"],
            Subscription.is_active == True,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Membro já possui uma assinatura ativa")

    start = datetime.utcnow()
    subscription = Subscription(
        member_id=current_user["user_id"],
        plan_id=plan.id,
        start_date=start,
        end_date=start + timedelta(days=plan.duration_days),
        auto_renew=payload.auto_renew,
    )
    db.add(subscription)
    await db.flush()
    await db.refresh(subscription)
    return subscription


@router.get("/me", response_model=list[SubscriptionResponse], summary="Minhas assinaturas")
async def get_my_subscriptions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(Subscription.member_id == current_user["user_id"])
    )
    return result.scalars().all()


@router.get("/", response_model=list[SubscriptionResponse], summary="Listar todas (admin)")
async def list_subscriptions(
    _: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Subscription))
    return result.scalars().all()


@router.patch("/{subscription_id}/cancel", response_model=MessageResponse, summary="Cancelar assinatura")
async def cancel_subscription(
    subscription_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.member_id == current_user["user_id"],
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    if not sub.is_active:
        raise HTTPException(status_code=400, detail="Assinatura já cancelada")

    sub.is_active = False
    sub.auto_renew = False
    return MessageResponse(message="Assinatura cancelada com sucesso")
