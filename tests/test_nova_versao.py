#!/usr/bin/env python3
"""
Testes para validar as melhorias implementadas no servidor DNS
Execute com: python test_melhorias.py
"""

import asyncio
import sys
import time

# Adiciona o diretório raiz ao path
sys.path.insert(0, ".")

from dnslib import QTYPE, RR, A

from server import CacheEntry, DNSSecurityValidator, RateLimiter
from src.cache_lru import LRUCache

# ============================================================================
# TESTES DE CACHE COM EXPIRAÇÃO TTL
# ============================================================================


async def test_cache_expiration():
    """Testa expiração automática de cache baseada em TTL"""
    print("\n" + "=" * 70)
    print("TESTE 1: Cache com Expiração TTL")
    print("=" * 70)

    cache = LRUCache()

    # Cria entrada com TTL curto (2 segundos)
    rr = RR("test.com", QTYPE.A, ttl=2, rdata=A("1.2.3.4"))
    await cache.set("test.com", QTYPE.A, rr, ttl=2)

    # Teste 1: Deve encontrar imediatamente
    result = await cache.get("test.com", QTYPE.A)
    assert result is not None, "❌ Cache deveria ter retornado resultado"
    print("✅ Cache retornou resultado imediatamente")

    # Teste 2: Verifica TTL restante
    remaining = result.ttl
    assert 0 < remaining <= 2, f"❌ TTL restante deveria ser ≤2, mas é {remaining}"
    print(f"✅ TTL restante correto: {remaining}s")

    # Teste 3: Aguarda expiração
    print("⏳ Aguardando 3 segundos para expiração...")
    await asyncio.sleep(3)

    result = await cache.get("test.com", QTYPE.A)
    assert result is None, "❌ Cache deveria ter expirado"
    print("✅ Cache expirou corretamente após TTL")

    # Teste 4: Verifica estatísticas
    stats = cache.get_stats()
    assert stats["hits"] == 1, f"❌ Deveria ter 1 hit, mas tem {stats['hits']}"
    assert stats["misses"] == 1, f"❌ Deveria ter 1 miss, mas tem {stats['misses']}"
    assert stats["expirations"] == 1, (
        f"❌ Deveria ter 1 expiration, mas tem {stats['expirations']}"
    )
    print(f"✅ Estatísticas corretas: {stats}")

    print("\n✅ TESTE 1 PASSOU: Cache com expiração funciona corretamente\n")


async def test_cache_cleanup():
    """Testa limpeza automática de entradas expiradas"""
    print("\n" + "=" * 70)
    print("TESTE 2: Limpeza Automática de Cache")
    print("=" * 70)

    cache = LRUCache()

    # Adiciona múltiplas entradas
    for i in range(5):
        rr = RR(f"test{i}.com", QTYPE.A, ttl=1, rdata=A(f"1.2.3.{i}"))
        await cache.set(f"test{i}.com", QTYPE.A, rr, ttl=1)

    initial_count = cache.get_stats()["entries"]
    assert initial_count == 5, f"❌ Deveria ter 5 entradas, mas tem {initial_count}"
    print(f"✅ {initial_count} entradas adicionadas ao cache")

    # Aguarda expiração
    print("⏳ Aguardando 2 segundos para expiração...")
    await asyncio.sleep(2)

    # Executa cleanup manual
    removed = await cache.cleanup_expired()
    assert removed == 5, f"❌ Deveria remover 5 entradas, mas removeu {removed}"
    print(f"✅ Cleanup removeu {removed} entradas expiradas")

    final_count = cache.get_stats()["entries"]
    assert final_count == 0, (
        f"❌ Cache deveria estar vazio, mas tem {final_count} entradas"
    )
    print(f"✅ Cache limpo: {final_count} entradas restantes")

    print("\n✅ TESTE 2 PASSOU: Limpeza automática funciona corretamente\n")


# ============================================================================
# TESTES DE RATE LIMITING
# ============================================================================


