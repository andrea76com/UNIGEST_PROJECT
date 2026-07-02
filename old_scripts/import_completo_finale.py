
"""
UNIGEST - Import Completo Finale
Importa tutto in ordine corretto con tutti i ForeignKey
"""

import os
import sys
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from core.models import *

def log(msg):
    """Stampa e salva su file"""
    print(msg)
    with open('import_log.txt', 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def import_gruppi():
    """Importa gruppi corsi"""
    log("\n📦 Importazione Gruppi Corsi...")

    cursor = connections['old_database'].cursor()
    cursor.execute("SELECT ID, Gruppo FROM TGruppi")

    importati = 0
    for row in cursor.fetchall():
        if row[1]:
            try:
                _, created = GruppoCorso.objects.get_or_create(
                    id=row[0],
                    defaults={'nome': row[1]}
                )
                if created:
                    importati += 1
                    log(f"  ✅ Gruppo: {row[1]}")
            except Exception as e:
                log(f"  ⚠️ Errore gruppo {row[0]}: {e}")

    log(f"✅ {importati} gruppi importati")
    return importati

def import_professioni():
    """Importa professioni"""
    log("\n💼 Importazione Professioni...")

    cursor = connections['old_database'].cursor()

    # Attuali
    cursor.execute("SELECT ProfAtt FROM TProfAtt")
    att = 0
    for row in cursor.fetchall():
        if row[0]:
            try:
                _, created = ProfessioneAttuale.objects.get_or_create(descrizione=row[0])
                if created:
                    att += 1
            except:
                pass

    # Passate
    cursor.execute("SELECT ProfPass FROM TProfPass")
    pas = 0
    for row in cursor.fetchall():
        if row[0]:
            try:
                _, created = ProfessionePassata.objects.get_or_create(descrizione=row[0])
                if created:
                    pas += 1
            except:
                pass

    log(f"✅ {att} prof. attuali, {pas} prof. passate")
    return att + pas

def import_autorita():
    """Importa autorità"""
    log("\n🏛️  Importazione Autorità...")

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT ID, Prefisso, Autorita, Carica, Indirizzo,
               Paese, Note, Attivo, Email
        FROM TAutorita
    """)

    importati = 0
    for row in cursor.fetchall():
        try:
            Autorita.objects.create(
                id=row[0],
                titolo=row[1] or '',
                nome=row[2] or 'Sconosciuto',
                carica=row[3] or '',
                indirizzo=row[4] or '',
                comune_id=row[5] if row[5] and int(row[5]) != 0 else None,
                note=row[6] or '',
                attivo=bool(row[7]) if row[7] is not None else True,
                email=row[8] or ''
            )
            importati += 1
        except Exception as e:
            if importati == 0:  # Mostra solo primo errore
                log(f"  ⚠️ Errore: {e}")

    log(f"✅ {importati} autorità importate")
    return importati

def import_corsi_mancanti():
    """Importa corsi che erano falliti per mancanza gruppi"""
    log("\n📖 Importazione Corsi Mancanti...")

    cursor = connections['old_database'].cursor()
    cursor.execute("SELECT Codice, Corsi, Dettaglio, CAT, GRUPPO, Visibile FROM TCorsi")

    importati = 0
    esistenti = 0
    errori = 0

    for row in cursor.fetchall():
        # Verifica se esiste già
        if Corso.objects.filter(codice=row[0]).exists():
            esistenti += 1
            continue

        try:
            # Gestisci categoria e gruppo
            cat_id = None
            if row[3]:
                try:
                    cat_id = int(row[3])
                    if cat_id == 0 or not CategoriaCorso.objects.filter(id=cat_id).exists():
                        cat_id = None
                except:
                    cat_id = None

            gruppo_id = None
            if row[4]:
                try:
                    gruppo_id = int(row[4])
                    if gruppo_id == 0 or not GruppoCorso.objects.filter(id=gruppo_id).exists():
                        gruppo_id = None
                except:
                    gruppo_id = None

            Corso.objects.create(
                codice=row[0],
                nome=row[1] or f'Corso_{row[0]}',
                descrizione=row[2] or '',
                categoria_id=cat_id,
                gruppo_id=gruppo_id,
                visibile=bool(row[5]) if row[5] is not None else True
            )
            importati += 1

        except Exception as e:
            errori += 1
            if errori <= 3:
                log(f"  ⚠️ Errore corso {row[0]}: {e}")

    log(f"✅ {importati} corsi nuovi, {esistenti} già esistenti, {errori} errori")
    return importati

def import_edizioni():
    """Importa edizioni corsi"""
    log("\n📚 Importazione Edizioni Corsi...")

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT ID, Anno, Codice, Descrizione, Quadrimestre, Insegnante,
               Assistente, Vice, Giorni, Dalle, Alle, Note
        FROM TCorsiAnnualiDocenti
    """)

    importati = 0
    errori = 0

    for row in cursor.fetchall():
        try:
            # Converti anno
            anno_str = str(row[1]).replace('/', '-')
            anno = AnnoAccademico.objects.filter(anno=anno_str).first()
            corso = Corso.objects.filter(codice=row[2]).first()
            docente = Docente.objects.filter(id=row[5]).first()
            quad = Quadrimestre.objects.filter(numero=row[4]).first()

            if not all([anno, corso, docente, quad]):
                errori += 1
                continue

            # Orari con default
            ora_inizio = row[9] if row[9] else '09:00:00'
            ora_fine = row[10] if row[10] else '11:00:00'

            # Assistenti (possono essere None)
            assistente_id = None
            if row[6]:
                try:
                    ass_id = int(row[6])
                    if Iscritto.objects.filter(matricola=ass_id).exists():
                        assistente_id = ass_id
                except:
                    pass

            vice_id = None
            if row[7]:
                try:
                    v_id = int(row[7])
                    if Iscritto.objects.filter(matricola=v_id).exists():
                        vice_id = v_id
                except:
                    pass

            EdizioneCorso.objects.create(
                id=row[0],
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
            importati += 1

            if importati % 100 == 0:
                log(f"  Importate {importati}...")

        except Exception as e:
            errori += 1
            if errori <= 3:
                log(f"  ⚠️ Errore edizione {row[0]}: {e}")

    log(f"✅ {importati} edizioni importate ({errori} errori)")
    return importati

def import_iscrizioni_anno():
    """Importa iscrizioni anno"""
    log("\n✍️  Importazione Iscrizioni Anno...")

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT AnnoAccademico, Matricola, Ricevuta, Data
        FROM TIscrizioneAnnoAccademico
    """)

    importati = 0
    errori = 0

    for row in cursor.fetchall():
        try:
            anno_str = str(row[0]).replace('/', '-')
            anno = AnnoAccademico.objects.filter(anno=anno_str).first()
            iscritto = Iscritto.objects.filter(matricola=row[1]).first()

            if anno and iscritto:
                _, created = IscrizioneAnnoAccademico.objects.get_or_create(
                    anno_accademico=anno,
                    iscritto=iscritto,
                    defaults={
                        'numero_ricevuta': row[2] or 0,
                        'data_iscrizione': row[3] if row[3] else anno.data_inizio
                    }
                )
                if created:
                    importati += 1

                    if importati % 500 == 0:
                        log(f"  Importate {importati}...")
        except Exception as e:
            errori += 1

    log(f"✅ {importati} iscrizioni anno importate ({errori} errori)")
    return importati

def import_iscrizioni_corso():
    """Importa iscrizioni corsi"""
    log("\n📝 Importazione Iscrizioni Corsi...")

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT AnnoAccademico, Corso, Matricola, Ricevuta, Data
        FROM TFrequenzaCorsi
    """)

    importati = 0
    errori = 0

    for row in cursor.fetchall():
        try:
            anno_str = str(row[0]).replace('/', '-')
            anno = AnnoAccademico.objects.filter(anno=anno_str).first()
            iscritto = Iscritto.objects.filter(matricola=row[2]).first()

            # Trova edizione (può essere None se corso non ha edizioni)
            edizione = EdizioneCorso.objects.filter(
                anno_accademico=anno,
                corso__codice=row[1]
            ).first()

            if all([anno, iscritto, edizione]):
                _, created = IscrizioneCorso.objects.get_or_create(
                    anno_accademico=anno,
                    edizione_corso=edizione,
                    iscritto=iscritto,
                    defaults={
                        'numero_ricevuta': row[3],
                        'data_iscrizione': row[4] if row[4] else anno.data_inizio
                    }
                )
                if created:
                    importati += 1

                    if importati % 1000 == 0:
                        log(f"  Importate {importati}...")
        except Exception as e:
            errori += 1

    log(f"✅ {importati} iscrizioni corso importate ({errori} errori)")
    return importati

