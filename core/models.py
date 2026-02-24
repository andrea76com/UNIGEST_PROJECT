"""
UNIGEST - Models
File: core/models.py
Descrizione: Modelli del database per il gestionale università adulti
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from datetime import date


# ============================================================================
# MODELLI DI SUPPORTO (Lookup Tables)
# ============================================================================

class Comune(models.Model):
    """
    Modello per i comuni (paesi)
    """
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome Comune")
    provincia = models.CharField(max_length=2, blank=True, verbose_name="Sigla Provincia")
    cap = models.CharField(max_length=5, blank=True, verbose_name="CAP")
    
    class Meta:
        verbose_name = "Comune"
        verbose_name_plural = "Comuni"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class TitoloStudio(models.Model):
    """
    Modello per i titoli di studio (es: Laurea, Diploma, ecc.)
    """
    descrizione = models.CharField(max_length=50, unique=True, verbose_name="Titolo di Studio")
    
    class Meta:
        verbose_name = "Titolo di Studio"
        verbose_name_plural = "Titoli di Studio"
        ordering = ['descrizione']
    
    def __str__(self):
        return self.descrizione


class ProfessioneAttuale(models.Model):
    """
    Modello per le professioni attuali
    """
    descrizione = models.CharField(max_length=100, unique=True, verbose_name="Professione")
    
    class Meta:
        verbose_name = "Professione Attuale"
        verbose_name_plural = "Professioni Attuali"
        ordering = ['descrizione']
    
    def __str__(self):
        return self.descrizione


class ProfessionePassata(models.Model):
    """
    Modello per le professioni passate
    """
    descrizione = models.CharField(max_length=100, unique=True, verbose_name="Professione")
    
    class Meta:
        verbose_name = "Professione Passata"
        verbose_name_plural = "Professioni Passate"
        ordering = ['descrizione']
    
    def __str__(self):
        return self.descrizione


# ============================================================================
# MODELLI ANAGRAFICI
# ============================================================================

class Iscritto(models.Model):
    """
    Modello per gli iscritti all'università
    Corrisponde a TAnagrafe nel vecchio database
    """
    SESSO_CHOICES = [
        ('M', 'Maschio'),
        ('F', 'Femmina'),
    ]
    
    SITUAZIONE_CHOICES = [
        ('Celibe/Nubile', 'Celibe/Nubile'),
        ('Coniugato/a', 'Coniugato/a'),
        ('Vedovo/a', 'Vedovo/a'),
        ('Divorziato/a', 'Divorziato/a'),
    ]
    
    # Dati anagrafici principali
    matricola = models.AutoField(primary_key=True, verbose_name="Matricola")
    sesso = models.CharField(max_length=1, choices=SESSO_CHOICES, verbose_name="Sesso")
    titolo = models.CharField(max_length=10, blank=True, verbose_name="Titolo (Sig./Sig.ra)")
    nominativo = models.CharField(max_length=255, verbose_name="Nome e Cognome")
    codice_fiscale = models.CharField(max_length=16, blank=True, unique=True, null=True, verbose_name="Codice Fiscale")
    
    # Dati nascita
    luogo_nascita = models.CharField(max_length=100, blank=True, verbose_name="Luogo di Nascita")
    data_nascita = models.DateField(null=True, blank=True, verbose_name="Data di Nascita")
    
    # Indirizzo
    indirizzo = models.CharField(max_length=255, blank=True, verbose_name="Indirizzo")
    comune = models.ForeignKey(Comune, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Comune")
    
    # Contatti
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Telefono")
    cellulare = models.CharField(max_length=20, blank=True, verbose_name="Cellulare")
    email = models.EmailField(blank=True, verbose_name="Email")
    ha_whatsapp = models.BooleanField(default=False, verbose_name="Ha WhatsApp")
    
    # Dati culturali/professionali
    titolo_studio = models.ForeignKey(TitoloStudio, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Titolo di Studio")
    professione_attuale = models.ForeignKey(ProfessioneAttuale, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Professione Attuale")
    professione_passata = models.ForeignKey(ProfessionePassata, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Professione Passata")
    situazione = models.CharField(max_length=20, choices=SITUAZIONE_CHOICES, blank=True, verbose_name="Stato Civile")
    e_pensionato = models.BooleanField(default=False, verbose_name="È Pensionato")
    
    # Riferimenti familiari
    coniuge = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Coniuge (se iscritto)")
    
    # Comunicazioni
    riceve_posta = models.BooleanField(default=True, verbose_name="Riceve Posta Cartacea")
    
    # Flags speciali
    e_collaboratore = models.BooleanField(default=False, verbose_name="È Collaboratore")
    e_assistente = models.BooleanField(default=False, verbose_name="Può essere Assistente")
    
    # Metadati
    data_inserimento = models.DateTimeField(auto_now_add=True, verbose_name="Data Inserimento")
    data_modifica = models.DateTimeField(auto_now=True, verbose_name="Ultima Modifica")
    note = models.TextField(blank=True, verbose_name="Note")
    
    class Meta:
        verbose_name = "Iscritto"
        verbose_name_plural = "Iscritti"
        ordering = ['nominativo']
        indexes = [
            models.Index(fields=['nominativo']),
            models.Index(fields=['codice_fiscale']),
        ]
    
    def __str__(self):
        return f"{self.matricola} - {self.nominativo}"
    
    def get_absolute_url(self):
        return reverse('core:iscritto_detail', kwargs={'pk': self.pk})
    
    @property
    def eta(self):
        """Calcola l'età dell'iscritto"""
        if self.data_nascita:
            oggi = date.today()
            return oggi.year - self.data_nascita.year - ((oggi.month, oggi.day) < (self.data_nascita.month, self.data_nascita.day))
        return None
    
    @property
    def fascia_eta(self):
        """Restituisce la fascia d'età (es: 60-69)"""
        eta = self.eta
        if eta:
            fascia = (eta // 10) * 10
            return f"{fascia}-{fascia+9}"
        return "Non disponibile"


class Docente(models.Model):
    """
    Modello per i docenti
    """
    nome = models.CharField(max_length=100, verbose_name="Nome e Cognome")
    titolo = models.CharField(max_length=50, blank=True, verbose_name="Titolo/Prefisso")
    
    # Contatti
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Telefono")
    cellulare = models.CharField(max_length=20, blank=True, verbose_name="Cellulare")
    email = models.EmailField(blank=True, verbose_name="Email")
    
    # Indirizzo
    indirizzo = models.CharField(max_length=255, blank=True, verbose_name="Indirizzo")
    comune = models.ForeignKey(Comune, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Comune")
    
    # Info aggiuntive
    note = models.TextField(blank=True, verbose_name="Note")
    attivo = models.BooleanField(default=True, verbose_name="Attivo")
    
    # Metadati
    data_inserimento = models.DateTimeField(auto_now_add=True, verbose_name="Data Inserimento")
    data_modifica = models.DateTimeField(auto_now=True, verbose_name="Ultima Modifica")
    
    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docenti"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome
    
    def get_absolute_url(self):
        return reverse('core:docente_detail', kwargs={'pk': self.pk})


class Autorita(models.Model):
    """
    Modello per le autorità (cariche istituzionali, ecc.)
    """
    nome = models.CharField(max_length=100, verbose_name="Nome e Cognome")
    titolo = models.CharField(max_length=50, blank=True, verbose_name="Titolo/Prefisso")
    carica = models.CharField(max_length=100, verbose_name="Carica")
    
    # Contatti
    indirizzo = models.CharField(max_length=255, blank=True, verbose_name="Indirizzo")
    comune = models.ForeignKey(Comune, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Comune")
    email = models.EmailField(blank=True, verbose_name="Email")
    
    # Info aggiuntive
    note = models.TextField(blank=True, verbose_name="Note")
    attivo = models.BooleanField(default=True, verbose_name="Attivo")
    
    class Meta:
        verbose_name = "Autorità"
        verbose_name_plural = "Autorità"
        ordering = ['carica', 'nome']
    
    def __str__(self):
        return f"{self.carica} - {self.nome}"


# ============================================================================
# MODELLI CORSI
# ============================================================================

class CategoriaCorso(models.Model):
    """
    Modello per le categorie di corsi (Culturali, Laboratori, Lingue, Altri)
    """
    nome = models.CharField(max_length=50, unique=True, verbose_name="Categoria")
    descrizione = models.TextField(blank=True, verbose_name="Descrizione")
    ordine = models.IntegerField(default=0, verbose_name="Ordine Visualizzazione")
    
    class Meta:
        verbose_name = "Categoria Corso"
        verbose_name_plural = "Categorie Corsi"
        ordering = ['ordine', 'nome']
    
    def __str__(self):
        return self.nome


class GruppoCorso(models.Model):
    """
    Modello per i gruppi di corsi (raggruppamento ulteriore)
    """
    nome = models.CharField(max_length=50, unique=True, verbose_name="Gruppo")
    descrizione = models.TextField(blank=True, verbose_name="Descrizione")
    
    class Meta:
        verbose_name = "Gruppo Corso"
        verbose_name_plural = "Gruppi Corsi"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class Corso(models.Model):
    """
    Modello per i corsi (master, non legati all'anno accademico)
    """
    codice = models.IntegerField(unique=True, verbose_name="Codice Corso")
    nome = models.CharField(max_length=100, verbose_name="Nome Corso")
    descrizione = models.TextField(blank=True, verbose_name="Descrizione Dettagliata")
    
    # Classificazione
    categoria = models.ForeignKey(CategoriaCorso, on_delete=models.SET_NULL, null=True, verbose_name="Categoria")
    gruppo = models.ForeignKey(GruppoCorso, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Gruppo")
    
    # Configurazione
    visibile = models.BooleanField(default=True, verbose_name="Visibile nelle Iscrizioni")
    numero_min_partecipanti = models.IntegerField(null=True, blank=True, verbose_name="N° Minimo Partecipanti")
    numero_max_partecipanti = models.IntegerField(null=True, blank=True, verbose_name="N° Massimo Partecipanti")
    
    class Meta:
        verbose_name = "Corso"
        verbose_name_plural = "Corsi"
        ordering = ['codice', 'nome']
    
    def __str__(self):
        return f"{self.codice} - {self.nome}"
    
    def get_absolute_url(self):
        return reverse('core:corso_detail', kwargs={'pk': self.pk})


class AnnoAccademico(models.Model):
    """
    Modello per gli anni accademici (es: 2023-2024)
    """
    anno = models.CharField(max_length=9, unique=True, verbose_name="Anno Accademico", 
                           help_text="Formato: YYYY-YYYY (es: 2023-2024)")
    data_inizio = models.DateField(verbose_name="Data Inizio")
    data_fine = models.DateField(verbose_name="Data Fine")
    attivo = models.BooleanField(default=False, verbose_name="Anno Corrente")
    
    class Meta:
        verbose_name = "Anno Accademico"
        verbose_name_plural = "Anni Accademici"
        ordering = ['-anno']
    
    def __str__(self):
        return self.anno
    
    def save(self, *args, **kwargs):
        """Se questo anno è impostato come attivo, disattiva gli altri"""
        if self.attivo:
            AnnoAccademico.objects.exclude(pk=self.pk).update(attivo=False)
        super().save(*args, **kwargs)


class Quadrimestre(models.Model):
    """
    Modello per i quadrimestri (1° e 2°)
    """
    QUADRIMESTRE_CHOICES = [
        (1, '1° Quadrimestre (Ottobre-Gennaio)'),
        (2, '2° Quadrimestre (Febbraio-Aprile)'),
    ]
    
    numero = models.IntegerField(choices=QUADRIMESTRE_CHOICES, unique=True, verbose_name="Quadrimestre")
    
    class Meta:
        verbose_name = "Quadrimestre"
        verbose_name_plural = "Quadrimestri"
        ordering = ['numero']
    
    def __str__(self):
        return self.get_numero_display()


class EdizioneCorso(models.Model):
    """
    Modello per le edizioni dei corsi in un anno accademico specifico
    Corrisponde a TCorsiAnnualiDocenti nel vecchio database
    """
    # Riferimenti principali
    anno_accademico = models.ForeignKey(AnnoAccademico, on_delete=models.CASCADE, verbose_name="Anno Accademico")
    corso = models.ForeignKey(Corso, on_delete=models.CASCADE, verbose_name="Corso")
    quadrimestre = models.ForeignKey(Quadrimestre, on_delete=models.CASCADE, verbose_name="Quadrimestre")
    
    # Descrizione personalizzata (opzionale, se diversa dal corso master)
    descrizione_custom = models.CharField(max_length=255, blank=True, verbose_name="Descrizione Personalizzata")
    
    # Staff del corso
    docente = models.ForeignKey(Docente, on_delete=models.PROTECT, related_name='corsi_come_docente', verbose_name="Docente")
    assistente = models.ForeignKey(Iscritto, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='corsi_come_assistente', verbose_name="Assistente",
                                  limit_choices_to={'e_assistente': True})
    vice_assistente = models.ForeignKey(Iscritto, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='corsi_come_vice', verbose_name="Vice Assistente",
                                       limit_choices_to={'e_assistente': True})
    
    # Orari
    giorni_settimana = models.CharField(max_length=100, verbose_name="Giorni della Settimana",
                                       help_text="Es: Lunedì, Mercoledì")
    ora_inizio = models.TimeField(verbose_name="Ora Inizio")
    ora_fine = models.TimeField(verbose_name="Ora Fine")
    
    # Info aggiuntive
    note = models.TextField(blank=True, verbose_name="Note")
    
    class Meta:
        verbose_name = "Edizione Corso"
        verbose_name_plural = "Edizioni Corsi"
        ordering = ['-anno_accademico', 'quadrimestre', 'corso__nome']
        unique_together = ['anno_accademico', 'corso', 'quadrimestre', 'giorni_settimana', 'ora_inizio']
    
    def __str__(self):
        return f"{self.corso.nome} - {self.anno_accademico} ({self.quadrimestre})"
    
    def get_absolute_url(self):
        return reverse('core:edizione_detail', kwargs={'pk': self.pk})
    
    @property
    def descrizione_completa(self):
        """Restituisce la descrizione personalizzata o quella del corso master"""
        return self.descrizione_custom if self.descrizione_custom else self.corso.descrizione
    
    @property
    def numero_iscritti(self):
        """Conta il numero di iscritti a questa edizione"""
        return self.iscrizioni.count()
    
    @property
    def numero_lezioni(self):
        """Conta il numero di lezioni effettuate"""
        return self.lezioni.count()


# ============================================================================
# MODELLI ISCRIZIONI E PRESENZE
# ============================================================================

class IscrizioneAnnoAccademico(models.Model):
    """
    Modello per l'iscrizione annuale di uno studente
    """
    anno_accademico = models.ForeignKey(AnnoAccademico, on_delete=models.CASCADE, verbose_name="Anno Accademico")
    iscritto = models.ForeignKey(Iscritto, on_delete=models.CASCADE, verbose_name="Iscritto")
    
    # Dati amministrativi
    numero_ricevuta = models.IntegerField(verbose_name="Numero Ricevuta", help_text="Numero progressivo ricevuta")
    data_iscrizione = models.DateField(verbose_name="Data Iscrizione")
    
    # Metadati
    data_inserimento = models.DateTimeField(auto_now_add=True, verbose_name="Data Inserimento")
    
    class Meta:
        verbose_name = "Iscrizione Anno Accademico"
        verbose_name_plural = "Iscrizioni Anno Accademico"
        ordering = ['-anno_accademico', 'data_iscrizione']
        unique_together = ['anno_accademico', 'iscritto']
    
    def __str__(self):
        return f"{self.iscritto.nominativo} - {self.anno_accademico}"


class IscrizioneCorso(models.Model):
    """
    Modello per l'iscrizione di uno studente a un corso specifico
    Corrisponde a TFrequenzaCorsi nel vecchio database
    """
    anno_accademico = models.ForeignKey(AnnoAccademico, on_delete=models.CASCADE, verbose_name="Anno Accademico")
    edizione_corso = models.ForeignKey(EdizioneCorso, on_delete=models.CASCADE, related_name='iscrizioni', verbose_name="Corso")
    iscritto = models.ForeignKey(Iscritto, on_delete=models.CASCADE, verbose_name="Iscritto")
    
    # Dati amministrativi
    numero_ricevuta = models.IntegerField(null=True, blank=True, verbose_name="Numero Ricevuta")
    data_iscrizione = models.DateField(verbose_name="Data Iscrizione")
    
    # Metadati
    data_inserimento = models.DateTimeField(auto_now_add=True, verbose_name="Data Inserimento")
    
    class Meta:
        verbose_name = "Iscrizione Corso"
        verbose_name_plural = "Iscrizioni Corsi"
        ordering = ['-anno_accademico', 'edizione_corso', 'iscritto__nominativo']
        unique_together = ['anno_accademico', 'edizione_corso', 'iscritto']
    
    def __str__(self):
        return f"{self.iscritto.nominativo} - {self.edizione_corso}"


class Lezione(models.Model):
    """
    Modello per le singole lezioni di un corso
    Corrisponde a TPresenzeCorsisti nel vecchio database
    """
    edizione_corso = models.ForeignKey(EdizioneCorso, on_delete=models.CASCADE, related_name='lezioni', verbose_name="Edizione Corso")
    data_lezione = models.DateField(verbose_name="Data Lezione")
    
    # Info lezione
    descrizione = models.CharField(max_length=255, blank=True, verbose_name="Argomento/Descrizione")
    docente = models.ForeignKey(Docente, on_delete=models.SET_NULL, null=True, verbose_name="Docente Effettivo")
    ore_lezione = models.DecimalField(max_digits=3, decimal_places=1, default=2.0, verbose_name="Ore Lezione")
    
    # Presenze
    numero_presenti = models.IntegerField(default=0, verbose_name="Numero Presenti")
    
    # Metadati
    data_inserimento = models.DateTimeField(auto_now_add=True, verbose_name="Data Inserimento")
    data_modifica = models.DateTimeField(auto_now=True, verbose_name="Ultima Modifica")
    note = models.TextField(blank=True, verbose_name="Note")
    
    class Meta:
        verbose_name = "Lezione"
        verbose_name_plural = "Lezioni"
        ordering = ['-data_lezione', 'edizione_corso']
        unique_together = ['edizione_corso', 'data_lezione']
    
    def __str__(self):
        return f"{self.edizione_corso.corso.nome} - {self.data_lezione.strftime('%d/%m/%Y')}"
    
    def get_absolute_url(self):
        return reverse('core:lezione_detail', kwargs={'pk': self.pk})


class PresenzaLezione(models.Model):
    """
    Modello per registrare la presenza di ogni singolo studente a una lezione
    (Tabella di dettaglio per il foglio presenze)
    """
    lezione = models.ForeignKey(Lezione, on_delete=models.CASCADE, related_name='presenze', verbose_name="Lezione")
    iscritto = models.ForeignKey(Iscritto, on_delete=models.CASCADE, verbose_name="Iscritto")
    presente = models.BooleanField(default=True, verbose_name="Presente")
    
    class Meta:
        verbose_name = "Presenza Lezione"
        verbose_name_plural = "Presenze Lezioni"
        ordering = ['lezione', 'iscritto__nominativo']
        unique_together = ['lezione', 'iscritto']
    
    def __str__(self):
        stato = "Presente" if self.presente else "Assente"
        return f"{self.iscritto.nominativo} - {stato}"
