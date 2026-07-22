#!/bin/bash

# UNIGEST - Script di Installazione Completa (v1.3.9)
# Compatibile con Debian/Ubuntu
# FIX: Aggiornamento attivo .env e prevenzione Access Denied

set -e # Ferma lo script in caso di errore

REPO_URL="https://github.com/andrea76com/UNIGEST_PROJECT"
PROJECT_DIR="UNIGEST_PROJECT"

echo "===================================================="
echo "   UNIGEST - Installazione Gestionale v1.3.9"
echo "===================================================="

# Scelta del Database
echo ""
echo "Quale database vuoi utilizzare come principale?"
echo "1) SQLite (Zero configurazioni, un solo file db.sqlite3 locale, CONSIGLIATO)"
echo "2) MariaDB/MySQL (Richiede installazione e permessi MySQL)"
read -p "Scegli (1-2): " scelta_db

# 1. Installazione dipendenze di sistema
echo -e "\n[1/7] Installazione dipendenze di sistema..."
sudo apt-get update

if [[ "$scelta_db" == "2" ]]; then
    sudo apt-get install -y git curl python3 python3-venv python3-dev default-libmysqlclient-dev build-essential mariadb-server mariadb-client pkg-config libjpeg-dev zlib1g-dev libfreetype6-dev
else
    # Per SQLite non servono i server MariaDB
    sudo apt-get install -y git curl python3 python3-venv python3-dev default-libmysqlclient-dev build-essential pkg-config libjpeg-dev zlib1g-dev libfreetype6-dev
fi

# 2. Sincronizzazione Codice
if [ -f "manage.py" ]; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "non-git")
    echo "  • Branch attuale: $CURRENT_BRANCH"
    git pull || echo "  • Nota: git pull non riuscito, procedo con i file locali."
    CURRENT_DIR=$(pwd)
else
    if [ ! -d "$PROJECT_DIR" ]; then
        git clone "$REPO_URL" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    else
        cd "$PROJECT_DIR"
        git pull || true
    fi
    CURRENT_DIR=$(pwd)
fi

# AUTORIPARAZIONE requirements.txt
if [ -f "requirements.txt" ]; then
    if grep -q "pandas==2.1.3" requirements.txt; then
        sed -i 's/pandas==2.1.3/pandas==2.2.3/g' requirements.txt
    fi
fi

# 3. Creazione struttura cartelle
echo -e "\n[3/7] Creazione cartelle..."
mkdir -p logs backups static media core/management/commands
sudo chown -R $USER:$USER .
touch core/management/__init__.py core/management/commands/__init__.py

# 4. Configurazione Database (se MariaDB)
if [[ "$scelta_db" == "2" ]]; then
    echo -e "\n[4/7] Configurazione MariaDB..."
    sudo systemctl start mariadb || sudo systemctl start mysql
    sudo mysql -e "CREATE DATABASE IF NOT EXISTS unigest_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    sudo mysql -e "CREATE USER IF NOT EXISTS 'unigest_user'@'localhost' IDENTIFIED BY 'cultura';"
    sudo mysql -e "GRANT ALL PRIVILEGES ON unigest_db.* TO 'unigest_user'@'localhost';"
    sudo mysql -e "FLUSH PRIVILEGES;"
else
    echo -e "\n[4/7] Utilizzo SQLite: nessuna installazione DB necessaria."
fi

# 5. Ambiente Virtuale e Dipendenze
echo -e "\n[5/7] Setup ambiente virtuale Python..."
if [ -d "venv" ]; then rm -rf venv; fi
python3 -m venv venv
. venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install --no-cache-dir --only-binary=:all: numpy==2.1.0 pandas==2.2.3 Pillow==11.0.0
pip install --no-cache-dir -r requirements.txt

# 6. Configurazione ambiente (.env)
echo -e "\n[6/7] Configurazione file .env..."
# Creiamo il file .env se manca del tutto
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        echo "SECRET_KEY=unigest-$(date +%s)" > .env
    fi
fi

# AGGIORNIAMO ATTIVAMENTE .env in base alla scelta dell'utente per evitare conflitti stale
if [[ "$scelta_db" == "1" ]]; then
    echo "  • Imposto .env per l'uso di SQLite..."
    # Rimuoviamo vecchie impostazioni DB per evitare conflitti
    sed -i '/^DB_ENGINE=/d' .env || true
    sed -i '/^DB_NAME=/d' .env || true
    sed -i '/^OLD_DB_NAME=/d' .env || true
    # Appendiamo le nuove chiavi per SQLite
    echo "DB_ENGINE=sqlite" >> .env
    echo "DB_NAME=db.sqlite3" >> .env
    echo "OLD_DB_NAME=" >> .env # Svuotato per evitare connessione automatica a MariaDB
else
    echo "  • Imposto .env per l'uso di MariaDB..."
    sed -i '/^DB_ENGINE=/d' .env || true
    echo "DB_ENGINE=mysql" >> .env
fi

# 7. Inizializzazione Django
echo -e "\n[7/7] Migrazioni e File Statici..."
python3 manage.py migrate
python3 manage.py collectstatic --noinput

echo -e "\n===================================================="
echo "   INSTALLAZIONE COMPLETATA CON SUCCESSO!"
echo "===================================================="
echo "La cartella è: $CURRENT_DIR"
echo "Per avviare: python3 manage.py runserver"
echo "===================================================="
