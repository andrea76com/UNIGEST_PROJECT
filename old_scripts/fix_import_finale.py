"""
UNIGEST - Fix Import Iscrizioni e Edizioni
Corregge il problema del formato anno / vs -
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
    """Log su console e file"""
    print(msg)
    with open('fix_import_log.txt', 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def fix_edizioni_mancanti():
    """Importa edizioni che erano fallite"""
    log("\n📚 Fix Edizioni Mancanti...")

    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT ID, Anno, Codice, Descrizione, Quadrimestre, Insegnante,
               Assistente, Vice, Giorni, Dalle, Alle, Note
        FROM TCorsiAnnualiDocenti
    """)

    importate = 0
    esistenti = 0
    errori = 0
    errori_dettaglio = {}

    for row in cursor.fetchall():
        # Salta se esiste già
        if EdizioneCorso.objects.filter(id=row[0]).exists():
            esistenti += 1
            continue

        try:
            # Converti anno
            anno_str = str(row[1]).replace('/', '-')
            anno = AnnoAccademico.objects.filter(anno=anno_str).first()

            if not anno:
                errore = f"Anno non trovato: {row[1]}"
                errori_dettaglio[errore] = errori_dettaglio.get(errore, 0) + 1
                errori += 1
                continue

            # Trova corso
            corso = Corso.objects.filter(codice=row[2]).first()
            if not corso:
                errore = f"Corso non trovato: {row[2]}"
                errori_dettaglio[errore] = errori_dettaglio.get(errore, 0) + 1
                errori += 1
                continue

            # Trova docente
            docente = Docente.objects.filter(id=row[5]).first()
            if not docente:
                errore = f"Docente non trovato: {row[5]}"
                errori_dettaglio[errore] = errori_dettaglio.get(errore, 0) + 1
                errori += 1
                continue

            # Quadrimestre
            quad = Quadrimestre.objects.filter(numero=row[4]).first()
            if not quad:
                errore = f"Quadrimestre non trovato: {row[4]}"
                errori_dettaglio[errore] = errori_dettaglio.get(errore, 0) + 1
                errori += 1
                continue

            # Orari
            ora_inizio = row[9] if row[9] else '09:00:00'
            ora_fine = row[10] if row[10] else '11:00:00'

            # Assistenti
            assistente_id = None
            if row[6]:
                if Iscritto.objects.filter(matricola=row[6]).exists():
                    assistente_id = row[6]

            vice_id = None
            if row[7]:
                if Iscritto.objects.filter(matricola=row[7]).exists():
                    vice_id = row[7]

            # Crea edizione
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
            importate += 1

            if importate % 100 == 0:
                log(f"  Importate {importate}...")

        except Exception as e:
            errore = str(e)[:50]
            errori_dettaglio[errore] = errori_dettaglio.get(errore, 0) + 1
            errori += 1

    log(f"✅ {importate} nuove, {esistenti} esistenti, {errori} errori")

    if errori_dettaglio:
        log("\n📋 Dettaglio errori:")
        for errore, count in sorted(errori_dettaglio.items(), key=lambda x: x[1], reverse=True)[:5]:
            log(f"  • {errore}: {count} volte")

    return importate


