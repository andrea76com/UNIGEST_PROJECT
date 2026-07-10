#!/bin/bash

# UNIGEST - Gestione Container (Sviluppo e Build)
# Da usare per creare l'immagine da trasferire o per avviare il progetto.

set -e

echo "--- UNIGEST: Gestione Container ---"

# 1. Preparazione file .env se manca
if [ ! -f .env ]; then
    echo "[1/3] Creazione file .env da docker.env.example..."
    cp docker.env.example .env
fi

# 2. Scelta azione
echo ""
echo "Cosa vuoi fare?"
echo "1) Build Immagine e Avvio locale"
echo "2) Build e Salva immagine per trasferimento (crea unigest_web.tar.gz)"
echo "3) Solo Avvio (se l'immagine è già stata caricata)"
read -p "Scegli (1-3): " scelta

case $scelta in
    1)
        echo "Build e Avvio in corso..."
        docker compose up -d --build
        ;;
    2)
        echo "Build immagine..."
        docker compose build
        # Ricaviamo il nome esatto dell'immagine generata (solitamente progetto-web)
        IMAGE_NAME=$(docker compose config --images web)
        echo "Salvataggio immagine $IMAGE_NAME in unigest_web.tar.gz..."
        docker save $IMAGE_NAME | gzip > unigest_web.tar.gz
        echo "Fatto! Ora puoi trasferire unigest_web.tar.gz sulla macchina di produzione."
        ;;
    3)
        echo "Avvio container..."
        docker compose up -d
        ;;
    *)
        echo "Scelta non valida."
        exit 1
        ;;
esac

echo "--- Operazione completata ---"
