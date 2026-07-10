#!/bin/bash

# UNIGEST - Script di Installazione Completa (v1.3.6)
# Compatibile con Debian/Ubuntu
# FIX: Autoriparazione requirements.txt e Diagnostica Avanzata

set -e # Ferma lo script in caso di errore

REPO_URL="https://github.com/andrea76com/UNIGEST_PROJECT"
PROJECT_DIR="UNIGEST_PROJECT"

echo "===================================================="
echo "   UNIGEST - Installazione Gestionale Completa v1.3.6"
echo "===================================================="

# 1. Installazione dipendenze di sistema
echo -e "\n[1/7] Installazione dipendenze di sistema..."
sudo apt-get update
sudo apt-get install -y git curl python3 python3-venv python3-dev default-libmysqlclient-dev build-essential mariadb-server mariadb-client pkg-config libjpeg-dev zlib1g-dev libfreetype6-dev

# 2. Diagnostica e Sincronizzazione Codice
echo -e "\n[2/7] Verifica stato Repository Git..."

if [ -f "manage.py" ]; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "non-git")
    echo "  • Branch attuale: $CURRENT_BRANCH"

    echo "  • Verifica aggiornamenti..."
    git pull || echo "  • Nota: git pull non riuscito, procedo con i file locali."
    CURRENT_DIR=$(pwd)
else
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "  • Download del progetto..."
        git clone "$REPO_URL" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    else
        cd "$PROJECT_DIR"
        git pull || true
    fi
    CURRENT_DIR=$(pwd)
fi

# AUTORIPARAZIONE requirements.txt
echo "  • Controllo integrità requirements.txt..."
if [ -f "requirements.txt" ]; then
    # Forza la versione corretta di pandas se trova quella vecchia
    if grep -q "pandas==2.1.3" requirements.txt; then
        echo "  • Rilevato pandas 2.1.3 errato. Applico patch automatica..."
        sed -i 's/pandas==2.1.3/pandas==2.2.3/g' requirements.txt
    fi
    # Visualizza la riga attuale per conferma
    PANDAS_LINE=$(grep "pandas==" requirements.txt || echo "non trovato")
    echo "  • Configurazione pandas: $PANDAS_LINE"
else
    echo "  • ERRORE: requirements.txt non trovato!"
    exit 1
fi

# 3. Creazione struttura cartelle
echo -e "\n[3/7] Creazione cartelle e file necessari..."
mkdir -p logs backups static media core/management/commands
sudo chown -R $USER:$USER .
touch core/management/__init__.py core/management/commands/__init__.py

# 4. Configurazione Database
echo -e "\n[4/7] Configurazione Database..."
sudo systemctl start mariadb || sudo systemctl start mysql
sudo mysql -e "CREATE DATABASE IF NOT EXISTS unigest_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'unigest_user'@'localhost' IDENTIFIED BY 'cultura';"
sudo mysql -e "GRANT ALL PRIVILEGES ON unigest_db.* TO 'unigest_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# 5. Ambiente Virtuale e Dipendenze
echo -e "\n[5/7] Setup ambiente virtuale Python..."
if [ -d "venv" ]; then rm -rf venv; fi
python3 -m venv venv
. venv/bin/activate

echo "  • Aggiornamento pip e strumenti di build..."
pip install --upgrade pip setuptools wheel

echo "  • Installazione binari (wheels) per Python 3.13..."
# Installiamo separatamente i binari critici
pip install --no-cache-dir --only-binary=:all: numpy==2.1.0 pandas==2.2.3 Pillow==11.0.0

echo "  • Installazione altre dipendenze..."
pip install --no-cache-dir -r requirements.txt

# 6. Configurazione ambiente (.env)
echo -e "\n[6/7] Configurazione file .env..."
if [ ! -f ".env" ]; then
    cp .env.example .env || echo "SECRET_KEY=unigest-$(date +%s)" > .env
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
