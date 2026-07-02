"""
Import Edizioni - FIX Formato Orari
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
    """
    Converte vari formati orari in time object
    Input: "9,15", "9", "9.00", " 9,15", "09:15"
    Output: time(9, 15)
    """
    if not ora_str:
        return None

    # Pulisci stringa
    ora_str = str(ora_str).strip()

    # Sostituisci separatori
    ora_str = ora_str.replace(',', ':')
    ora_str = ora_str.replace('.', ':')

    # Split
    parti = ora_str.split(':')

    try:
        ore = int(parti[0])
        minuti = int(parti[1]) if len(parti) > 1 else 0

        # Validazione
        if ore < 0 or ore > 23:
            return None
        if minuti < 0 or minuti > 59:
            return None

        return time(ore, minuti)
    except:
        return None


def import_edizioni():
    print("="*70)
    print("UNIGEST - Import Edizioni FINALE (con fix orari)")
    print("="*70)

    cursor = connections['old_database'].cursor()

    print("\n1. Cerco edizioni valide...")
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
        WHERE c.ID > 0
        AND c.Codice > 0
        AND c.Insegnante > 0
        GROUP BY c.ID, c.Anno, c.Codice, c.Descrizione, c.Quadrimestre,
                 c.Insegnante, c.Assistente, c.Vice, c.Giorni, c.Dalle, c.Alle, c.Note
    """)

    edizioni = cursor.fetchall()
    print(f"   Trovate {len(edizioni)} edizioni valide")

    # Test normalizzazione orari
    print("\n2. Test normalizzazione orari (primi 3):")
    for row in edizioni[:3]:
        ora_inizio_str = row[9]
        ora_fine_str = row[10]
        ora_in = normalizza_ora(ora_inizio_str)
        ora_fi = normalizza_ora(ora_fine_str)
        print(f"   '{ora_inizio_str}' -> {ora_in}, '{ora_fine_str}' -> {ora_fi}")

    risposta = input("\nVuoi procedere? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's']:
        return

    print("\n3. Importazione...")

    importate = 0
    saltate = 0
    errori = []
    errori_orario = 0

    for row in edizioni:
        id_vecchio = row[0]

        # SKIP se ID invalido
        if not id_vecchio or id_vecchio == 0:
            saltate += 1
            continue

        try:
            # Anno
            anno_str = str(row[1]).replace('/', '-')
            anno = AnnoAccademico.objects.filter(anno=anno_str).first()
            if not anno:
                saltate += 1
                continue

            # Corso
            codice_corso = row[2]
            if not codice_corso or codice_corso == 0:
                saltate += 1
                continue

            corso = Corso.objects.filter(codice=codice_corso).first()
            if not corso:
                saltate += 1
                continue

            # Quadrimestre
            quad_num = row[4]
            if not quad_num or quad_num == 0:
                saltate += 1
                continue

            quad = Quadrimestre.objects.filter(numero=quad_num).first()
            if not quad:
                saltate += 1
                continue

            # Verifica duplicati
            edizione_esistente = EdizioneCorso.objects.filter(
                anno_accademico=anno,
                corso=corso,
                quadrimestre=quad,
                giorni_settimana=row[8] or ''
            ).first()

            if edizione_esistente:
                saltate += 1
                continue

            # Docente
            id_docente = row[5]
            if not id_docente or id_docente == 0:
                saltate += 1
                continue

            docente = Docente.objects.filter(id=id_docente).first()
            if not docente:
                try:
                    docente = Docente.objects.create(
                        id=id_docente,
                        nome=f'Docente_{id_docente}',
                        attivo=False
                    )
                except:
                    saltate += 1
                    continue

            # Assistenti
            assistente_id = row[6] if row[6] and row[6] != 0 else None
            if assistente_id and not Iscritto.objects.filter(matricola=assistente_id).exists():
                assistente_id = None

            vice_id = row[7] if row[7] and row[7] != 0 else None
            if vice_id and not Iscritto.objects.filter(matricola=vice_id).exists():
                vice_id = None

            # Orari (NORMALIZZATI)
            ora_inizio = normalizza_ora(row[9])
            ora_fine = normalizza_ora(row[10])

            # Se orari invalidi, usa default
            if not ora_inizio:
                ora_inizio = time(9, 0)
                errori_orario += 1

            if not ora_fine:
                ora_fine = time(11, 0)
                errori_orario += 1

            # Crea edizione
            EdizioneCorso.objects.create(
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
                print(f"   Importate: {importate}")

        except Exception as e:
            errori.append(str(e)[:100])
            if len(errori) <= 3:
                print(f"   ⚠️ Errore: {e}")

    print("\n" + "="*70)
    print("RISULTATO")
    print("="*70)
    print(f"✅ Importate: {importate}")
    print(f"⏭️  Saltate: {saltate}")
    print(f"⚠️  Orari corretti: {errori_orario}")
    print(f"❌ Errori: {len(errori)}")

    print(f"\nEdizioni totali DB: {EdizioneCorso.objects.count()}")
    print("="*70)


if __name__ == '__main__':
    import_edizioni()
