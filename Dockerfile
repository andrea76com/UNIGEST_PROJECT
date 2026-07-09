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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installa le dipendenze Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copia il resto del codice dell'applicazione
COPY . /app/

# Rendi eseguibile lo script di entrypoint (verrà creato nel prossimo step)
# Se il file non esiste ancora, il comando fallirà se lo metto qui ora.
# Lo aggiungerò dopo aver creato il file o userò una tecnica sicura.
# Per ora lo commento o assumo di crearlo subito dopo.

# Espone la porta 8000
EXPOSE 8000

# Comando di avvio gestito dall'entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]
