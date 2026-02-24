"""
UNIGEST - Admin Interface
File: core/admin.py
Descrizione: Configurazione interfaccia amministrativa Django
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import (
    Comune, TitoloStudio, ProfessioneAttuale, ProfessionePassata,
    Iscritto, Docente, Autorita,
    CategoriaCorso, GruppoCorso, Corso, AnnoAccademico, Quadrimestre,
    EdizioneCorso, IscrizioneAnnoAccademico, IscrizioneCorso,
    Lezione, PresenzaLezione
)


# ============================================================================
# CONFIGURAZIONI ADMIN PER MODELLI DI SUPPORTO
# ============================================================================

@admin.register(Comune)
class ComuneAdmin(admin.ModelAdmin):
    list_display = ['nome', 'provincia', 'cap']
    search_fields = ['nome', 'provincia']
    list_filter = ['provincia']
    ordering = ['nome']


@admin.register(TitoloStudio)
class TitoloStudioAdmin(admin.ModelAdmin):
    list_display = ['descrizione']
    search_fields = ['descrizione']


@admin.register(ProfessioneAttuale)
class ProfessioneAttualeAdmin(admin.ModelAdmin):
    list_display = ['descrizione']
    search_fields = ['descrizione']


@admin.register(ProfessionePassata)
class ProfessionePassataAdmin(admin.ModelAdmin):
    list_display = ['descrizione']
    search_fields = ['descrizione']


# ============================================================================
# CONFIGURAZIONI ADMIN PER ANAGRAFICHE
# ============================================================================

@admin.register(Iscritto)
class IscrittoAdmin(admin.ModelAdmin):
    list_display = [
        'matricola', 'nominativo', 'sesso', 'data_nascita', 'eta_display',
        'comune', 'cellulare', 'email', 'e_assistente', 'e_collaboratore'
    ]
    list_filter = [
        'sesso', 'e_assistente', 'e_collaboratore', 'e_pensionato',
        'titolo_studio', 'comune'
    ]
    search_fields = ['nominativo', 'codice_fiscale', 'email', 'cellulare']
    readonly_fields = ['matricola', 'data_inserimento', 'data_modifica']
    
    fieldsets = (
        ('Dati Anagrafici', {
            'fields': (
                'matricola', 'sesso', 'titolo', 'nominativo', 'codice_fiscale',
                'luogo_nascita', 'data_nascita', 'situazione', 'coniuge'
            )
        }),
        ('Residenza', {
            'fields': ('indirizzo', 'comune')
        }),
        ('Contatti', {
            'fields': ('telefono', 'cellulare', 'email', 'ha_whatsapp', 'riceve_posta')
        }),
        ('Informazioni Culturali/Professionali', {
            'fields': (
                'titolo_studio', 'professione_attuale', 'professione_passata',
                'e_pensionato'
            )
        }),
        ('Flags Speciali', {
            'fields': ('e_collaboratore', 'e_assistente')
        }),
        ('Note e Metadati', {
            'fields': ('note', 'data_inserimento', 'data_modifica'),
            'classes': ('collapse',)
        }),
    )
    
    def eta_display(self, obj):
        """Mostra l'età calcolata"""
        eta = obj.eta
        return f"{eta} anni" if eta else "-"
    eta_display.short_description = "Età"
    
    # Azioni personalizzate
    actions = ['marca_come_assistente', 'marca_come_collaboratore']
    
    def marca_come_assistente(self, request, queryset):
        """Marca gli iscritti selezionati come assistenti"""
        updated = queryset.update(e_assistente=True)
        self.message_user(request, f"{updated} iscritti marcati come assistenti.")
    marca_come_assistente.short_description = "Marca come Assistente"
    
    def marca_come_collaboratore(self, request, queryset):
        """Marca gli iscritti selezionati come collaboratori"""
        updated = queryset.update(e_collaboratore=True)
        self.message_user(request, f"{updated} iscritti marcati come collaboratori.")
    marca_come_collaboratore.short_description = "Marca come Collaboratore"


