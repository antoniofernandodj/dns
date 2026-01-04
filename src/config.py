# src/config.py

from pydantic import BaseModel, Field
from typing import List, Optional
import yaml
from pathlib import Path


class DatabaseConfig(BaseModel):
    url: str
    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int
    echo: bool


class DNSConfig(BaseModel):
    upstream_servers: List[str]
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
    blocked_qtypes: List[str]


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
    file: Optional[str]


class AppConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    dns: DNSConfig = Field(default_factory=DNSConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    circuit_breaker: CircuitBreakerConfig = Field(
        default_factory=CircuitBreakerConfig
    )
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, path: str) -> "AppConfig":
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)


def load_config(path: str = "config.yaml") -> AppConfig:
    return AppConfig.from_yaml(path)
