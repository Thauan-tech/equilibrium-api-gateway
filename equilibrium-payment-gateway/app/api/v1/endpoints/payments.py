from fastapi import APIRouter, Depends, HTTPException, Request, Header
from uuid import UUID
from datetime import datetime
import hmac
import hashlib

from app.repositories import (
    AbstractSubscriptionRepository,
    AbstractPaymentRepository,
    get_subscription_repo,
    get_payment_repo,
)
from app.core.security import get_current_user, require_admin
from app.core.config import settings
from app.models.models import PaymentStatus
from app.schemas.schemas import (
    PaymentCreate,
    PaymentResponse,
    WebhookPayload,
    MessageResponse,
)
from app.services.payment_gateway import PaymentGateway

router = APIRouter()

gateway = PaymentGateway(
    stripe_key=settings.STRIPE_SECRET_KEY,
    pagarme_key=settings.PAGARME_API_KEY,
)


@router.post(
    "/", response_model=PaymentResponse, status_code=201, summary="Realizar pagamento"
)
async def create_payment(
    payload: PaymentCreate,
    current_user: dict = Depends(get_current_user),
    sub_repo: AbstractSubscriptionRepository = Depends(get_subscription_repo),
    payment_repo: AbstractPaymentRepository = Depends(get_payment_repo),
):
    member_id = UUID(current_user["user_id"])
    sub = await sub_repo.get_by_id(payload.subscription_id)
    if not sub or str(sub.member_id) != str(member_id):
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")

    amount = sub.plan.price
    result = await gateway.charge(
        amount=amount,
        method=payload.method,
        member_id=member_id,
        description=f"Academia - {sub.plan.name}",
        metadata={"subscription_id": str(sub.id)},
    )

    return await payment_repo.create(
        member_id=member_id,
        subscription_id=sub.id,
        amount=amount,
        method=payload.method,
        status=PaymentStatus.PAID if result.success else PaymentStatus.FAILED,
        provider=result.provider,
        provider_transaction_id=result.transaction_id,
        provider_payment_url=result.payment_url,
        description=f"Academia - {sub.plan.name}",
        paid_at=datetime.utcnow() if result.success else None,
    )


@router.get(
    "/me", response_model=list[PaymentResponse], summary="Meu histórico de pagamentos"
)
async def get_my_payments(
    current_user: dict = Depends(get_current_user),
    repo: AbstractPaymentRepository = Depends(get_payment_repo),
):
    return await repo.list_by_member(UUID(current_user["user_id"]))


@router.get(
    "/", response_model=list[PaymentResponse], summary="Listar todos pagamentos (admin)"
)
async def list_payments(
    _: dict = Depends(require_admin),
    repo: AbstractPaymentRepository = Depends(get_payment_repo),
):
    return await repo.list_all()


@router.get(
    "/{payment_id}", response_model=PaymentResponse, summary="Detalhe de pagamento"
)
async def get_payment(
    payment_id: UUID,
    current_user: dict = Depends(get_current_user),
    repo: AbstractPaymentRepository = Depends(get_payment_repo),
):
    payment = await repo.get_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    if (
        current_user["role"] != "admin"
        and str(payment.member_id) != current_user["user_id"]
    ):
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return payment


@router.post(
    "/{payment_id}/refund",
    response_model=MessageResponse,
    summary="Reembolsar pagamento (admin)",
)
async def refund_payment(
    payment_id: UUID,
    _: dict = Depends(require_admin),
    repo: AbstractPaymentRepository = Depends(get_payment_repo),
):
    payment = await repo.get_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    if payment.status != PaymentStatus.PAID:
        raise HTTPException(
            status_code=400,
            detail="Apenas pagamentos confirmados podem ser reembolsados",
        )

    refund = await gateway.refund(payment.provider_transaction_id, payment.provider)
    if refund.success:
        await repo.update_status(payment_id, PaymentStatus.REFUNDED)
        return MessageResponse(message="Reembolso realizado com sucesso")

    raise HTTPException(
        status_code=502, detail=f"Falha no reembolso: {refund.error_message}"
    )


@router.post("/webhook", summary="Receber notificações de provedores de pagamento")
async def payment_webhook(
    request: Request,
    payload: WebhookPayload,
    x_signature: str = Header(None, alias="X-Webhook-Signature"),
    repo: AbstractPaymentRepository = Depends(get_payment_repo),
):
    body = await request.body()
    expected = hmac.new(
        settings.STRIPE_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    if x_signature and not hmac.compare_digest(x_signature, expected):
        raise HTTPException(status_code=401, detail="Assinatura de webhook inválida")

    payment = await repo.get_by_transaction_id(payload.transaction_id)
    if payment:
        status_map = {
            "paid": PaymentStatus.PAID,
            "failed": PaymentStatus.FAILED,
            "refunded": PaymentStatus.REFUNDED,
        }
        if new_status := status_map.get(payload.status):
            paid_at = datetime.utcnow() if new_status == PaymentStatus.PAID else None
            await repo.update_status(payment.id, new_status, paid_at)

    return {"received": True}
