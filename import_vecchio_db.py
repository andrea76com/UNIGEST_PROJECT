"""
UNIGEST - Import Dati da Vecchio Database
Script standalone per importare dati dal vecchio database UNI
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections, transaction
from core.models import (
    Comune, TitoloStudio, ProfessioneAttuale, ProfessionePassata,
    Iscritto, Docente, Autorita,
    CategoriaCorso, GruppoCorso, Corso, AnnoAccademico, Quadrimestre,
    EdizioneCorso, IscrizioneAnnoAccademico, IscrizioneCorso,
    Lezione, PresenzaLezione
)

# Statistiche
stats = {
    'comuni': 0,
    'titoli_studio': 0,
    'professioni_attuali': 0,
    'professioni_passate': 0,
    'iscritti': 0,
    'docenti': 0,
    'autorita': 0,
    'categorie': 0,
    'gruppi': 0,
    'corsi': 0,
    'anni': 0,
    'edizioni': 0,
    'iscrizioni_anno': 0,
    'iscrizioni_corso': 0,
    'lezioni': 0,
    'errori': 0
}

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print('='*70)

def print_section(text):
    print(f"\n{text}")

def import_anni_accademici():
    """Importa anni accademici dal vecchio DB"""
    print_section('📅 Importazione Anni Accademici...')

    cursor = connections['old_database'].cursor()
    cursor.execute("SELECT AnnoAccademico, progr FROM TAnnoAccademico ORDER BY progr DESC")

    for i, row in enumerate(cursor.fetchall()):
        anno_str = row[0]
        if not anno_str:
            continue

        try:
            # Estrai anno di inizio (es: "2023-2024" -> 2023)
            anni = anno_str.split('-')
            anno_inizio = int(anni[0])

            # Date standard
            data_inizio = datetime(anno_inizio, 10, 1).date()  # 1 ottobre
            data_fine = datetime(anno_inizio + 1, 4, 30).date()  # 30 aprile

            # Crea anno (il più recente sarà attivo solo se non ne esiste già uno attivo)
            anno_attivo_esistente = AnnoAccademico.objects.filter(attivo=True).exists()

            anno, created = AnnoAccademico.objects.get_or_create(
                anno=anno_str,
                defaults={
                    'data_inizio': data_inizio,
                    'data_fine': data_fine,
                    'attivo': (i == 0 and not anno_attivo_esistente)  # Solo il primo se non c'è già un attivo
                }
            )

            if created:
                stats['anni'] += 1
                status = "✅ Creato"
            else:
                status = "⏭️  Già esistente"

            print(f"  {status}: {anno_str} (Attivo: {anno.attivo})")

        except Exception as e:
            print(f"  ⚠️ Errore anno {anno_str}: {e}")
            stats['errori'] += 1

    print(f"✅ {stats['anni']} anni accademici importati")


def import_comuni():
    """Importa comuni"""
    print_section('📍 Importazione Comuni...')

    cursor = connections['old_database'].cursor()
    # Estrai comuni unici dalla tabella iscritti
    cursor.execute("""
        SELECT DISTINCT Paese
        FROM TAnagrafe
        WHERE Paese IS NOT NULL
        AND Paese != ''
        AND Paese != 0
    """)

    for row in cursor.fetchall():
        paese_id = row[0]
        try:
            # Il nome del comune dovrebbe essere in una tabella di lookup
            # Per ora usiamo un placeholder
            nome = f"Comune_{paese_id}"

            Comune.objects.get_or_create(
                id=paese_id,
                defaults={'nome': nome}
            )
            stats['comuni'] += 1
        except Exception as e:
            print(f"  ⚠️ Errore comune {paese_id}: {e}")
            stats['errori'] += 1

    print(f"✅ {stats['comuni']} comuni importati")


def import_titoli_studio():
    """Importa titoli di studio"""
    print_section('📚 Importazione Titoli di Studio...')

    cursor = connections['old_database'].cursor()
    cursor.execute("SELECT TitoloStudio FROM TTitoloStudio")

    for row in cursor.fetchall():
        if row[0]:
            try:
                TitoloStudio.objects.get_or_create(descrizione=row[0])
                stats['titoli_studio'] += 1
            except Exception as e:
                stats['errori'] += 1

    print(f"✅ {stats['titoli_studio']} titoli importati")


def import_professioni():
    """Importa professioni"""
    print_section('💼 Importazione Professioni...')

    cursor = connections['old_database'].cursor()

    # Professioni attuali
    cursor.execute("SELECT ProfAtt FROM TProfAtt")
    for row in cursor.fetchall():
        if row[0]:
            try:
                ProfessioneAttuale.objects.get_or_create(descrizione=row[0])
                stats['professioni_attuali'] += 1
            except:
                stats['errori'] += 1

    # Professioni passate
    cursor.execute("SELECT ProfPass FROM TProfPass")
    for row in cursor.fetchall():
        if row[0]:
            try:
                ProfessionePassata.objects.get_or_create(descrizione=row[0])
                stats['professioni_passate'] += 1
            except:
                stats['errori'] += 1

    print(f"✅ {stats['professioni_attuali']} prof. attuali, {stats['professioni_passate']} prof. passate")


def import_docenti():
    """Importa docenti"""
    print_section('👨‍🏫 Importazione Docenti...')

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT ID, Prefisso, Insegnante, Telefono, Cellulare,
               Indirizzo, Paese, Note, Email
        FROM TDocenti
    """)

    for row in cursor.fetchall():
        try:
            Docente.objects.create(
                id=row[0],
                titolo=row[1] or '',
                nome=row[2] or 'Sconosciuto',
                telefono=row[3] or '',
                cellulare=row[4] or '',
                indirizzo=row[5] or '',
                comune_id=row[6] if row[6] and row[6] != 0 else None,
                note=row[7] or '',
                email=row[8] or '',
                attivo=True
            )
            stats['docenti'] += 1

            if stats['docenti'] % 10 == 0:
                print(f"  Importati {stats['docenti']} docenti...")

        except Exception as e:
            stats['errori'] += 1
            if '--verbose' in sys.argv:
                print(f"  ⚠️ Errore docente {row[0]}: {e}")

    print(f"✅ {stats['docenti']} docenti importati")