async def test_rate_limiting():
    """Testa rate limiting por IP"""
    print("\n" + "=" * 70)
    print("TESTE 3: Rate Limiting por IP")
    print("=" * 70)

    # Configuração: máximo 5 requests em 10 segundos
    limiter = RateLimiter(max_requests=5, window_seconds=10, block_duration=5)

    client_ip = "192.168.1.100"

    # Teste 1: Primeiras 5 requisições devem passar
    for i in range(5):
        allowed, msg = limiter.check_rate_limit(client_ip)
        assert allowed, f"❌ Requisição {i + 1} deveria ser permitida: {msg}"
    print("✅ Primeiras 5 requisições permitidas")

    # Teste 2: 6ª requisição deve ser bloqueada
    allowed, msg = limiter.check_rate_limit(client_ip)
    assert not allowed, "❌ 6ª requisição deveria ser bloqueada"
    assert "Rate limit exceeded" in msg, f"❌ Mensagem incorreta: {msg}"
    print(f"✅ 6ª requisição bloqueada: {msg}")

    # Teste 3: Verifica estatísticas
    stats = limiter.get_stats()
    assert stats["blocked_clients"] == 1, (
        f"❌ Deveria ter 1 cliente bloqueado, mas tem {stats['blocked_clients']}"
    )
    print(f"✅ Estatísticas corretas: {stats}")

    # Teste 4: Aguarda desbloqueio
    print("⏳ Aguardando 6 segundos para desbloqueio...")
    await asyncio.sleep(6)

    allowed, msg = limiter.check_rate_limit(client_ip)
    assert allowed, f"❌ Cliente deveria estar desbloqueado: {msg}"
    print("✅ Cliente desbloqueado após período de bloqueio")

    print("\n✅ TESTE 3 PASSOU: Rate limiting funciona corretamente\n")


async def test_rate_limiting_multiple_ips():
    """Testa rate limiting com múltiplos IPs"""
    print("\n" + "=" * 70)
    print("TESTE 4: Rate Limiting com Múltiplos IPs")
    print("=" * 70)

    limiter = RateLimiter(max_requests=3, window_seconds=10, block_duration=5)

    # IP1: Excede limite
    for _ in range(4):
        limiter.check_rate_limit("192.168.1.1")

    # IP2: Dentro do limite
    for _ in range(2):
        limiter.check_rate_limit("192.168.1.2")

    # Verifica que apenas IP1 está bloqueado
    allowed1, msg1 = limiter.check_rate_limit("192.168.1.1")
    allowed2, msg2 = limiter.check_rate_limit("192.168.1.2")

    assert not allowed1, "❌ IP1 deveria estar bloqueado"
    assert allowed2, f"❌ IP2 deveria estar permitido: {msg2}"
    print("✅ Rate limiting isolado por IP funciona corretamente")

    stats = limiter.get_stats()
    assert stats["total_clients"] == 2, (
        f"❌ Deveria ter 2 clientes, mas tem {stats['total_clients']}"
    )
    assert stats["blocked_clients"] == 1, (
        f"❌ Deveria ter 1 bloqueado, mas tem {stats['blocked_clients']}"
    )
    print(f"✅ Estatísticas corretas: {stats}")

    print("\n✅ TESTE 4 PASSOU: Rate limiting por IP funciona corretamente\n")


# ============================================================================
# TESTES DE VALIDAÇÃO DE SEGURANÇA
# ============================================================================


def test_security_validation():
    """Testa validação de queries DNS"""
    print("\n" + "=" * 70)
    print("TESTE 5: Validação de Segurança")
    print("=" * 70)

    validator = DNSSecurityValidator()

    # Teste 1: Domínio válido
    is_valid, msg = validator.validate_domain_name("google.com")
    assert is_valid, f"❌ 'google.com' deveria ser válido: {msg}"
    print("✅ Domínio válido aceito: google.com")

    # Teste 2: Domínio muito longo
    long_domain = "a" * 254
    is_valid, msg = validator.validate_domain_name(long_domain)
    assert not is_valid, "❌ Domínio muito longo deveria ser rejeitado"
    print(f"✅ Domínio muito longo rejeitado ({len(long_domain)} chars)")

    # Teste 3: Label muito longo
    is_valid, msg = validator.validate_domain_name("a" * 64 + ".com")
    assert not is_valid, "❌ Label muito longo deveria ser rejeitado"
    print("✅ Label muito longo rejeitado (>63 chars)")

    # Teste 4: Caracteres inválidos
    is_valid, msg = validator.validate_domain_name("test@#$.com")
    assert not is_valid, "❌ Caracteres inválidos deveriam ser rejeitados"
    print("✅ Caracteres inválidos rejeitados")

    # Teste 5: Label começando com hífen
    is_valid, msg = validator.validate_domain_name("-test.com")
    assert not is_valid, "❌ Label com hífen no início deveria ser rejeitado"
    print("✅ Label com hífen no início rejeitado")

    # Teste 6: Query ANY bloqueada
    is_blocked = validator.is_suspicious_qtype(QTYPE.ANY)
    assert is_blocked, "❌ Query tipo ANY deveria ser bloqueada"
    print("✅ Query tipo ANY bloqueada (previne amplification attacks)")

    # Teste 7: Tamanho de query
    small_query = b"x" * 400
    large_query = b"x" * 600

    assert validator.validate_query_size(small_query), "❌ Query pequena deveria passar"
    assert not validator.validate_query_size(large_query), (
        "❌ Query grande deveria ser rejeitada"
    )
    print("✅ Validação de tamanho funciona corretamente")

    print("\n✅ TESTE 5 PASSOU: Validação de segurança funciona corretamente\n")


