from fastapi import APIRouter, Depends, HTTPException, status

from app.repositories import AbstractMemberRepository, get_member_repo
from app.core.security import verify_password, create_access_token
from app.schemas.schemas import LoginRequest, TokenResponse
from app.core.config import settings

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Autenticar membro ou admin")
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
        raise HTTPException(status_code=403, detail="Conta suspensa. Entre em contato com a academia.")

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
