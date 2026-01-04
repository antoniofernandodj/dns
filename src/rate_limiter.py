import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from src.cache_lru import LRUCache


@dataclass
class RateLimitEntry:
    """
    Representa o estado de rate limiting para um IP.

    Controla:
    - Quantidade de requisições
    - Janela de tempo
    - Período de bloqueio
    """

    request_count: int = 0
    first_request_time: float = field(default_factory=time.time)
    blocked_until: float = 0.0

    def is_blocked(self) -> bool:
        """
        Verifica se o IP está bloqueado no momento.

        :return: True se bloqueado
        """
        return time.time() < self.blocked_until

    def should_reset(self, window_seconds: int) -> bool:
        """
        Verifica se a janela de rate limiting expirou.

        :param window_seconds: Duração da janela
        :return: True se deve resetar contadores
        """
        return time.time() - self.first_request_time > window_seconds


class RateLimiter:
    """
    Implementa rate limiting por IP usando sliding window.

    Funcionalidades:
    - Limita número de requisições por IP
    - Bloqueia IPs abusivos temporariamente
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        block_duration: int = 300,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_duration = block_duration
        self.clients = LRUCache[str, RateLimitEntry]()
        self._cleanup_task: asyncio.Task | None = None

    def check_rate_limit(self, client_ip: str) -> tuple[bool, str]:
        """
        Verifica se um IP pode realizar a requisição.

        :param client_ip: Endereço IP do cliente
        :return: (permitido, mensagem)
        """
        current_time = time.time()

        # Cria entrada se não existir
        if client_ip not in self.clients:
            self.clients[client_ip] = RateLimitEntry()

        entry = self.clients[client_ip]

        # Verifica se está bloqueado
        if entry.is_blocked():
            remaining = int(entry.blocked_until - current_time)
            return False, f"Rate limit exceeded. Blocked for {remaining}s"

        # Reset se a janela passou
        if entry.should_reset(self.window_seconds):
            entry.request_count = 0
            entry.first_request_time = current_time

        # Incrementa contador
        entry.request_count += 1

        # Verifica limite
        if entry.request_count > self.max_requests:
            entry.blocked_until = current_time + self.block_duration
            logging.warning(
                f"IP {client_ip} exceeded rate limit "
                f"({entry.request_count} requests in {self.window_seconds}s). "
                f"Blocked for {self.block_duration}s"
            )
            return False, f"Rate limit exceeded. Blocked for {self.block_duration}s"

        return True, ""

    def get_stats(self) -> dict[str, Any]:
        """
        Retorna estatísticas atuais do rate limiter.
        """
        blocked = sum(1 for entry in self.clients.values() if entry.is_blocked())
        return {
            "total_clients": len(self.clients),
            "blocked_clients": blocked,
            "active_clients": len(self.clients) - blocked,
        }
