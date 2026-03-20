from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.repositories import AbstractMemberRepository, get_member_repo
from app.core.security import verify_password, create_access_token, hash_password
from app.schemas.schemas import (
    LoginRequest,
    TokenResponse,
    AdminSetupRequest,
    MemberResponse,
)
from app.core.config import settings

router = APIRouter()

setup_key_header = APIKeyHeader(name="X-Setup-Key", auto_error=False)


@router.post(
    "/login", response_model=TokenResponse, summary="Autenticar membro ou admin"
)
async def login(
    payload: LoginRequest,
    repo: AbstractMemberRepository = Depends(get_member_repo),
):
    member = await repo.get_by_email(payload.email)

    if not member or not verify_password(payload.password, member.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    if member.status.value == "suspended":
        raise HTTPException(
            status_code=403, detail="Conta suspensa. Entre em contato com a academia."
        )

    token = create_access_token(
        data={
            "sub": str(member.id),
            "role": "admin" if member.is_admin else "member",
            "email": member.email,
        }
    )

    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/setup",
    response_model=MemberResponse,
    status_code=201,
    summary="Criar primeiro admin do sistema",
    description=(
        "Cria o usuário administrador inicial. "
        "Requer o header `X-Setup-Key` com o valor de `ADMIN_SETUP_KEY`. "
        "Falha se já existir qualquer admin cadastrado."
    ),
)
async def setup_first_admin(
    payload: AdminSetupRequest,
    setup_key: str = Security(setup_key_header),
    repo: AbstractMemberRepository = Depends(get_member_repo),
):
    if not setup_key or setup_key != settings.ADMIN_SETUP_KEY:
        raise HTTPException(status_code=403, detail="X-Setup-Key inválida ou ausente")

    if await repo.has_any_admin():
        raise HTTPException(
            status_code=409,
            detail="Já existe um administrador cadastrado. Use POST /members/{id}/promote para promover outros membros.",
        )

    if await repo.find_by_email_or_cpf(payload.email, payload.cpf):
        raise HTTPException(status_code=409, detail="Email ou CPF já cadastrado")

    return await repo.create(
        name=payload.name,
        email=payload.email,
        cpf=payload.cpf,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        is_admin=True,
    )
