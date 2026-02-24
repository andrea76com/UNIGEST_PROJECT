# UNIGEST - Gestionale Università degli Adulti

Sistema di gestione completo per l'Università degli Adulti, sviluppato con Django e MySQL.

## 📋 Indice

- [Caratteristiche](#caratteristiche)
- [Requisiti](#requisiti)
- [Installazione](#installazione)
- [Configurazione](#configurazione)
- [Migrazione Dati](#migrazione-dati)
- [Utilizzo](#utilizzo)
- [Struttura Progetto](#struttura-progetto)
- [Manutenzione](#manutenzione)

---

## ✨ Caratteristiche

### Anagrafiche
- **Iscritti**: Gestione completa anagrafica studenti con storico corsi
- **Docenti**: Anagrafica docenti con corsi tenuti
- **Autorità**: Gestione cariche istituzionali

### Corsi
- Catalogo corsi master con categorie (Culturali, Laboratori, Lingue, Altri)
- Edizioni corsi per anno accademico e quadrimestre
- Assegnazione docenti e assistenti
- Gestione orari e calendario

### Iscrizioni
- Iscrizione annuale all'università
- Iscrizione ai singoli corsi
- Storico iscrizioni per statistiche

### Lezioni e Presenze
- Registro lezioni con data, orario e argomenti
- Foglio presenze per ogni lezione
- Calcolo automatico presenze

### Report
- Fogli presenze per corso
- Elenchi iscritti
- Statistiche per anno accademico
- Export in PDF ed Excel

---

## 💻 Requisiti

- **Sistema Operativo**: Debian/Ubuntu Linux
- **Python**: 3.9 o superiore
- **MySQL**: 5.7 o superiore
- **VSCode**: (opzionale) per lo sviluppo

---

## 🚀 Installazione

### 1. Clona o crea la directory del progetto

```bash
mkdir ~/UNIGEST_PROJECT
cd ~/UNIGEST_PROJECT
```

### 2. Crea ambiente virtuale Python

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installa le dipendenze

Crea il file `requirements.txt` e installa:

```bash
pip install -r requirements.txt
```

### 4. Crea il progetto Django

```bash
django-admin startproject config .
python manage.py startapp core
```

### 5. Copia i file forniti

Copia tutti i file Python, HTML, CSS e JS nelle rispettive directory secondo la struttura fornita.

### 6. Crea le cartelle necessarie

```bash
mkdir -p logs backups static media
mkdir -p core/templates/anagrafiche
mkdir -p core/templates/corsi
mkdir -p core/templates/iscrizioni
mkdir -p core/templates/lezioni
mkdir -p core/templates/report
mkdir -p core/static/css
mkdir -p core/static/js
mkdir -p core/management/commands
```

### 7. Crea i file `__init__.py`

```bash
touch core/management/__init__.py
touch core/management/commands/__init__.py
```

---

## ⚙️ Configurazione

### 1. Configura MySQL

Crea il database MySQL:

```sql
CREATE DATABASE unigest_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'unigest_user'@'localhost' IDENTIFIED BY 'tua_password_sicura';
GRANT ALL PRIVILEGES ON unigest_db.* TO 'unigest_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Configura il file `.env`

Modifica il file `.env` nella root del progetto:

```bash
SECRET_KEY=django-insecure-GENERA-UNA-CHIAVE-SICURA
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=unigest_db
DB_USER=unigest_user
DB_PASSWORD=tua_password_sicura
DB_HOST=localhost
DB_PORT=3306

# Database vecchio (per migrazione)
OLD_DB_NAME=vecchio_database
OLD_DB_USER=root
OLD_DB_PASSWORD=password_mysql
```

**Per generare una SECRET_KEY sicura:**

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 3. Esegui le migrazioni

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Crea un superuser

```bash
python manage.py createsuperuser
```

Segui le istruzioni per creare l'utente amministratore.

### 5. Raccogli i file statici

```bash
python manage.py collectstatic
```

---

## 🔄 Migrazione Dati

### Importa dal vecchio database

Se hai già un database MySQL importato da Access, usa lo script di migrazione:

```bash
# Test (dry-run, non salva i dati)
python manage.py import_old_data --dry-run --verbose

# Importazione reale
python manage.py import_old_data --verbose
```

Lo script importerà automaticamente:
- ✅ Comuni e tabelle di supporto
- ✅ Anagrafiche (iscritti, docenti, autorità)
- ✅ Corsi e categorie
- ✅ Anni accademici ed edizioni
- ✅ Iscrizioni e lezioni

### Popola dati di base manualmente

Se parti da zero, accedi all'admin Django e crea:

1. **Quadrimestri** (1° e 2°)
2. **Categorie Corsi** (Culturali, Laboratori, Lingue, Altri)
3. **Anno Accademico** corrente
4. Poi inizia ad aggiungere iscritti e corsi

---

## 🎯 Utilizzo

### Avvia il server di sviluppo

```bash
python manage.py runserver
```

Apri il browser su: **http://localhost:8000/unigest/**

### Accedi all'admin Django

**http://localhost:8000/admin/**

Usa le credenziali del superuser creato.

### Menu Principale

L'applicazione ha 5 sezioni principali:

1. **Anagrafiche** → Gestione iscritti, docenti, autorità
2. **Corsi** → Catalogo corsi ed edizioni annuali
3. **Iscrizioni** → Iscrizioni anno e corsi
4. **Lezioni** → Registro lezioni e presenze
5. **Report** → Stampe e statistiche

---

## 📂 Struttura Progetto

```
UNIGEST_PROJECT/
├── config/                 # Configurazione Django
│   ├── settings.py        # Impostazioni progetto
│   ├── urls.py            # URL principali
│   └── wsgi.py
├── core/                   # App principale
│   ├── management/
│   │   └── commands/
│   │       └── import_old_data.py  # Script migrazione
│   ├── migrations/        # Migrazioni database
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css  # Stili personalizzati
│   │   └── js/
│   │       └── script.js  # JavaScript
│   ├── templates/         # Template HTML
│   │   ├── base.html      # Template base
│   │   ├── home.html      # Homepage
│   │   ├── anagrafiche/   # Template anagrafiche
│   │   ├── corsi/         # Template corsi
│   │   ├── iscrizioni/    # Template iscrizioni
│   │   ├── lezioni/       # Template lezioni
│   │   └── report/        # Template report
│   ├── admin.py           # Interfaccia admin
│   ├── models.py          # Modelli database
│   ├── views.py           # Viste applicazione
│   ├── forms.py           # Form Django
│   └── urls.py            # URL app core
├── logs/                   # File di log
├── backups/               # Backup database
├── media/                 # Upload utenti
├── static/                # File statici globali
├── venv/                  # Ambiente virtuale Python
├── .env                   # Configurazioni sensibili
├── manage.py              # Script gestione Django
├── requirements.txt       # Dipendenze Python
└── README.md             # Questo file
```

---

## 🛠️ Manutenzione

### Backup Database

```bash
# Backup manuale
python manage.py dbbackup

# Ripristino
python manage.py dbrestore
```

### Verifica integrità dati

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

### Log applicazione

I log vengono salvati in `logs/unigest.log`

```bash
tail -f logs/unigest.log
```

### Pulizia file statici

```bash
python manage.py collectstatic --noinput --clear
```

---

## 🐛 Risoluzione Problemi

### Errore connessione MySQL

Verifica che MySQL sia in esecuzione:

```bash
sudo systemctl status mysql
```

Verifica credenziali in `.env`

### Errore import mysqlclient

Installa le dipendenze di sistema:

```bash
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient
```

### Template non trovati

Verifica che le cartelle template esistano:

```bash
ls -la core/templates/
```

### Static files non caricati

```bash
python manage.py collectstatic
python manage.py runserver --insecure  # Solo in sviluppo
```

---

## 📚 Risorse Utili

- **Django Documentation**: https://docs.djangoproject.com/
- **Bootstrap 5**: https://getbootstrap.com/docs/5.3/
- **Bootstrap Icons**: https://icons.getbootstrap.com/

---

## 📝 Note Sviluppo

### Convenzioni Codice

- **Lingua**: Codice in inglese, commenti e UI in italiano
- **Style**: PEP 8 per Python, Prettier per HTML/CSS/JS
- **Git**: Commit descrittivi in italiano

### TODO Future Implementazioni

- [ ] Generazione PDF report con ReportLab
- [ ] Export Excel con openpyxl
- [ ] Invio email automatiche
- [ ] Dashboard statistiche avanzate con grafici
- [ ] API REST per integrazioni
- [ ] App mobile companion

---

## 👨‍💻 Autore

Sviluppato per l'Università degli Adulti

---

## 📄 Licenza

Uso interno - Tutti i diritti riservati

---

## 🆘 Supporto

Per problemi o domande, contattare il reparto IT.

---

**Versione**: 1.0.0  
**Data**: Novembre 2024  
**Django**: 4.2.7  
**Python**: 3.9+
