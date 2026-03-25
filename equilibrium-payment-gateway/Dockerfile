FROM public.ecr.aws/docker/library/python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ─── Build stage ─────────────────────────────────────────────────────────────
FROM base AS builder

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# ─── Final stage ─────────────────────────────────────────────────────────────
FROM base AS final

COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/* && rm -rf /wheels

COPY . .

RUN addgroup --system app && adduser --system --group app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