def import_iscritti():
    """Importa iscritti"""
    print_section('👥 Importazione Iscritti...')

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT Matr, `M/F`, Sig, Nominativo, Moglie, Indirizzo, Paese,
               Telefono, Cellulare, Luogo, Nascita, TitoloStudio,
               ProfAtt, ProfPass, Pensionato, Posta, Email, Whatsapp, CF
        FROM TAnagrafe
    """)

    # Prima passata: crea iscritti
    iscritti_map = {}
    for row in cursor.fetchall():
        try:
            pensionato = False
            if row[14]:
                pensionato = str(row[14]).lower() in ['si', 'sì', 'yes', '1', 'true']

            iscritto = Iscritto.objects.create(
                matricola=row[0],
                sesso='M' if row[1] == 'M' else 'F',
                titolo=row[2] or '',
                nominativo=row[3] or 'Sconosciuto',
                indirizzo=row[5] or '',
                comune_id=row[6] if row[6] and row[6] != 0 else None,
                telefono=row[7] or '',
                cellulare=row[8] or '',
                luogo_nascita=row[9] or '',
                data_nascita=row[10] if row[10] else None,
                email=row[16] or '',
                ha_whatsapp=bool(row[17]) if row[17] else False,
                codice_fiscale=row[18] or None,
                e_pensionato=pensionato,
                riceve_posta=bool(row[15]) if row[15] is not None else True
            )

            iscritti_map[row[0]] = (iscritto, row[4])  # Salva matricola moglie
            stats['iscritti'] += 1

            if stats['iscritti'] % 50 == 0:
                print(f"  Importati {stats['iscritti']} iscritti...")

        except Exception as e:
            stats['errori'] += 1
            if '--verbose' in sys.argv:
                print(f"  ⚠️ Errore iscritto {row[0]}: {e}")

    # Seconda passata: collega coniugi
    print("  Collegamento coniugi...")
    for matricola, (iscritto, moglie_id) in iscritti_map.items():
        if moglie_id and moglie_id in iscritti_map:
            iscritto.coniuge = iscritti_map[moglie_id][0]
            iscritto.save()

    print(f"✅ {stats['iscritti']} iscritti importati")


def import_categorie():
    """Importa categorie corsi"""
    print_section('📂 Importazione Categorie Corsi...')

    cursor = connections['old_database'].cursor()
    cursor.execute("SELECT IDCAT, Categoria FROM TCategorie")

    for row in cursor.fetchall():
        if row[1]:
            try:
                CategoriaCorso.objects.get_or_create(
                    id=row[0],
                    defaults={'nome': row[1], 'ordine': row[0]}
                )
                stats['categorie'] += 1
            except:
                stats['errori'] += 1

    print(f"✅ {stats['categorie']} categorie importate")


def import_gruppi():
    """Importa gruppi corsi"""
    print_section('📦 Importazione Gruppi Corsi...')

    cursor = connections['old_database'].cursor()
    cursor.execute("SELECT ID, Gruppo FROM TGruppi")

    for row in cursor.fetchall():
        if row[1]:
            try:
                GruppoCorso.objects.get_or_create(
                    id=row[0],
                    defaults={'nome': row[1]}
                )
                stats['gruppi'] += 1
            except:
                stats['errori'] += 1

    print(f"✅ {stats['gruppi']} gruppi importati")


def import_corsi():
    """Importa corsi"""
    print_section('📖 Importazione Corsi...')

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT Codice, Corsi, Dettaglio, CAT, GRUPPO, Visibile
        FROM TCorsi
    """)

    for row in cursor.fetchall():
        try:
            Corso.objects.create(
                codice=row[0],
                nome=row[1] or 'Corso senza nome',
                descrizione=row[2] or '',
                categoria_id=row[3] if row[3] and row[3] != 0 else None,
                gruppo_id=row[4] if row[4] and row[4] != 0 else None,
                visibile=bool(row[5]) if row[5] is not None else True
            )
            stats['corsi'] += 1

        except Exception as e:
            stats['errori'] += 1
            if '--verbose' in sys.argv:
                print(f"  ⚠️ Errore corso {row[0]}: {e}")

    print(f"✅ {stats['corsi']} corsi importati")


