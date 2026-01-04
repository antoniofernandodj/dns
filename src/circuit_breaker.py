# src/circuit_breaker.py

import asyncio
import time
from enum import Enum
from typing import Callable, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerStats:
    failure_count: int = field(default=0)
    success_count: int = field(default=0)
    last_failure_time: float = field(default=0.0)
    last_success_time: float = field(default=0.0)
    total_calls: int = field(default=0)
    total_failures: int = field(default=0)


class CircuitBreaker:
    """
    Circuit Breaker pattern para proteger contra falhas em serviços externos
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_duration: int = 60,
        half_open_max_calls: int = 3,
        name: str = "default",
    ):
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.half_open_max_calls = half_open_max_calls
        self.name = name

        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        return self._stats

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Executa função protegida pelo circuit breaker
        """
        async with self._lock:
            self._stats.total_calls += 1

            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"Circuit breaker [{self.name}]: Entering HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker [{self.name}] is OPEN"
                    )

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker [{self.name}] max half-open calls reached"
                    )
                self._half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result

        except Exception as e:
            await self._on_failure()
            raise

    async def _on_success(self):
        """Registra sucesso"""
        async with self._lock:
            self._stats.success_count += 1
            self._stats.last_success_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    logger.info(f"Circuit breaker [{self.name}]: Closing circuit")
                    self._state = CircuitState.CLOSED
                    self._stats.failure_count = 0

    async def _on_failure(self):
        """Registra falha"""
        async with self._lock:
            self._stats.failure_count += 1
            self._stats.total_failures += 1
            self._stats.last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                logger.warning(
                    f"Circuit breaker [{self.name}]: Failure in HALF_OPEN, opening circuit"
                )
                self._state = CircuitState.OPEN
                return

            if self._stats.failure_count >= self.failure_threshold:
                logger.error(
                    f"Circuit breaker [{self.name}]: Opening circuit "
                    f"(failures: {self._stats.failure_count})"
                )
                self._state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Verifica se deve tentar resetar o circuito"""
        return (
            time.time() - self._stats.last_failure_time
        ) >= self.timeout_duration

    async def reset(self):
        """Reseta o circuit breaker manualmente"""
        async with self._lock:
            logger.info(f"Circuit breaker [{self.name}]: Manual reset")
            self._state = CircuitState.CLOSED
            self._stats.failure_count = 0
            self._half_open_calls = 0


class CircuitBreakerOpenError(Exception):
    """Exceção lançada quando o circuit breaker está aberto"""

    pass
