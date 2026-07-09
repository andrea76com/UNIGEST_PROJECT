#!/bin/bash

# Funzione per attendere che il database sia pronto
wait_for_db() {
    echo "In attesa del database MariaDB..."
    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 1
    done
    echo "Database pronto!"
}

# Attendi il DB
wait_for_db

# Applica le migrazioni
echo "Applicazione delle migrazioni..."
python manage.py migrate --noinput

# Colleziona i file statici
echo "Collezione dei file statici..."
python manage.py collectstatic --noinput

# Crea le cartelle necessarie se mancano
mkdir -p logs static media

# Avvia il server Gunicorn
echo "Avvio di Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --access-logfile /app/logs/gunicorn-access.log \
    --error-logfile /app/logs/gunicorn-error.log