def import_lezioni():
    """Importa lezioni"""
    log("\n📓 Importazione Lezioni...")

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT ID_corso_annuale, data, corso, descrizione,
               insegnante, presenze, ore, annoacc
        FROM TPresenzeCorsisti
    """)

    importati = 0
    errori = 0

    for row in cursor.fetchall():
        try:
            edizione = EdizioneCorso.objects.filter(id=row[0]).first()

            if edizione and row[1]:
                docente = Docente.objects.filter(id=row[4]).first()

                _, created = Lezione.objects.get_or_create(
                    edizione_corso=edizione,
                    data_lezione=row[1],
                    defaults={
                        'descrizione': row[3] or '',
                        'docente': docente or edizione.docente,
                        'numero_presenti': row[5] or 0,
                        'ore_lezione': float(row[6]) if row[6] else 2.0
                    }
                )
                if created:
                    importati += 1

                    if importati % 500 == 0:
                        log(f"  Importate {importati}...")
        except Exception as e:
            errori += 1

    log(f"✅ {importati} lezioni importate ({errori} errori)")
    return importati

# MAIN
if __name__ == '__main__':
    # Inizializza log
    with open('import_log.txt', 'w', encoding='utf-8') as f:
        f.write("UNIGEST - Log Importazione\n")
        f.write("="*70 + "\n")

    log("="*70)
    log("UNIGEST - Importazione Completa")
    log("="*70)

    risposta = input("\nImporta dati mancanti? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's', 'yes', 'y']:
        print("❌ Annullato")
        sys.exit(0)

    log("\n🚀 Inizio importazione dati mancanti...")

    totali = {}
    totali['gruppi'] = import_gruppi()
    totali['professioni'] = import_professioni()
    totali['autorita'] = import_autorita()
    totali['corsi'] = import_corsi_mancanti()
    totali['edizioni'] = import_edizioni()
    totali['iscr_anno'] = import_iscrizioni_anno()
    totali['iscr_corso'] = import_iscrizioni_corso()
    totali['lezioni'] = import_lezioni()

    # Riepilogo
    log("\n" + "="*70)
    log("RIEPILOGO FINALE:")
    log("="*70)
    log(f"  Gruppi Corsi:         {totali['gruppi']}")
    log(f"  Professioni:          {totali['professioni']}")
    log(f"  Autorità:             {totali['autorita']}")
    log(f"  Corsi mancanti:       {totali['corsi']}")
    log(f"  Edizioni Corsi:       {totali['edizioni']}")
    log(f"  Iscrizioni Anno:      {totali['iscr_anno']}")
    log(f"  Iscrizioni Corso:     {totali['iscr_corso']}")
    log(f"  Lezioni:              {totali['lezioni']}")
    log("="*70)

    log("\n✅ Importazione completata!")
    log("📄 Log salvato in: import_log.txt")

    print("\n" + "="*70)
    print("STATO FINALE DATABASE:")
    print("="*70)
    print(f"  Anni Accademici:  {AnnoAccademico.objects.count()}")
    print(f"  Iscritti:         {Iscritto.objects.count()}")
    print(f"  Docenti:          {Docente.objects.count()}")
    print(f"  Corsi:            {Corso.objects.count()}")
    print(f"  Edizioni Corsi:   {EdizioneCorso.objects.count()}")
    print(f"  Iscrizioni Anno:  {IscrizioneAnnoAccademico.objects.count()}")
    print(f"  Iscrizioni Corso: {IscrizioneCorso.objects.count()}")
    print(f"  Lezioni:          {Lezione.objects.count()}")
    print("="*70)
