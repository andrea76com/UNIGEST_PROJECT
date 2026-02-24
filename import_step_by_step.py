"""
UNIGEST - Import Step by Step (senza transazioni)
"""

import os
import sys
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from core.models import *

def test_connessione_vecchio_db():
    """Test connessione al vecchio database"""
    print("\n🔍 Test connessione vecchio database...")
    try:
        cursor = connections['old_database'].cursor()
        cursor.execute("SHOW TABLES")
        tabelle = [row[0] for row in cursor.fetchall()]
        print(f"✅ Connesso! Tabelle trovate: {len(tabelle)}")

        # Conta records principali
        cursor.execute("SELECT COUNT(*) FROM TAnagrafe")
        print(f"  - TAnagrafe: {cursor.fetchone()[0]} records")

        cursor.execute("SELECT COUNT(*) FROM TDocenti")
        print(f"  - TDocenti: {cursor.fetchone()[0]} records")

        cursor.execute("SELECT COUNT(*) FROM TCorsi")
        print(f"  - TCorsi: {cursor.fetchone()[0]} records")

        cursor.execute("SELECT DISTINCT AnnoAccademico FROM TAnnoAccademico LIMIT 3")
        print("  - Anni accademici (primi 3):")
        for row in cursor.fetchall():
            print(f"    • {row[0]}")

        return True
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        return False


def import_anni():
    """Importa anni accademici"""
    print("\n📅 Importazione Anni Accademici...")

    cursor = connections['old_database'].cursor()
    cursor.execute("SELECT AnnoAccademico FROM TAnnoAccademico ORDER BY AnnoAccademico DESC")

    importati = 0
    for i, row in enumerate(cursor.fetchall()):
        anno_str = str(row[0]).strip().replace('/', '-')

        if not anno_str:
            continue

        try:
            parti = anno_str.split('-')
            anno_inizio = int(parti[0])

            data_inizio = datetime(anno_inizio, 10, 1).date()
            data_fine = datetime(anno_inizio + 1, 4, 30).date()

            # Controlla se esiste già anno attivo
            anno_attivo_esiste = AnnoAccademico.objects.filter(attivo=True).exists()

            anno, created = AnnoAccademico.objects.get_or_create(
                anno=anno_str,
                defaults={
                    'data_inizio': data_inizio,
                    'data_fine': data_fine,
                    'attivo': (i == 0 and not anno_attivo_esiste)
                }
            )

            if created:
                importati += 1
                print(f"  ✅ {anno_str} {'[ATTIVO]' if anno.attivo else ''}")
            else:
                print(f"  ⏭️  {anno_str} (già esistente)")

        except Exception as e:
            print(f"  ⚠️ Errore {anno_str}: {e}")

    print(f"\n✅ {importati} anni importati")
    return importati


def import_comuni():
    """Importa comuni"""
    print("\n📍 Importazione Comuni...")

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT DISTINCT Paese
        FROM TAnagrafe
        WHERE Paese IS NOT NULL
        AND Paese != ''
        AND Paese != 0
    """)

    importati = 0
    for row in cursor.fetchall():
        paese_id = row[0]
        try:
            comune, created = Comune.objects.get_or_create(
                id=paese_id,
                defaults={'nome': f'Comune_{paese_id}'}
            )
            if created:
                importati += 1
        except Exception as e:
            print(f"  ⚠️ Errore comune {paese_id}: {e}")

    print(f"✅ {importati} comuni importati")
    return importati


def import_titoli_studio():
    """Importa titoli di studio"""
    print("\n📚 Importazione Titoli di Studio...")

    cursor = connections['old_database'].cursor()
    cursor.execute("SELECT TitoloStudio FROM TTitoloStudio")

    importati = 0
    for row in cursor.fetchall():
        if row[0]:
            try:
                _, created = TitoloStudio.objects.get_or_create(descrizione=row[0])
                if created:
                    importati += 1
            except:
                pass

    print(f"✅ {importati} titoli importati")
    return importati


def import_docenti():
    """Importa docenti"""
    print("\n👨‍🏫 Importazione Docenti...")

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT ID, Prefisso, Insegnante, Telefono, Cellulare,
               Indirizzo, Paese, Note, Email
        FROM TDocenti
    """)

    importati = 0
    for row in cursor.fetchall():
        try:
            Docente.objects.create(
                id=row[0],
                titolo=row[1] or '',
                nome=row[2] or 'Sconosciuto',
                telefono=row[3] or '',
                cellulare=row[4] or '',
                indirizzo=row[5] or '',
                comune_id=row[6] if row[6] and int(row[6]) != 0 else None,
                note=row[7] or '',
                email=row[8] or '',
                attivo=True
            )
            importati += 1
            if importati % 10 == 0:
                print(f"  Importati {importati}...")
        except Exception as e:
            print(f"  ⚠️ Errore docente {row[0]}: {e}")

    print(f"✅ {importati} docenti importati")
    return importati


