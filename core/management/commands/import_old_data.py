"""
UNIGEST - Import Old Data Command
File: core/management/commands/import_old_data.py
Descrizione: Script per importare i dati dal vecchio database Access/MySQL

Utilizzo:
    python manage.py import_old_data
    
Opzioni:
    --dry-run : Simula l'importazione senza salvare i dati
    --verbose : Mostra dettagli aggiuntivi durante l'importazione
"""

from django.core.management.base import BaseCommand
from django.db import connections, transaction
from core.models import (
    Comune, TitoloStudio, ProfessioneAttuale, ProfessionePassata,
    Iscritto, Docente, Autorita,
    CategoriaCorso, GruppoCorso, Corso, AnnoAccademico, Quadrimestre,
    EdizioneCorso, IscrizioneAnnoAccademico, IscrizioneCorso,
    Lezione, PresenzaLezione
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Importa i dati dal vecchio database MySQL'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula l\'importazione senza salvare',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostra dettagli aggiuntivi',
        )
    
    def __init__(self):
        super().__init__()
        self.dry_run = False
        self.verbose = False
        self.stats = {
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
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('UNIGEST - Importazione Dati dal Vecchio Database'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('MODALITÀ DRY-RUN: I dati non verranno salvati\n'))
        
        try:
            # Esegui importazione in transazione
            with transaction.atomic():
                # 1. Importa tabelle di supporto
                self.import_comuni()
                self.import_titoli_studio()
                self.import_professioni()
                
                # 2. Importa anagrafiche
                self.import_docenti()
                self.import_autorita()
                self.import_iscritti()
                
                # 3. Importa corsi
                self.import_categorie()
                self.import_gruppi()
                self.import_corsi()
                self.import_anni_accademici()
                self.import_quadrimestri()
                
                # 4. Importa edizioni e iscrizioni
                self.import_edizioni_corsi()
                self.import_iscrizioni_anno()
                self.import_iscrizioni_corso()
                
                # 5. Importa lezioni e presenze
                self.import_lezioni()
                
                # Se è dry-run, rollback
                if self.dry_run:
                    raise Exception("DRY-RUN: Rollback transaction")
        
        except Exception as e:
            if self.dry_run:
                self.stdout.write(self.style.WARNING('\n✓ Dry-run completato con successo'))
            else:
                self.stdout.write(self.style.ERROR(f'\n✗ Errore durante l\'importazione: {str(e)}'))
                raise
        
        # Mostra statistiche
        self.print_stats()
    
    def import_comuni(self):
        """Importa comuni dal vecchio database"""
        self.stdout.write('\n📍 Importazione Comuni...')
        
        cursor = connections['old_database'].cursor()
        
        # Nota: Nel vecchio DB i comuni sono referenziati ma potrebbero non avere una tabella dedicata
        # Estraiamo i comuni unici dall'anagrafe
        cursor.execute("SELECT DISTINCT Paese FROM TAnagrafe WHERE Paese IS NOT NULL AND Paese != ''")
        
        for row in cursor.fetchall():
            paese_id = row[0]
            # Cerca di ricavare il nome del comune (potrebbe essere solo un ID)
            # Qui dovresti avere una tabella di lookup per i comuni, altrimenti usiamo l'ID
            nome = f"Comune_{paese_id}"  # Placeholder
            
            if not self.dry_run:
                Comune.objects.get_or_create(
                    id=paese_id,
                    defaults={'nome': nome}
                )
            self.stats['comuni'] += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["comuni"]} comuni importati'))
    
    def import_titoli_studio(self):
        """Importa titoli di studio"""
        self.stdout.write('\n📚 Importazione Titoli di Studio...')
        
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT TitoloStudio FROM TTitoloStudio")
        
        for row in cursor.fetchall():
            if row[0] and not self.dry_run:
                TitoloStudio.objects.get_or_create(descrizione=row[0])
            self.stats['titoli_studio'] += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["titoli_studio"]} titoli importati'))
    
    def import_professioni(self):
        """Importa professioni"""
        self.stdout.write('\n💼 Importazione Professioni...')
        
        cursor = connections['old_database'].cursor()
        
        # Professioni attuali
        cursor.execute("SELECT ProfAtt FROM TProfAtt")
        for row in cursor.fetchall():
            if row[0] and not self.dry_run:
                ProfessioneAttuale.objects.get_or_create(descrizione=row[0])
            self.stats['professioni_attuali'] += 1
        
        # Professioni passate
        cursor.execute("SELECT ProfPass FROM TProfPass")
        for row in cursor.fetchall():
            if row[0] and not self.dry_run:
                ProfessionePassata.objects.get_or_create(descrizione=row[0])
            self.stats['professioni_passate'] += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {self.stats["professioni_attuali"]} prof. attuali, '
            f'{self.stats["professioni_passate"]} prof. passate'
        ))
    
    def import_docenti(self):
        """Importa docenti"""
        self.stdout.write('\n👨‍🏫 Importazione Docenti...')
        
        cursor = connections['old_database'].cursor()
        cursor.execute("""
            SELECT ID, Prefisso, Insegnante, Telefono, Cellulare, 
                   Indirizzo, Paese, Note, Email
            FROM TDocenti
        """)
        
        for row in cursor.fetchall():
            if not self.dry_run:
                try:
                    Docente.objects.create(
                        id=row[0],
                        titolo=row[1] or '',
                        nome=row[2] or 'Sconosciuto',
                        telefono=row[3] or '',
                        cellulare=row[4] or '',
                        indirizzo=row[5] or '',
                        comune_id=row[6] if row[6] else None,
                        note=row[7] or '',
                        email=row[8] or '',
                        attivo=True
                    )
                    self.stats['docenti'] += 1
                except Exception as e:
                    self.stats['errori'] += 1
                    if self.verbose:
                        self.stdout.write(self.style.ERROR(f'    Errore docente {row[0]}: {str(e)}'))
            else:
                self.stats['docenti'] += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["docenti"]} docenti importati'))
    
    def import_autorita(self):
        """Importa autorità"""
        self.stdout.write('\n🏛️  Importazione Autorità...')
        
        cursor = connections['old_database'].cursor()
        cursor.execute("""
            SELECT ID, Prefisso, Autorita, Carica, Indirizzo, 
                   Paese, Note, Attivo, Email
            FROM TAutorita
        """)
        
        for row in cursor.fetchall():
            if not self.dry_run:
                try:
                    Autorita.objects.create(
                        id=row[0],
                        titolo=row[1] or '',
                        nome=row[2] or 'Sconosciuto',
                        carica=row[3] or '',
                        indirizzo=row[4] or '',
                        comune_id=row[5] if row[5] else None,
                        note=row[6] or '',
                        attivo=bool(row[7]) if row[7] is not None else True,
                        email=row[8] or ''
                    )
                    self.stats['autorita'] += 1
                except Exception as e:
                    self.stats['errori'] += 1
                    if self.verbose:
                        self.stdout.write(self.style.ERROR(f'    Errore autorità {row[0]}: {str(e)}'))
            else:
                self.stats['autorita'] += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["autorita"]} autorità importate'))
    
    def import_iscritti(self):
        """Importa iscritti"""
        self.stdout.write('\n👥 Importazione Iscritti...')
        
        cursor = connections['old_database'].cursor()
        cursor.execute("""
            SELECT Matr, `M/F`, Sig, Nominativo, Moglie, Indirizzo, Paese,
                   Telefono, Cellulare, Luogo, Nascita, TitoloStudio, 
                   ProfAtt, ProfPass, Pensionato, Posta, Email, Whatsapp, CF
            FROM TAnagrafe
        """)
        
        # Prima passata: crea tutti gli iscritti senza coniuge
        iscritti_map = {}
        for row in cursor.fetchall():
            if not self.dry_run:
                try:
                    # Converti pensionato in boolean
                    pensionato = False
                    if row[14]:
                        pensionato = str(row[14]).lower() in ['si', 'sì', 'yes', '1', 'true']
                    
                    iscritto = Iscritto.objects.create(
                        matricola=row[0],
                        sesso='M' if row[1] == 'M' else 'F',
                        titolo=row[2] or '',
                        nominativo=row[3] or 'Sconosciuto',
                        indirizzo=row[5] or '',
                        comune_id=row[6] if row[6] else None,
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
                    self.stats['iscritti'] += 1
                    
                except Exception as e:
                    self.stats['errori'] += 1
                    if self.verbose:
                        self.stdout.write(self.style.ERROR(f'    Errore iscritto {row[0]}: {str(e)}'))
            else:
                self.stats['iscritti'] += 1
        
        # Seconda passata: collega i coniugi
        if not self.dry_run:
            for matricola, (iscritto, moglie_id) in iscritti_map.items():
                if moglie_id and moglie_id in iscritti_map:
                    iscritto.coniuge = iscritti_map[moglie_id][0]
                    iscritto.save()
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["iscritti"]} iscritti importati'))
    
    def import_categorie(self):
        """Importa categorie corsi"""
        self.stdout.write('\n📂 Importazione Categorie Corsi...')
        
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT IDCAT, Categoria FROM TCategorie")
        
        for row in cursor.fetchall():
            if row[1] and not self.dry_run:
                CategoriaCorso.objects.get_or_create(
                    id=row[0],
                    defaults={'nome': row[1], 'ordine': row[0]}
                )
            self.stats['categorie'] += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["categorie"]} categorie importate'))
    
    def import_gruppi(self):
        """Importa gruppi corsi"""
        self.stdout.write('\n📦 Importazione Gruppi Corsi...')
        
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT ID, Gruppo FROM TGruppi")
        
        for row in cursor.fetchall():
            if row[1] and not self.dry_run:
                GruppoCorso.objects.get_or_create(
                    id=row[0],
                    defaults={'nome': row[1]}
                )
            self.stats['gruppi'] += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["gruppi"]} gruppi importati'))
    
    def import_corsi(self):
        """Importa corsi"""
        self.stdout.write('\n📖 Importazione Corsi...')
        
        cursor = connections['old_database'].cursor()
        cursor.execute("""
            SELECT Codice, Corsi, Dettaglio, CAT, GRUPPO, Visibile
            FROM TCorsi
        """)
        
        for row in cursor.fetchall():
            if not self.dry_run:
                try:
                    Corso.objects.create(
                        codice=row[0],
                        nome=row[1] or 'Corso senza nome',
                        descrizione=row[2] or '',
                        categoria_id=row[3] if row[3] else None,
                        gruppo_id=row[4] if row[4] else None,
                        visibile=bool(row[5]) if row[5] is not None else True
                    )
                    self.stats['corsi'] += 1
                except Exception as e:
                    self.stats['errori'] += 1
                    if self.verbose:
                        self.stdout.write(self.style.ERROR(f'    Errore corso {row[0]}: {str(e)}'))
            else:
                self.stats['corsi'] += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["corsi"]} corsi importati'))
    
    def import_anni_accademici(self):
        """Importa anni accademici"""
        self.stdout.write('\n📅 Importazione Anni Accademici...')
        
        cursor = connections['old_database'].cursor()
        cursor.execute("SELECT AnnoAccademico FROM TAnnoAccademico ORDER BY progr DESC")
        
        for i, row in enumerate(cursor.fetchall()):
            if row[0] and not self.dry_run:
                # L'anno più recente sarà attivo
                anno_str = row[0]
                anni = anno_str.split('-')
                
                try:
                    anno_inizio = int(anni[0])
                    data_inizio = datetime(anno_inizio, 10, 1).date()  # 1 ottobre
                    data_fine = datetime(anno_inizio + 1, 4, 30).date()  # 30 aprile
                    
                    AnnoAccademico.objects.get_or_create(
                        anno=anno_str,
                        defaults={
                            'data_inizio': data_inizio,
                            'data_fine': data_fine,
                            'attivo': i == 0  # Solo il primo è attivo
                        }
                    )
                    self.stats['anni'] += 1
                except Exception as e:
                    self.stats['errori'] += 1
                    if self.verbose:
                        self.stdout.write(self.style.ERROR(f'    Errore anno {anno_str}: {str(e)}'))
            else:
                self.stats['anni'] += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["anni"]} anni accademici importati'))
    
    def import_quadrimestri(self):
        """Crea i quadrimestri se non esistono"""
        self.stdout.write('\n📆 Creazione Quadrimestri...')
        
        if not self.dry_run:
            Quadrimestre.objects.get_or_create(numero=1)
            Quadrimestre.objects.get_or_create(numero=2)
        
        self.stdout.write(self.style.SUCCESS('  ✓ Quadrimestri creati'))
    
    def import_edizioni_corsi(self):
        """Importa edizioni corsi annuali"""
        self.stdout.write('\n📚 Importazione Edizioni Corsi...')
        
        cursor = connections['old_database'].cursor()
        cursor.execute("""
            SELECT ID, Anno, Codice, Descrizione, Quadrimestre, Insegnante,
                   Assistente, Vice, Giorni, Dalle, Alle, Note
            FROM TCorsiAnnualiDocenti
        """)
        
        for row in cursor.fetchall():
            if not self.dry_run:
                try:
                    # Validazioni
                    anno = AnnoAccademico.objects.filter(anno=row[1]).first()
                    corso = Corso.objects.filter(codice=row[2]).first()
                    docente = Docente.objects.filter(id=row[5]).first()
                    quad = Quadrimestre.objects.filter(numero=row[4]).first()
                    
                    if not all([anno, corso, docente, quad]):
                        self.stats['errori'] += 1
                        continue
                    
                    # Crea edizione
                    edizione = EdizioneCorso.objects.create(
                        anno_accademico=anno,
                        corso=corso,
                        quadrimestre=quad,
                        descrizione_custom=row[3] or '',
                        docente=docente,
                        assistente_id=row[6] if row[6] else None,
                        vice_assistente_id=row[7] if row[7] else None,
                        giorni_settimana=row[8] or '',
                        ora_inizio=row[9] if row[9] else '09:00',
                        ora_fine=row[10] if row[10] else '11:00',
                        note=row[11] or ''
                    )
                    self.stats['edizioni'] += 1
                    
                except Exception as e:
                    self.stats['errori'] += 1
                    if self.verbose:
                        self.stdout.write(self.style.ERROR(f'    Errore edizione {row[0]}: {str(e)}'))
            else:
                self.stats['edizioni'] += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["edizioni"]} edizioni importate'))
    
    def import_iscrizioni_anno(self):
        """Importa iscrizioni anno accademico"""
        self.stdout.write('\n✍️  Importazione Iscrizioni Anno...')
        
        cursor = connections['old_database'].cursor()
        cursor.execute("""
            SELECT AnnoAccademico, Matricola, Ricevuta, Data
            FROM TIscrizioneAnnoAccademico
        """)
        
        for row in cursor.fetchall():
            if not self.dry_run:
                try:
                    anno = AnnoAccademico.objects.filter(anno=row[0]).first()
                    iscritto = Iscritto.objects.filter(matricola=row[1]).first()
                    
                    if anno and iscritto:
                        IscrizioneAnnoAccademico.objects.create(
                            anno_accademico=anno,
                            iscritto=iscritto,
                            numero_ricevuta=row[2] or 0,
                            data_iscrizione=row[3] if row[3] else anno.data_inizio
                        )
                        self.stats['iscrizioni_anno'] += 1
                except Exception as e:
                    self.stats['errori'] += 1
                    if self.verbose:
                        self.stdout.write(self.style.ERROR(f'    Errore iscrizione anno: {str(e)}'))
            else:
                self.stats['iscrizioni_anno'] += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["iscrizioni_anno"]} iscrizioni anno importate'))
    
    def import_iscrizioni_corso(self):
        """Importa iscrizioni corsi"""
        self.stdout.write('\n📝 Importazione Iscrizioni Corsi...')
        
        cursor = connections['old_database'].cursor()
        cursor.execute("""
            SELECT AnnoAccademico, Corso, Matricola, Ricevuta, Data
            FROM TFrequenzaCorsi
        """)
        
        for row in cursor.fetchall():
            if not self.dry_run:
                try:
                    anno = AnnoAccademico.objects.filter(anno=row[0]).first()
                    iscritto = Iscritto.objects.filter(matricola=row[2]).first()
                    # Trova l'edizione del corso (potrebbero essercene più di una)
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
                        self.stats['iscrizioni_corso'] += 1
                except Exception as e:
                    self.stats['errori'] += 1
                    if self.verbose:
                        self.stdout.write(self.style.ERROR(f'    Errore iscrizione corso: {str(e)}'))
            else:
                self.stats['iscrizioni_corso'] += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["iscrizioni_corso"]} iscrizioni corso importate'))
    
    def import_lezioni(self):
        """Importa lezioni"""
        self.stdout.write('\n📓 Importazione Lezioni...')
        
        cursor = connections['old_database'].cursor()
        cursor.execute("""
            SELECT ID_corso_annuale, data, corso, descrizione, 
                   insegnante, presenze, ore, annoacc
            FROM TPresenzeCorsisti
        """)
        
        for row in cursor.fetchall():
            if not self.dry_run:
                try:
                    # Trova l'edizione del corso
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
                        self.stats['lezioni'] += 1
                except Exception as e:
                    self.stats['errori'] += 1
                    if self.verbose:
                        self.stdout.write(self.style.ERROR(f'    Errore lezione: {str(e)}'))
            else:
                self.stats['lezioni'] += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {self.stats["lezioni"]} lezioni importate'))
    
    def print_stats(self):
        """Stampa statistiche finali"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('RIEPILOGO IMPORTAZIONE'))
        self.stdout.write('='*70)
        
        self.stdout.write(f'\n📊 TABELLE DI SUPPORTO:')
        self.stdout.write(f'  • Comuni: {self.stats["comuni"]}')
        self.stdout.write(f'  • Titoli di Studio: {self.stats["titoli_studio"]}')
        self.stdout.write(f'  • Professioni Attuali: {self.stats["professioni_attuali"]}')
        self.stdout.write(f'  • Professioni Passate: {self.stats["professioni_passate"]}')
        
        self.stdout.write(f'\n👥 ANAGRAFICHE:')
        self.stdout.write(f'  • Iscritti: {self.stats["iscritti"]}')
        self.stdout.write(f'  • Docenti: {self.stats["docenti"]}')
        self.stdout.write(f'  • Autorità: {self.stats["autorita"]}')
        
        self.stdout.write(f'\n📚 CORSI:')
        self.stdout.write(f'  • Categorie: {self.stats["categorie"]}')
        self.stdout.write(f'  • Gruppi: {self.stats["gruppi"]}')
        self.stdout.write(f'  • Corsi: {self.stats["corsi"]}')
        self.stdout.write(f'  • Anni Accademici: {self.stats["anni"]}')
        self.stdout.write(f'  • Edizioni Corsi: {self.stats["edizioni"]}')
        
        self.stdout.write(f'\n✍️  ISCRIZIONI E LEZIONI:')
        self.stdout.write(f'  • Iscrizioni Anno: {self.stats["iscrizioni_anno"]}')
        self.stdout.write(f'  • Iscrizioni Corso: {self.stats["iscrizioni_corso"]}')
        self.stdout.write(f'  • Lezioni: {self.stats["lezioni"]}')
        
        if self.stats['errori'] > 0:
            self.stdout.write(f'\n⚠️  ERRORI: {self.stats["errori"]}')
            self.stdout.write(self.style.WARNING('   Alcuni record non sono stati importati'))
        
        self.stdout.write('\n' + '='*70)
        
        if not self.dry_run:
            self.stdout.write(self.style.SUCCESS('\n✓ Importazione completata con successo!\n'))
        else:
            self.stdout.write(self.style.WARNING('\n✓ Simulazione completata. Nessun dato salvato.\n'))
