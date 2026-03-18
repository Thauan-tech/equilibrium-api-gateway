.PHONY: help dev build up down logs test lint migrate seed clean

help: ## Mostra todos os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ─── Dev ──────────────────────────────────────────────────────────────────────
dev: ## Sobe ambiente de desenvolvimento com hot-reload
	docker-compose up --build

up: ## Sobe os serviços em background
	docker-compose up -d

down: ## Para e remove os containers
	docker-compose down

logs: ## Exibe logs em tempo real
	docker-compose logs -f api

build: ## Rebuild da imagem da API
	docker-compose build api

# ─── Database ─────────────────────────────────────────────────────────────────
migrate: ## Executa as migrations pendentes
	docker-compose exec api alembic upgrade head

migrate-create: ## Cria nova migration (use: make migrate-create name=descricao)
	docker-compose exec api alembic revision --autogenerate -m "$(name)"

migrate-down: ## Reverte última migration
	docker-compose exec api alembic downgrade -1

seed: ## Popula o banco com dados iniciais
	docker-compose exec api python scripts/seed.py

# ─── Tests ───────────────────────────────────────────────────────────────────
test: ## Executa todos os testes
	docker-compose exec api pytest tests/ -v

test-cov: ## Executa testes com relatório de cobertura
	docker-compose exec api pytest tests/ --cov=app --cov-report=term-missing

test-unit: ## Executa apenas testes unitários
	docker-compose exec api pytest tests/unit/ -v

test-integration: ## Executa apenas testes de integração
	docker-compose exec api pytest tests/integration/ -v

# ─── Code Quality ─────────────────────────────────────────────────────────────
lint: ## Lint + format check com Ruff
	ruff check . && ruff format --check .

format: ## Auto-formata o código
	ruff format .

# ─── Prod ─────────────────────────────────────────────────────────────────────
prod-up: ## Sobe ambiente de produção
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down: ## Para ambiente de produção
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# ─── Util ─────────────────────────────────────────────────────────────────────
clean: ## Remove containers, volumes e imagens órfãs
	docker-compose down -v --remove-orphans
	docker system prune -f

shell: ## Abre shell no container da API
	docker-compose exec api bash
