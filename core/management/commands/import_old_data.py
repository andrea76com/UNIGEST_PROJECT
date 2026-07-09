"""
UNIGEST - Import Old Data Command
File: core/management/commands/import_old_data.py
Descrizione: Script v2.4 - FIX DEFINITIVO MAPPING E CATALOGO.
Corregge gli indici basandosi sulla diagnostica reale di UNIPIEVE.
"""

import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import connections
from core.models import (
    Comune, TitoloStudio, ProfessioneAttuale, ProfessionePassata,
    Iscritto, Docente, Autorita,
    CategoriaCorso, GruppoCorso, Corso, AnnoAccademico, Quadrimestre,
    EdizioneCorso, IscrizioneAnnoAccademico, IscrizioneCorso,
    Lezione
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Importa i dati dal vecchio database MySQL UNIPIEVE'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Simula l\'importazione')
        parser.add_argument('--verbose', action='store_true', help='Dettagli aggiuntivi')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = {
            'comuni': 0, 'titoli': 0, 'prof_att': 0, 'prof_pass': 0,
            'iscritti': 0, 'docenti': 0, 'autorita': 0,
            'categorie': 0, 'gruppi': 0, 'corsi': 0,
            'anni': 0, 'edizioni': 0, 'isc_anno': 0, 'isc_corso': 0,
            'lezioni': 0, 'errori': 0
        }

    def log(self, msg, level='info'):
        if level == 'error': self.stdout.write(self.style.ERROR(f"  ✗ {msg}"))
        elif level == 'warning': self.stdout.write(self.style.WARNING(f"  ⚠️ {msg}"))
        elif level == 'success': self.stdout.write(self.style.SUCCESS(f"  ✓ {msg}"))
        else:
            if self.verbose or level == 'important': self.stdout.write(f"  • {msg}")

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']

        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  UNIGEST - IMPORTAZIONE DATI FINALE (v2.4)'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        if not self.dry_run:
            for q in [0, 1, 2, 3]: Quadrimestre.objects.get_or_create(numero=q)
            Docente.objects.get_or_create(id=99999, defaults={'nome': 'DOCENTE GENERICO', 'attivo': True})
            Corso.objects.get_or_create(codice=0, defaults={'nome': 'CORSO GENERICO'})
        else:
            # Crea fallback fittizi per evitare errori durante il dry-run
            from unittest.mock import MagicMock
            self.mock_docente = MagicMock(spec=Docente, id=99999)
            self.mock_corso = MagicMock(spec=Corso, codice=0)

        tasks = [
            ('Tabelle Supporto', self.import_supporto),
            ('Staff Docente', self.import_staff),
            ('Anagrafica Iscritti', self.import_iscritti),
            ('Catalogo Corsi', self.import_catalogo),
            ('Anni Accademici', self.import_periodi),
            ('Edizioni Annuali', self.import_edizioni),
            ('Iscrizioni', self.import_iscrizioni),
            ('Registro Lezioni', self.import_lezioni),
        ]

        for section_name, task_func in tasks:
            self.stdout.write(self.style.MIGRATE_LABEL(f'\n--- {section_name} ---'))
            try:
                task_func()
            except Exception as e:
                self.log(f"Errore critico in {section_name}: {e}", 'error')

        self.print_summary()

    def import_supporto(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT DISTINCT Paese FROM `TAnagrafe` WHERE Paese IS NOT NULL AND Paese != ''")
        for row in cursor.fetchall():
            if not self.dry_run: Comune.objects.get_or_create(id=row[0], defaults={'nome': f"Comune_{row[0]}"})
            self.stats['comuni'] += 1

        cursor.execute("SELECT TitoloStudio FROM `TTitoloStudio`")
        for row in cursor.fetchall():
            if row[0] and not self.dry_run: TitoloStudio.objects.get_or_create(descrizione=row[0])
            self.stats['titoli'] += 1

        for table, key, model in [('TProfAtt', 'prof_att', ProfessioneAttuale), ('TProfPass', 'prof_pass', ProfessionePassata)]:
            cursor.execute(f"SELECT * FROM `{table}`")
            for row in cursor.fetchall():
                if row[0] and not self.dry_run: model.objects.get_or_create(descrizione=row[0])
                self.stats[key] += 1

    def import_staff(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT * FROM `TDocenti`")
        for row in cursor.fetchall():
            try:
                if not self.dry_run and row[0] != 0:
                    Docente.objects.get_or_create(id=row[0], defaults={
                        'titolo': row[1] or '', 'nome': row[2] or 'Sconosciuto',
                        'telefono': row[3] or '', 'cellulare': row[4] or '',
                        'indirizzo': row[5] or '', 'comune_id': row[6] if row[6] != 0 else None,
                        'email': row[8] or '', 'attivo': True
                    })
                self.stats['docenti'] += 1
            except: self.stats['errori'] += 1

        cursor.execute("SELECT * FROM `TAutorita`")
        for row in cursor.fetchall():
            try:
                if not self.dry_run:
                    Autorita.objects.get_or_create(id=row[0], defaults={
                        'titolo': row[1] or '', 'nome': row[2] or 'Sconosciuto',
                        'carica': row[3] or '', 'email': row[8] or '', 'attivo': True
                    })
                self.stats['autorita'] += 1
            except: self.stats['errori'] += 1

    def import_iscritti(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT * FROM `TAnagrafe`")
        rows = cursor.fetchall()
        for row in rows:
            try:
                if not self.dry_run:
                    cf = str(row[18]) if len(row) > 18 and row[18] else None
                    if cf and len(cf) < 10: cf = None
                    ts = TitoloStudio.objects.filter(descrizione=row[11]).first() if row[11] else None
                    pa = ProfessioneAttuale.objects.filter(descrizione=row[12]).first() if row[12] else None
                    pp = ProfessionePassata.objects.filter(descrizione=row[13]).first() if row[13] else None

                    Iscritto.objects.get_or_create(matricola=row[0], defaults={
                        'sesso': 'M' if row[1] == 'M' else 'F', 'titolo': row[2] or '',
                        'nominativo': row[3] or 'Sconosciuto', 'indirizzo': row[5] or '',
                        'comune_id': row[6] if row[6] != 0 else None, 'telefono': row[7] or '',
                        'cellulare': row[8] or '', 'luogo_nascita': row[9] or '',
                        'data_nascita': row[10] if isinstance(row[10], datetime) else None,
                        'codice_fiscale': cf, 'email': row[16] or '',
                        'ha_whatsapp': bool(row[17]), 'riceve_posta': bool(row[15]),
                        'titolo_studio': ts, 'professione_attuale': pa, 'professione_passata': pp,
                        'e_pensionato': str(row[14]).lower() in ['si', 'sì', '1', 'true', 'attivo']
                    })
                self.stats['iscritti'] += 1
            except Exception as e:
                self.stats['errori'] += 1
                if self.verbose: self.log(f"Errore iscritto {row[0]}: {e}", 'error')

        if not self.dry_run:
            for row in rows:
                if row[4] and row[4] != 0:
                    try:
                        m1 = Iscritto.objects.get(matricola=row[0])
                        m2 = Iscritto.objects.get(matricola=row[4])
                        m1.coniuge = m2
                        m1.save()
                    except: pass

    def import_catalogo(self):
        cursor = connections['old_database'].cursor()
        for table, model, key in [('TCategorie', CategoriaCorso, 'categorie'), ('TGruppi', GruppoCorso, 'gruppi')]:
            cursor.execute(f"SELECT * FROM `{table}`")
            for row in cursor.fetchall():
                try:
                    if not self.dry_run:
                        if key == 'categorie': model.objects.get_or_create(id=row[0], defaults={'nome': row[1], 'ordine': row[0]})
                        else: model.objects.get_or_create(id=row[0], defaults={'nome': row[1]})
                    self.stats[key] += 1
                except: self.stats['errori'] += 1

        cursor.execute("SELECT * FROM `TCorsi`")
        for row in cursor.fetchall():
            try:
                if not self.dry_run:
                    Corso.objects.get_or_create(codice=row[0], defaults={
                        'nome': row[1] or f"Corso {row[0]}", 'descrizione': row[2] or '',
                        'categoria_id': row[3] if row[3] != 0 else None, 'gruppo_id': row[4] if row[4] != 0 else None
                    })
                self.stats['corsi'] += 1
            except: self.stats['errori'] += 1

    def import_periodi(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT * FROM `TAnnoAccademico` ORDER BY progr DESC")
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
        cursor.execute("SELECT * FROM `TCorsiAnnualiDocenti`")
        for row in cursor.fetchall():
            try:
                anno_val = str(row[1]).replace('/', '-')
                if not self.dry_run:
                    anno = AnnoAccademico.objects.filter(anno=anno_val).first()
                    corso = Corso.objects.filter(codice=row[2]).first() or Corso.objects.get(codice=0)
                    docente = Docente.objects.filter(id=row[5]).first() or Docente.objects.get(id=99999)
                else:
                    anno = AnnoAccademico.objects.filter(anno=anno_val).first()
                    corso = Corso.objects.filter(codice=row[2]).first() or self.mock_corso
                    docente = Docente.objects.filter(id=row[5]).first() or self.mock_docente
                    q_num = row[4] if row[4] in [0, 1, 2, 3] else 0
                    if anno:
                        EdizioneCorso.objects.get_or_create(id=row[0], defaults={
                            'anno_accademico': anno, 'corso': corso, 'quadrimestre_id': q_num,
                            'docente': docente, 'descrizione_custom': row[3] or '',
                            'giorni_settimana': row[8] or '', 'ora_inizio': row[9] or '09:00',
                            'ora_fine': row[10] or '11:00'
                        })
                        self.stats['edizioni'] += 1
                    else: self.stats['errori'] += 1
                else: self.stats['edizioni'] += 1
            except: self.stats['errori'] += 1

    def import_iscrizioni(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT * FROM `TIscrizioneAnnoAccademico`")
        for row in cursor.fetchall():
            try:
                if not self.dry_run:
                    anno = AnnoAccademico.objects.filter(anno=str(row[0]).replace('/', '-')).first()
                    isc = Iscritto.objects.filter(matricola=row[1]).first()
                    if anno and isc: IscrizioneAnnoAccademico.objects.get_or_create(anno_accademico=anno, iscritto=isc, defaults={'numero_ricevuta': row[2] or 0, 'data_iscrizione': row[3] if isinstance(row[3], datetime) else anno.data_inizio})
                self.stats['isc_anno'] += 1
            except: self.stats['errori'] += 1

        cursor.execute("SELECT * FROM `TFrequenzaCorsi`")
        for row in cursor.fetchall():
            try:
                if not self.dry_run:
                    anno = AnnoAccademico.objects.filter(anno=str(row[0]).replace('/', '-')).first()
                    isc = Iscritto.objects.filter(matricola=row[2]).first()
                    ediz = EdizioneCorso.objects.filter(anno_accademico=anno, corso__codice=row[1]).first()
                    if anno and isc and ediz: IscrizioneCorso.objects.get_or_create(anno_accademico=anno, iscritto=isc, edizione_corso=ediz, defaults={'numero_ricevuta': row[3] or 0, 'data_iscrizione': row[4] if isinstance(row[4], datetime) else anno.data_inizio})
                self.stats['isc_corso'] += 1
            except: self.stats['errori'] += 1

    def import_lezioni(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT * FROM `TPresenzeCorsisti`")
        for row in cursor.fetchall():
            try:
                if not self.dry_run:
                    ediz = EdizioneCorso.objects.filter(id=row[0]).first()
                    if ediz and row[1]:
                        doc_id = row[4] if Docente.objects.filter(id=row[4]).exists() else ediz.docente_id
                        Lezione.objects.get_or_create(edizione_corso=ediz, data_lezione=row[1], defaults={'descrizione': row[3] or '', 'docente_id': doc_id, 'numero_presenti': row[5] or 0, 'ore_lezione': float(row[6]) if row[6] else 2.0})
                self.stats['lezioni'] += 1
            except: self.stats['errori'] += 1

    def print_summary(self):
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS(f"  RIEPILOGO IMPORTAZIONE FINALE (v2.4{' - DRY RUN' if self.dry_run else ''})"))
        self.stdout.write('='*70)
        self.stdout.write(f"  • Comuni/Titoli: {self.stats['comuni']} / {self.stats['titoli']}")
        self.stdout.write(f"  • Staff: {self.stats['docenti']} docenti, {self.stats['autorita']} autorità")
        self.stdout.write(f"  • Iscritti: {self.stats['iscritti']}")
        self.stdout.write(f"  • Catalogo: {self.stats['categorie']} cat, {self.stats['gruppi']} gruppi, {self.stats['corsi']} corsi")
        self.stdout.write(f"  • Periodi: {self.stats['anni']} anni accademici")
        self.stdout.write(f"  • Didattica: {self.stats['edizioni']} edizioni, {self.stats['lezioni']} lezioni")
        self.stdout.write(f"  • Iscrizioni: {self.stats['isc_anno']} annuali, {self.stats['isc_corso']} ai corsi")
        if self.stats['errori'] > 0: self.stdout.write(self.style.WARNING(f"\n  ⚠️ Record saltati o con errori: {self.stats['errori']}"))
        self.stdout.write('\n' + '='*70 + '\n')
