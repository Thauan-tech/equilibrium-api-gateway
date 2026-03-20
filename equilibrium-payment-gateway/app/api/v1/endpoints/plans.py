from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID

from app.repositories import AbstractPlanRepository, get_plan_repo
from app.core.security import require_admin
from app.schemas.schemas import PlanCreate, PlanUpdate, PlanResponse, MessageResponse

router = APIRouter()


@router.get("/", response_model=list[PlanResponse], summary="Listar planos disponíveis")
async def list_plans(
    active_only: bool = Query(True),
    repo: AbstractPlanRepository = Depends(get_plan_repo),
):
    return await repo.list(active_only=active_only)


@router.get("/{plan_id}", response_model=PlanResponse, summary="Detalhes de um plano")
async def get_plan(
    plan_id: UUID,
    repo: AbstractPlanRepository = Depends(get_plan_repo),
):
    plan = await repo.get_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return plan


@router.post(
    "/", response_model=PlanResponse, status_code=201, summary="Criar plano (admin)"
)
async def create_plan(
    payload: PlanCreate,
    _: dict = Depends(require_admin),
    repo: AbstractPlanRepository = Depends(get_plan_repo),
):
    return await repo.create(**payload.model_dump())


@router.patch(
    "/{plan_id}", response_model=PlanResponse, summary="Atualizar plano (admin)"
)
async def update_plan(
    plan_id: UUID,
    payload: PlanUpdate,
    _: dict = Depends(require_admin),
    repo: AbstractPlanRepository = Depends(get_plan_repo),
):
    plan = await repo.update(plan_id, **payload.model_dump(exclude_none=True))
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return plan


@router.delete(
    "/{plan_id}", response_model=MessageResponse, summary="Desativar plano (admin)"
)
async def deactivate_plan(
    plan_id: UUID,
    _: dict = Depends(require_admin),
    repo: AbstractPlanRepository = Depends(get_plan_repo),
):
    if not await repo.deactivate(plan_id):
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return MessageResponse(message="Plano desativado com sucesso")
