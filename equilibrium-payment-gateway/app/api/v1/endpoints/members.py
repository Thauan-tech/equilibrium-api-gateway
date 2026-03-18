from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user, require_admin, hash_password
from app.models.models import Member
from app.schemas.schemas import MemberCreate, MemberUpdate, MemberResponse, MessageResponse

router = APIRouter()


@router.post("/", response_model=MemberResponse, status_code=201, summary="Cadastrar novo membro")
async def create_member(payload: MemberCreate, db: AsyncSession = Depends(get_db)):
    # Check duplicates
    existing = await db.execute(
        select(Member).where(
            (Member.email == payload.email) | (Member.cpf == payload.cpf)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email ou CPF já cadastrado")

    member = Member(
        name=payload.name,
        email=payload.email,
        cpf=payload.cpf,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member


@router.get("/me", response_model=MemberResponse, summary="Dados do membro autenticado")
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Member).where(Member.id == current_user["user_id"]))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Membro não encontrado")
    return member


@router.get("/", response_model=list[MemberResponse], summary="Listar membros (admin)")
async def list_members(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    result = await db.execute(select(Member).offset(offset).limit(per_page))
    return result.scalars().all()


@router.get("/{member_id}", response_model=MemberResponse, summary="Buscar membro por ID (admin)")
async def get_member(
    member_id: UUID,
    _: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Membro não encontrado")
    return member


@router.patch("/{member_id}", response_model=MemberResponse, summary="Atualizar membro (admin)")
async def update_member(
    member_id: UUID,
    payload: MemberUpdate,
    _: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Membro não encontrado")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(member, field, value)

    await db.flush()
    await db.refresh(member)
    return member


@router.delete("/{member_id}", response_model=MessageResponse, summary="Remover membro (admin)")
async def delete_member(
    member_id: UUID,
    _: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Membro não encontrado")
    await db.delete(member)
    return MessageResponse(message="Membro removido com sucesso")
