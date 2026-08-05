# Dockerfile para Bounty Hunter AI v2.0 Daemon en la Nube (24/7 Gratis)
FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Comando de ejecución del daemon autónomo en segundo plano
CMD ["python", "tools/profit_daemon.py"]
