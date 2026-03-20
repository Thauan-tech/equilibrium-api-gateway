import pytest
from uuid import uuid4

from app.services.payment_gateway import (
    PaymentGateway,
    StripeProvider,
    PagarmeProvider,
)
from app.models.models import PaymentMethod


# ─── StripeProvider ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stripe_process_payment_success():
    provider = StripeProvider(api_key="sk_test_fake")
    result = await provider.process_payment(
        amount=99.90,
        method=PaymentMethod.CREDIT_CARD,
        member_id=uuid4(),
        description="Plano Mensal",
    )
    assert result.success is True
    assert result.transaction_id is not None
    assert result.provider == "stripe"


@pytest.mark.asyncio
async def test_stripe_refund_success():
    provider = StripeProvider(api_key="sk_test_fake")
    result = await provider.refund_payment("txn_123")
    assert result.success is True


# ─── PagarmeProvider ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pagarme_pix_returns_payment_url():
    provider = PagarmeProvider(api_key="ak_test_fake")
    result = await provider.process_payment(
        amount=99.90,
        method=PaymentMethod.PIX,
        member_id=uuid4(),
        description="Plano Mensal",
    )
    assert result.success is True
    assert result.payment_url is not None
    assert result.provider == "pagarme"


@pytest.mark.asyncio
async def test_pagarme_boleto_returns_payment_url():
    provider = PagarmeProvider(api_key="ak_test_fake")
    result = await provider.process_payment(
        amount=99.90,
        method=PaymentMethod.BOLETO,
        member_id=uuid4(),
        description="Plano Mensal",
    )
    assert result.success is True
    assert result.payment_url is not None


# ─── PaymentGateway ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_gateway_routes_card_to_stripe():
    gateway = PaymentGateway(stripe_key="sk_test", pagarme_key="ak_test")
    result = await gateway.charge(
        amount=120.00,
        method=PaymentMethod.CREDIT_CARD,
        member_id=uuid4(),
        description="Plano Trimestral",
    )
    assert result.provider == "stripe"


@pytest.mark.asyncio
async def test_gateway_routes_pix_to_pagarme():
    gateway = PaymentGateway(stripe_key="sk_test", pagarme_key="ak_test")
    result = await gateway.charge(
        amount=120.00,
        method=PaymentMethod.PIX,
        member_id=uuid4(),
        description="Plano Trimestral",
    )
    assert result.provider == "pagarme"


@pytest.mark.asyncio
async def test_gateway_raises_when_no_provider():
    gateway = PaymentGateway()  # sem providers
    with pytest.raises(ValueError, match="Nenhum provedor"):
        await gateway.charge(
            amount=50.00,
            method=PaymentMethod.CREDIT_CARD,
            member_id=uuid4(),
            description="Teste",
        )
