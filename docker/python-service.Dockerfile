# syntax=docker/dockerfile:1.7
# ---------------------------------------------------------------------------
# Tüm Python mikroservisleri için ortak, çok aşamalı (multi-stage) imaj.
# Build context: repo kökü (libs/py-common paylaşılan çekirdeğe erişmek için).
#   docker build -f docker/python-service.Dockerfile --build-arg SERVICE=post-service .
# ---------------------------------------------------------------------------
ARG PYTHON_VERSION=3.12

# ---- 1) builder: bağımlılıkları izole bir venv'e kur ----------------------
FROM python:${PYTHON_VERSION}-slim AS builder
ARG SERVICE
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /build
COPY services/${SERVICE}/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY libs/py-common ./py-common
RUN pip install --no-deps ./py-common

# ---- 2) runtime: yalnızca venv + uygulama kodu, root olmayan kullanıcı -----
FROM python:${PYTHON_VERSION}-slim AS runtime
ARG SERVICE
ARG APP_PORT=8000
LABEL org.opencontainers.image.source="https://github.com/your-org/devblog" \
      org.opencontainers.image.title="devblog-${SERVICE}" \
      org.opencontainers.image.licenses="MIT"
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_PORT=${APP_PORT}
RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app --no-create-home app
COPY --from=builder /opt/venv /opt/venv
WORKDIR /srv
COPY --chown=app:app services/${SERVICE}/app ./app
USER 10001:10001
EXPOSE ${APP_PORT}

# /health/ready veritabanı + redis kontrolü yapar; compose depends_on bunu bekler
HEALTHCHECK --interval=10s --timeout=4s --start-period=40s --retries=6 \
  CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"APP_PORT\"]}/health/ready', timeout=3).status==200 else 1)"

# Tek süreç: ölçekleme konteyner/pod replikası ile yapılır (outbox relay + consumer süreç başına bir kez).
# Erişim logu uvicorn yerine devblog_common middleware'i tarafından JSON olarak yazılır.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT} --proxy-headers --forwarded-allow-ips='*' --no-server-header --no-access-log --timeout-graceful-shutdown 20"]
