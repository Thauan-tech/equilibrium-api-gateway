from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.models.models import PaymentMethod


@dataclass
class PaymentResult:
    success: bool
    transaction_id: Optional[str] = None
    payment_url: Optional[str] = None  # for boleto/pix
    error_message: Optional[str] = None
    provider: str = ""


class PaymentProvider(ABC):
    """Interface base para provedores de pagamento."""

    @abstractmethod
    async def process_payment(
        self,
        amount: float,
        method: PaymentMethod,
        member_id: UUID,
        description: str,
        metadata: Optional[dict] = None,
    ) -> PaymentResult:
        pass

    @abstractmethod
    async def refund_payment(self, transaction_id: str, amount: Optional[float] = None) -> PaymentResult:
        pass

    @abstractmethod
    async def get_payment_status(self, transaction_id: str) -> str:
        pass


class StripeProvider(PaymentProvider):
    """Integração com Stripe (cartão de crédito/débito internacional)."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.provider_name = "stripe"

    async def process_payment(self, amount, method, member_id, description, metadata=None) -> PaymentResult:
        # TODO: Integrar com stripe SDK
        # import stripe
        # stripe.api_key = self.api_key
        # intent = stripe.PaymentIntent.create(amount=int(amount*100), currency="brl", ...)
        return PaymentResult(
            success=True,
            transaction_id="stripe_mock_txn_123",
            provider=self.provider_name,
        )

    async def refund_payment(self, transaction_id, amount=None) -> PaymentResult:
        # TODO: stripe.Refund.create(payment_intent=transaction_id)
        return PaymentResult(success=True, transaction_id=transaction_id, provider=self.provider_name)

    async def get_payment_status(self, transaction_id) -> str:
        # TODO: stripe.PaymentIntent.retrieve(transaction_id)
        return "paid"


class PagarmeProvider(PaymentProvider):
    """Integração com Pagar.me (PIX e Boleto bancário)."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.provider_name = "pagarme"

    async def process_payment(self, amount, method, member_id, description, metadata=None) -> PaymentResult:
        # TODO: Integrar com SDK do Pagar.me
        if method == PaymentMethod.PIX:
            return PaymentResult(
                success=True,
                transaction_id="pagarme_mock_pix_123",
                payment_url="https://pix.pagarme.com/mock/qrcode",
                provider=self.provider_name,
            )
        elif method == PaymentMethod.BOLETO:
            return PaymentResult(
                success=True,
                transaction_id="pagarme_mock_boleto_123",
                payment_url="https://boleto.pagarme.com/mock/123456789",
                provider=self.provider_name,
            )
        return PaymentResult(success=False, error_message="Método não suportado", provider=self.provider_name)

    async def refund_payment(self, transaction_id, amount=None) -> PaymentResult:
        return PaymentResult(success=True, transaction_id=transaction_id, provider=self.provider_name)

    async def get_payment_status(self, transaction_id) -> str:
        return "paid"


class PaymentGateway:
    """Orquestrador de provedores de pagamento."""

    def __init__(self, stripe_key: str = "", pagarme_key: str = ""):
        self._providers: dict[str, PaymentProvider] = {}
        if stripe_key:
            self._providers["stripe"] = StripeProvider(stripe_key)
        if pagarme_key:
            self._providers["pagarme"] = PagarmeProvider(pagarme_key)

    def _select_provider(self, method: PaymentMethod) -> PaymentProvider:
        """Seleciona automaticamente o provedor com base no método de pagamento."""
        if method in (PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD):
            provider = self._providers.get("stripe")
        else:
            provider = self._providers.get("pagarme")

        if not provider:
            # Fallback: retorna o primeiro disponível
            if self._providers:
                return next(iter(self._providers.values()))
            raise ValueError("Nenhum provedor de pagamento configurado")

        return provider

    async def charge(
        self,
        amount: float,
        method: PaymentMethod,
        member_id: UUID,
        description: str,
        metadata: Optional[dict] = None,
    ) -> PaymentResult:
        provider = self._select_provider(method)
        return await provider.process_payment(amount, method, member_id, description, metadata)

    async def refund(self, transaction_id: str, provider_name: str, amount: Optional[float] = None) -> PaymentResult:
        provider = self._providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provedor '{provider_name}' não encontrado")
        return await provider.refund_payment(transaction_id, amount)
