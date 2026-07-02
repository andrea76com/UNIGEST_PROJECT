"""
Import Edizioni SENZA forzare ID
Lascia che Django generi gli ID automaticamente
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from core.models import *
from datetime import time

def import_edizioni():
    print("="*70)
    print("UNIGEST - Import Edizioni SENZA ID Fisso")
    print("="*70)

    cursor = connections['old_database'].cursor()

    print("\n1. Cerco edizioni con iscrizioni...")
    cursor.execute("""
        SELECT DISTINCT
            c.ID,
            c.Anno,
            c.Codice,
            c.Descrizione,
            c.Quadrimestre,
            c.Insegnante,
            c.Assistente,
            c.Vice,
            c.Giorni,
            c.Dalle,
            c.Alle,
            c.Note
        FROM TCorsiAnnualiDocenti c
        INNER JOIN TFrequenzaCorsi f ON f.Corso = c.ID
        GROUP BY c.ID, c.Anno, c.Codice, c.Descrizione, c.Quadrimestre,
                 c.Insegnante, c.Assistente, c.Vice, c.Giorni, c.Dalle, c.Alle, c.Note
    """)

    edizioni = cursor.fetchall()
    print(f"   Trovate {len(edizioni)} edizioni")

    risposta = input("\nVuoi procedere? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's']:
        return

    print("\n2. Importazione...")

    # Crea mappa ID vecchio -> ID nuovo
    mappa_id = {}
    importate = 0
    errori = []

    for row in edizioni:
        id_vecchio = row[0]

        try:
            # Converti anno
            anno_str = str(row[1]).replace('/', '-')
            anno = AnnoAccademico.objects.filter(anno=anno_str).first()
            if not anno:
                continue

            # Corso
            corso = Corso.objects.filter(codice=row[2]).first()
            if not corso:
                continue

            # Verifica se esiste già questa combinazione
            edizione_esistente = EdizioneCorso.objects.filter(
                anno_accademico=anno,
                corso=corso,
                quadrimestre__numero=row[4]
            ).first()

            if edizione_esistente:
                # Usa quella esistente
                mappa_id[id_vecchio] = edizione_esistente.id
                continue

            # Docente (con placeholder se manca)
            docente = Docente.objects.filter(id=row[5]).first()
            if not docente:
                docente, _ = Docente.objects.get_or_create(
                    id=row[5],
                    defaults={'nome': f'Docente_{row[5]}', 'attivo': False}
                )

            # Quadrimestre
            quad = Quadrimestre.objects.filter(numero=row[4]).first()
            if not quad:
                continue

            # Orari
            ora_inizio = row[9] if row[9] else time(9, 0)
            ora_fine = row[10] if row[10] else time(11, 0)

            # Crea edizione SENZA specificare ID
            nuova_edizione = EdizioneCorso.objects.create(
                anno_accademico=anno,
                corso=corso,
                quadrimestre=quad,
                descrizione_custom=row[3] or '',
                docente=docente,
                assistente_id=row[6] if row[6] and Iscritto.objects.filter(matricola=row[6]).exists() else None,
                vice_assistente_id=row[7] if row[7] and Iscritto.objects.filter(matricola=row[7]).exists() else None,
                giorni_settimana=row[8] or '',
                ora_inizio=ora_inizio,
                ora_fine=ora_fine,
                note=row[11] or ''
            )

            # Salva mapping
            mappa_id[id_vecchio] = nuova_edizione.id
            importate += 1

            if importate % 100 == 0:
                print(f"   {importate}...")

        except Exception as e:
            if len(errori) < 5:
                print(f"   ⚠️ Errore: {e}")
            errori.append(str(e))

    print(f"\n✅ {importate} edizioni importate")
    print(f"❌ {len(errori)} errori")

    # Salva mappa per reimportare iscrizioni
    print("\n3. Salvo mappa ID vecchi -> nuovi...")
    with open('mappa_edizioni.txt', 'w') as f:
        for vecchio, nuovo in mappa_id.items():
            f.write(f"{vecchio},{nuovo}\n")

    print(f"✅ Salvati {len(mappa_id)} mapping in mappa_edizioni.txt")
    print(f"\nEdizioni totali: {EdizioneCorso.objects.count()}")


if __name__ == '__main__':
    import_edizioni()
