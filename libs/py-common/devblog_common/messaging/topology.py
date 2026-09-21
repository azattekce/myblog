"""RabbitMQ topolojisinin tek doğruluk kaynağı.

Her servis bağlandığında TÜM topolojiyi idempotent olarak declare eder. Böylece
hangi servis önce ayağa kalkarsa kalksın, tüketici kuyrukları yayın başlamadan
önce mevcut olur ve mesaj kaybı yaşanmaz.

Naming convention:
  exchange : devblog.events (topic)       routing key : <aggregate>.<past_tense_verb>
  queue    : <consumer-service>.<purpose>  dlq         : <queue>.dlq
"""

EVENTS_EXCHANGE = "devblog.events"
DEAD_LETTER_EXCHANGE = "devblog.events.dlx"
DELIVERY_LIMIT = 5

QUEUES: dict[str, list[str]] = {
    "post-service.comment-events": ["comment.approved", "comment.rejected", "comment.deleted"],
    "comment-service.post-events": ["post.published", "post.updated", "post.unpublished", "post.deleted"],
    "activity-worker.all-events": ["#"],
}


def declare_topology(channel) -> None:
    channel.exchange_declare(exchange=EVENTS_EXCHANGE, exchange_type="topic", durable=True)
    channel.exchange_declare(exchange=DEAD_LETTER_EXCHANGE, exchange_type="topic", durable=True)
    for queue, routing_keys in QUEUES.items():
        dlq = f"{queue}.dlq"
        channel.queue_declare(queue=dlq, durable=True, arguments={"x-queue-type": "quorum"})
        channel.queue_bind(queue=dlq, exchange=DEAD_LETTER_EXCHANGE, routing_key=queue)
        channel.queue_declare(
            queue=queue,
            durable=True,
            arguments={
                "x-queue-type": "quorum",
                "x-delivery-limit": DELIVERY_LIMIT,
                "x-dead-letter-exchange": DEAD_LETTER_EXCHANGE,
                "x-dead-letter-routing-key": queue,
            },
        )
        for key in routing_keys:
            channel.queue_bind(queue=queue, exchange=EVENTS_EXCHANGE, routing_key=key)