def fix_iscrizioni_corso():
    """
    Importa iscrizioni corso con FIX formato anno
    """
    log("\n📝 Fix Iscrizioni Corso...")

    cursor = connections['old_database'].cursor()

    # Prima conta quelle importabili
    cursor.execute("""
        SELECT COUNT(*)
        FROM TFrequenzaCorsi f
        WHERE EXISTS (
            SELECT 1 FROM TCorsiAnnualiDocenti c
            WHERE REPLACE(c.Anno, '/', '-') = REPLACE(f.AnnoAccademico, '/', '-')
            AND c.Codice = f.Corso
        )
    """)
    importabili = cursor.fetchone()[0]
    log(f"  Iscrizioni potenzialmente importabili: {importabili}")

    # Importa con batch per non sovraccaricare
    cursor.execute("""
        SELECT f.AnnoAccademico, f.Corso, f.Matricola, f.Ricevuta, f.Data,
               c.ID as edizione_id
        FROM TFrequenzaCorsi f
        INNER JOIN TCorsiAnnualiDocenti c
            ON REPLACE(c.Anno, '/', '-') = REPLACE(f.AnnoAccademico, '/', '-')
            AND c.Codice = f.Corso
        ORDER BY f.AnnoAccademico DESC
    """)

    importate = 0
    duplicate = 0
    errori = 0
    batch_size = 1000

    rows = cursor.fetchall()
    total = len(rows)

    log(f"  Totale record da processare: {total}")

    for i, row in enumerate(rows):
        try:
            # Converti anno
            anno_str = str(row[0]).replace('/', '-')
            anno = AnnoAccademico.objects.filter(anno=anno_str).first()

            if not anno:
                errori += 1
                continue

            # Trova iscritto
            iscritto = Iscritto.objects.filter(matricola=row[2]).first()
            if not iscritto:
                errori += 1
                continue

            # Trova edizione
            edizione = EdizioneCorso.objects.filter(id=row[5]).first()
            if not edizione:
                errori += 1
                continue

            # Crea iscrizione (controlla duplicati)
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
                importate += 1
            else:
                duplicate += 1

            # Progress ogni batch
            if (i + 1) % batch_size == 0:
                percentuale = (i + 1) / total * 100
                log(f"  Progresso: {i+1}/{total} ({percentuale:.1f}%) - Importate: {importate}")

        except Exception as e:
            errori += 1
            if errori <= 3:
                log(f"  ⚠️ Errore: {e}")

    log(f"✅ {importate} importate, {duplicate} duplicate, {errori} errori")
    return importate


def verifica_finale():
    """Verifica stato finale"""
    log("\n" + "="*70)
    log("VERIFICA FINALE DATABASE")
    log("="*70)

    totali = {
        'anni': AnnoAccademico.objects.count(),
        'iscritti': Iscritto.objects.count(),
        'docenti': Docente.objects.count(),
        'corsi': Corso.objects.count(),
        'edizioni': EdizioneCorso.objects.count(),
        'iscr_anno': IscrizioneAnnoAccademico.objects.count(),
        'iscr_corso': IscrizioneCorso.objects.count(),
        'lezioni': Lezione.objects.count(),
    }

    log(f"  Anni Accademici:      {totali['anni']}")
    log(f"  Iscritti:             {totali['iscritti']}")
    log(f"  Docenti:              {totali['docenti']}")
    log(f"  Corsi:                {totali['corsi']}")
    log(f"  Edizioni Corsi:       {totali['edizioni']}")
    log(f"  Iscrizioni Anno:      {totali['iscr_anno']}")
    log(f"  Iscrizioni Corso:     {totali['iscr_corso']}")
    log(f"  Lezioni:              {totali['lezioni']}")

    # Verifica anno esempio
    log("\n📊 Verifica Anno 2023-2024:")
    anno_test = AnnoAccademico.objects.filter(anno='2023-2024').first()
    if anno_test:
        ed = EdizioneCorso.objects.filter(anno_accademico=anno_test).count()
        iscr = IscrizioneCorso.objects.filter(anno_accademico=anno_test).count()
        log(f"  - Edizioni: {ed}")
        log(f"  - Iscrizioni: {iscr}")

    log("="*70)


# MAIN
if __name__ == '__main__':
    # Inizializza log
    with open('fix_import_log.txt', 'w', encoding='utf-8') as f:
        f.write("UNIGEST - Fix Import Log\n")
        f.write("="*70 + "\n")

    log("="*70)
    log("UNIGEST - Fix Import Iscrizioni e Edizioni")
    log("="*70)

    risposta = input("\nVuoi procedere con il fix? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's', 'yes', 'y']:
        print("❌ Annullato")
        sys.exit(0)

    log("\n🚀 Inizio fix import...")

    # Esegui fix
    edizioni_nuove = fix_edizioni_mancanti()
    iscrizioni_nuove = fix_iscrizioni_corso()

    # Verifica finale
    verifica_finale()

    log("\n✅ Fix completato!")
    log("📄 Log salvato in: fix_import_log.txt")

    print(f"\n{'='*70}")
    print("RIEPILOGO:")
    print(f"{'='*70}")
    print(f"  Edizioni importate:     {edizioni_nuove}")
    print(f"  Iscrizioni importate:   {iscrizioni_nuove}")
    print(f"{'='*70}")
