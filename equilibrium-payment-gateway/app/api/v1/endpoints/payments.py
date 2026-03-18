from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
import hmac, hashlib

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.core.config import settings
from app.models.models import Payment, Subscription, PaymentStatus
from app.schemas.schemas import PaymentCreate, PaymentResponse, WebhookPayload, MessageResponse
from app.services.payment_gateway import PaymentGateway

router = APIRouter()

gateway = PaymentGateway(
    stripe_key=settings.STRIPE_SECRET_KEY,
    pagarme_key=settings.PAGARME_API_KEY,
)


@router.post("/", response_model=PaymentResponse, status_code=201, summary="Realizar pagamento")
async def create_payment(
    payload: PaymentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch subscription
    sub_result = await db.execute(
        select(Subscription).where(
            Subscription.id == payload.subscription_id,
            Subscription.member_id == current_user["user_id"],
        )
    )
    subscription = sub_result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")

    # Load plan price
    plan = subscription.plan
    amount = plan.price

    # Process via gateway
    result = await gateway.charge(
        amount=amount,
        method=payload.method,
        member_id=current_user["user_id"],
        description=f"Academia - {plan.name}",
        metadata={"subscription_id": str(subscription.id)},
    )

    payment = Payment(
        member_id=current_user["user_id"],
        subscription_id=subscription.id,
        amount=amount,
        method=payload.method,
        status=PaymentStatus.PAID if result.success else PaymentStatus.FAILED,
        provider=result.provider,
        provider_transaction_id=result.transaction_id,
        provider_payment_url=result.payment_url,
        description=f"Academia - {plan.name}",
        paid_at=datetime.utcnow() if result.success else None,
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)
    return payment


@router.get("/me", response_model=list[PaymentResponse], summary="Meu histórico de pagamentos")
async def get_my_payments(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment).where(Payment.member_id == current_user["user_id"])
        .order_by(Payment.created_at.desc())
    )
    return result.scalars().all()


@router.get("/", response_model=list[PaymentResponse], summary="Listar todos pagamentos (admin)")
async def list_payments(
    _: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Payment).order_by(Payment.created_at.desc()))
    return result.scalars().all()


@router.get("/{payment_id}", response_model=PaymentResponse, summary="Detalhe de pagamento")
async def get_payment(
    payment_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Payment).where(Payment.id == payment_id)
    if current_user["role"] != "admin":
        query = query.where(Payment.member_id == current_user["user_id"])
    result = await db.execute(query)
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return payment


@router.post("/{payment_id}/refund", response_model=MessageResponse, summary="Reembolsar pagamento (admin)")
async def refund_payment(
    payment_id: UUID,
    _: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    if payment.status != PaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="Apenas pagamentos confirmados podem ser reembolsados")

    refund = await gateway.refund(payment.provider_transaction_id, payment.provider)
    if refund.success:
        payment.status = PaymentStatus.REFUNDED
        return MessageResponse(message="Reembolso realizado com sucesso")

    raise HTTPException(status_code=502, detail=f"Falha no reembolso: {refund.error_message}")


@router.post("/webhook", summary="Receber notificações de provedores de pagamento")
async def payment_webhook(
    request: Request,
    payload: WebhookPayload,
    x_signature: str = Header(None, alias="X-Webhook-Signature"),
    db: AsyncSession = Depends(get_db),
):
    # Validate webhook signature
    body = await request.body()
    expected = hmac.new(
        settings.STRIPE_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    if x_signature and not hmac.compare_digest(x_signature, expected):
        raise HTTPException(status_code=401, detail="Assinatura de webhook inválida")

    # Find and update payment
    result = await db.execute(
        select(Payment).where(Payment.provider_transaction_id == payload.transaction_id)
    )
    payment = result.scalar_one_or_none()
    if payment:
        status_map = {
            "paid": PaymentStatus.PAID,
            "failed": PaymentStatus.FAILED,
            "refunded": PaymentStatus.REFUNDED,
        }
        if new_status := status_map.get(payload.status):
            payment.status = new_status
            if new_status == PaymentStatus.PAID:
                payment.paid_at = datetime.utcnow()

    return {"received": True}
