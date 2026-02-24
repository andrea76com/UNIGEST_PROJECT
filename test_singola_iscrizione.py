"""
Test: Prova a importare UNA SOLA iscrizione manualmente
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from core.models import *

print("="*70)
print("TEST: Import di UNA SINGOLA iscrizione")
print("="*70)

cursor = connections['old_database'].cursor()

# 1. Prendi TUTTE le iscrizioni 2023/2024
cursor.execute("""
    SELECT Corso, Matricola, Ricevuta, Data
    FROM TFrequenzaCorsi
    WHERE AnnoAccademico = '2023/2024'
    LIMIT 100
""")

iscrizioni = cursor.fetchall()
print(f"\n1. Trovate {len(iscrizioni)} iscrizioni nel vecchio DB")

if not iscrizioni:
    print("❌ Nessuna iscrizione trovata!")
    exit(1)

# 2. Anno nel nuovo DB
anno = AnnoAccademico.objects.get(anno='2023-2024')
print(f"\n2. Anno nel nuovo DB: {anno.anno} (ID: {anno.id})")

# 3. Edizioni disponibili
edizioni = EdizioneCorso.objects.filter(anno_accademico=anno)
print(f"\n3. Edizioni disponibili: {edizioni.count()}")

# Crea dizionario codice_corso -> edizione
mappa_edizioni = {}
for ed in edizioni:
    mappa_edizioni[ed.corso.codice] = ed
    print(f"   Codice {ed.corso.codice}: {ed.corso.nome}")

# 4. Prova a importare
print(f"\n4. Tento import di {len(iscrizioni)} iscrizioni...")

importate = 0
errori = {
    'corso_non_trovato': [],
    'iscritto_non_trovato': [],
    'edizione_non_trovata': [],
    'altro': []
}

for row in iscrizioni:
    codice_corso = row[0]
    matricola = row[1]
    ricevuta = row[2]
    data = row[3]

    # Trova edizione
    if codice_corso not in mappa_edizioni:
        errori['edizione_non_trovata'].append(codice_corso)
        continue

    edizione = mappa_edizioni[codice_corso]

    # Trova iscritto
    iscritto = Iscritto.objects.filter(matricola=matricola).first()
    if not iscritto:
        errori['iscritto_non_trovato'].append(matricola)
        continue

    # Crea iscrizione
    try:
        iscr, created = IscrizioneCorso.objects.get_or_create(
            anno_accademico=anno,
            edizione_corso=edizione,
            iscritto=iscritto,
            defaults={
                'numero_ricevuta': ricevuta,
                'data_iscrizione': data if data else anno.data_inizio
            }
        )

        if created:
            importate += 1
            if importate <= 3:
                print(f"   ✅ {iscritto.nominativo} -> {edizione.corso.nome}")

    except Exception as e:
        errori['altro'].append(str(e))

print(f"\n5. RISULTATO:")
print(f"   ✅ Importate: {importate}")
print(f"   ❌ Edizioni non trovate: {len(errori['edizione_non_trovata'])} (codici: {set(errori['edizione_non_trovata'])})")
print(f"   ❌ Iscritti non trovati: {len(errori['iscritto_non_trovato'])}")
print(f"   ❌ Altri errori: {len(errori['altro'])}")

# 6. Verifica nel DB
count = IscrizioneCorso.objects.filter(anno_accademico=anno).count()
print(f"\n6. Iscrizioni 2023-2024 nel nuovo DB: {count}")

print("="*70)
