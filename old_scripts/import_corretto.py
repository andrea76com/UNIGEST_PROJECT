"""
UNIGEST - Import Corretto (con fix formato anno)
"""

import os
import sys
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections, transaction
from core.models import *

stats = {
    'anni': 0, 'comuni': 0, 'titoli': 0, 'prof_att': 0, 'prof_pass': 0,
    'iscritti': 0, 'docenti': 0, 'categorie': 0, 'gruppi': 0, 'corsi': 0,
    'edizioni': 0, 'iscr_anno': 0, 'iscr_corso': 0, 'lezioni': 0, 'errori': 0
}

def import_anni():
    """Importa anni con FIX formato"""
    print('\n📅 Importazione Anni Accademici...')
    cursor = connections['old_database'].cursor()
    cursor.execute("SELECT AnnoAccademico FROM TAnnoAccademico ORDER BY AnnoAccademico DESC")

    for i, row in enumerate(cursor.fetchall()):
        anno_str = str(row[0]).strip()
        if not anno_str:
            continue

        try:
            # FIX: Sostituisci / con -
            anno_str = anno_str.replace('/', '-')

            # Estrai anno iniziale
            parti = anno_str.split('-')
            if len(parti) != 2:
                print(f"  ⚠️ Formato strano: {anno_str}")
                continue

            anno_inizio = int(parti[0])

            # Date
            data_inizio = datetime(anno_inizio, 10, 1).date()
            data_fine = datetime(anno_inizio + 1, 4, 30).date()

            # Controlla se esiste già un anno attivo
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
                stats['anni'] += 1
                print(f"  ✅ {anno_str} (Attivo: {anno.attivo})")

        except Exception as e:
            print(f"  ⚠️ Errore {anno_str}: {e}")
            stats['errori'] += 1

    print(f"✅ {stats['anni']} anni importati")


def import_iscritti():
    """Importa iscritti con più debug"""
    print('\n👥 Importazione Iscritti...')
    cursor = connections['old_database'].cursor()

    # Prima conta
    cursor.execute("SELECT COUNT(*) FROM TAnagrafe")
    totale = cursor.fetchone()[0]
    print(f"  Totale iscritti nel vecchio DB: {totale}")

    if totale == 0:
        print("  ⚠️ Tabella TAnagrafe vuota!")
        return

    # Query con LIMIT per debug
    cursor.execute("""
        SELECT Matr, `M/F`, Nominativo, Indirizzo, Paese,
               Telefono, Cellulare, Email
        FROM TAnagrafe
        LIMIT 5
    """)

    print("\n  Prime 5 righe (per debug):")
    for row in cursor.fetchall():
        print(f"    Matricola: {row[0]}, Nome: {row[2]}")

    # Ora importa tutti
    cursor.execute("""
        SELECT Matr, `M/F`, Sig, Nominativo, Moglie, Indirizzo, Paese,
               Telefono, Cellulare, Luogo, Nascita, Email, CF
        FROM TAnagrafe
    """)

    iscritti_map = {}
    for row in cursor.fetchall():
        try:
            # Gestisci sesso con default
            sesso = 'M' if str(row[1]).upper() == 'M' else 'F'

            iscritto = Iscritto.objects.create(
                matricola=row[0],
                sesso=sesso,
                titolo=row[2] or '',
                nominativo=row[3] or f'Iscritto_{row[0]}',
                indirizzo=row[5] or '',
                comune_id=row[6] if row[6] and int(row[6]) != 0 else None,
                telefono=row[7] or '',
                cellulare=row[8] or '',
                luogo_nascita=row[9] or '',
                data_nascita=row[10] if row[10] else None,
                email=row[11] or '',
                codice_fiscale=row[12] if row[12] else None
            )

            iscritti_map[row[0]] = (iscritto, row[4])
            stats['iscritti'] += 1

            if stats['iscritti'] % 100 == 0:
                print(f"  Importati {stats['iscritti']}/{totale}...")

        except Exception as e:
            print(f"  ⚠️ Errore iscritto {row[0]}: {e}")
            stats['errori'] += 1

    print(f"✅ {stats['iscritti']} iscritti importati")


def import_categorie():
    """Importa categorie se non esistono"""
    print('\n📂 Importazione Categorie...')

    # Controlla se esistono già (le hai create a mano?)
    if CategoriaCorso.objects.count() > 0:
        print(f"  ⏭️  {CategoriaCorso.objects.count()} categorie già presenti (saltate)")
        return

    cursor = connections['old_database'].cursor()
    cursor.execute("SELECT IDCAT, Categoria FROM TCategorie")

    for row in cursor.fetchall():
        if row[1]:
            CategoriaCorso.objects.get_or_create(
                id=row[0],
                defaults={'nome': row[1], 'ordine': row[0]}
            )
            stats['categorie'] += 1

    print(f"✅ {stats['categorie']} categorie importate")


def import_corsi():
    """Importa corsi"""
    print('\n📖 Importazione Corsi...')
    cursor = connections['old_database'].cursor()

    cursor.execute("SELECT COUNT(*) FROM TCorsi")
    totale = cursor.fetchone()[0]
    print(f"  Totale corsi nel vecchio DB: {totale}")

    cursor.execute("SELECT Codice, Corsi, Dettaglio, CAT, GRUPPO, Visibile FROM TCorsi")

    for row in cursor.fetchall():
        try:
            Corso.objects.create(
                codice=row[0],
                nome=row[1] or f'Corso_{row[0]}',
                descrizione=row[2] or '',
                categoria_id=row[3] if row[3] and int(row[3]) != 0 else None,
                gruppo_id=row[4] if row[4] and int(row[4]) != 0 else None,
                visibile=bool(row[5]) if row[5] is not None else True
            )
            stats['corsi'] += 1
        except Exception as e:
            print(f"  ⚠️ Errore corso {row[0]}: {e}")
            stats['errori'] += 1

    print(f"✅ {stats['corsi']} corsi importati")


# MAIN
if __name__ == '__main__':
    print("="*70)
    print("UNIGEST - Importazione CORRETTA")
    print("="*70)

    risposta = input("\nVuoi procedere? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's']:
        print("❌ Annullato")
        sys.exit(0)

    try:
        with transaction.atomic():
            import_anni()
            import_iscritti()
            import_categorie()
            import_corsi()

            # Stampa riepilogo
            print("\n" + "="*70)
            print("RIEPILOGO:")
            print(f"  Anni: {stats['anni']}")
            print(f"  Iscritti: {stats['iscritti']}")
            print(f"  Categorie: {stats['categorie']}")
            print(f"  Corsi: {stats['corsi']}")
            print(f"  Errori: {stats['errori']}")
            print("="*70)

            print("\n✅ Importazione completata!")

    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()
