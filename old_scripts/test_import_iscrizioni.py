"""
Test Import Iscrizioni - Solo anno 2023-2024
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from core.models import *

print("="*70)
print("Test Import Iscrizioni 2023-2024")
print("="*70)

cursor = connections['old_database'].cursor()

# Step 1: Trova tutte le iscrizioni 2023-2024 nel vecchio DB
print("\n1. Cerca iscrizioni 2023-2024 nel vecchio DB...")
cursor.execute("""
    SELECT COUNT(*)
    FROM TFrequenzaCorsi
    WHERE AnnoAccademico IN ('2023/2024', '2023-2024')
""")
totale_vecchio = cursor.fetchone()[0]
print(f"   Trovate: {totale_vecchio}")

# Step 2: Verifica anno nel nuovo DB
print("\n2. Verifica anno accademico nel nuovo DB...")
anno = AnnoAccademico.objects.filter(anno='2023-2024').first()
if not anno:
    print("   ❌ Anno 2023-2024 non trovato!")
    exit(1)
print(f"   ✅ Anno trovato: {anno.anno} (ID: {anno.id})")

# Step 3: Conta edizioni
print("\n3. Conta edizioni 2023-2024...")
edizioni_count = EdizioneCorso.objects.filter(anno_accademico=anno).count()
print(f"   Edizioni: {edizioni_count}")

# Step 4: Mostra prima edizione
edizione_test = EdizioneCorso.objects.filter(anno_accademico=anno).first()
if edizione_test:
    print(f"   Prima edizione: ID={edizione_test.id}, Corso={edizione_test.corso.nome} (Codice={edizione_test.corso.codice})")

    # Cerca iscrizioni per questa edizione nel vecchio DB
    cursor.execute(f"""
        SELECT Matricola, Ricevuta, Data
        FROM TFrequenzaCorsi
        WHERE AnnoAccademico IN ('2023/2024', '2023-2024')
        AND Corso = {edizione_test.corso.codice}
        LIMIT 3
    """)

    print(f"\n4. Iscrizioni per questo corso nel vecchio DB:")
    rows = cursor.fetchall()
    print(f"   Trovate: {len(rows)}")
    for row in rows:
        print(f"   - Matricola: {row[0]}, Ricevuta: {row[1]}")

    # Step 5: Prova a importarle
    print(f"\n5. Provo a importare queste {len(rows)} iscrizioni...")
    importate = 0
    for row in rows:
        try:
            iscritto = Iscritto.objects.filter(matricola=row[0]).first()
            if not iscritto:
                print(f"   ⚠️ Iscritto {row[0]} non trovato")
                continue

            iscr, created = IscrizioneCorso.objects.get_or_create(
                anno_accademico=anno,
                edizione_corso=edizione_test,
                iscritto=iscritto,
                defaults={
                    'numero_ricevuta': row[1],
                    'data_iscrizione': row[2] if row[2] else anno.data_inizio
                }
            )

            if created:
                importate += 1
                print(f"   ✅ Importato: {iscritto.nominativo}")
            else:
                print(f"   ⏭️  Già esistente: {iscritto.nominativo}")

        except Exception as e:
            print(f"   ❌ Errore: {e}")

    print(f"\n   Importate: {importate}")

    # Verifica
    print(f"\n6. Verifica finale:")
    count = IscrizioneCorso.objects.filter(
        anno_accademico=anno,
        edizione_corso=edizione_test
    ).count()
    print(f"   Iscrizioni nel nuovo DB per questo corso: {count}")

else:
    print("   ❌ Nessuna edizione trovata!")

print("\n" + "="*70)
