# src/config.py

from pathlib import Path

import yaml
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    url: str
    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int
    echo: bool


class DNSConfig(BaseModel):
    upstream_servers: list[str]
    timeout: float
    retries: int


class CacheConfig(BaseModel):
    max_size: int
    cleanup_interval: int
    default_ttl: int


class RateLimitConfig(BaseModel):
    enabled: bool
    max_requests: int
    window_seconds: int
    block_duration: int


class SecurityConfig(BaseModel):
    max_query_size: int
    validate_dnssec: bool
    blocked_qtypes: list[str]


class CircuitBreakerConfig(BaseModel):
    enabled: bool
    failure_threshold: int
    timeout_duration: int
    half_open_max_calls: int


class ServerConfig(BaseModel):
    host: str
    port: int
    workers: int


class LoggingConfig(BaseModel):
    level: str
    format: str
    file: str | None


class AppConfig(BaseModel):
    server: ServerConfig
    database: DatabaseConfig
    dns: DNSConfig
    cache: CacheConfig
    rate_limit: RateLimitConfig
    security: SecurityConfig
    circuit_breaker: CircuitBreakerConfig
    logging: LoggingConfig

    @classmethod
    def from_yaml(cls, path: str) -> "AppConfig":
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(config_path) as f:
            data = yaml.safe_load(f)

        return cls(**data)


__config: AppConfig | None = None


def load_config(path: str = "config.yaml") -> AppConfig:
    global __config
    if __config is not None:
        return __config

    config = AppConfig.from_yaml(path)
    __config = config
    return config
