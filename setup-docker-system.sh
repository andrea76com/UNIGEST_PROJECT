#!/bin/bash

# UNIGEST - Script di Configurazione Sistema Docker
# Da eseguire sulla macchina dove si vuole installare Docker (Produzione o Sviluppo)
# Supportato su Debian/Ubuntu

set -e

echo "--- UNIGEST: Installazione Docker sul Sistema ---"

# 1. Aggiornamento sistema
echo "[1/3] Aggiornamento pacchetti di sistema..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Installazione Docker
if ! command -v docker &> /dev/null; then
    echo "[2/3] Installazione Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "NOTA: Potrebbe essere necessario riavviare la sessione (logout/login) per usare docker senza sudo."
else
    echo "[2/3] Docker è già installato."
fi

# 3. Installazione Docker Compose
if ! docker compose version &> /dev/null; then
    echo "[3/3] Installazione Docker Compose Plugin..."
    sudo apt-get install -y docker-compose-plugin
else
    echo "[3/3] Docker Compose è già installato."
fi

echo "--- Configurazione completata! ---"
