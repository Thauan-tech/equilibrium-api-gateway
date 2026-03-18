from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.models import Member
from app.schemas.schemas import LoginRequest, TokenResponse
from app.core.config import settings

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Autenticar membro ou admin")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Member).where(Member.email == payload.email))
    member = result.scalar_one_or_none()

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
