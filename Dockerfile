# Usa una versione ufficiale di Python come base
FROM python:3.13-slim

# Imposta variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Imposta la directory di lavoro
WORKDIR /app

# Installa le dipendenze di sistema necessarie per mysqlclient e altre librerie
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-openbsd \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installa le dipendenze Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copia esplicitamente l'entrypoint prima del resto per sicurezza
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Copia il resto del codice dell'applicazione
COPY . /app/

# Espone la porta 8000
EXPOSE 8000

# Comando di avvio gestito dall'entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]
