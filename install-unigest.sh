#!/bin/bash

# UNIGEST - Script di Installazione Completa (v1.2)
# Compatibile con Debian/Ubuntu
# Questo script può essere eseguito da qualsiasi cartella per installare il progetto da zero.

set -e # Ferma lo script in caso di errore

REPO_URL="https://github.com/andrea76com/UNIGEST_PROJECT"
PROJECT_DIR="UNIGEST_PROJECT"

echo "===================================================="
echo "   UNIGEST - Installazione Gestionale Completa"
echo "===================================================="

# 1. Installazione dipendenze di sistema
echo -e "\n[1/7] Installazione dipendenze di sistema..."
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-dev default-libmysqlclient-dev build-essential mariadb-server mariadb-client pkg-config

# 2. Download del progetto (Git)
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "\n[2/7] Download del progetto tramite Git..."
    git clone "$REPO_URL" "$PROJECT_DIR"
else
    echo -e "\n[2/7] Cartella progetto già esistente, salto il download."
fi

# Spostiamoci nella cartella del progetto
cd "$PROJECT_DIR"

# 3. Creazione struttura cartelle
echo -e "\n[3/7] Creazione cartelle e file necessari..."
mkdir -p logs backups static media
mkdir -p core/templates/anagrafiche
mkdir -p core/templates/corsi
mkdir -p core/templates/iscrizioni
mkdir -p core/templates/lezioni
mkdir -p core/templates/report
mkdir -p core/static/css
mkdir -p core/static/js
mkdir -p core/management/commands
touch core/management/__init__.py
touch core/management/commands/__init__.py

# 4. Configurazione Database
echo -e "\n[4/7] Configurazione Database..."
sudo systemctl start mariadb || sudo systemctl start mysql

# Creazione DB e Utente (se non esistono)
sudo mysql -e "CREATE DATABASE IF NOT EXISTS unigest_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'unigest_user'@'localhost' IDENTIFIED BY 'cultura';"
sudo mysql -e "GRANT ALL PRIVILEGES ON unigest_db.* TO 'unigest_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# 5. Ambiente Virtuale e Dipendenze
echo -e "\n[5/7] Setup ambiente virtuale Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Attivazione venv e installazione
. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. Configurazione ambiente (.env)
echo -e "\n[6/7] Configurazione file .env..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "File .env creato. Ricordati di personalizzarlo se necessario."
fi

# 7. Inizializzazione Django
echo -e "\n[7/7] Migrazioni e File Statici..."
python3 manage.py migrate
python3 manage.py collectstatic --noinput

echo -e "\n===================================================="
echo "   INSTALLAZIONE COMPLETATA CON SUCCESSO!"
echo "===================================================="
echo "La cartella del progetto è: $(pwd)"
echo -e "\nPer avviare il server:"
echo "cd $(pwd)"
echo "source venv/bin/activate"
echo "python3 manage.py runserver"
echo "===================================================="