def import_edizioni_corsi():
    """Importa edizioni corsi"""
    print_section('📚 Importazione Edizioni Corsi...')

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT ID, Anno, Codice, Descrizione, Quadrimestre, Insegnante,
               Assistente, Vice, Giorni, Dalle, Alle, Note
        FROM TCorsiAnnualiDocenti
    """)

    for row in cursor.fetchall():
        try:
            # Verifica esistenza
            anno = AnnoAccademico.objects.filter(anno=row[1]).first()
            corso = Corso.objects.filter(codice=row[2]).first()
            docente = Docente.objects.filter(id=row[5]).first()
            quad = Quadrimestre.objects.filter(numero=row[4]).first()

            if not all([anno, corso, docente, quad]):
                stats['errori'] += 1
                continue

            # Ora inizio/fine con valori di default
            ora_inizio = row[9] if row[9] else '09:00'
            ora_fine = row[10] if row[10] else '11:00'

            EdizioneCorso.objects.create(
                id=row[0],
                anno_accademico=anno,
                corso=corso,
                quadrimestre=quad,
                descrizione_custom=row[3] or '',
                docente=docente,
                assistente_id=row[6] if row[6] and row[6] != 0 else None,
                vice_assistente_id=row[7] if row[7] and row[7] != 0 else None,
                giorni_settimana=row[8] or '',
                ora_inizio=ora_inizio,
                ora_fine=ora_fine,
                note=row[11] or ''
            )
            stats['edizioni'] += 1

            if stats['edizioni'] % 20 == 0:
                print(f"  Importate {stats['edizioni']} edizioni...")

        except Exception as e:
            stats['errori'] += 1
            if '--verbose' in sys.argv:
                print(f"  ⚠️ Errore edizione {row[0]}: {e}")

    print(f"✅ {stats['edizioni']} edizioni importate")


def import_iscrizioni_anno():
    """Importa iscrizioni anno"""
    print_section('✍️  Importazione Iscrizioni Anno...')

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT AnnoAccademico, Matricola, Ricevuta, Data
        FROM TIscrizioneAnnoAccademico
    """)

    for row in cursor.fetchall():
        try:
            anno = AnnoAccademico.objects.filter(anno=row[0]).first()
            iscritto = Iscritto.objects.filter(matricola=row[1]).first()

            if anno and iscritto:
                IscrizioneAnnoAccademico.objects.get_or_create(
                    anno_accademico=anno,
                    iscritto=iscritto,
                    defaults={
                        'numero_ricevuta': row[2] or 0,
                        'data_iscrizione': row[3] if row[3] else anno.data_inizio
                    }
                )
                stats['iscrizioni_anno'] += 1

        except Exception as e:
            stats['errori'] += 1

    print(f"✅ {stats['iscrizioni_anno']} iscrizioni anno importate")


