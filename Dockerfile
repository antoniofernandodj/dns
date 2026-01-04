# Dockerfile

# Multi-stage build para imagem otimizada
FROM python:3.11-slim AS builder

# Instala dependências de build
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Cria virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copia requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage final
FROM python:3.11-slim

# Instala apenas runtime deps
RUN apt-get update && apt-get install -y \
    libcap2-bin \
    && rm -rf /var/lib/apt/lists/*

# Copia virtualenv do builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Cria usuário não-root
RUN useradd -m -u 1000 dnsuser && \
    mkdir -p /app /data && \
    chown -R dnsuser:dnsuser /app /data

WORKDIR /app

# Copia código
COPY --chown=dnsuser:dnsuser . .

# Muda para usuário não-root
USER dnsuser

EXPOSE 53/udp

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(2); s.sendto(b'\\x00\\x00\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x07example\\x03com\\x00\\x00\\x01\\x00\\x01', ('127.0.0.1', 5353)); s.close()"

CMD ["./app.py"]