@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'titolo', 'cellulare', 'email', 'comune', 'attivo']
    list_filter = ['attivo', 'comune']
    search_fields = ['nome', 'email', 'cellulare']
    readonly_fields = ['data_inserimento', 'data_modifica']
    
    fieldsets = (
        ('Dati Personali', {
            'fields': ('titolo', 'nome', 'attivo')
        }),
        ('Contatti', {
            'fields': ('telefono', 'cellulare', 'email')
        }),
        ('Residenza', {
            'fields': ('indirizzo', 'comune')
        }),
        ('Note e Metadati', {
            'fields': ('note', 'data_inserimento', 'data_modifica'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Autorita)
class AutoritaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'carica', 'email', 'comune', 'attivo']
    list_filter = ['attivo', 'carica']
    search_fields = ['nome', 'carica', 'email']
    
    fieldsets = (
        ('Dati Personali', {
            'fields': ('titolo', 'nome', 'carica', 'attivo')
        }),
        ('Contatti', {
            'fields': ('email', 'indirizzo', 'comune')
        }),
        ('Note', {
            'fields': ('note',),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# CONFIGURAZIONI ADMIN PER CORSI
# ============================================================================

@admin.register(CategoriaCorso)
class CategoriaCorsoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ordine', 'descrizione']
    list_editable = ['ordine']
    ordering = ['ordine', 'nome']


@admin.register(GruppoCorso)
class GruppoCorsoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descrizione']
    search_fields = ['nome']


@admin.register(Corso)
class CorsoAdmin(admin.ModelAdmin):
    list_display = [
        'codice', 'nome', 'categoria', 'gruppo', 'visibile',
        'numero_min_partecipanti', 'numero_max_partecipanti'
    ]
    list_filter = ['categoria', 'gruppo', 'visibile']
    search_fields = ['codice', 'nome', 'descrizione']
    list_editable = ['visibile']
    
    fieldsets = (
        ('Informazioni Base', {
            'fields': ('codice', 'nome', 'descrizione')
        }),
        ('Classificazione', {
            'fields': ('categoria', 'gruppo')
        }),
        ('Configurazione', {
            'fields': (
                'visibile', 'numero_min_partecipanti', 'numero_max_partecipanti'
            )
        }),
    )


@admin.register(AnnoAccademico)
class AnnoAccademicoAdmin(admin.ModelAdmin):
    list_display = ['anno', 'data_inizio', 'data_fine', 'attivo']
    list_filter = ['attivo']
    list_editable = ['attivo']


@admin.register(Quadrimestre)
class QuadrimestreAdmin(admin.ModelAdmin):
    list_display = ['numero', 'get_descrizione']
    
    def get_descrizione(self, obj):
        return obj.get_numero_display()
    get_descrizione.short_description = "Descrizione"


class IscrizioneCorsoInline(admin.TabularInline):
    """Inline per visualizzare le iscrizioni dentro l'edizione corso"""
    model = IscrizioneCorso
    extra = 0
    fields = ['iscritto', 'data_iscrizione', 'numero_ricevuta']
    raw_id_fields = ['iscritto']


class LezioneInline(admin.TabularInline):
    """Inline per visualizzare le lezioni dentro l'edizione corso"""
    model = Lezione
    extra = 0
    fields = ['data_lezione', 'descrizione', 'ore_lezione', 'numero_presenti']


@admin.register(EdizioneCorso)
class EdizioneCorsoAdmin(admin.ModelAdmin):
    list_display = [
        'corso', 'anno_accademico', 'quadrimestre', 'docente',
        'giorni_settimana', 'ora_inizio', 'ora_fine', 'numero_iscritti_display'
    ]
    list_filter = ['anno_accademico', 'quadrimestre', 'corso__categoria']
    search_fields = ['corso__nome', 'docente__nome', 'descrizione_custom']
    raw_id_fields = ['assistente', 'vice_assistente']
    inlines = [IscrizioneCorsoInline, LezioneInline]
    
    fieldsets = (
        ('Informazioni Base', {
            'fields': ('anno_accademico', 'corso', 'quadrimestre', 'descrizione_custom')
        }),
        ('Staff', {
            'fields': ('docente', 'assistente', 'vice_assistente')
        }),
        ('Orari', {
            'fields': ('giorni_settimana', 'ora_inizio', 'ora_fine')
        }),
        ('Note', {
            'fields': ('note',),
            'classes': ('collapse',)
        }),
    )
    
    def numero_iscritti_display(self, obj):
        """Mostra il numero di iscritti"""
        count = obj.numero_iscritti
        return format_html(
            '<span style="background-color: #4CAF50; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            count
        )
    numero_iscritti_display.short_description = "Iscritti"


# ============================================================================
# CONFIGURAZIONI ADMIN PER ISCRIZIONI
# ============================================================================

@admin.register(IscrizioneAnnoAccademico)
class IscrizioneAnnoAccademicoAdmin(admin.ModelAdmin):
    list_display = [
        'iscritto', 'anno_accademico', 'numero_ricevuta', 'data_iscrizione'
    ]
    list_filter = ['anno_accademico', 'data_iscrizione']
    search_fields = ['iscritto__nominativo', 'numero_ricevuta']
    date_hierarchy = 'data_iscrizione'
    raw_id_fields = ['iscritto']


@admin.register(IscrizioneCorso)
class IscrizioneCorsoAdmin(admin.ModelAdmin):
    list_display = [
        'iscritto', 'edizione_corso', 'anno_accademico', 'data_iscrizione'
    ]
    list_filter = ['anno_accademico', 'edizione_corso__quadrimestre', 'data_iscrizione']
    search_fields = ['iscritto__nominativo', 'edizione_corso__corso__nome']
    date_hierarchy = 'data_iscrizione'
    raw_id_fields = ['iscritto', 'edizione_corso']


# ============================================================================
# CONFIGURAZIONI ADMIN PER LEZIONI E PRESENZE
# ============================================================================

class PresenzaLezioneInline(admin.TabularInline):
    """Inline per gestire le presenze dentro la lezione"""
    model = PresenzaLezione
    extra = 0
    fields = ['iscritto', 'presente']
    raw_id_fields = ['iscritto']


@admin.register(Lezione)
class LezioneAdmin(admin.ModelAdmin):
    list_display = [
        'edizione_corso', 'data_lezione', 'docente', 'ore_lezione',
        'numero_presenti', 'descrizione'
    ]
    list_filter = [
        'edizione_corso__anno_accademico',
        'edizione_corso__quadrimestre',
        'data_lezione'
    ]
    search_fields = ['edizione_corso__corso__nome', 'descrizione']
    date_hierarchy = 'data_lezione'
    inlines = [PresenzaLezioneInline]
    
    fieldsets = (
        ('Informazioni Lezione', {
            'fields': ('edizione_corso', 'data_lezione', 'docente', 'ore_lezione')
        }),
        ('Dettagli', {
            'fields': ('descrizione', 'numero_presenti')
        }),
        ('Note', {
            'fields': ('note',),
            'classes': ('collapse',)
        }),
    )


@admin.register(PresenzaLezione)
class PresenzaLezioneAdmin(admin.ModelAdmin):
    list_display = ['lezione', 'iscritto', 'presente_display']
    list_filter = ['presente', 'lezione__data_lezione']
    search_fields = ['iscritto__nominativo', 'lezione__edizione_corso__corso__nome']
    raw_id_fields = ['lezione', 'iscritto']
    
    def presente_display(self, obj):
        """Mostra presenza con colore"""
        if obj.presente:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Presente</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Assente</span>'
        )
    presente_display.short_description = "Stato"
