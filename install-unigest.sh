#!/bin/bash

# UNIGEST - Script di Installazione Completa v1.4.1
# Destinazione Predefinita: /opt/UNIGEST_PROJECT
# Compatibile con Debian/Ubuntu, Python 3.13 e installazioni pulite.

set -e # Ferma lo script in caso di errore

REPO_URL="https://github.com/andrea76com/UNIGEST_PROJECT"
TARGET_DIR="/opt/UNIGEST_PROJECT"

echo "===================================================="
echo "   UNIGEST - Installazione Gestionale Completa v1.4.1"
echo "===================================================="

# Richiesta database
echo ""
echo "Quale database vuoi utilizzare come principale?"
echo "1) SQLite (Zero configurazioni, un solo file db.sqlite3 locale, CONSIGLIATO)"
echo "2) MariaDB/MySQL (Richiede installazione e permessi MySQL)"
read -p "Scegli (1-2): " scelta_db

# Se sceglie SQLite, chiediamo se vuole preservare/scaricare il DB esistente o crearne uno nuovo vuoto
scelta_sqlite_tipo="1"
if [ "$scelta_db" = "1" ]; then
    echo ""
    echo "Come vuoi configurare il database SQLite?"
    echo "1) Usa il database popolato esistente (Preserva db.sqlite3 se presente, o usa quello corrente)"
    echo "2) Crea un database vuoto da zero (Esegue una migrazione pulita e cancella db.sqlite3 attuale)"
    read -p "Scegli (1-2): " scelta_sqlite_tipo
fi

# 1. Installazione dipendenze di sistema
echo -e "\n[1/7] Installazione dipendenze di sistema..."
sudo apt-get update

if [ "$scelta_db" = "2" ]; then
    sudo apt-get install -y git curl python3 python3-venv python3-dev default-libmysqlclient-dev build-essential mariadb-server mariadb-client pkg-config libjpeg-dev zlib1g-dev libfreetype6-dev
else
    # Per SQLite non servono i server MariaDB
    sudo apt-get install -y git curl python3 python3-venv python3-dev default-libmysqlclient-dev build-essential pkg-config libjpeg-dev zlib1g-dev libfreetype6-dev
fi

# 2. Creazione della cartella di destinazione /opt con permessi adeguati
echo -e "\n[2/7] Preparazione cartella di sistema $TARGET_DIR..."
# Se l'utente vuole preservare il DB SQLite, facciamo un backup temporaneo prima di pulire la cartella
PRESERVE_DB=false
if [ "$scelta_db" = "1" ] && [ "$scelta_sqlite_tipo" = "1" ] && [ -f "$TARGET_DIR/db.sqlite3" ]; then
    echo "  • Trovato database esistente in $TARGET_DIR. Creazione backup temporaneo..."
    cp "$TARGET_DIR/db.sqlite3" /tmp/db.sqlite3.bak
    PRESERVE_DB=true
fi

sudo mkdir -p "$TARGET_DIR"
sudo chown -R $USER:$USER "$TARGET_DIR"

