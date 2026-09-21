import logging
import signal
import threading

from prometheus_client import Counter, start_http_server

from app.config import Settings
from app.handlers import ActivityHandler, LogNotifier
from devblog_common.cache import create_redis
from devblog_common.logging import configure_logging
from devblog_common.messaging import RabbitMqConsumer

QUEUE = "activity-worker.all-events"
PROCESSED = Counter("devblog_consumer_messages_total", "Consumer sonuçları", ["queue", "event_type", "result"])


def main() -> None:
    settings = Settings()
    configure_logging(settings.service_name, settings.log_level, settings.environment)
    log = logging.getLogger("activity-worker")
    start_http_server(settings.metrics_port)

    consumer = RabbitMqConsumer(
        settings.rabbitmq_url,
        QUEUE,
        ActivityHandler(LogNotifier()),
        create_redis(settings.redis_url),
        on_processed=lambda et, res: PROCESSED.labels(QUEUE, et, res).inc(),
    )
    stop = threading.Event()

    def _shutdown(*_):
        log.info("Kapatma sinyali alındı")
        stop.set()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    consumer.start()
    log.info("activity-worker çalışıyor", extra={"queue": QUEUE, "metrics_port": settings.metrics_port})
    stop.wait()
    consumer.stop()


if __name__ == "__main__":
    main()