# ============================================================================
# TESTES DE TYPE HINTS
# ============================================================================


def test_type_hints():
    """Verifica se type hints estão presentes nos métodos críticos"""
    print("\n" + "=" * 70)
    print("TESTE 6: Verificação de Type Hints")
    print("=" * 70)

    import inspect

    # Verifica CacheEntry
    sig = inspect.signature(CacheEntry.is_expired)
    assert sig.return_annotation is bool, "❌ is_expired deveria retornar bool"
    print("✅ CacheEntry.is_expired tem type hint correto")

    sig = inspect.signature(CacheEntry.remaining_ttl)
    assert sig.return_annotation is int, "❌ remaining_ttl deveria retornar int"
    print("✅ CacheEntry.remaining_ttl tem type hint correto")

    # Verifica LRUCache
    sig = inspect.signature(LRUCache.get)
    # async methods retornam Coroutine, então verificamos isso
    assert "return" in str(sig), "❌ LRUCache.get deveria ter annotation"
    print("✅ LRUCache.get tem type hint")

    # Verifica RateLimiter
    sig = inspect.signature(RateLimiter.check_rate_limit)
    assert "return" in str(sig), "❌ check_rate_limit deveria ter annotation"
    print("✅ RateLimiter.check_rate_limit tem type hint")

    print("\n✅ TESTE 6 PASSOU: Type hints estão presentes\n")


# ============================================================================
# TESTE DE INTEGRAÇÃO
# ============================================================================


async def test_integration():
    """Teste de integração: cache + rate limiting + validação"""
    print("\n" + "=" * 70)
    print("TESTE 7: Integração Completa")
    print("=" * 70)

    cache = LRUCache()
    limiter = RateLimiter(max_requests=10, window_seconds=60)
    validator = DNSSecurityValidator()

    client_ip = "10.0.0.1"
    domain = "example.com"

    # Simula 5 queries válidas
    for i in range(5):
        # 1. Rate limiting
        allowed, msg = limiter.check_rate_limit(client_ip)
        assert allowed, f"❌ Request {i + 1} bloqueada indevidamente"

        # 2. Validação
        is_valid, msg = validator.validate_domain_name(domain)
        assert is_valid, f"❌ Domínio válido rejeitado: {msg}"

        # 3. Verifica cache (primeira vez será miss)
        cached = await cache.get(domain, QTYPE.A)

        if cached is None and i == 0:
            # Primeira vez: adiciona ao cache
            rr = RR(domain, QTYPE.A, ttl=60, rdata=A("93.184.216.34"))
            await cache.set(domain, QTYPE.A, rr, ttl=60)
            print(f"✅ Request {i + 1}: Cache miss → adicionado")
        elif cached is not None and i > 0:
            print(f"✅ Request {i + 1}: Cache hit")
        else:
            raise AssertionError(f"❌ Estado inesperado na request {i + 1}")

    # Verifica estatísticas finais
    cache_stats = cache.get_stats()
    limiter_stats = limiter.get_stats()

    assert cache_stats["hits"] >= 4, (
        f"❌ Deveria ter ≥4 cache hits, mas tem {cache_stats['hits']}"
    )
    assert limiter_stats["total_clients"] == 1, "❌ Deveria ter 1 cliente"

    print(f"✅ Cache stats: {cache_stats}")
    print(f"✅ Limiter stats: {limiter_stats}")

    print("\n✅ TESTE 7 PASSOU: Integração completa funciona corretamente\n")


# ============================================================================
# RUNNER PRINCIPAL
# ============================================================================


async def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "🧪" * 35)
    print("EXECUTANDO SUITE DE TESTES DAS MELHORIAS")
    print("🧪" * 35)

    start_time = time.time()

    try:
        # Testes assíncronos
        await test_cache_expiration()
        await test_cache_cleanup()
        await test_rate_limiting()
        await test_rate_limiting_multiple_ips()
        await test_integration()

        # Testes síncronos
        test_security_validation()
        test_type_hints()

        elapsed = time.time() - start_time

        print("\n" + "=" * 70)
        print("🎉 TODOS OS TESTES PASSARAM! 🎉")
        print("=" * 70)
        print("✅ 7 testes executados com sucesso")
        print(f"⏱️  Tempo total: {elapsed:.2f}s")
        print("\nMelhorias validadas:")
        print("  ✓ Cache com expiração TTL")
        print("  ✓ Limpeza automática de cache")
        print("  ✓ Rate limiting por IP")
        print("  ✓ Rate limiting multi-IP")
        print("  ✓ Validação de segurança")
        print("  ✓ Type hints completos")
        print("  ✓ Integração completa")
        print("=" * 70 + "\n")

        return True

    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}\n")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
