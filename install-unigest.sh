#!/bin/bash

# UNIGEST - Script di Installazione Completa (v1.3.5)
# Compatibile con Debian/Ubuntu
# FIX DIAGNOSTICO: Verifica Git e requirements.txt

set -e # Ferma lo script in caso di errore

REPO_URL="https://github.com/andrea76com/UNIGEST_PROJECT"
PROJECT_DIR="UNIGEST_PROJECT"

echo "===================================================="
echo "   UNIGEST - Installazione Gestionale Completa v1.3.5"
echo "===================================================="

# 1. Installazione dipendenze di sistema
echo -e "\n[1/7] Installazione dipendenze di sistema..."
sudo apt-get update
sudo apt-get install -y git curl python3 python3-venv python3-dev default-libmysqlclient-dev build-essential mariadb-server mariadb-client pkg-config libjpeg-dev zlib1g-dev libfreetype6-dev

# 2. Diagnostica e Sincronizzazione Codice
echo -e "\n[2/7] Verifica stato Repository Git..."

if [ -f "manage.py" ]; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    echo "  • Branch attuale: $CURRENT_BRANCH"

    # Se il branch non è quello di sviluppo di Jules, avvisiamo
    if [[ "$CURRENT_BRANCH" != "jules-"* ]]; then
        echo "  • ATTENZIONE: Non sei sul branch di sviluppo Jules."
    fi

    echo "  • Verifica aggiornamenti in corso..."
    if ! git pull; then
        echo "  • Git pull fallito (conflitti locali?)."
        read -p "  • Vuoi forzare il riallineamento totale col server? (s/n): " force_sync
        if [[ $force_sync == "s" ]]; then
            git reset --hard origin/$CURRENT_BRANCH
            git pull
        fi
    fi
    CURRENT_DIR=$(pwd)
else
    # Se non siamo in una cartella git, cloniamo
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "  • Download del progetto..."
        git clone "$REPO_URL" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    else
        cd "$PROJECT_DIR"
        git pull
    fi
    CURRENT_DIR=$(pwd)
fi

# Verifica REALE del contenuto di requirements.txt
echo "  • Controllo versioni in requirements.txt..."
DETECTED_PANDAS=$(grep "pandas==" requirements.txt | cut -d'=' -f3)
echo "  • Versione pandas rilevata: '$DETECTED_PANDAS'"

if [[ "$DETECTED_PANDAS" == "2.1.3" ]]; then
    echo -e "\n[!] ERRORE CRITICO: requirements.txt contiene ancora la versione 2.1.3."
    echo "    Il tuo repository locale non è sincronizzato correttamente."
    echo "    Esegui questi comandi manualmente e riavvia lo script:"
    echo "    git fetch origin"
    echo "    git reset --hard origin/$(git rev-parse --abbrev-ref HEAD)"
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
# Usiamo --only-binary per evitare che parta la compilazione di Cython che fallisce
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
