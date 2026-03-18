from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.models import Plan
from app.schemas.schemas import PlanCreate, PlanUpdate, PlanResponse, MessageResponse

router = APIRouter()


@router.get("/", response_model=list[PlanResponse], summary="Listar planos disponíveis")
async def list_plans(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    query = select(Plan)
    if active_only:
        query = query.where(Plan.is_active == True)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{plan_id}", response_model=PlanResponse, summary="Detalhes de um plano")
async def get_plan(plan_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return plan


@router.post("/", response_model=PlanResponse, status_code=201, summary="Criar plano (admin)")
async def create_plan(
    payload: PlanCreate,
    _: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    plan = Plan(**payload.model_dump())
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


@router.patch("/{plan_id}", response_model=PlanResponse, summary="Atualizar plano (admin)")
async def update_plan(
    plan_id: UUID,
    payload: PlanUpdate,
    _: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(plan, field, value)

    await db.flush()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}", response_model=MessageResponse, summary="Desativar plano (admin)")
async def deactivate_plan(
    plan_id: UUID,
    _: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    plan.is_active = False
    return MessageResponse(message="Plano desativado com sucesso")
