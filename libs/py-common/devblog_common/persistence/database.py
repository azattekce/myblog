import logging
import re
import time

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..config import ServiceSettings

log = logging.getLogger(__name__)
_DB_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")


def ensure_database(settings: ServiceSettings) -> None:
    """MSSQL hazır olana kadar bekler ve servisin kendi veritabanını oluşturur (idempotent)."""
    if not settings.is_mssql:
        return
    if not _DB_NAME.match(settings.db_name):
        raise ValueError(f"Geçersiz veritabanı adı: {settings.db_name!r}")

    import pymssql  # sadece MSSQL ortamında gerekli

    last_error: Exception | None = None
    for attempt in range(1, settings.db_connect_retries + 1):
        try:
            conn = pymssql.connect(
                server=settings.db_host,
                port=str(settings.db_port),
                user=settings.db_user,
                password=settings.db_password,
                database="master",
                autocommit=True,
                login_timeout=5,
            )
            try:
                cur = conn.cursor()
                cur.execute(f"IF DB_ID(N'{settings.db_name}') IS NULL CREATE DATABASE [{settings.db_name}]")
                try:
                    # Yalnızca kapalıysa aç: ROLLBACK IMMEDIATE, çalışan diğer replikaların
                    # transaction'larını keseceği için her açılışta koşulsuz çalıştırılmamalı.
                    cur.execute(
                        f"IF EXISTS (SELECT 1 FROM sys.databases WHERE name = N'{settings.db_name}' "
                        f"AND is_read_committed_snapshot_on = 0) "
                        f"ALTER DATABASE [{settings.db_name}] SET READ_COMMITTED_SNAPSHOT ON WITH ROLLBACK IMMEDIATE"
                    )
                except Exception:  # noqa: BLE001 - opsiyonel optimizasyon
                    log.warning("READ_COMMITTED_SNAPSHOT etkinleştirilemedi")
            finally:
                conn.close()
            log.info("Veritabanı hazır", extra={"database": settings.db_name, "attempt": attempt})
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            log.warning("MSSQL bekleniyor", extra={"attempt": attempt, "error": str(exc)[:200]})
            time.sleep(3)
    raise RuntimeError(f"MSSQL'e bağlanılamadı: {last_error}")


def build_engine(settings: ServiceSettings) -> Engine:
    url = settings.sqlalchemy_url()
    if str(url).startswith("sqlite"):
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in str(url) or str(url) in ("sqlite://", "sqlite+pysqlite://"):
            kwargs["poolclass"] = StaticPool
        return create_engine(url, **kwargs)
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=1800,
    )


def build_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
