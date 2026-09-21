from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class ServiceSettings(BaseSettings):
    """Tüm servislerin ortak konfigürasyonu (12-factor: her şey environment'tan)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    service_name: str = "service"
    environment: str = "development"
    log_level: str = "INFO"

    # Database (Database-per-Service)
    database_url: str | None = None  # testlerde sqlite:// ile override edilir
    db_host: str = "mssql"
    db_port: int = 1433
    db_user: str = "sa"
    db_password: str = ""
    db_name: str = ""
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_connect_retries: int = 40

    # Redis / RabbitMQ
    redis_url: str = "redis://redis:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/%2F"
    messaging_enabled: bool = True
    outbox_poll_interval: float = 1.0

    # JWT (identity-service imzalar, diğerleri doğrular)
    jwt_secret: str = "change-me-in-production-please-32chars"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "devblog-identity"
    jwt_audience: str = "devblog-api"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_mssql(self) -> bool:
        return not self.database_url or self.database_url.startswith("mssql")

    def sqlalchemy_url(self) -> str | URL:
        if self.database_url:
            return self.database_url
        return URL.create(
            "mssql+pymssql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )
