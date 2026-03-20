from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from datetime import datetime, timedelta

from app.repositories import (
    AbstractPlanRepository,
    AbstractSubscriptionRepository,
    get_plan_repo,
    get_subscription_repo,
)
from app.core.security import get_current_user, require_admin
from app.schemas.schemas import (
    SubscriptionCreate,
    SubscriptionResponse,
    MessageResponse,
)

router = APIRouter()


@router.post(
    "/",
    response_model=SubscriptionResponse,
    status_code=201,
    summary="Assinar um plano",
)
async def create_subscription(
    payload: SubscriptionCreate,
    current_user: dict = Depends(get_current_user),
    plan_repo: AbstractPlanRepository = Depends(get_plan_repo),
    sub_repo: AbstractSubscriptionRepository = Depends(get_subscription_repo),
):
    plan = await plan_repo.get_by_id(payload.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plano não encontrado ou inativo")

    member_id = UUID(current_user["user_id"])
    if await sub_repo.get_active_by_member(member_id):
        raise HTTPException(
            status_code=409, detail="Membro já possui uma assinatura ativa"
        )

    start = datetime.utcnow()
    return await sub_repo.create(
        member_id=member_id,
        plan_id=plan.id,
        start_date=start,
        end_date=start + timedelta(days=plan.duration_days),
        auto_renew=payload.auto_renew,
    )


@router.get(
    "/me", response_model=list[SubscriptionResponse], summary="Minhas assinaturas"
)
async def get_my_subscriptions(
    current_user: dict = Depends(get_current_user),
    repo: AbstractSubscriptionRepository = Depends(get_subscription_repo),
):
    return await repo.list_by_member(UUID(current_user["user_id"]))


@router.get(
    "/", response_model=list[SubscriptionResponse], summary="Listar todas (admin)"
)
async def list_subscriptions(
    _: dict = Depends(require_admin),
    repo: AbstractSubscriptionRepository = Depends(get_subscription_repo),
):
    return await repo.list_all()


@router.patch(
    "/{subscription_id}/cancel",
    response_model=MessageResponse,
    summary="Cancelar assinatura",
)
async def cancel_subscription(
    subscription_id: UUID,
    current_user: dict = Depends(get_current_user),
    repo: AbstractSubscriptionRepository = Depends(get_subscription_repo),
):
    sub = await repo.get_by_id(subscription_id)
    if not sub or str(sub.member_id) != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    if not sub.is_active:
        raise HTTPException(status_code=400, detail="Assinatura já cancelada")

    await repo.cancel(subscription_id)
    return MessageResponse(message="Assinatura cancelada com sucesso")
