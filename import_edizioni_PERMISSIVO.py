"""
Import Edizioni PERMISSIVO
Importa TUTTE le edizioni anche con dati mancanti/anomali
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from core.models import *
from datetime import time

def normalizza_ora(ora_str):
    """Normalizza formato orari"""
    if not ora_str:
        return None

    ora_str = str(ora_str).strip().replace(',', ':').replace('.', ':')
    parti = ora_str.split(':')

    try:
        ore = int(parti[0])
        minuti = int(parti[1]) if len(parti) > 1 else 0
        if 0 <= ore <= 23 and 0 <= minuti <= 59:
            return time(ore, minuti)
    except:
        pass
    return None


def import_edizioni_permissivo():
    print("="*70)
    print("UNIGEST - Import Edizioni PERMISSIVO")
    print("="*70)

    cursor = connections['old_database'].cursor()

    # Prendi TUTTE le edizioni con iscrizioni (anche con problemi)
    print("\n1. Cerco TUTTE le edizioni con iscrizioni...")
    cursor.execute("""
        SELECT DISTINCT
            c.ID, c.Anno, c.Codice, c.Descrizione, c.Quadrimestre,
            c.Insegnante, c.Assistente, c.Vice, c.Giorni,
            c.Dalle, c.Alle, c.Note
        FROM TCorsiAnnualiDocenti c
        INNER JOIN TFrequenzaCorsi f ON f.Corso = c.ID
        WHERE c.ID > 0
    """)

    edizioni = cursor.fetchall()
    print(f"   Trovate: {len(edizioni)}")

    risposta = input("\nImporta TUTTE (anche con dati anomali)? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's']:
        return

    print("\n2. Importazione PERMISSIVA...")

    importate = 0
    errori = []
    docenti_creati = 0
    quadrimestri_creati = 0

    for row in edizioni:
        id_ed = row[0]

        # Skip se esiste già
        if EdizioneCorso.objects.filter(id=id_ed).exists():
            continue

        try:
            # Anno (OBBLIGATORIO)
            anno_str = str(row[1]).replace('/', '-')
            anno = AnnoAccademico.objects.filter(anno=anno_str).first()
            if not anno:
                continue

            # Corso (OBBLIGATORIO)
            codice_corso = row[2] if row[2] and row[2] != 0 else None
            if not codice_corso:
                continue

            corso = Corso.objects.filter(codice=codice_corso).first()
            if not corso:
                continue

            # Quadrimestre (PERMISSIVO - crea se non esiste)
            quad_num = row[4] if row[4] else 1
            quad = Quadrimestre.objects.filter(numero=quad_num).first()
            if not quad:
                # Crea quadrimestre non standard
                quad = Quadrimestre.objects.create(numero=quad_num)
                quadrimestri_creati += 1
                print(f"   ✨ Creato Quadrimestre {quad_num}")

            # Docente (PERMISSIVO - crea placeholder se manca)
            id_docente = row[5] if row[5] and row[5] != 0 else None
            if not id_docente:
                # Usa docente generico
                id_docente = 9999

            docente = Docente.objects.filter(id=id_docente).first()
            if not docente:
                docente = Docente.objects.create(
                    id=id_docente,
                    nome=f'Docente_{id_docente}',
                    attivo=False
                )
                docenti_creati += 1

            # Assistenti (opzionali)
            ass_id = row[6] if row[6] and row[6] != 0 and Iscritto.objects.filter(matricola=row[6]).exists() else None
            vice_id = row[7] if row[7] and row[7] != 0 and Iscritto.objects.filter(matricola=row[7]).exists() else None

            # Orari (con default)
            ora_in = normalizza_ora(row[9]) or time(9, 0)
            ora_fi = normalizza_ora(row[10]) or time(11, 0)

            # Crea edizione
            EdizioneCorso.objects.create(
                id=id_ed,
                anno_accademico=anno,
                corso=corso,
                quadrimestre=quad,
                descrizione_custom=row[3] or '',
                docente=docente,
                assistente_id=ass_id,
                vice_assistente_id=vice_id,
                giorni_settimana=row[8] or '',
                ora_inizio=ora_in,
                ora_fine=ora_fi,
                note=row[11] or ''
            )

            importate += 1

            if importate % 100 == 0:
                print(f"   Importate: {importate}")

        except Exception as e:
            errori.append(str(e)[:100])
            if len(errori) <= 3:
                print(f"   ⚠️ {e}")

    print("\n" + "="*70)
    print("RISULTATO")
    print("="*70)
    print(f"✅ Edizioni importate: {importate}")
    print(f"✨ Docenti placeholder creati: {docenti_creati}")
    print(f"✨ Quadrimestri creati: {quadrimestri_creati}")
    print(f"❌ Errori: {len(errori)}")
    print(f"\n📊 Edizioni totali: {EdizioneCorso.objects.count()}")
    print("="*70)


if __name__ == '__main__':
    import_edizioni_permissivo()