def import_iscritti():
    """Importa iscritti"""
    print("\n👥 Importazione Iscritti...")

    cursor = connections['old_database'].cursor()

    # Prima conta
    cursor.execute("SELECT COUNT(*) FROM TAnagrafe")
    totale = cursor.fetchone()[0]
    print(f"  Totale nel vecchio DB: {totale}")

    if totale == 0:
        print("  ⚠️ Tabella TAnagrafe vuota!")
        return 0

    # Mostra primi 3 per debug
    cursor.execute("SELECT Matr, Nominativo FROM TAnagrafe LIMIT 3")
    print("  Prime 3 righe:")
    for row in cursor.fetchall():
        print(f"    - {row[0]}: {row[1]}")

    # Importa tutti
    cursor.execute("""
        SELECT Matr, `M/F`, Sig, Nominativo, Moglie, Indirizzo, Paese,
               Telefono, Cellulare, Luogo, Nascita, Email, CF
        FROM TAnagrafe
    """)

    importati = 0
    errori = 0
    iscritti_map = {}

    for row in cursor.fetchall():
        try:
            # Gestisci sesso
            sesso_raw = str(row[1]).upper() if row[1] else 'M'
            sesso = 'M' if sesso_raw == 'M' else 'F'

            # Gestisci comune
            comune_id = None
            if row[6]:
                try:
                    comune_id = int(row[6])
                    if comune_id == 0:
                        comune_id = None
                except:
                    comune_id = None

            iscritto = Iscritto.objects.create(
                matricola=row[0],
                sesso=sesso,
                titolo=row[2] or '',
                nominativo=row[3] or f'Iscritto_{row[0]}',
                indirizzo=row[5] or '',
                comune_id=comune_id,
                telefono=row[7] or '',
                cellulare=row[8] or '',
                luogo_nascita=row[9] or '',
                data_nascita=row[10] if row[10] else None,
                email=row[11] or '',
                codice_fiscale=row[12] if row[12] else None
            )

            iscritti_map[row[0]] = (iscritto, row[4])  # Salva per coniugi
            importati += 1

            if importati % 100 == 0:
                print(f"  Importati {importati}/{totale}...")

        except Exception as e:
            errori += 1
            if errori <= 5:  # Mostra solo primi 5 errori
                print(f"  ⚠️ Errore iscritto {row[0]}: {e}")

    print(f"✅ {importati} iscritti importati ({errori} errori)")

    # Collega coniugi
    if iscritti_map:
        print("  Collegamento coniugi...")
        collegamenti = 0
        for matr, (iscritto, moglie_id) in iscritti_map.items():
            if moglie_id and moglie_id in iscritti_map:
                iscritto.coniuge = iscritti_map[moglie_id][0]
                iscritto.save()
                collegamenti += 1
        print(f"  ✅ {collegamenti} coniugi collegati")

    return importati


def import_corsi():
    """Importa corsi"""
    print("\n📖 Importazione Corsi...")

    cursor = connections['old_database'].cursor()
    cursor.execute("SELECT COUNT(*) FROM TCorsi")
    totale = cursor.fetchone()[0]
    print(f"  Totale nel vecchio DB: {totale}")

    cursor.execute("SELECT Codice, Corsi, Dettaglio, CAT, GRUPPO, Visibile FROM TCorsi")

    importati = 0
    errori = 0

    for row in cursor.fetchall():
        try:
            cat_id = None
            if row[3]:
                try:
                    cat_id = int(row[3])
                    if cat_id == 0:
                        cat_id = None
                except:
                    cat_id = None

            Corso.objects.create(
                codice=row[0],
                nome=row[1] or f'Corso_{row[0]}',
                descrizione=row[2] or '',
                categoria_id=cat_id,
                gruppo_id=row[4] if row[4] and int(row[4]) != 0 else None,
                visibile=bool(row[5]) if row[5] is not None else True
            )
            importati += 1

        except Exception as e:
            errori += 1
            if errori <= 5:
                print(f"  ⚠️ Errore corso {row[0]}: {e}")

    print(f"✅ {importati} corsi importati ({errori} errori)")
    return importati


# MAIN
if __name__ == '__main__':
    print("="*70)
    print("UNIGEST - Importazione Step by Step")
    print("="*70)

    # Test connessione
    if not test_connessione_vecchio_db():
        print("\n❌ Impossibile connettersi al vecchio database!")
        print("Verifica il file .env:")
        print("  - OLD_DB_NAME")
        print("  - OLD_DB_USER")
        print("  - OLD_DB_PASSWORD")
        sys.exit(1)

    # Chiedi conferma
    risposta = input("\nVuoi procedere con l'importazione? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's', 'yes', 'y']:
        print("❌ Annullato")
        sys.exit(0)

    print("\n🚀 Inizio importazione...")

    # Importa in sequenza
    totali = {}
    totali['anni'] = import_anni()
    totali['comuni'] = import_comuni()
    totali['titoli'] = import_titoli_studio()
    totali['docenti'] = import_docenti()
    totali['iscritti'] = import_iscritti()
    totali['corsi'] = import_corsi()

    # Riepilogo
    print("\n" + "="*70)
    print("RIEPILOGO IMPORTAZIONE:")
    print("="*70)
    print(f"  Anni Accademici:  {totali['anni']}")
    print(f"  Comuni:           {totali['comuni']}")
    print(f"  Titoli Studio:    {totali['titoli']}")
    print(f"  Docenti:          {totali['docenti']}")
    print(f"  Iscritti:         {totali['iscritti']}")
    print(f"  Corsi:            {totali['corsi']}")
    print("="*70)

    print("\n✅ Importazione completata!")
    print("\nControlla i dati importati nell'admin Django:")
    print("  http://127.0.0.1:8000/admin/")
