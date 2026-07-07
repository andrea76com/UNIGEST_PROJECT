"""
UNIGEST - Import Old Data Command
File: core/management/commands/import_old_data.py
Descrizione: Script v2.2 - Massima resilienza e gestione fallback.
Risolve i crash causati dai valori 0 e garantisce il popolamento del catalogo.
"""

import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import connections, transaction
from core.models import (
    Comune, TitoloStudio, ProfessioneAttuale, ProfessionePassata,
    Iscritto, Docente, Autorita,
    CategoriaCorso, GruppoCorso, Corso, AnnoAccademico, Quadrimestre,
    EdizioneCorso, IscrizioneAnnoAccademico, IscrizioneCorso,
    Lezione, PresenzaLezione
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Importa i dati dal vecchio database MySQL UNIPIEVE'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Simula l\'importazione')
        parser.add_argument('--verbose', action='store_true', help='Dettagli aggiuntivi')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dry_run = False
        self.verbose = False
        self.stats = {
            'comuni': 0, 'titoli': 0, 'prof_att': 0, 'prof_pass': 0,
            'iscritti': 0, 'docenti': 0, 'autorita': 0,
            'categorie': 0, 'gruppi': 0, 'corsi': 0,
            'anni': 0, 'edizioni': 0, 'isc_anno': 0, 'isc_corso': 0,
            'lezioni': 0, 'errori': 0
        }

    def log(self, msg, level='info'):
        if level == 'error':
            self.stdout.write(self.style.ERROR(f"  ✗ {msg}"))
        elif level == 'warning':
            self.stdout.write(self.style.WARNING(f"  ⚠️ {msg}"))
        elif level == 'success':
            self.stdout.write(self.style.SUCCESS(f"  ✓ {msg}"))
        else:
            if self.verbose or level == 'important':
                self.stdout.write(f"  • {msg}")

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']

        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  UNIGEST - IMPORTAZIONE DATI RESILIENTE (v2.2)'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Inizializzazione Quadrimestri
        if not self.dry_run:
            for q in [0, 1, 2, 3]:
                Quadrimestre.objects.get_or_create(numero=q)

        # Creazione record di fallback per evitare fallimenti Foreign Key
        if not self.dry_run:
            Docente.objects.get_or_create(nome='DOCENTE GENERICO', defaults={'id': 99999, 'attivo': True})
            Corso.objects.get_or_create(codice=0, defaults={'nome': 'CORSO GENERICO'})

        tasks = [
            ('Supporto', self.import_supporto),
            ('Staff', self.import_staff),
            ('Iscritti', self.import_iscritti),
            ('Catalogo', self.import_catalogo),
            ('Periodi', self.import_periodi),
            ('Didattica', self.import_edizioni),
            ('Iscrizioni', self.import_iscrizioni),
            ('Lezioni', self.import_lezioni),
        ]

        for section_name, task_func in tasks:
            self.stdout.write(self.style.MIGRATE_LABEL(f'\n--- {section_name} ---'))
            try:
                task_func()
            except Exception as e:
                self.log(f"Errore fatale nella sezione {section_name}: {e}", 'error')

        self.print_summary()

    def import_supporto(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT DISTINCT Paese FROM `TAnagrafe` WHERE Paese IS NOT NULL AND Paese != ''")
        for row in cursor.fetchall():
            if not self.dry_run:
                Comune.objects.get_or_create(id=row[0], defaults={'nome': f"Comune_{row[0]}"})
            self.stats['comuni'] += 1

        cursor.execute("SELECT TitoloStudio FROM `TTitoloStudio`")
        for row in cursor.fetchall():
            if row[0] and not self.dry_run:
                TitoloStudio.objects.get_or_create(descrizione=row[0])
            self.stats['titoli'] += 1

        for table, key in [('TProfAtt', 'prof_att'), ('TProfPass', 'prof_pass')]:
            cursor.execute(f"SELECT * FROM `{table}`")
            for row in cursor.fetchall():
                if row[0] and not self.dry_run:
                    if key == 'prof_att': ProfessioneAttuale.objects.get_or_create(descrizione=row[0])
                    else: ProfessionePassata.objects.get_or_create(descrizione=row[0])
                self.stats[key] += 1

    def import_staff(self):
        cursor = connections['old_database'].cursor()
        
        cursor.execute("SELECT ID, Prefisso, Insegnante, Telefono, Cellulare, Indirizzo, Paese, Email FROM `TDocenti`")
        for row in cursor.fetchall():
            try:
                if not self.dry_run and row[0] != 0:
                    Docente.objects.get_or_create(id=row[0], defaults={
                        'titolo': row[1] or '', 'nome': row[2] or 'Sconosciuto',
                        'telefono': row[3] or '', 'cellulare': row[4] or '',
                        'indirizzo': row[5] or '', 'comune_id': row[6] if row[6] and row[6] != 0 else None,
                        'email': row[7] or '', 'attivo': True
                    })
                self.stats['docenti'] += 1
            except Exception as e:
                self.stats['errori'] += 1

        cursor.execute("SELECT ID, Prefisso, Autorita, Carica, Email FROM `TAutorita`")
        for row in cursor.fetchall():
            try:
                if not self.dry_run:
                    Autorita.objects.get_or_create(id=row[0], defaults={
                        'titolo': row[1] or '', 'nome': row[2] or 'Sconosciuto',
                        'carica': row[3] or '', 'email': row[4] or '', 'attivo': True
                    })
                self.stats['autorita'] += 1
            except Exception as e:
                self.stats['errori'] += 1

    def import_iscritti(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT Matr, `M/F`, Sig, Nominativo, Moglie, Indirizzo, Paese, Telefono, Cellulare, Luogo, Nascita, CF, Pensionato FROM `TAnagrafe`")
        rows = cursor.fetchall()
        for row in rows:
            try:
                if not self.dry_run:
                    cf = str(row[11]) if row[11] else None
                    if cf and len(cf) < 10: cf = None
                    Iscritto.objects.get_or_create(matricola=row[0], defaults={
                        'sesso': 'M' if row[1] == 'M' else 'F', 'titolo': row[2] or '',
                        'nominativo': row[3] or 'Sconosciuto', 'indirizzo': row[5] or '',
                        'comune_id': row[6] if row[6] and row[6] != 0 else None,
                        'data_nascita': row[10] if isinstance(row[10], datetime) else None,
                        'codice_fiscale': cf,
                        'e_pensionato': str(row[12]).lower() in ['si', 'sì', '1', 'true', 'attivo']
                    })
                self.stats['iscritti'] += 1
            except:
                self.stats['errori'] += 1

        if not self.dry_run:
            self.log("Collegamento coniugi...", 'important')
            for row in rows:
                if row[4] and row[4] != 0:
                    try:
                        marito = Iscritto.objects.get(matricola=row[0])
                        moglie = Iscritto.objects.get(matricola=row[4])
                        marito.coniuge = moglie
                        marito.save()
                    except: pass

    def import_catalogo(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT IDCAT, Categoria FROM `TCategorie`")
        for row in cursor.fetchall():
            try:
                if not self.dry_run:
                    CategoriaCorso.objects.get_or_create(id=row[0], defaults={'nome': row[1], 'ordine': row[0]})
                self.stats['categorie'] += 1
            except: self.stats['errori'] += 1

        cursor.execute("SELECT ID, Gruppo FROM `TGruppi`")
        for row in cursor.fetchall():
            try:
                if not self.dry_run:
                    GruppoCorso.objects.get_or_create(id=row[0], defaults={'nome': row[1]})
                self.stats['gruppi'] += 1
            except: self.stats['errori'] += 1

        cursor.execute("SELECT Codice, Corsi, Dettaglio, CAT, GRUPPO FROM `TCorsi`")
        for row in cursor.fetchall():
            try:
                if not self.dry_run:
                    cat = row[3] if row[3] and row[3] != 0 else None
                    grp = row[4] if row[4] and row[4] != 0 else None
                    Corso.objects.get_or_create(codice=row[0], defaults={
                        'nome': row[1] or f"Corso {row[0]}", 'descrizione': row[2] or '',
                        'categoria_id': cat, 'gruppo_id': grp
                    })
                self.stats['corsi'] += 1
            except: self.stats['errori'] += 1

    def import_periodi(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT AnnoAccademico FROM `TAnnoAccademico` ORDER BY progr DESC")
        for i, row in enumerate(cursor.fetchall()):
            if not row[0]: continue
            anno_fix = str(row[0]).replace('/', '-')
            try:
                if not self.dry_run:
                    a_start = int(anno_fix.split('-')[0]) if anno_fix.split('-')[0].isdigit() else 2000
                    AnnoAccademico.objects.get_or_create(anno=anno_fix, defaults={
                        'data_inizio': datetime(a_start, 10, 1).date(),
                        'data_fine': datetime(a_start + 1, 5, 31).date(),
                        'attivo': i == 0
                    })
                self.stats['anni'] += 1
            except: self.stats['errori'] += 1

    def import_edizioni(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT ID, Anno, Codice, Descrizione, Quadrimestre, Insegnante, Giorni, Dalle, Alle FROM `TCorsiAnnualiDocenti`")
        for row in cursor.fetchall():
            try:
                anno_fix = str(row[1]).replace('/', '-')
                anno = AnnoAccademico.objects.filter(anno=anno_fix).first()
                corso = Corso.objects.filter(codice=row[2]).first() or Corso.objects.get(codice=0)
                docente = Docente.objects.filter(id=row[5]).first() or Docente.objects.get(nome='DOCENTE GENERICO')
                q_num = row[4] if row[4] in [0, 1, 2, 3] else 0
                quad = Quadrimestre.objects.get(numero=q_num)

                if anno and not self.dry_run:
                    EdizioneCorso.objects.get_or_create(id=row[0], defaults={
                        'anno_accademico': anno, 'corso': corso, 'quadrimestre': quad,
                        'docente': docente, 'descrizione_custom': row[3] or '',
                        'giorni_settimana': row[6] or '', 'ora_inizio': row[7] or '09:00',
                        'ora_fine': row[8] or '11:00'
                    })
                self.stats['edizioni'] += 1
            except Exception as e:
                self.stats['errori'] += 1

    def import_iscrizioni(self):
        cursor = connections['old_database'].cursor()
        # Annuali
        cursor.execute("SELECT AnnoAccademico, Matricola, Ricevuta, Data FROM `TIscrizioneAnnoAccademico`")
        for row in cursor.fetchall():
            try:
                anno = AnnoAccademico.objects.filter(anno=str(row[0]).replace('/', '-')).first()
                iscritto = Iscritto.objects.filter(matricola=row[1]).first()
                if anno and iscritto and not self.dry_run:
                    IscrizioneAnnoAccademico.objects.get_or_create(anno_accademico=anno, iscritto=iscritto, defaults={'numero_ricevuta': row[2] or 0, 'data_iscrizione': row[3] if isinstance(row[3], datetime) else anno.data_inizio})
                self.stats['isc_anno'] += 1
            except: self.stats['errori'] += 1

        # Ai Corsi
        cursor.execute("SELECT AnnoAccademico, Corso, Matricola, Ricevuta, Data FROM `TFrequenzaCorsi`")
        for row in cursor.fetchall():
            try:
                anno = AnnoAccademico.objects.filter(anno=str(row[0]).replace('/', '-')).first()
                iscritto = Iscritto.objects.filter(matricola=row[2]).first()
                edizione = EdizioneCorso.objects.filter(anno_accademico=anno, corso__codice=row[1]).first()
                if anno and iscritto and edizione and not self.dry_run:
                    IscrizioneCorso.objects.get_or_create(anno_accademico=anno, iscritto=iscritto, edizione_corso=edizione, defaults={'numero_ricevuta': row[3] or 0, 'data_iscrizione': row[4] if isinstance(row[4], datetime) else anno.data_inizio})
                self.stats['isc_corso'] += 1
            except: self.stats['errori'] += 1

    def import_lezioni(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT ID_corso_annuale, data, descrizione, insegnante, presenze, ore FROM `TPresenzeCorsisti`")
        for row in cursor.fetchall():
            try:
                edizione = EdizioneCorso.objects.filter(id=row[0]).first()
                if edizione and row[1] and not self.dry_run:
                    Lezione.objects.get_or_create(edizione_corso=edizione, data_lezione=row[1], defaults={'descrizione': row[2] or '', 'docente_id': row[3] if Docente.objects.filter(id=row[3]).exists() else edizione.docente_id, 'numero_presenti': row[4] or 0, 'ore_lezione': float(row[5]) if row[5] else 2.0})
                self.stats['lezioni'] += 1
            except: self.stats['errori'] += 1

    def print_summary(self):
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('  RIEPILOGO IMPORTAZIONE FINALE (v2.2)'))
        self.stdout.write('='*70)
        self.stdout.write(f"  • Comuni: {self.stats['comuni']} | Titoli: {self.stats['titoli']}")
        self.stdout.write(f"  • Staff: {self.stats['docenti']} docenti, {self.stats['autorita']} autorità")
        self.stdout.write(f"  • Iscritti: {self.stats['iscritti']}")
        self.stdout.write(f"  • Catalogo: {self.stats['categorie']} cat, {self.stats['gruppi']} gruppi, {self.stats['corsi']} corsi")
        self.stdout.write(f"  • Periodi: {self.stats['anni']} anni accademici")
        self.stdout.write(f"  • Didattica: {self.stats['edizioni']} edizioni, {self.stats['lezioni']} lezioni")
        self.stdout.write(f"  • Iscrizioni: {self.stats['isc_anno']} annuali, {self.stats['isc_corso']} ai corsi")
        if self.stats['errori'] > 0: self.stdout.write(self.style.WARNING(f"\n  ⚠️ Record saltati o con errori: {self.stats['errori']}"))
        self.stdout.write('\n' + '='*70 + '\n')