# 3. Sincronizzazione codice Git direttamente in /opt/UNIGEST_PROJECT
echo -e "\n[3/7] Sincronizzazione del codice tramite Git..."
if [ ! -d "$TARGET_DIR/.git" ]; then
    echo "  • Cartella non inizializzata. Clonazione del codice sorgente..."
    if [ "$(ls -A "$TARGET_DIR")" ]; then
        echo "  • Pulizia file temporanei in $TARGET_DIR..."
        rm -rf "$TARGET_DIR"/*
    fi
    git clone "$REPO_URL" "$TARGET_DIR"
else
    echo "  • Cartella già inizializzata. Aggiornamento codice..."
    cd "$TARGET_DIR"
    git fetch origin
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
    git reset --hard "origin/$CURRENT_BRANCH"
fi

# Spostiamoci definitivamente nella cartella di installazione corretta
cd "$TARGET_DIR"

# Se avevamo fatto il backup del DB, lo ripristiniamo ora nella cartella aggiornata
if [ "$PRESERVE_DB" = true ]; then
    echo "  • Ripristino del database SQLite popolato in $TARGET_DIR..."
    cp /tmp/db.sqlite3.bak "$TARGET_DIR/db.sqlite3"
    rm /tmp/db.sqlite3.bak
fi

# Se l'utente ha scelto di resettare/creare un DB vuoto, cancelliamo il vecchio
if [ "$scelta_db" = "1" ] && [ "$scelta_sqlite_tipo" = "2" ]; then
    echo "  • Cancellazione del database SQLite precedente come richiesto..."
    rm -f db.sqlite3
fi

# AUTORIPARAZIONE requirements.txt
if [ -f "requirements.txt" ]; then
    if grep -q "pandas==2.1.3" requirements.txt; then
        sed -i 's/pandas==2.1.3/pandas==2.2.3/g' requirements.txt
    fi
fi

# 4. Creazione struttura cartelle interne
echo -e "\n[4/7] Creazione sotto-cartelle e file di runtime..."
mkdir -p logs backups static media core/management/commands
touch core/management/__init__.py core/management/commands/__init__.py

# 5. Configurazione Database (se MariaDB)
if [ "$scelta_db" = "2" ]; then
    echo -e "\n[5/7] Configurazione MariaDB..."
    sudo systemctl start mariadb || sudo systemctl start mysql
    sudo mysql -e "CREATE DATABASE IF NOT EXISTS unigest_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    sudo mysql -e "CREATE USER IF NOT EXISTS 'unigest_user'@'localhost' IDENTIFIED BY 'cultura';"
    sudo mysql -e "GRANT ALL PRIVILEGES ON unigest_db.* TO 'unigest_user'@'localhost';"
    sudo mysql -e "FLUSH PRIVILEGES;"
else
    echo -e "\n[5/7] Utilizzo SQLite: nessuna installazione DB necessaria."
fi

# 6. Ambiente Virtuale e Dipendenze Python
echo -e "\n[6/7] Setup ambiente virtuale Python (venv)..."
if [ -d "venv" ]; then rm -rf venv; fi
python3 -m venv venv
. venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install --no-cache-dir --only-binary=:all: numpy==2.1.0 pandas==2.2.3 Pillow==11.0.0
pip install --no-cache-dir -r requirements.txt

# Configurazione file .env
echo -e "\n[7/7] Configurazione file .env..."
if [ ! -f ".env" ]; then
    cp .env.example .env || echo "SECRET_KEY=unigest-$(date +%s)" > .env
fi

# Assicuriamo la compatibilità Unix rimuovendo caratteri CRLF (\r) da .env
tr -d '\r' < .env > .env.tmp && mv .env.tmp .env

# Aggiornamento parametri DB in .env
if [ "$scelta_db" = "1" ]; then
    echo "  • Configurazione .env per SQLite..."
    sed -i '/^DB_ENGINE=/d' .env || true
    sed -i '/^DB_NAME=/d' .env || true
    echo "DB_ENGINE=sqlite" >> .env
    echo "DB_NAME=db.sqlite3" >> .env
else
    echo "  • Configurazione .env per MariaDB..."
    sed -i '/^DB_ENGINE=/d' .env || true
    echo "DB_ENGINE=mysql" >> .env
fi

# 7. Inizializzazione Django
echo -e "\nInizializzazione del Database Django e file statici..."
python3 manage.py migrate
python3 manage.py collectstatic --noinput

echo -e "\n===================================================="
echo "   INSTALLAZIONE COMPLETATA CON SUCCESSO!"
echo "===================================================="
echo "Il progetto è stato installato in: $TARGET_DIR"
echo -e "\nPer avviare il server:"
echo "cd $TARGET_DIR"
echo ". venv/bin/activate"
echo "python3 manage.py runserver"
echo "===================================================="
