"""
UNIGEST - Import Iscrizioni DEFINITIVO
Usa TCorsiAnnualiDocenti.ID invece di TCorsi.Codice
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from core.models import *

def import_iscrizioni():
    print("="*70)
    print("UNIGEST - Import Iscrizioni DEFINITIVO")
    print("="*70)

    cursor = connections['old_database'].cursor()

    # Query CORRETTA con JOIN
    print("\n1. Carico iscrizioni dal vecchio DB...")
    cursor.execute("""
        SELECT
            f.AnnoAccademico,
            f.Corso as ID_Edizione_Vecchia,
            c.Codice as Codice_Corso_Vero,
            f.Matricola,
            f.Ricevuta,
            f.Data
        FROM TFrequenzaCorsi f
        INNER JOIN TCorsiAnnualiDocenti c ON f.Corso = c.ID
        ORDER BY f.AnnoAccademico DESC
    """)

    records = cursor.fetchall()
    totale = len(records)
    print(f"   Trovati {totale} record")

    if totale == 0:
        print("❌ Nessuna iscrizione da importare!")
        return

    # Mostra esempi
    print("\n2. Prime 3 iscrizioni:")
    for i, row in enumerate(records[:3]):
        print(f"   Anno: {row[0]}, Corso: {row[2]}, Matricola: {row[3]}")

    risposta = input(f"\nVuoi importare {totale} iscrizioni? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's']:
        print("❌ Annullato")
        return

    print("\n3. Importazione in corso...")

    importate = 0
    errori = {
        'anno_non_trovato': 0,
        'corso_non_trovato': 0,
        'iscritto_non_trovato': 0,
        'edizione_non_trovata': 0,
        'altro': 0
    }

    for i, row in enumerate(records):
        anno_vecchio = row[0]
        id_edizione_vecchia = row[1]
        codice_corso_vero = row[2]
        matricola = row[3]
        ricevuta = row[4]
        data = row[5]

        try:
            # Converti anno
            anno_str = str(anno_vecchio).replace('/', '-')
            anno = AnnoAccademico.objects.filter(anno=anno_str).first()
            if not anno:
                errori['anno_non_trovato'] += 1
                continue

            # Trova corso
            corso = Corso.objects.filter(codice=codice_corso_vero).first()
            if not corso:
                errori['corso_non_trovato'] += 1
                continue

            # Trova edizione
            edizione = EdizioneCorso.objects.filter(
                anno_accademico=anno,
                corso=corso
            ).first()

            if not edizione:
                errori['edizione_non_trovata'] += 1
                continue

            # Trova iscritto
            iscritto = Iscritto.objects.filter(matricola=matricola).first()
            if not iscritto:
                errori['iscritto_non_trovato'] += 1
                continue

            # Crea iscrizione
            _, created = IscrizioneCorso.objects.get_or_create(
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

                # Progress
                if importate % 500 == 0:
                    perc = (i + 1) / totale * 100
                    print(f"   Progresso: {i+1}/{totale} ({perc:.1f}%) - Importate: {importate}")

        except Exception as e:
            errori['altro'] += 1
            if errori['altro'] <= 3:
                print(f"   ⚠️ Errore: {e}")

    # Riepilogo
    print("\n" + "="*70)
    print("RISULTATO FINALE")
    print("="*70)
    print(f"✅ Importate: {importate}")
    print(f"\nErrori:")
    print(f"  - Anni non trovati: {errori['anno_non_trovato']}")
    print(f"  - Corsi non trovati: {errori['corso_non_trovato']}")
    print(f"  - Iscritti non trovati: {errori['iscritto_non_trovato']}")
    print(f"  - Edizioni non trovate: {errori['edizione_non_trovata']}")
    print(f"  - Altri errori: {errori['altro']}")

    # Verifica
    print("\n" + "="*70)
    print("VERIFICA DATABASE")
    print("="*70)
    print(f"Iscrizioni totali: {IscrizioneCorso.objects.count()}")

    # Verifica per anno
    anno_2023 = AnnoAccademico.objects.filter(anno='2023-2024').first()
    if anno_2023:
        count = IscrizioneCorso.objects.filter(anno_accademico=anno_2023).count()
        print(f"Iscrizioni 2023-2024: {count}")

    print("="*70)


if __name__ == '__main__':
    import_iscrizioni()
