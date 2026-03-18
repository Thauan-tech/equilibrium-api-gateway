# Equilibrium Payment Gateway

API de gateway de pagamentos construída com **FastAPI** e **Python 3.12**.

---

## Estrutura do Projeto

```
equilibrium-payment-gateway/
├── app/
│   ├── main.py                          # Entrypoint FastAPI
│   ├── api/v1/
│   │   ├── router.py                    # Agrega todos os routers
│   │   └── endpoints/
│   │       ├── auth.py                  # Autenticação JWT
│   │       ├── members.py               # Gestão de membros
│   │       ├── plans.py                 # Planos de assinatura
│   │       ├── subscriptions.py         # Assinaturas
│   │       └── payments.py              # Pagamentos + webhooks
│   ├── core/
│   │   ├── config.py                    # Settings via variáveis de ambiente
│   │   ├── database.py                  # SQLAlchemy async + session
│   │   ├── security.py                  # JWT, bcrypt, dependências de auth
│   │   └── middleware.py                # Logging, rate limiting
│   ├── models/models.py                 # ORM: Member, Plan, Subscription, Payment
│   ├── schemas/schemas.py               # Pydantic v2: request/response
│   └── services/
│       └── payment_gateway.py           # Abstração Stripe / Pagar.me
├── migrations/
│   ├── env.py                           # Alembic async config
│   └── versions/
│       └── 0001_initial.py              # Schema inicial
├── tests/
│   ├── unit/test_payment_gateway.py     # Testes do serviço de pagamento
│   └── integration/test_api.py          # Testes dos endpoints HTTP
├── scripts/
│   └── seed.py                          # Dados iniciais para dev
├── .github/workflows/
│   └── ci-cd.yml                        # Pipeline GitHub Actions
├── docker-compose.yml                   # Dev: API + Redis
├── docker-compose.prod.yml              # Overrides de produção
├── Dockerfile                           # Multi-stage build
├── Makefile                             # Comandos utilitários
├── alembic.ini                          # Config migrations
├── requirements.txt
└── env.example
```

---

## Quickstart

### Pré-requisitos
- Docker & Docker Compose
- Python 3.12+ (para dev local sem Docker)

### 1. Clonar e configurar

```bash
git clone https://github.com/seu-usuario/equilibrium-payment-gateway.git
cd equilibrium-payment-gateway

cp env.example .env
# Edite o .env com suas chaves
```

### 2. Subir o ambiente

```bash
make dev
# ou manualmente:
docker compose up --build
```

### 3. Acessar

| Serviço  | URL                         |
|----------|-----------------------------|
| API Docs | http://localhost:8000/docs  |
| ReDoc    | http://localhost:8000/redoc |

> **Banco de dados:** a integração com PostgreSQL ainda não está ativa. Os endpoints que dependem do banco retornarão erro até que a conexão seja configurada.

---

## Endpoints

### Health
| Método | Rota       | Descrição       | Auth    |
|--------|------------|-----------------|---------|
| GET    | `/`        | Info da API     | Público |
| GET    | `/health`  | Liveness probe  | Público |

### Auth
| Método | Rota                   | Descrição          | Auth    |
|--------|------------------------|--------------------|---------|
| POST   | `/api/v1/auth/login`   | Login, retorna JWT | Público |

### Members
| Método | Rota                   | Descrição             | Auth    |
|--------|------------------------|-----------------------|---------|
| POST   | `/api/v1/members/`     | Cadastrar novo membro | Público |
| GET    | `/api/v1/members/me`   | Meus dados            | Membro  |
| GET    | `/api/v1/members/`     | Listar todos          | Admin   |
| GET    | `/api/v1/members/{id}` | Buscar por ID         | Admin   |
| PATCH  | `/api/v1/members/{id}` | Atualizar membro      | Admin   |
| DELETE | `/api/v1/members/{id}` | Remover membro        | Admin   |

### Plans
| Método | Rota                 | Descrição            | Auth    |
|--------|----------------------|----------------------|---------|
| GET    | `/api/v1/plans/`     | Listar planos ativos | Público |
| GET    | `/api/v1/plans/{id}` | Detalhe do plano     | Público |
| POST   | `/api/v1/plans/`     | Criar plano          | Admin   |
| PATCH  | `/api/v1/plans/{id}` | Atualizar plano      | Admin   |
| DELETE | `/api/v1/plans/{id}` | Desativar plano      | Admin   |

