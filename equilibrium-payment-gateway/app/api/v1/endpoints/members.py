from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID

from app.repositories import AbstractMemberRepository, get_member_repo
from app.core.security import get_current_user, require_admin, hash_password
from app.schemas.schemas import MemberCreate, MemberUpdate, MemberResponse, MessageResponse

router = APIRouter()


@router.post("/", response_model=MemberResponse, status_code=201, summary="Cadastrar novo membro")
async def create_member(
    payload: MemberCreate,
    repo: AbstractMemberRepository = Depends(get_member_repo),
):
    if await repo.find_by_email_or_cpf(payload.email, payload.cpf):
        raise HTTPException(status_code=409, detail="Email ou CPF já cadastrado")

    return await repo.create(
        name=payload.name,
        email=payload.email,
        cpf=payload.cpf,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
    )


@router.get("/me", response_model=MemberResponse, summary="Dados do membro autenticado")
async def get_me(
    current_user: dict = Depends(get_current_user),
    repo: AbstractMemberRepository = Depends(get_member_repo),
):
    member = await repo.get_by_id(UUID(current_user["user_id"]))
    if not member:
        raise HTTPException(status_code=404, detail="Membro não encontrado")
    return member


@router.get("/", response_model=list[MemberResponse], summary="Listar membros (admin)")
async def list_members(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _: dict = Depends(require_admin),
    repo: AbstractMemberRepository = Depends(get_member_repo),
):
    return await repo.list(offset=(page - 1) * per_page, limit=per_page)


@router.get("/{member_id}", response_model=MemberResponse, summary="Buscar membro por ID (admin)")
async def get_member(
    member_id: UUID,
    _: dict = Depends(require_admin),
    repo: AbstractMemberRepository = Depends(get_member_repo),
):
    member = await repo.get_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Membro não encontrado")
    return member


@router.patch("/{member_id}", response_model=MemberResponse, summary="Atualizar membro (admin)")
async def update_member(
    member_id: UUID,
    payload: MemberUpdate,
    _: dict = Depends(require_admin),
    repo: AbstractMemberRepository = Depends(get_member_repo),
):
    member = await repo.update(member_id, **payload.model_dump(exclude_none=True))
    if not member:
        raise HTTPException(status_code=404, detail="Membro não encontrado")
    return member


@router.delete("/{member_id}", response_model=MessageResponse, summary="Remover membro (admin)")
async def delete_member(
    member_id: UUID,
    _: dict = Depends(require_admin),
    repo: AbstractMemberRepository = Depends(get_member_repo),
):
    if not await repo.delete(member_id):
        raise HTTPException(status_code=404, detail="Membro não encontrado")
    return MessageResponse(message="Membro removido com sucesso")
