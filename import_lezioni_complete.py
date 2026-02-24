"""
UNIGEST - Import Lezioni Complete
Importa tutte le lezioni per le edizioni esistenti
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from core.models import *

def import_lezioni():
    print("="*70)
    print("UNIGEST - Import Lezioni")
    print("="*70)

    cursor = connections['old_database'].cursor()

    # 1. Conta lezioni nel vecchio DB
    cursor.execute("SELECT COUNT(*) FROM TPresenzeCorsisti")
    totale_vecchio = cursor.fetchone()[0]
    print(f"\n1. Lezioni nel vecchio DB: {totale_vecchio}")

    # 2. Conta lezioni per edizioni importate
    edizioni_ids = list(EdizioneCorso.objects.values_list('id', flat=True))
    print(f"\n2. Edizioni nel nuovo DB: {len(edizioni_ids)}")

    if not edizioni_ids:
        print("❌ Nessuna edizione trovata!")
        return

    # Query in batch (MySQL ha limite su IN clause)
    batch_size = 1000
    totale_importabili = 0

    for i in range(0, len(edizioni_ids), batch_size):
        batch = edizioni_ids[i:i+batch_size]
        ids_str = ','.join(str(id) for id in batch)

        cursor.execute(f"""
            SELECT COUNT(*)
            FROM TPresenzeCorsisti
            WHERE ID_corso_annuale IN ({ids_str})
        """)
        totale_importabili += cursor.fetchone()[0]

    print(f"   Lezioni importabili: {totale_importabili}")
    print(f"   Lezioni già importate: {Lezione.objects.count()}")

    if totale_importabili == 0:
        print("\n❌ Nessuna lezione da importare!")
        return

    risposta = input(f"\nVuoi importare {totale_importabili} lezioni? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's']:
        return

    print("\n3. Importazione lezioni...")

    importate = 0
    duplicate = 0
    errori = 0

    # Import in batch
    for i in range(0, len(edizioni_ids), batch_size):
        batch = edizioni_ids[i:i+batch_size]
        ids_str = ','.join(str(id) for id in batch)

        cursor.execute(f"""
            SELECT ID_corso_annuale, data, corso, descrizione,
                   insegnante, presenze, ore, annoacc
            FROM TPresenzeCorsisti
            WHERE ID_corso_annuale IN ({ids_str})
        """)

        for row in cursor.fetchall():
            try:
                id_edizione = row[0]
                data_lezione = row[1]

                if not data_lezione:
                    errori += 1
                    continue

                # Trova edizione
                edizione = EdizioneCorso.objects.filter(id=id_edizione).first()
                if not edizione:
                    errori += 1
                    continue

                # Trova docente (opzionale)
                id_docente = row[4]
                docente = None
                if id_docente and id_docente > 0:
                    docente = Docente.objects.filter(id=id_docente).first()

                if not docente:
                    docente = edizione.docente

                # Ore lezione
                ore_str = str(row[6]) if row[6] else '2'
                ore_str = ore_str.replace(',', '.')
                try:
                    ore = float(ore_str)
                except:
                    ore = 2.0

                # Crea lezione
                _, created = Lezione.objects.get_or_create(
                    edizione_corso=edizione,
                    data_lezione=data_lezione,
                    defaults={
                        'descrizione': row[3] or '',
                        'docente': docente,
                        'numero_presenti': row[5] or 0,
                        'ore_lezione': ore
                    }
                )

                if created:
                    importate += 1
                else:
                    duplicate += 1

                # Progress
                if importate % 500 == 0 and importate > 0:
                    perc = (importate / totale_importabili) * 100
                    print(f"   Importate: {importate}/{totale_importabili} ({perc:.1f}%)")

            except Exception as e:
                errori += 1
                if errori <= 3:
                    print(f"   ⚠️ Errore: {e}")

    # Risultato
    print("\n" + "="*70)
    print("RISULTATO")
    print("="*70)
    print(f"✅ Importate: {importate}")
    print(f"⏭️  Duplicate: {duplicate}")
    print(f"❌ Errori: {errori}")
    print(f"\n📊 Lezioni totali: {Lezione.objects.count()}")
    print("="*70)


if __name__ == '__main__':
    import_lezioni()
