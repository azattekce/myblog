# syntax=docker/dockerfile:1.7
# Arka plan tüketicileri (HTTP API'si olmayan) için imaj. Metrikler :9100'de.
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder
ARG SERVICE=activity-worker
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /build
COPY services/${SERVICE}/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY libs/py-common ./py-common
RUN pip install --no-deps ./py-common

FROM python:${PYTHON_VERSION}-slim AS runtime
ARG SERVICE=activity-worker
LABEL org.opencontainers.image.title="devblog-${SERVICE}"
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 METRICS_PORT=9100
RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app --no-create-home app
COPY --from=builder /opt/venv /opt/venv
WORKDIR /srv
COPY --chown=app:app services/${SERVICE}/app ./app
USER 10001:10001
EXPOSE 9100
HEALTHCHECK --interval=15s --timeout=4s --start-period=20s --retries=5 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"METRICS_PORT\"]}/metrics', timeout=3)"
STOPSIGNAL SIGTERM
CMD ["python", "-m", "app.main"]
