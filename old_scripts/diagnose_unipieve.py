import os
import django
from django.db import connections

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_table(table_name):
    print(f"\n--- Tabella: {table_name} ---")
    try:
        cursor = connections['old_database'].cursor()
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        count = cursor.fetchone()[0]
        print(f"Righe presenti: {count}")

        if count > 0:
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 1")
            columns = [col[0] for col in cursor.description]
            print(f"Colonne trovate: {', '.join(columns)}")
            row = cursor.fetchone()
            print(f"Esempio dati: {row}")
        else:
            # Check structure anyway
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"Tabella VUOTA. Colonne: {', '.join(columns)}")

    except Exception as e:
        print(f"ERRORE su {table_name}: {e}")

tables = [
    'TCategorie', 'TGruppi', 'TCorsi',
    'TCorsiAnnualiDocenti', 'TFrequenzaCorsi',
    'TPresenzeCorsisti', 'TAnnoAccademico',
    'TAnagrafe', 'TDocenti'
]

print("=== DIAGNOSTICA DATABASE UNIPIEVE ===")
for t in tables:
    check_table(t)
