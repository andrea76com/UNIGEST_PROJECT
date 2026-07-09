#!/bin/bash

# UNIGEST - Script di Installazione Docker (v1.2)
# Supportato su Debian/Ubuntu

set -e

echo "--- UNIGEST: Inizio Installazione Docker ---"

# 1. Aggiornamento sistema
echo "[1/6] Aggiornamento pacchetti di sistema..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Installazione Docker e Docker Compose (se non presenti)
if ! command -v docker &> /dev/null; then
    echo "[2/6] Installazione Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo "[2/6] Docker è già installato."
fi

if ! command -v docker-compose &> /dev/null; then
    echo "[2/6] Installazione Docker Compose..."
    sudo apt-get install -y docker-compose-plugin
else
    echo "[2/6] Docker Compose è già installato."
fi

# 3. Preparazione directory e file .env
echo "[3/6] Configurazione ambiente..."
if [ ! -f .env ]; then
    cp docker.env.example .env
    echo "ATTENZIONE: Creato file .env predefinito. Modificalo se necessario."
fi

mkdir -p init-db logs static media

# 4. Istruzioni per il Database
echo "[4/6] Configurazione Database..."
echo "IMPORTANTE: Copia il tuo file .sql del database (dump completo: core, auth, django) in 'init-db/'"
echo "MariaDB lo importerà automaticamente al primo avvio."
echo ""

# 5. Avvio dei container
echo "[5/6] Avvio di UNIGEST in Docker..."
# Usa il plugin docker compose se disponibile, altrimenti il comando vecchio
if docker compose version &> /dev/null; then
    sudo docker compose up -d --build
else
    sudo docker-compose up -d --build
fi

# 6. Verifica e Fine
echo "[6/6] Installazione completata!"
echo "Il servizio è ora disponibile su http://localhost:8000"
echo "I container si riavvieranno automaticamente al riavvio del server (restart: always)."
echo ""
echo "Note per il trasferimento su altra macchina:"
echo " 1. Salva immagine: docker save unigest-web | gzip > image.tar.gz"
echo " 2. Carica immagine: docker load < image.tar.gz"
echo ""
echo "Comandi utili:"
echo " - Visualizza log: sudo docker compose logs -f"
echo " - Ferma tutto:    sudo docker compose down"
echo " - Riavvia:        sudo docker compose restart"