def import_iscrizioni_corso():
    """Importa iscrizioni corsi"""
    print_section('📝 Importazione Iscrizioni Corsi...')

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT AnnoAccademico, Corso, Matricola, Ricevuta, Data
        FROM TFrequenzaCorsi
    """)

    for row in cursor.fetchall():
        try:
            anno = AnnoAccademico.objects.filter(anno=row[0]).first()
            iscritto = Iscritto.objects.filter(matricola=row[2]).first()
            edizione = EdizioneCorso.objects.filter(
                anno_accademico=anno,
                corso__codice=row[1]
            ).first()

            if all([anno, iscritto, edizione]):
                IscrizioneCorso.objects.get_or_create(
                    anno_accademico=anno,
                    edizione_corso=edizione,
                    iscritto=iscritto,
                    defaults={
                        'numero_ricevuta': row[3],
                        'data_iscrizione': row[4] if row[4] else anno.data_inizio
                    }
                )
                stats['iscrizioni_corso'] += 1

                if stats['iscrizioni_corso'] % 50 == 0:
                    print(f"  Importate {stats['iscrizioni_corso']} iscrizioni corso...")

        except Exception as e:
            stats['errori'] += 1

    print(f"✅ {stats['iscrizioni_corso']} iscrizioni corso importate")


def import_lezioni():
    """Importa lezioni"""
    print_section('📓 Importazione Lezioni...')

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT ID_corso_annuale, data, corso, descrizione,
               insegnante, presenze, ore, annoacc
        FROM TPresenzeCorsisti
    """)

    for row in cursor.fetchall():
        try:
            edizione = EdizioneCorso.objects.filter(id=row[0]).first()
            docente = Docente.objects.filter(id=row[4]).first()

            if edizione and row[1]:
                Lezione.objects.get_or_create(
                    edizione_corso=edizione,
                    data_lezione=row[1],
                    defaults={
                        'descrizione': row[3] or '',
                        'docente': docente or edizione.docente,
                        'numero_presenti': row[5] or 0,
                        'ore_lezione': float(row[6]) if row[6] else 2.0
                    }
                )
                stats['lezioni'] += 1

        except Exception as e:
            stats['errori'] += 1

    print(f"✅ {stats['lezioni']} lezioni importate")


def print_stats():
    """Stampa statistiche finali"""
    print_header('RIEPILOGO IMPORTAZIONE')

    print(f'\n📊 TABELLE DI SUPPORTO:')
    print(f'  • Comuni: {stats["comuni"]}')
    print(f'  • Titoli di Studio: {stats["titoli_studio"]}')
    print(f'  • Professioni Attuali: {stats["professioni_attuali"]}')
    print(f'  • Professioni Passate: {stats["professioni_passate"]}')

    print(f'\n👥 ANAGRAFICHE:')
    print(f'  • Iscritti: {stats["iscritti"]}')
    print(f'  • Docenti: {stats["docenti"]}')

    print(f'\n📚 CORSI:')
    print(f'  • Categorie: {stats["categorie"]}')
    print(f'  • Gruppi: {stats["gruppi"]}')
    print(f'  • Corsi: {stats["corsi"]}')
    print(f'  • Anni Accademici: {stats["anni"]}')
    print(f'  • Edizioni Corsi: {stats["edizioni"]}')

    print(f'\n✍️  ISCRIZIONI E LEZIONI:')
    print(f'  • Iscrizioni Anno: {stats["iscrizioni_anno"]}')
    print(f'  • Iscrizioni Corso: {stats["iscrizioni_corso"]}')
    print(f'  • Lezioni: {stats["lezioni"]}')

    if stats['errori'] > 0:
        print(f'\n⚠️  ERRORI: {stats["errori"]}')

    print('\n' + '='*70)


# MAIN
if __name__ == '__main__':
    print_header('UNIGEST - Importazione Dati da Vecchio Database')

    print("\n⚠️  ATTENZIONE:")
    print("  Questo script importerà i dati dal vecchio database 'UNI'")
    print("  Assicurati che il file .env sia configurato correttamente")
    print("  con OLD_DB_NAME, OLD_DB_USER, OLD_DB_PASSWORD")

    risposta = input("\nVuoi procedere? (si/no): ")

    if risposta.lower() not in ['si', 'sì', 's', 'yes', 'y']:
        print("\n❌ Importazione annullata")
        sys.exit(0)

    print("\n🚀 Inizio importazione...")

    try:
        with transaction.atomic():
            # Importa in ordine
            import_anni_accademici()       # PRIMA GLI ANNI!
            import_comuni()
            import_titoli_studio()
            import_professioni()
            import_docenti()
            import_iscritti()
            import_categorie()
            import_gruppi()
            import_corsi()
            import_edizioni_corsi()
            import_iscrizioni_anno()
            import_iscrizioni_corso()
            import_lezioni()

            print_stats()
            print('\n✅ Importazione completata con successo!\n')

    except Exception as e:
        print(f'\n❌ ERRORE durante l\'importazione: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
