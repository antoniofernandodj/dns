# src/cache_lru.py

import asyncio
import logging
import time
from collections import OrderedDict
from collections.abc import Iterable
from typing import Any, Generic, TypeVar, cast

logger = logging.getLogger(__name__)


K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    """
    Cache LRU com limite de tamanho e expiração por TTL
    """

    def __init__(self, max_size: int = 10000, cleanup_interval: int = 60):
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self._cache: OrderedDict = OrderedDict[K, V]()
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task | None = None
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "expirations": 0}

    def _make_key(self, qname: str, qtype: int) -> str:
        return f"{qname.lower()}:{qtype}"

    @property
    def capacity(self):
        return self.max_size

    async def get(self, qname: str, qtype: int, key: str | None = None) -> Any | None:
        """Busca item no cache (LRU)"""
        if key is None:
            key = self._make_key(qname, qtype)

        async with self._lock:
            if key not in self._cache:
                self.stats["misses"] += 1
                return None

            entry = self._cache[key]

            # Verifica expiração
            if self._is_expired(entry):
                del self._cache[key]
                self.stats["expirations"] += 1
                self.stats["misses"] += 1
                return None

            # Move para o final (mais recente)
            self._cache.move_to_end(key)
            self.stats["hits"] += 1

            # Atualiza TTL restante
            entry["data"].ttl = self._remaining_ttl(entry)
            return entry["data"]

    async def set(self, qname: str, qtype: int, data: Any, ttl: int) -> None:
        """Adiciona item ao cache"""
        key = self._make_key(qname, qtype)

        async with self._lock:
            # Remove item antigo se existir
            if key in self._cache:
                del self._cache[key]

            # Evict LRU se necessário
            if len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self.stats["evictions"] += 1
                logger.debug(f"LRU eviction: {oldest_key}")

            # Adiciona novo item
            self._cache[key] = {
                "data": data,
                "ttl": ttl,
                "created_at": time.time(),
            }

    def _is_expired(self, entry: dict) -> bool:
        """Verifica se entrada expirou"""
        age = int(time.time() - entry["created_at"])
        return age > int(entry["ttl"])

    def _remaining_ttl(self, entry: dict) -> int:
        """Calcula TTL restante"""
        age = int(time.time() - entry["created_at"])
        remaining = int(entry["ttl"]) - age
        return max(0, remaining)

    async def cleanup_expired(self) -> int:
        """Remove entradas expiradas"""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if self._is_expired(entry)
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                self.stats["expirations"] += len(expired_keys)
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

            return len(expired_keys)

    def start_cleanup(self) -> None:
        """Inicia limpeza periódica"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self) -> None:
        """Loop de limpeza"""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            await self.cleanup_expired()

    def get_stats(self) -> dict[str, Any]:
        """Retorna estatísticas"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "expirations": self.stats["expirations"],
            "hit_rate": f"{hit_rate:.2f}%",
        }

    def __contains__(self, key: K) -> bool:
        return key in self._cache

    def __getitem__(self, key: K) -> V:
        if key not in self._cache:
            raise KeyError(key)

        # Marca como recentemente usado
        self._cache.move_to_end(key)
        return cast(V, self._cache[key])

    def __setitem__(self, key: K, value: V) -> None:
        if key in self._cache:
            # Atualização → move para o fim
            self._cache.move_to_end(key)
        else:
            # Inserção → remove LRU se necessário
            if len(self._cache) >= self.capacity:
                self._cache.popitem(last=False)

        self._cache[key] = value

    def values(self) -> Iterable[V]:
        # Não altera a ordem (não conta como acesso)
        return self._cache.values()

    def __len__(self) -> int:
        return len(self._cache)

    def clear(self) -> None:
        self._cache.clear()
