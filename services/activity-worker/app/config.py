from devblog_common.config import ServiceSettings


class Settings(ServiceSettings):
    service_name: str = "activity-worker"
    metrics_port: int = 9100
