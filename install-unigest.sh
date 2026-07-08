#!/bin/bash

# UNIGEST - Script di Installazione Automatica
# Compatibile con Debian/Ubuntu

set -e # Ferma lo script in caso di errore

echo "===================================================="
echo "   UNIGEST - Installazione Gestionale"
echo "===================================================="

# 1. Aggiornamento sistema e installazione dipendenze
echo -e "\n[1/6] Installazione dipendenze di sistema..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-dev default-libmysqlclient-dev build-essential mariadb-server mariadb-client

# 2. Avvio e configurazione MariaDB/MySQL
echo -e "\n[2/6] Configurazione Database..."
sudo systemctl start mariadb || sudo systemctl start mysql

# Creazione DB e Utente (se non esistono)
# Usiamo -e per eseguire i comandi SQL direttamente
sudo mysql -e "CREATE DATABASE IF NOT EXISTS unigest_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'unigest_user'@'localhost' IDENTIFIED BY 'cultura';"
sudo mysql -e "GRANT ALL PRIVILEGES ON unigest_db.* TO 'unigest_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# 3. Creazione Ambiente Virtuale
echo -e "\n[3/6] Creazione ambiente virtuale Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 4. Installazione pacchetti Python
echo -e "\n[4/6] Installazione pacchetti Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configurazione .env (se non esiste)
echo -e "\n[5/6] Configurazione file .env..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "File .env creato da .env.example. Personalizzalo se necessario."
fi

# 6. Migrazioni Django
echo -e "\n[6/6] Esecuzione migrazioni e finalizzazione..."
python3 manage.py migrate
python3 manage.py collectstatic --noinput

echo -e "\n===================================================="
echo "   INSTALLAZIONE COMPLETATA CON SUCCESSO!"
echo "===================================================="
echo "Per avviare il server:"
echo "source venv/bin/activate"
echo "python3 manage.py runserver"
echo "===================================================="
