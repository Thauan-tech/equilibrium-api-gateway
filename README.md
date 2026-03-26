# 🚀 Equilibrium API Gateway

Infraestrutura moderna baseada em **Terraform + CI/CD + Docker + AWS**, com deploy automatizado e baixo acoplamento operacional.

---

## 📌 Visão Geral

Este projeto implementa uma API containerizada com:

* **Provisionamento automático** via Terraform (Infrastructure as Code)
* **Build e entrega contínua** com GitHub Actions
* **Deploy simplificado** em instância EC2
* **Distribuição de imagens** via Amazon ECR

---

## 🏗️ Arquitetura

```
GitHub (CI/CD)
   ↓
Amazon ECR (Docker Images)
   ↓
EC2 (Docker Runtime)
   ↓
API (porta 8000)
```

---

## ⚙️ Stack Tecnológica

* Terraform
* AWS (EC2, ECR, IAM, Security Groups, Elastic IP)
* Docker
* GitHub Actions
* Python (FastAPI + Uvicorn)

---

## 🧱 Infraestrutura (Terraform)

### Recursos provisionados

* EC2 (Amazon Linux 2023)
* ECR (repositório de imagens Docker)
* IAM Role (acesso seguro ao ECR)
* Security Group (liberação de portas 80, 8000 e SSH)
* Elastic IP (IP fixo)

### Execução

```bash
terraform init
terraform plan
terraform apply
```

---

## 🔁 CI/CD Pipeline

### CI (Build)

Disparado a cada push na branch `main`:

* Build da imagem Docker
* Push para o Amazon ECR

### CD (Deploy)

* EC2 executa um loop contínuo:

  * Faz pull da imagem `latest`
  * Substitui o container em execução
  * Mantém a aplicação sempre atualizada

---

## 🐳 Execução da Aplicação

A aplicação roda em container Docker:

```bash
docker run -d -p 8000:8000 equilibrium-api
```

A API estará disponível em:

```
http://<EC2_PUBLIC_IP>:8000
```

---

## 🔐 Segurança

* EC2 autenticada via **IAM Role (sem credenciais hardcoded)**
* Security Group restringe acesso SSH
* Comunicação com ECR via credenciais temporárias

---

## 📦 Estrutura do Projeto

```
infra/
  └── terraform/
app/
  └── (código da API)
.github/
  └── workflows/
```

---

## ⚠️ Considerações

* Deploy simplificado (sem orquestrador como ECS/Kubernetes)
* Sem rollback automático
* Estratégia ideal para projetos enxutos ou MVPs

---

## 🚀 Evoluções Futuras

* Migrar para AWS ECS (Fargate)
* Adicionar Load Balancer (ALB)
* Implementar ambientes (dev/hml/prod)
* Observabilidade com CloudWatch

---

## 🧠 Resumo

Infraestrutura provisionada com Terraform, build automatizado via CI e deploy contínuo simplificado em EC2 utilizando Docker e ECR.

---
