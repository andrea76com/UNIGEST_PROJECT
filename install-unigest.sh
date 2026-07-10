#!/bin/bash

# UNIGEST - Script di Installazione Completa (v1.3.3)
# Compatibile con Debian/Ubuntu
# FIX AGGRESSIVO: Dipendenze Python 3.13 e Cache Pip

set -e # Ferma lo script in caso di errore

REPO_URL="https://github.com/andrea76com/UNIGEST_PROJECT"
PROJECT_DIR="UNIGEST_PROJECT"

echo "===================================================="
echo "   UNIGEST - Installazione Gestionale Completa v1.3.3"
echo "===================================================="

# 1. Installazione dipendenze di sistema
echo -e "\n[1/7] Installazione dipendenze di sistema..."
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-dev default-libmysqlclient-dev build-essential mariadb-server mariadb-client pkg-config libjpeg-dev zlib1g-dev libfreetype6-dev

# 2. Download o posizionamento nel progetto
if [ -f "manage.py" ]; then
    echo -e "\n[2/7] Sei già nella cartella del progetto. Aggiorno il codice..."
    git pull || echo "Aggiornamento git fallito, procedo comunque..."
    CURRENT_DIR=$(pwd)
else
    if [ ! -d "$PROJECT_DIR" ]; then
        echo -e "\n[2/7] Download del progetto tramite Git..."
        git clone "$REPO_URL" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    else
        echo -e "\n[2/7] Cartella progetto già esistente, entro e aggiorno..."
        cd "$PROJECT_DIR"
        git pull || echo "Aggiornamento git fallito, procedo comunque..."
    fi
    CURRENT_DIR=$(pwd)
fi

# 3. Creazione struttura cartelle (con gestione permessi)
echo -e "\n[3/7] Creazione cartelle e file necessari..."
mkdir -p logs backups static media
mkdir -p core/management/commands
sudo chown -R $USER:$USER .

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
if [ -d "venv" ]; then
    echo "Rilevato venv esistente, lo elimino per una installazione pulita..."
    rm -rf venv
fi
python3 -m venv venv

# Attivazione venv e installazione
. venv/bin/activate

echo "Verifica contenuto requirements.txt prima dell'installazione:"
cat requirements.txt
echo "----------------------------------------------------"

echo "Aggiornamento strumenti di build..."
pip install --upgrade pip setuptools wheel

echo "Installazione PRIORITARIA (solo binari/wheels per evitare errori Cython)..."
# Disinstalliamo per sicurezza
pip uninstall -y pandas numpy Pillow || true

# Forziamo l'uso di binary wheels per le librerie critiche
pip install --no-cache-dir --only-binary=:all: numpy==2.1.0 pandas==2.2.3 Pillow==11.0.0

echo "Installazione altre dipendenze..."
pip install --no-cache-dir -r requirements.txt

# 6. Configurazione ambiente (.env)
echo -e "\n[6/7] Configurazione file .env..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        echo "SECRET_KEY=unigest-secret-$(date +%s)" > .env
        echo "DEBUG=True" >> .env
        echo "DB_NAME=unigest_db" >> .env
        echo "DB_USER=unigest_user" >> .env
        echo "DB_PASSWORD=cultura" >> .env
        echo "DB_HOST=localhost" >> .env
        echo "DB_PORT=3306" >> .env
    fi
fi

# 7. Inizializzazione Django
echo -e "\n[7/7] Migrazioni e File Statici..."
python3 manage.py migrate
python3 manage.py collectstatic --noinput

echo -e "\n===================================================="
echo "   INSTALLAZIONE COMPLETATA CON SUCCESSO!"
echo "===================================================="
echo "La cartella del progetto è: $CURRENT_DIR"
echo -e "\nPer avviare il server:"
echo "cd $CURRENT_DIR"
echo ". venv/bin/activate"
echo "python3 manage.py runserver"
echo "===================================================="
