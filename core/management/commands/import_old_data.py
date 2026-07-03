"""
UNIGEST - Import Old Data Command
File: core/management/commands/import_old_data.py
Descrizione: Script ottimizzato per importare i dati dal vecchio database Access/MySQL.
Include correzioni per il formato degli anni accademici e logiche dagli script utente.

Utilizzo:
    python manage.py import_old_data [--verbose] [--dry-run]
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
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula l\'importazione senza salvare modifiche definitive (usa get_or_create)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostra dettagli aggiuntivi durante l\'importazione',
        )

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
        self.stdout.write(self.style.SUCCESS('  UNIGEST - IMPORTAZIONE DATI OTTIMIZZATA'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        if self.dry_run:
            self.stdout.write(self.style.WARNING('!!! MODALITÀ DRY-RUN ATTIVA !!!\n'))

        # Ordine di esecuzione per rispettare i ForeignKey
        tasks = [
            ('Tabelle di Supporto', self.import_supporto),
            ('Anagrafiche (Docenti, Autorità)', self.import_staff),
            ('Iscritti e Coniugi', self.import_iscritti),
            ('Catalogo Corsi', self.import_catalogo),
            ('Anni e Quadrimestri', self.import_periodi),
            ('Edizioni Corsi Annuali', self.import_edizioni),
            ('Iscrizioni (Anno e Corsi)', self.import_iscrizioni),
            ('Lezioni effettuate', self.import_lezioni),
        ]

        for section_name, task_func in tasks:
            self.stdout.write(self.style.MIGRATE_LABEL(f'\n--- {section_name} ---'))
            try:
                task_func()
            except Exception as e:
                self.log(f"Errore critico nella sezione {section_name}: {e}", 'error')

        self.print_summary()

    def import_supporto(self):
        cursor = connections['old_database'].cursor()
        
        # Comuni
        cursor.execute("SELECT DISTINCT Paese FROM TAnagrafe WHERE Paese IS NOT NULL AND Paese != ''")
        for row in cursor.fetchall():
            if not self.dry_run:
                Comune.objects.get_or_create(id=row[0], defaults={'nome': f"Comune_{row[0]}"})
            self.stats['comuni'] += 1

        # Titoli Studio
        cursor.execute("SELECT TitoloStudio FROM TTitoloStudio")
        for row in cursor.fetchall():
            if row[0] and not self.dry_run:
                TitoloStudio.objects.get_or_create(descrizione=row[0])
                self.stats['titoli'] += 1

        # Professioni
        cursor.execute("SELECT ProfAtt FROM TProfAtt")
        for row in cursor.fetchall():
            if row[0] and not self.dry_run:
                ProfessioneAttuale.objects.get_or_create(descrizione=row[0])
                self.stats['prof_att'] += 1

        cursor.execute("SELECT ProfPass FROM TProfPass")
        for row in cursor.fetchall():
            if row[0] and not self.dry_run:
                ProfessionePassata.objects.get_or_create(descrizione=row[0])
                self.stats['prof_pass'] += 1

    def import_staff(self):
        cursor = connections['old_database'].cursor()
        
        # Docenti
        cursor.execute("SELECT ID, Prefisso, Insegnante, Telefono, Cellulare, Indirizzo, Paese, Email FROM TDocenti")
        for row in cursor.fetchall():
            try:
                if not self.dry_run:
                    Docente.objects.get_or_create(id=row[0], defaults={
                        'titolo': row[1] or '', 'nome': row[2] or 'Sconosciuto',
                        'telefono': row[3] or '', 'cellulare': row[4] or '',
                        'indirizzo': row[5] or '', 'comune_id': row[6] if row[6] else None,
                        'email': row[7] or '', 'attivo': True
                    })
                self.stats['docenti'] += 1
            except Exception as e:
                self.stats['errori'] += 1
                self.log(f"Errore docente {row[0]}: {e}", 'error')

        # Autorità
        cursor.execute("SELECT ID, Prefisso, Autorita, Carica, Email FROM TAutorita")
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
        cursor.execute("""
            SELECT Matr, `M/F`, Sig, Nominativo, Moglie, Indirizzo, Paese,
                   Telefono, Cellulare, Luogo, Nascita, CF, Pensionato
            FROM TAnagrafe
        """)
        
        iscritti_rows = cursor.fetchall()
        for row in iscritti_rows:
            try:
                if not self.dry_run:
                    Iscritto.objects.get_or_create(matricola=row[0], defaults={
                        'sesso': 'M' if row[1] == 'M' else 'F', 'titolo': row[2] or '',
                        'nominativo': row[3] or 'Sconosciuto', 'indirizzo': row[5] or '',
                        'comune_id': row[6] if row[6] else None, 'telefono': row[7] or '',
                        'cellulare': row[8] or '', 'luogo_nascita': row[9] or '',
                        'data_nascita': row[10] if row[10] else None, 'codice_fiscale': row[11] or None,
                        'e_pensionato': str(row[12]).lower() in ['si', 'sì', '1', 'true']
                    })
                self.stats['iscritti'] += 1
            except Exception as e:
                self.stats['errori'] += 1
                self.log(f"Errore iscritto {row[0]}: {e}", 'error')

        # Seconda passata per coniugi (Logica da collega_coniugi.py)
        if not self.dry_run:
            self.log("Collegamento coniugi...", 'important')
            for row in iscritti_rows:
                if row[4]: # Moglie (ID)
                    try:
                        marito = Iscritto.objects.get(matricola=row[0])
                        moglie = Iscritto.objects.get(matricola=row[4])
                        marito.coniuge = moglie
                        marito.save()
                    except:
                        pass

    def import_catalogo(self):
        cursor = connections['old_database'].cursor()
        
        # Categorie
        cursor.execute("SELECT IDCAT, Categoria FROM TCategorie")
        for row in cursor.fetchall():
            if not self.dry_run:
                CategoriaCorso.objects.get_or_create(id=row[0], defaults={'nome': row[1], 'ordine': row[0]})
            self.stats['categorie'] += 1

        # Gruppi
        cursor.execute("SELECT ID, Gruppo FROM TGruppi")
        for row in cursor.fetchall():
            if not self.dry_run:
                GruppoCorso.objects.get_or_create(id=row[0], defaults={'nome': row[1]})
            self.stats['gruppi'] += 1

        # Corsi (Master)
        cursor.execute("SELECT Codice, Corsi, Dettaglio, CAT, GRUPPO FROM TCorsi")
        for row in cursor.fetchall():
            try:
                if not self.dry_run:
                    Corso.objects.get_or_create(codice=row[0], defaults={
                        'nome': row[1] or f"Corso {row[0]}", 'descrizione': row[2] or '',
                        'categoria_id': row[3] if row[3] else None, 'gruppo_id': row[4] if row[4] else None
                    })
                self.stats['corsi'] += 1
            except Exception as e:
                self.stats['errori'] += 1

    def import_periodi(self):
        cursor = connections['old_database'].cursor()
        
        # Anni Accademici (FIX FORMATO: 2023/2024 -> 2023-2024)
        cursor.execute("SELECT AnnoAccademico FROM TAnnoAccademico ORDER BY progr DESC")
        for i, row in enumerate(cursor.fetchall()):
            if not row[0]: continue
            anno_fix = str(row[0]).replace('/', '-')
            try:
                if not self.dry_run:
                    anno_inizio = int(anno_fix.split('-')[0])
                    AnnoAccademico.objects.get_or_create(anno=anno_fix, defaults={
                        'data_inizio': datetime(anno_inizio, 10, 1).date(),
                        'data_fine': datetime(anno_inizio + 1, 5, 31).date(),
                        'attivo': i == 0
                    })
                self.stats['anni'] += 1
            except Exception as e:
                self.log(f"Errore anno {row[0]}: {e}", 'error')

        # Quadrimestri
        if not self.dry_run:
            Quadrimestre.objects.get_or_create(numero=1)
            Quadrimestre.objects.get_or_create(numero=2)

    def import_edizioni(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("""
            SELECT ID, Anno, Codice, Descrizione, Quadrimestre, Insegnante,
                   Assistente, Vice, Giorni, Dalle, Alle
            FROM TCorsiAnnualiDocenti
        """)
        for row in cursor.fetchall():
            try:
                anno_fix = str(row[1]).replace('/', '-')
                anno = AnnoAccademico.objects.filter(anno=anno_fix).first()
                corso = Corso.objects.filter(codice=row[2]).first()
                docente = Docente.objects.filter(id=row[5]).first()
                quad = Quadrimestre.objects.filter(numero=row[4]).first()

                if anno and corso and docente and quad and not self.dry_run:
                    EdizioneCorso.objects.get_or_create(id=row[0], defaults={
                        'anno_accademico': anno, 'corso': corso, 'quadrimestre': quad,
                        'docente': docente, 'descrizione_custom': row[3] or '',
                        'giorni_settimana': row[8] or '', 'ora_inizio': row[9] or '09:00',
                        'ora_fine': row[10] or '11:00'
                    })
                    self.stats['edizioni'] += 1
                elif not self.dry_run:
                    self.stats['errori'] += 1
            except Exception as e:
                self.stats['errori'] += 1

    def import_iscrizioni(self):
        cursor = connections['old_database'].cursor()
        
        # Iscrizioni Anno
        cursor.execute("SELECT AnnoAccademico, Matricola, Ricevuta, Data FROM TIscrizioneAnnoAccademico")
        for row in cursor.fetchall():
            try:
                anno_fix = str(row[0]).replace('/', '-')
                anno = AnnoAccademico.objects.filter(anno=anno_fix).first()
                iscritto = Iscritto.objects.filter(matricola=row[1]).first()
                if anno and iscritto and not self.dry_run:
                    IscrizioneAnnoAccademico.objects.get_or_create(
                        anno_accademico=anno, iscritto=iscritto,
                        defaults={'numero_ricevuta': row[2] or 0, 'data_iscrizione': row[3] or anno.data_inizio}
                    )
                    self.stats['isc_anno'] += 1
            except:
                self.stats['errori'] += 1

        # Iscrizioni Corsi
        cursor.execute("SELECT AnnoAccademico, Corso, Matricola, Ricevuta, Data FROM TFrequenzaCorsi")
        for row in cursor.fetchall():
            try:
                anno_fix = str(row[0]).replace('/', '-')
                anno = AnnoAccademico.objects.filter(anno=anno_fix).first()
                iscritto = Iscritto.objects.filter(matricola=row[2]).first()
                edizione = EdizioneCorso.objects.filter(anno_accademico=anno, corso__codice=row[1]).first()
                if anno and iscritto and edizione and not self.dry_run:
                    IscrizioneCorso.objects.get_or_create(
                        anno_accademico=anno, iscritto=iscritto, edizione_corso=edizione,
                        defaults={'numero_ricevuta': row[3] or 0, 'data_iscrizione': row[4] or anno.data_inizio}
                    )
                    self.stats['isc_corso'] += 1
            except:
                self.stats['errori'] += 1

    def import_lezioni(self):
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT ID_corso_annuale, data, descrizione, insegnante, presenze, ore FROM TPresenzeCorsisti")
        for row in cursor.fetchall():
            try:
                edizione = EdizioneCorso.objects.filter(id=row[0]).first()
                if edizione and row[1] and not self.dry_run:
                    Lezione.objects.get_or_create(
                        edizione_corso=edizione, data_lezione=row[1],
                        defaults={
                            'descrizione': row[2] or '',
                            'docente_id': row[3] if row[3] else edizione.docente_id,
                            'numero_presenti': row[4] or 0,
                            'ore_lezione': float(row[5]) if row[5] else 2.0
                        }
                    )
                    self.stats['lezioni'] += 1
            except:
                self.stats['errori'] += 1

    def print_summary(self):
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('  RIEPILOGO IMPORTAZIONE FINALE'))
        self.stdout.write('='*70)
        self.stdout.write(f"  • Comuni: {self.stats['comuni']} | Titoli: {self.stats['titoli']}")
        self.stdout.write(f"  • Professioni: {self.stats['prof_att']} attuali, {self.stats['prof_pass']} passate")
        self.stdout.write(f"  • Staff: {self.stats['docenti']} docenti, {self.stats['autorita']} autorità")
        self.stdout.write(f"  • Iscritti: {self.stats['iscritti']}")
        self.stdout.write(f"  • Catalogo: {self.stats['categorie']} cat, {self.stats['gruppi']} gruppi, {self.stats['corsi']} corsi")
        self.stdout.write(f"  • Periodi: {self.stats['anni']} anni accademici")
        self.stdout.write(f"  • Didattica: {self.stats['edizioni']} edizioni, {self.stats['lezioni']} lezioni")
        self.stdout.write(f"  • Iscrizioni: {self.stats['isc_anno']} annuali, {self.stats['isc_corso']} ai corsi")
        
        if self.stats['errori'] > 0:
            self.stdout.write(self.style.WARNING(f"\n  ⚠️ Record non importati per errori: {self.stats['errori']}"))
        
        self.stdout.write('\n' + '='*70 + '\n')
