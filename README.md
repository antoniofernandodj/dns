# Visão Geral do Projeto

Este projeto implementa um **servidor DNS assíncrono completo**, escrito em Python, com foco em **performance, segurança, extensibilidade e persistência**. Ele não se limita a resolver consultas DNS em tempo real, mas atua como uma **plataforma de resolução DNS**, combinando cache em memória, banco de dados, circuit breaker, rate limiting e validação de segurança.

O sistema foi projetado para operar em ambientes de produção, mitigando abusos (DDoS, amplification), reduzindo latência e evitando dependência excessiva de servidores DNS externos.

---

# Arquitetura Geral

O fluxo de resolução DNS segue a hierarquia abaixo:

1. **Recebimento da query via UDP**
2. **Validação de segurança da requisição**
3. **Rate limiting por IP**
4. **Cache em memória (LRU + TTL)**
5. **Banco de dados persistente**
6. **Resolução DNS externa (upstream)**
7. **Validação DNSSEC (opcional)**
8. **Persistência do resultado + cache**
9. **Resposta ao cliente**

Essa abordagem reduz drasticamente latência, carga externa e exposição a falhas de rede.

---

# Principais Componentes

## 1. DNSServer

O `DNSServer` é o **núcleo da aplicação**. Ele:

* Escuta requisições DNS via UDP usando `asyncio`
* Mantém handlers por tipo de registro (A, AAAA, MX, etc.)
* Aplica validações de segurança e rate limiting
* Coordena cache, banco e resolução externa

Ele funciona como um **dispatcher**, delegando a resolução real aos handlers registrados.

### Conceitos usados

* Programação assíncrona (`asyncio`)
* UDP Datagram Protocol
* Dispatcher de handlers

---

## 2. DNSProtocol

Classe baseada em `asyncio.DatagramProtocol`. É responsável apenas por:

* Receber datagramas UDP
* Criar tasks assíncronas para processamento

Isso garante que o servidor nunca bloqueie o loop principal, mesmo sob alta carga.

---

## 3. Cache LRU com TTL

O cache em memória é implementado com uma política **LRU (Least Recently Used)** e **TTL (Time To Live)**.

### Por que LRU?

* Remove automaticamente registros pouco utilizados
* Mantém os dados mais relevantes em memória

### Por que TTL?

* Respeita o comportamento do DNS
* Evita servir dados obsoletos

O cache é utilizado em **duas camadas**:

* Cache geral de respostas DNS
* Cache interno para rate limiting

---

## 4. Banco de Dados Assíncrono

O banco de dados atua como **cache persistente** entre reinicializações.

### Funções principais

* Armazenar registros DNS resolvidos externamente
* Permitir respostas mesmo sem conectividade externa
* Reduzir chamadas repetidas a upstreams

### Características

* Acesso totalmente assíncrono
* Repositórios separados por tipo de registro (A, MX, TXT, etc.)
* Conversão entre entidades de banco e `RR` do DNS

---

## 5. DatabaseBackedDNSServer

Esta classe estende o `DNSServer` e implementa a **estratégia de fallback**:

```
Cache → Banco → DNS Externo
```

Ela centraliza:

* Consulta ao banco
* Chamada a servidores DNS upstream
* Persistência automática de resultados

Esse padrão transforma o servidor em um **resolver inteligente**, e não apenas um proxy DNS.

---

## 6. Resolução DNS Externa

Quando um registro não é encontrado localmente, o servidor consulta **upstreams DNS configurados**.

### Proteções aplicadas

* Circuit Breaker
* Timeout controlado
* Tratamento explícito de erros DNS (NXDOMAIN, SERVFAIL)

---

## 7. Circuit Breaker

O **Circuit Breaker** protege o sistema contra falhas externas.

### Estados

* **Closed**: funcionamento normal
* **Open**: chamadas externas bloqueadas
* **Half-Open**: teste controlado de recuperação

### Benefícios

* Evita cascata de falhas
* Reduz latência quando upstreams estão indisponíveis
* Protege recursos internos

---

## 8. Rate Limiting

Implementado por IP usando **sliding window**.

### Comportamento

* Conta requisições por IP
* Reseta contadores por janela de tempo
* Bloqueia IPs abusivos temporariamente

### Objetivo

* Prevenir DDoS
* Evitar abuso do resolver
* Garantir qualidade de serviço

---

## 9. Validação de Segurança DNS

O `DNSSecurityValidator` protege contra ataques comuns.

### Validações realizadas

* Tamanho máximo da query
* Formato do nome de domínio (RFC 1035)
* Bloqueio de QTYPE.ANY (amplification)

Essas validações ocorrem **antes de qualquer resolução**, reduzindo custo computacional.

---

## 10. DNSSEC

Quando habilitado, o sistema valida respostas DNS usando **DNSSEC**.

### O que isso garante

* Autenticidade da resposta
* Integridade dos dados
* Proteção contra spoofing e cache poisoning

Caso a validação falhe, a resposta é rejeitada com SERVFAIL.

---

## 11. Handlers por Tipo de Registro

Cada tipo de registro DNS possui um handler específico:

* A
* AAAA
* MX
* CNAME
* TXT
* NS
* SOA
* SRV

Esses handlers:

* Chamam a lógica de fallback
* Aplicam TTL apropriado
* Facilitam extensão futura (ex: DNS over HTTPS)

---

## 12. Programação Assíncrona

Todo o projeto é baseado em **async/await**.

### Vantagens

* Alta concorrência
* Baixo consumo de threads
* Ideal para I/O intensivo (rede + banco)

O servidor pode lidar com milhares de requisições simultâneas sem bloqueio.

---

# Benefícios do Design

* Baixa latência
* Alta escalabilidade
* Segurança reforçada
* Persistência inteligente
* Fácil extensão
* Preparado para produção

---

# Possíveis Extensões Futuras

* DNS over HTTPS (DoH)
* DNS over TLS (DoT)
* Replicação de banco
* Métricas Prometheus
* Interface administrativa
* Cache distribuído (Redis)

---

# Conclusão

Este projeto não é apenas um servidor DNS, mas uma **plataforma de resolução DNS moderna**, projetada com princípios de engenharia de software, arquitetura resiliente e segurança em mente.

Ele combina conceitos clássicos de redes com padrões modernos de sistemas distribuídos, resultando em um resolver robusto, eficiente e extensível.
