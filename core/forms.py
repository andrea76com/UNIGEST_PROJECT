"""
UNIGEST - Forms
File: core/forms.py
Descrizione: Form per l'inserimento e modifica dati
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Iscritto, Docente, Autorita, Corso, EdizioneCorso,
    IscrizioneAnnoAccademico, IscrizioneCorso, Lezione, PresenzaLezione,
    AnnoAccademico
)


# ============================================================================
# FORMS PER ANAGRAFICHE
# ============================================================================

class IscrittoForm(forms.ModelForm):
    """
    Form per inserimento/modifica iscritti
    """
    class Meta:
        model = Iscritto
        fields = [
            'sesso', 'titolo', 'nominativo', 'codice_fiscale',
            'luogo_nascita', 'data_nascita', 'situazione', 'coniuge',
            'indirizzo', 'comune',
            'telefono', 'cellulare', 'email', 'ha_whatsapp', 'riceve_posta',
            'titolo_studio', 'professione_attuale', 'professione_passata', 'e_pensionato',
            'e_collaboratore', 'e_assistente',
            'note'
        ]
        widgets = {
            'sesso': forms.Select(attrs={'class': 'form-control'}),
            'titolo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sig./Sig.ra'}),
            'nominativo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Cognome'}),
            'codice_fiscale': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RSSMRA80A01H501X'}),
            'luogo_nascita': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Città di nascita'}),
            'data_nascita': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'situazione': forms.Select(attrs={'class': 'form-control'}),
            'coniuge': forms.Select(attrs={'class': 'form-control'}),
            'indirizzo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Via, numero civico'}),
            'comune': forms.Select(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '051 1234567'}),
            'cellulare': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '333 1234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@esempio.it'}),
            'ha_whatsapp': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'riceve_posta': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'titolo_studio': forms.Select(attrs={'class': 'form-control'}),
            'professione_attuale': forms.Select(attrs={'class': 'form-control'}),
            'professione_passata': forms.Select(attrs={'class': 'form-control'}),
            'e_pensionato': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'e_collaboratore': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'e_assistente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_codice_fiscale(self):
        """Validazione codice fiscale"""
        cf = self.cleaned_data.get('codice_fiscale', '').strip().upper()
        if cf and len(cf) != 16:
            raise ValidationError('Il codice fiscale deve essere di 16 caratteri')
        return cf
    
    def clean_email(self):
        """Validazione email univoca"""
        email = self.cleaned_data.get('email', '').strip().lower()
        if email:
            # Controlla se esiste già (escludendo l'istanza corrente in modifica)
            qs = Iscritto.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Questa email è già utilizzata da un altro iscritto')
        return email


class DocenteForm(forms.ModelForm):
    """
    Form per inserimento/modifica docenti
    """
    class Meta:
        model = Docente
        fields = [
            'nome', 'titolo', 'telefono', 'cellulare', 'email',
            'indirizzo', 'comune', 'note', 'attivo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Cognome'}),
            'titolo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prof./Dott./Ing.'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '051 1234567'}),
            'cellulare': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '333 1234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@esempio.it'}),
            'indirizzo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Via, numero civico'}),
            'comune': forms.Select(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_email(self):
        """Validazione email univoca"""
        email = self.cleaned_data.get('email', '').strip().lower()
        if email:
            qs = Docente.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Questa email è già utilizzata da un altro docente')
        return email


class AutoritaForm(forms.ModelForm):
    """
    Form per inserimento/modifica autorità
    """
    class Meta:
        model = Autorita
        fields = [
            'nome', 'titolo', 'carica', 'indirizzo', 'comune',
            'email', 'note', 'attivo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Cognome'}),
            'titolo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'On./Dott./Avv.'}),
            'carica': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es: Sindaco, Assessore'}),
            'indirizzo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Via, numero civico'}),
            'comune': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@esempio.it'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ============================================================================
# FORMS PER CORSI
# ============================================================================

class CorsoForm(forms.ModelForm):
    """
    Form per inserimento/modifica corsi
    """
    class Meta:
        model = Corso
        fields = [
            'codice', 'nome', 'descrizione', 'categoria', 'gruppo',
            'visibile', 'numero_min_partecipanti', 'numero_max_partecipanti'
        ]
        widgets = {
            'codice': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Es: 101'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome del corso'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descrizione dettagliata'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'gruppo': forms.Select(attrs={'class': 'form-control'}),
            'visibile': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'numero_min_partecipanti': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimo'}),
            'numero_max_partecipanti': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Massimo'}),
        }
    
    def clean_codice(self):
        """Validazione codice univoco"""
        codice = self.cleaned_data.get('codice')
        if codice:
            qs = Corso.objects.filter(codice=codice)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Questo codice corso è già utilizzato')
        return codice
    
    def clean(self):
        """Validazione numero partecipanti"""
        cleaned_data = super().clean()
        num_min = cleaned_data.get('numero_min_partecipanti')
        num_max = cleaned_data.get('numero_max_partecipanti')
        
        if num_min and num_max:
            if num_min > num_max:
                raise ValidationError(
                    'Il numero minimo di partecipanti non può essere maggiore del numero massimo'
                )
        
        return cleaned_data


class EdizioneCorsoForm(forms.ModelForm):
    """
    Form per inserimento/modifica edizioni corsi
    """
    class Meta:
        model = EdizioneCorso
        fields = [
            'anno_accademico', 'corso', 'quadrimestre', 'descrizione_custom',
            'docente', 'assistente', 'vice_assistente',
            'giorni_settimana', 'ora_inizio', 'ora_fine', 'note'
        ]
        widgets = {
            'anno_accademico': forms.Select(attrs={'class': 'form-control'}),
            'corso': forms.Select(attrs={'class': 'form-control'}),
            'quadrimestre': forms.Select(attrs={'class': 'form-control'}),
            'descrizione_custom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lascia vuoto per usare la descrizione del corso'
            }),
            'docente': forms.Select(attrs={'class': 'form-control'}),
            'assistente': forms.Select(attrs={'class': 'form-control'}),
            'vice_assistente': forms.Select(attrs={'class': 'form-control'}),
            'giorni_settimana': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Es: Lunedì, Mercoledì'
            }),
            'ora_inizio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'ora_fine': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra assistenti: solo iscritti che possono essere assistenti
        self.fields['assistente'].queryset = Iscritto.objects.filter(e_assistente=True)
        self.fields['vice_assistente'].queryset = Iscritto.objects.filter(e_assistente=True)
        # Filtra docenti attivi
        self.fields['docente'].queryset = Docente.objects.filter(attivo=True)
    
    def clean(self):
        """Validazione orari"""
        cleaned_data = super().clean()
        ora_inizio = cleaned_data.get('ora_inizio')
        ora_fine = cleaned_data.get('ora_fine')
        
        if ora_inizio and ora_fine:
            if ora_inizio >= ora_fine:
                raise ValidationError(
                    'L\'ora di inizio deve essere precedente all\'ora di fine'
                )
        
        return cleaned_data


# ============================================================================
# FORMS PER ISCRIZIONI
# ============================================================================

class IscrizioneAnnoForm(forms.ModelForm):
    """
    Form per iscrizione anno accademico
    """
    class Meta:
        model = IscrizioneAnnoAccademico
        fields = ['anno_accademico', 'iscritto', 'numero_ricevuta', 'data_iscrizione']
        widgets = {
            'anno_accademico': forms.Select(attrs={'class': 'form-control'}),
            'iscritto': forms.Select(attrs={'class': 'form-control'}),
            'numero_ricevuta': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Numero ricevuta'}),
            'data_iscrizione': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def clean(self):
        """Validazione iscrizione duplicata"""
        cleaned_data = super().clean()
        anno = cleaned_data.get('anno_accademico')
        iscritto = cleaned_data.get('iscritto')
        
        if anno and iscritto:
            # Controlla se esiste già un'iscrizione
            qs = IscrizioneAnnoAccademico.objects.filter(
                anno_accademico=anno,
                iscritto=iscritto
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    f'{iscritto.nominativo} è già iscritto all\'anno accademico {anno.anno}'
                )
        
        return cleaned_data


class IscrizioneCorsoForm(forms.ModelForm):
    """
    Form per iscrizione a un corso
    """
    class Meta:
        model = IscrizioneCorso
        fields = ['anno_accademico', 'edizione_corso', 'iscritto', 'numero_ricevuta', 'data_iscrizione']
        widgets = {
            'anno_accademico': forms.Select(attrs={'class': 'form-control'}),
            'edizione_corso': forms.Select(attrs={'class': 'form-control'}),
            'iscritto': forms.Select(attrs={'class': 'form-control'}),
            'numero_ricevuta': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Numero ricevuta (opzionale)'}),
            'data_iscrizione': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se c'è un anno accademico nel form, filtra le edizioni
        if 'anno_accademico' in self.data or self.instance.pk:
            try:
                anno_id = int(self.data.get('anno_accademico', self.instance.anno_accademico_id))
                self.fields['edizione_corso'].queryset = EdizioneCorso.objects.filter(
                    anno_accademico_id=anno_id
                ).select_related('corso')
            except (ValueError, TypeError):
                pass
    
    def clean(self):
        """Validazione iscrizione duplicata"""
        cleaned_data = super().clean()
        anno = cleaned_data.get('anno_accademico')
        edizione = cleaned_data.get('edizione_corso')
        iscritto = cleaned_data.get('iscritto')
        
        if anno and edizione and iscritto:
            # Verifica che l'iscritto sia iscritto all'anno accademico
            if not IscrizioneAnnoAccademico.objects.filter(
                anno_accademico=anno,
                iscritto=iscritto
            ).exists():
                raise ValidationError(
                    f'{iscritto.nominativo} non è iscritto all\'anno accademico {anno.anno}. '
                    'Effettua prima l\'iscrizione all\'anno accademico.'
                )
            
            # Controlla se esiste già un'iscrizione al corso
            qs = IscrizioneCorso.objects.filter(
                anno_accademico=anno,
                edizione_corso=edizione,
                iscritto=iscritto
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    f'{iscritto.nominativo} è già iscritto a questo corso'
                )
            
            # Verifica numero massimo partecipanti (se impostato)
            corso = edizione.corso
            if corso.numero_max_partecipanti:
                num_iscritti = IscrizioneCorso.objects.filter(edizione_corso=edizione).count()
                if num_iscritti >= corso.numero_max_partecipanti:
                    raise ValidationError(
                        f'Il corso ha raggiunto il numero massimo di partecipanti '
                        f'({corso.numero_max_partecipanti})'
                    )
        
        return cleaned_data


# ============================================================================
# FORMS PER LEZIONI
# ============================================================================

class LezioneForm(forms.ModelForm):
    """
    Form per inserimento/modifica lezioni
    """
    class Meta:
        model = Lezione
        fields = [
            'edizione_corso', 'data_lezione', 'descrizione',
            'docente', 'ore_lezione', 'numero_presenti', 'note'
        ]
        widgets = {
            'edizione_corso': forms.Select(attrs={'class': 'form-control'}),
            'data_lezione': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descrizione': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Argomento della lezione'
            }),
            'docente': forms.Select(attrs={'class': 'form-control'}),
            'ore_lezione': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'placeholder': 'Es: 2.0'
            }),
            'numero_presenti': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lascia 0 se non ancora calcolato'
            }),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra docenti attivi
        self.fields['docente'].queryset = Docente.objects.filter(attivo=True)
        
        # Se stiamo modificando, pre-seleziona il docente dell'edizione
        if not self.instance.pk and 'edizione_corso' in self.initial:
            try:
                edizione = EdizioneCorso.objects.get(pk=self.initial['edizione_corso'])
                self.fields['docente'].initial = edizione.docente
            except EdizioneCorso.DoesNotExist:
                pass
    
    def clean(self):
        """Validazione lezione duplicata"""
        cleaned_data = super().clean()
        edizione = cleaned_data.get('edizione_corso')
        data = cleaned_data.get('data_lezione')
        
        if edizione and data:
            # Controlla se esiste già una lezione in questa data
            qs = Lezione.objects.filter(
                edizione_corso=edizione,
                data_lezione=data
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    f'Esiste già una lezione per questo corso in data {data.strftime("%d/%m/%Y")}'
                )
        
        return cleaned_data


class PresenzaLezioneForm(forms.ModelForm):
    """
    Form per registrazione presenza a una lezione
    """
    class Meta:
        model = PresenzaLezione
        fields = ['lezione', 'iscritto', 'presente']
        widgets = {
            'lezione': forms.HiddenInput(),
            'iscritto': forms.HiddenInput(),
            'presente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ============================================================================
# FORMS PERSONALIZZATI PER RICERCA/FILTRI
# ============================================================================

class RicercaIscrittoForm(forms.Form):
    """
    Form per ricerca avanzata iscritti
    """
    nominativo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cerca per nome o cognome'
        })
    )
    comune = forms.ModelChoiceField(
        queryset=None,  # Verrà impostato nel __init__
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Tutti i comuni"
    )
    sesso = forms.ChoiceField(
        choices=[('', 'Tutti')] + list(Iscritto.SESSO_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    e_assistente = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Solo Assistenti"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Comune
        self.fields['comune'].queryset = Comune.objects.all().order_by('nome')


class FiltroAnnoAccademicoForm(forms.Form):
    """
    Form per filtrare per anno accademico
    """
    anno_accademico = forms.ModelChoiceField(
        queryset=AnnoAccademico.objects.all().order_by('-anno'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Tutti gli anni"
    )


class RicercaCorsoForm(forms.Form):
    """
    Form per ricerca corsi
    """
    nome = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cerca per nome corso'
        })
    )
    categoria = forms.ModelChoiceField(
        queryset=None,  # Verrà impostato nel __init__
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Tutte le categorie"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import CategoriaCorso
        self.fields['categoria'].queryset = CategoriaCorso.objects.all().order_by('ordine', 'nome')
