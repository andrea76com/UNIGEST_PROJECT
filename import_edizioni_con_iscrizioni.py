"""
UNIGEST - Import Edizioni che hanno Iscrizioni
Importa solo edizioni del vecchio DB che hanno studenti iscritti
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from core.models import *
from datetime import time

def import_edizioni_con_iscrizioni():
    print("="*70)
    print("UNIGEST - Import Edizioni con Iscrizioni")
    print("="*70)

    cursor = connections['old_database'].cursor()

    # Trova edizioni con iscrizioni che non esistono nel nuovo DB
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
            c.Note,
            COUNT(f.Matricola) as num_iscritti
        FROM TCorsiAnnualiDocenti c
        INNER JOIN TFrequenzaCorsi f ON f.Corso = c.ID
        GROUP BY c.ID, c.Anno, c.Codice, c.Descrizione, c.Quadrimestre,
                 c.Insegnante, c.Assistente, c.Vice, c.Giorni, c.Dalle, c.Alle, c.Note
        ORDER BY num_iscritti DESC
    """)

    edizioni_vecchio = cursor.fetchall()
    totale = len(edizioni_vecchio)
    print(f"   Trovate {totale} edizioni con iscrizioni nel vecchio DB")

    # Conta quante esistono già
    esistenti = EdizioneCorso.objects.filter(
        id__in=[row[0] for row in edizioni_vecchio]
    ).count()

    print(f"   Già esistenti nel nuovo DB: {esistenti}")
    print(f"   Da importare: {totale - esistenti}")

    if totale == esistenti:
        print("\n✅ Tutte le edizioni sono già state importate!")
        return

    risposta = input(f"\nVuoi importare le {totale - esistenti} edizioni mancanti? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's']:
        print("❌ Annullato")
        return

    print("\n2. Importazione edizioni...")

    importate = 0
    gia_esistenti = 0
    errori = {
        'anno': [],
        'corso': [],
        'docente': [],
        'quadrimestre': [],
        'altro': []
    }

    for row in edizioni_vecchio:
        id_edizione = row[0]

        # Salta se esiste già
        if EdizioneCorso.objects.filter(id=id_edizione).exists():
            gia_esistenti += 1
            continue

        try:
            # Converti anno
            anno_str = str(row[1]).replace('/', '-')
            anno = AnnoAccademico.objects.filter(anno=anno_str).first()
            if not anno:
                errori['anno'].append(row[1])
                continue

            # Trova corso
            corso = Corso.objects.filter(codice=row[2]).first()
            if not corso:
                errori['corso'].append(row[2])
                continue

            # Trova docente (o crea placeholder se manca)
            docente = Docente.objects.filter(id=row[5]).first()
            if not docente:
                # Crea docente placeholder
                docente = Docente.objects.create(
                    id=row[5],
                    nome=f"Docente_{row[5]}",
                    attivo=False
                )

            # Quadrimestre
            quad = Quadrimestre.objects.filter(numero=row[4]).first()
            if not quad:
                errori['quadrimestre'].append(row[4])
                continue

            # Orari (con default se mancano)
            ora_inizio = row[9] if row[9] else time(9, 0)
            ora_fine = row[10] if row[10] else time(11, 0)

            # Assistenti
            assistente_id = None
            if row[6] and Iscritto.objects.filter(matricola=row[6]).exists():
                assistente_id = row[6]

            vice_id = None
            if row[7] and Iscritto.objects.filter(matricola=row[7]).exists():
                vice_id = row[7]

            # Crea edizione
            EdizioneCorso.objects.create(
                id=id_edizione,
                anno_accademico=anno,
                corso=corso,
                quadrimestre=quad,
                descrizione_custom=row[3] or '',
                docente=docente,
                assistente_id=assistente_id,
                vice_assistente_id=vice_id,
                giorni_settimana=row[8] or '',
                ora_inizio=ora_inizio,
                ora_fine=ora_fine,
                note=row[11] or ''
            )

            importate += 1

            if importate % 100 == 0:
                print(f"   Importate {importate}...")
        except Exception as e:
            errori['altro'].append(str(e)[:100])
            # AGGIUNGI QUESTA RIGA PER VEDERE L'ERRORE:
            if len(errori['altro']) <= 5:
                print(f"   ⚠️ Errore: {e}")

    # Riepilogo
    print("\n" + "="*70)
    print("RISULTATO")
    print("="*70)
    print(f"✅ Importate: {importate}")
    print(f"⏭️  Già esistenti: {gia_esistenti}")

    if any(errori.values()):
        print(f"\nErrori:")
        if errori['anno']:
            print(f"  - Anni non trovati: {len(errori['anno'])} (es: {errori['anno'][:3]})")
        if errori['corso']:
            print(f"  - Corsi non trovati: {len(errori['corso'])} (es: {errori['corso'][:3]})")
        if errori['docente']:
            print(f"  - Docenti creati placeholder: {len(errori['docente'])}")
        if errori['altro']:
            print(f"  - Altri errori: {len(errori['altro'])}")

    print(f"\nEdizioni totali nel nuovo DB: {EdizioneCorso.objects.count()}")
    print("="*70)


if __name__ == '__main__':
    import_edizioni_con_iscrizioni()
