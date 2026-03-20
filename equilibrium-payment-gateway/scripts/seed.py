"""
Script para popular o banco com dados iniciais de desenvolvimento.
Execute: python scripts/seed.py
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.core.database import Base
from app.core.security import hash_password
from app.models.models import Member, Plan, PlanType


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        # Admin
        admin = Member(
            name="Admin Academia",
            email="admin@academia.com",
            cpf="000.000.000-00",
            password_hash=hash_password("admin123"),
            is_admin=True,
        )
        session.add(admin)

        # Membro exemplo
        member = Member(
            name="Carlos Teste",
            email="carlos@email.com",
            cpf="111.111.111-11",
            password_hash=hash_password("senha123"),
        )
        session.add(member)

        # Planos
        plans = [
            Plan(
                name="Plano Mensal",
                description="Acesso completo por 30 dias",
                plan_type=PlanType.MONTHLY,
                price=99.90,
                duration_days=30,
            ),
            Plan(
                name="Plano Trimestral",
                description="Acesso completo por 90 dias — economia de 10%",
                plan_type=PlanType.QUARTERLY,
                price=269.90,
                duration_days=90,
            ),
            Plan(
                name="Plano Anual",
                description="Acesso completo por 365 dias — melhor custo-benefício",
                plan_type=PlanType.ANNUAL,
                price=899.90,
                duration_days=365,
            ),
        ]
        for plan in plans:
            session.add(plan)

        await session.commit()
        print("✅ Seed concluído!")
        print("   Admin: admin@academia.com / admin123")
        print("   Membro: carlos@email.com / senha123")


if __name__ == "__main__":
    asyncio.run(seed())
