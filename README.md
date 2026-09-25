# commit/log — DevBlog

Yazılım üzerine kişisel blog platformu. Mikroservis mimarisi, DDD, CQRS, Event-Driven, Transactional Outbox.

**Stack:** FastAPI · React + TypeScript + Vite + Bootstrap 5 · MSSQL 2022 · Redis · RabbitMQ · Nginx · Docker · Kubernetes · Prometheus · Grafana · Loki

## Hızlı başlangıç

Gereksinim: Docker Desktop / Docker Engine + Compose v2, Docker'a ayrılmış **en az 6 GB RAM** (MSSQL tek başına 2 GB ister).

```bash
docker compose up -d --build        # ya da: make up
```

İlk açılış 2–4 dakika sürer (MSSQL hazır olana kadar servisler bekler). Durum: `docker compose ps` (tüm servisler `healthy` olmalı).

| Adres | Ne |
|---|---|
| http://localhost:8080 | Blog (tek giriş noktası: Nginx gateway) |
| http://localhost:8080/login | Yazar girişi — `admin` / `Admin123!` |
| http://localhost:3000 | Grafana — `admin` / `devblog-grafana` |
| http://localhost:9090 | Prometheus |
| http://localhost:15672 | RabbitMQ yönetimi — `devblog` / `devblog-rabbit-pass` |
| http://localhost:8081 | Redis Commander — `admin` / `admin` |
| http://localhost:8080/api/posts/docs | OpenAPI (yalnızca development) |

`.env` olmadan varsayılan geliştirme değerleriyle çalışır. Üretim için `cp .env.example .env` ve tüm gizli değerleri değiştirin.

E-posta alarmları için `.env`'e Gmail bilgilerinizi girin (`GRAFANA_SMTP_USER`, `GRAFANA_SMTP_PASSWORD` — [Uygulama Şifresi](https://myaccount.google.com/apppasswords), `GRAFANA_ALERT_EMAIL_TO`). Detay: [docs/ARCHITECTURE.md § 11](docs/ARCHITECTURE.md#11-monitoring-prometheus--grafana--loki).

> Apple Silicon: MSSQL imajı yalnızca amd64'tür; Docker Desktop'ta "Use Rosetta for x86/amd64 emulation" açık olmalı.

## Komutlar

```bash
make help            # tüm komutlar
make logs            # uygulama logları
make test            # backend (pytest) + frontend (vitest)
make lint            # ruff + bandit + tsc
make validate        # compose + prometheus kuralları
make clean           # her şeyi ve verileri sil
```

## Doğrulanmış olanlar

- Backend: 43 test (shared kernel 14, identity 11, post 9, comment 7, worker 2) — ruff (S/B/UP/SIM kuralları) ve bandit temiz
- Frontend: tip kontrolü, 8 vitest testi, production build
- Gateway üzerinden uçtan uca: login → CSRF'li refresh → yazı yayını → event ile yorum projeksiyonu → onay → sayaç senkronu → logout sonrası token iptali; rate limit, güvenlik başlıkları, correlation id
- Dayanıklılık: RabbitMQ kapalıyken yazı yayınlandı, olaylar outbox'ta bekledi, broker dönünce kayıpsız iletildi
- `docker compose config`, `promtool check/test rules`, `kustomize build | kubeconform` (dev + prod)

Mimari ayrıntılar: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**
