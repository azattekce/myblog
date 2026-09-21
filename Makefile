# DevBlog geliştirici komutları.  `make help` ile listele.
SERVICES := identity-service post-service comment-service activity-worker
COMPOSE  := docker compose

.PHONY: help up down logs ps clean test test-backend test-frontend lint lint-backend lint-frontend \
        validate k8s-validate venv

help: ## Komutları listele
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n",$$1,$$2}'

up: ## Tüm sistemi derle ve başlat (http://localhost:8080)
	$(COMPOSE) up -d --build
	@echo "Blog: http://localhost:8080  |  Grafana: http://localhost:3000  |  RabbitMQ: http://localhost:15672"

down: ## Sistemi durdur (veriler korunur)
	$(COMPOSE) down

clean: ## Sistemi durdur ve TÜM verileri sil
	$(COMPOSE) down -v --remove-orphans

logs: ## Uygulama loglarını izle
	$(COMPOSE) logs -f --tail=100 gateway identity-service post-service comment-service activity-worker

ps: ## Konteyner durumları
	$(COMPOSE) ps

venv: ## Yerel Python ortamı (.venv) kur
	python3 -m venv .venv && . .venv/bin/activate && pip install -q -r requirements-dev.txt \
	  -r services/identity-service/requirements.txt && pip install -q -e libs/py-common

test: test-backend test-frontend ## Tüm testler

test-backend: ## pytest (her servis kendi dizininde)
	@for s in $(SERVICES); do echo "== $$s"; (cd services/$$s && python -m pytest -q) || exit 1; done

test-frontend: ## typecheck + vitest
	cd frontend && npm run typecheck && npm test

lint: lint-backend lint-frontend ## Tüm statik analiz

lint-backend: ## ruff + bandit
	ruff check libs services
	bandit -q -r libs/py-common/devblog_common services/*/app -c pyproject.toml

lint-frontend:
	cd frontend && npm run typecheck

validate: ## Compose + Prometheus kuralları + nginx doğrulama
	$(COMPOSE) config -q && echo "compose OK"
	docker run --rm -v $$PWD/observability/prometheus:/etc/prometheus -w /etc/prometheus --entrypoint promtool prom/prometheus:v2.54.1 check config prometheus.yml
	docker run --rm -v $$PWD/observability/prometheus:/etc/prometheus -w /etc/prometheus --entrypoint promtool prom/prometheus:v2.54.1 test rules tests/alerts_test.yml

k8s-validate: ## Kustomize çıktısını üret ve şemaya göre doğrula
	kubectl kustomize k8s/overlays/dev  | kubeconform -strict -summary -ignore-missing-schemas
	kubectl kustomize k8s/overlays/prod | kubeconform -strict -summary -ignore-missing-schemas