### Subscriptions
| Método | Rota                                | Descrição           | Auth   |
|--------|-------------------------------------|---------------------|--------|
| POST   | `/api/v1/subscriptions/`            | Assinar plano       | Membro |
| GET    | `/api/v1/subscriptions/me`          | Minhas assinaturas  | Membro |
| GET    | `/api/v1/subscriptions/`            | Listar todas        | Admin  |
| PATCH  | `/api/v1/subscriptions/{id}/cancel` | Cancelar assinatura | Membro |

### Payments
| Método | Rota                           | Descrição             | Auth    |
|--------|--------------------------------|-----------------------|---------|
| POST   | `/api/v1/payments/`            | Realizar pagamento    | Membro  |
| GET    | `/api/v1/payments/me`          | Meu histórico         | Membro  |
| GET    | `/api/v1/payments/`            | Listar todos          | Admin   |
| GET    | `/api/v1/payments/{id}`        | Detalhe do pagamento  | Membro  |
| POST   | `/api/v1/payments/{id}/refund` | Reembolsar            | Admin   |
| POST   | `/api/v1/payments/webhook`     | Webhook de provedores | Público |

---

## Autenticação

A API usa **JWT Bearer Token**. Para autenticar:

```bash
# 1. Fazer login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "seu@email.com", "password": "senha"}'

# 2. Usar o token retornado
curl http://localhost:8000/api/v1/members/me \
  -H "Authorization: Bearer <token>"
```

No Swagger (`/docs`): clique em **Authorize** e cole o token no campo `HTTPBearer`.

---

## Provedores de Pagamento

A arquitetura usa o **padrão Strategy** para abstrair os provedores:

```
PaymentGateway
├── StripeProvider   → Cartão de crédito / débito
└── PagarmeProvider  → PIX / Boleto bancário
```

O gateway seleciona o provedor automaticamente com base no método de pagamento.
Para adicionar um novo provedor, basta implementar a interface `PaymentProvider`.

---

## Testes

```bash
make test              # todos os testes
make test-cov          # com relatório de cobertura
make test-unit         # apenas unitários
make test-integration  # apenas integração
```

---

## Migrations (Alembic)

> Requer PostgreSQL configurado e `DATABASE_URL` definida no `.env`.

```bash
make migrate                        # aplica migrations pendentes
make migrate-create name=descricao  # cria nova migration
make migrate-down                   # reverte última migration
```

---

## DevOps

### Docker

```bash
# Dev com hot-reload
make dev

# Produção
make prod-up
```

**Serviços no docker-compose (dev):**
- `equilibrium-api` — FastAPI na porta 8000
- `equilibrium-redis` — Redis na porta 6379

### CI/CD — GitHub Actions

O pipeline em `.github/workflows/ci-cd.yml` executa:

1. **Lint** — Ruff + mypy
2. **Test** — pytest com cobertura
3. **Build** — imagem Docker multi-stage, push para GHCR
4. **Deploy** — via SSH na branch `main`

---

## Makefile

```bash
make help           # lista todos os comandos

make dev            # ambiente dev com hot-reload
make up / down      # start/stop containers
make logs           # logs da API em tempo real
make shell          # shell no container

make migrate        # executa migrations
make seed           # popula banco
make test           # roda testes
make lint           # verifica código
make format         # formata código
make clean          # limpa containers e volumes
```

---

## Stack

| Camada     | Tecnologia                           |
|------------|--------------------------------------|
| Framework  | FastAPI 0.115                        |
| Linguagem  | Python 3.12                          |
| Banco      | PostgreSQL 16 + SQLAlchemy 2 (async) |
| Migrations | Alembic                              |
| Cache      | Redis 7                              |
| Auth       | JWT (python-jose) + bcrypt           |
| Validação  | Pydantic v2                          |
| Containers | Docker + Docker Compose              |
| CI/CD      | GitHub Actions                       |
| Testes     | pytest + pytest-asyncio + httpx      |
