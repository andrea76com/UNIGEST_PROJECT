"""
UNIGEST - Views
File: core/views.py
Descrizione: Viste per la gestione dell'applicazione
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import (
    Iscritto, Docente, Autorita, Corso, EdizioneCorso, AnnoAccademico,
    IscrizioneAnnoAccademico, IscrizioneCorso, Lezione, PresenzaLezione
)
from .forms import (
    IscrittoForm, DocenteForm, AutoritaForm, CorsoForm, EdizioneCorsoForm,
    IscrizioneAnnoForm, IscrizioneCorsoForm, LezioneForm
)


# ============================================================================
# HOME E DASHBOARD
# ============================================================================

def home(request):
    """
    Vista per la home page principale
    """
    # L'anno_attivo viene dal context processor
    anno_attivo = request.session.get('anno_accademico_id')
    if anno_attivo:
        anno_attivo = AnnoAccademico.objects.filter(id=anno_attivo).first()

    # Statistiche rapide
    context = {
        'totale_iscritti': Iscritto.objects.count(),
        'totale_docenti': Docente.objects.filter(attivo=True).count(),
        'totale_corsi': Corso.objects.filter(visibile=True).count(),
    }

    if anno_attivo:
        context['iscritti_anno_corrente'] = IscrizioneAnnoAccademico.objects.filter(
            anno_accademico=anno_attivo
        ).count()
        context['edizioni_anno_corrente'] = EdizioneCorso.objects.filter(
            anno_accademico=anno_attivo
        ).count()

    return render(request, 'home.html', context)


def dashboard(request):
    """
    Dashboard con statistiche dettagliate
    """
    # Ottieni anno dalla sessione
    anno_id = request.session.get('anno_accademico_id')
    anno_attivo = None
    if anno_id:
        anno_attivo = AnnoAccademico.objects.filter(id=anno_id).first()

    if not anno_attivo:
        anno_attivo = AnnoAccademico.objects.filter(attivo=True).first()

    context = {}

    if anno_attivo:
        # Statistiche iscrizioni
        context['iscritti_anno'] = IscrizioneAnnoAccademico.objects.filter(
            anno_accademico=anno_attivo
        ).count()

        # AGGIUNGI QUESTA RIGA ⬇️
        context['edizioni_anno_corrente'] = EdizioneCorso.objects.filter(
            anno_accademico=anno_attivo
        ).count()

        # Edizioni per categoria
        context['edizioni_per_categoria'] = EdizioneCorso.objects.filter(
            anno_accademico=anno_attivo
        ).values(
            'corso__categoria__nome'
        ).annotate(
            totale=Count('id')
        ).order_by('-totale')

        # Corsi più frequentati
        context['corsi_piu_frequentati'] = EdizioneCorso.objects.filter(
            anno_accademico=anno_attivo
        ).annotate(
            num_iscritti=Count('iscrizioni')
        ).order_by('-num_iscritti')[:10]

    return render(request, 'dashboard.html', context)


# ============================================================================
# VIEWS PER ISCRITTI
# ============================================================================

class IscrittoListView(ListView):
    """Lista di tutti gli iscritti"""
    model = Iscritto
    template_name = 'anagrafiche/iscritto_list.html'
    context_object_name = 'iscritti'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Ricerca per nominativo
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nominativo__icontains=search) |
                Q(codice_fiscale__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Filtro per sesso
        sesso = self.request.GET.get('sesso')
        if sesso:
            queryset = queryset.filter(sesso=sesso)
        
        # Filtro per comune
        comune = self.request.GET.get('comune')
        if comune:
            queryset = queryset.filter(comune_id=comune)
        
        return queryset.select_related('comune', 'titolo_studio')


class IscrittoDetailView(DetailView):
    """Dettaglio di un singolo iscritto"""
    model = Iscritto
    template_name = 'anagrafiche/iscritto_detail.html'
    context_object_name = 'iscritto'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Storico iscrizioni anni accademici
        context['iscrizioni_anni'] = IscrizioneAnnoAccademico.objects.filter(
            iscritto=self.object
        ).select_related('anno_accademico').order_by('-anno_accademico__anno')
        
        # Storico corsi frequentati
        context['corsi_frequentati'] = IscrizioneCorso.objects.filter(
            iscritto=self.object
        ).select_related(
            'edizione_corso__corso',
            'edizione_corso__anno_accademico'
        ).order_by('-anno_accademico__anno')
        
        # Corsi come assistente
        context['corsi_come_assistente'] = EdizioneCorso.objects.filter(
            Q(assistente=self.object) | Q(vice_assistente=self.object)
        ).select_related('corso', 'anno_accademico')
        
        return context


class IscrittoCreateView(CreateView):
    """Creazione nuovo iscritto"""
    model = Iscritto
    form_class = IscrittoForm
    template_name = 'anagrafiche/iscritto_form.html'
    success_url = reverse_lazy('core:iscritto_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Iscritto creato con successo!')
        return super().form_valid(form)


class IscrittoUpdateView(UpdateView):
    """Modifica iscritto esistente"""
    model = Iscritto
    form_class = IscrittoForm
    template_name = 'anagrafiche/iscritto_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Iscritto modificato con successo!')
        return super().form_valid(form)


class IscrittoDeleteView(DeleteView):
    """Eliminazione iscritto"""
    model = Iscritto
    template_name = 'anagrafiche/iscritto_confirm_delete.html'
    success_url = reverse_lazy('core:iscritto_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Iscritto eliminato con successo!')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# VIEWS PER DOCENTI
# ============================================================================

class DocenteListView(ListView):
    """Lista di tutti i docenti"""
    model = Docente
    template_name = 'anagrafiche/docente_list.html'
    context_object_name = 'docenti'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro per attivo/non attivo
        attivo = self.request.GET.get('attivo')
        if attivo == '1':
            queryset = queryset.filter(attivo=True)
        elif attivo == '0':
            queryset = queryset.filter(attivo=False)
        
        return queryset.select_related('comune')


class DocenteDetailView(DetailView):
    """Dettaglio di un singolo docente"""
    model = Docente
    template_name = 'anagrafiche/docente_detail.html'
    context_object_name = 'docente'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Corsi tenuti
        context['corsi_tenuti'] = EdizioneCorso.objects.filter(
            docente=self.object
        ).select_related(
            'corso',
            'anno_accademico'
        ).order_by('-anno_accademico__anno')
        
        return context


class DocenteCreateView(CreateView):
    """Creazione nuovo docente"""
    model = Docente
    form_class = DocenteForm
    template_name = 'anagrafiche/docente_form.html'
    success_url = reverse_lazy('core:docente_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Docente creato con successo!')
        return super().form_valid(form)


class DocenteUpdateView(UpdateView):
    """Modifica docente esistente"""
    model = Docente
    form_class = DocenteForm
    template_name = 'anagrafiche/docente_form.html'
    success_url = reverse_lazy('core:docente_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Docente modificato con successo!')
        return super().form_valid(form)


# ============================================================================
# VIEWS PER AUTORITÀ
# ============================================================================

class AutoritaListView(ListView):
    """Lista delle autorità"""
    model = Autorita
    template_name = 'anagrafiche/autorita_list.html'
    context_object_name = 'autorita'
    paginate_by = 50


class AutoritaDetailView(DetailView):
    """Dettaglio di un'autorità"""
    model = Autorita
    template_name = 'anagrafiche/autorita_detail.html'
    context_object_name = 'autorita'


class AutoritaCreateView(CreateView):
    """Creazione nuova autorità"""
    model = Autorita
    form_class = AutoritaForm
    template_name = 'anagrafiche/autorita_form.html'
    success_url = reverse_lazy('core:autorita_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Autorità creata con successo!')
        return super().form_valid(form)


class AutoritaUpdateView(UpdateView):
    """Modifica autorità esistente"""
    model = Autorita
    form_class = AutoritaForm
    template_name = 'anagrafiche/autorita_form.html'
    success_url = reverse_lazy('core:autorita_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Autorità modificata con successo!')
        return super().form_valid(form)


# ============================================================================
# VIEWS PER CORSI
# ============================================================================

class CorsoListView(ListView):
    """Lista di tutti i corsi"""
    model = Corso
    template_name = 'corsi/corso_list.html'
    context_object_name = 'corsi'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro per categoria
        categoria = self.request.GET.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        
        return queryset.select_related('categoria', 'gruppo')


class CorsoDetailView(DetailView):
    """Dettaglio di un corso"""
    model = Corso
    template_name = 'corsi/corso_detail.html'
    context_object_name = 'corso'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Edizioni del corso
        context['edizioni'] = EdizioneCorso.objects.filter(
            corso=self.object
        ).select_related(
            'anno_accademico',
            'docente'
        ).order_by('-anno_accademico__anno')
        
        return context


class CorsoCreateView(CreateView):
    """Creazione nuovo corso"""
    model = Corso
    form_class = CorsoForm
    template_name = 'corsi/corso_form.html'
    success_url = reverse_lazy('core:corso_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Corso creato con successo!')
        return super().form_valid(form)


class CorsoUpdateView(UpdateView):
    """Modifica corso esistente"""
    model = Corso
    form_class = CorsoForm
    template_name = 'corsi/corso_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Corso modificato con successo!')
        return super().form_valid(form)


# ============================================================================
# VIEWS PER EDIZIONI CORSI
# ============================================================================

class EdizioneCorsoListView(ListView):
    """Lista delle edizioni corsi"""
    model = EdizioneCorso
    template_name = 'corsi/edizione_list.html'
    context_object_name = 'edizioni'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtro per anno accademico
        anno = self.request.GET.get('anno')
        if anno:
            queryset = queryset.filter(anno_accademico_id=anno)
        else:
            # Default: anno dalla sessione
            anno_id = self.request.session.get('anno_accademico_id')
            if anno_id:
                queryset = queryset.filter(anno_accademico_id=anno_id)
            else:
                # Fallback: anno attivo
                anno_attivo = AnnoAccademico.objects.filter(attivo=True).first()
                if anno_attivo:
                    queryset = queryset.filter(anno_accademico=anno_attivo)

        # Filtro per quadrimestre
        quadrimestre = self.request.GET.get('quadrimestre')
        if quadrimestre:
            queryset = queryset.filter(quadrimestre_id=quadrimestre)

        return queryset.select_related(
            'corso',
            'anno_accademico',
            'quadrimestre',
            'docente'
        ).annotate(
            num_iscritti=Count('iscrizioni')
        )


class EdizioneCorsoDetailView(DetailView):
    """Dettaglio di un'edizione corso"""
    model = EdizioneCorso
    template_name = 'corsi/edizione_detail.html'
    context_object_name = 'edizione'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Iscritti al corso
        context['iscritti'] = IscrizioneCorso.objects.filter(
            edizione_corso=self.object
        ).select_related('iscritto').order_by('iscritto__nominativo')
        
        # Lezioni effettuate
        context['lezioni'] = Lezione.objects.filter(
            edizione_corso=self.object
        ).order_by('-data_lezione')
        
        return context


class EdizioneCorsoCreateView(CreateView):
    """Creazione nuova edizione corso"""
    model = EdizioneCorso
    form_class = EdizioneCorsoForm
    template_name = 'corsi/edizione_form.html'
    success_url = reverse_lazy('core:edizione_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Edizione corso creata con successo!')
        return super().form_valid(form)


class EdizioneCorsoUpdateView(UpdateView):
    """Modifica edizione corso esistente"""
    model = EdizioneCorso
    form_class = EdizioneCorsoForm
    template_name = 'corsi/edizione_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Edizione corso modificata con successo!')
        return super().form_valid(form)


def gestione_iscrizioni_corso(request, pk):
    """
    Vista per gestire le iscrizioni a un corso specifico
    """
    edizione = get_object_or_404(EdizioneCorso, pk=pk)
    
    # Iscritti già nel corso
    iscritti_corso = IscrizioneCorso.objects.filter(
        edizione_corso=edizione
    ).values_list('iscritto_id', flat=True)
    
    # Iscritti disponibili (iscritti all'anno ma non al corso)
    iscritti_disponibili = Iscritto.objects.filter(
        iscrizioneannoacademico__anno_accademico=edizione.anno_accademico
    ).exclude(
        id__in=iscritti_corso
    ).order_by('nominativo')
    
    context = {
        'edizione': edizione,
        'iscritti_disponibili': iscritti_disponibili,
    }
    
    return render(request, 'corsi/gestione_iscrizioni.html', context)


# ============================================================================
# VIEWS PER ISCRIZIONI
# ============================================================================

class IscrizioneAnnoListView(ListView):
    """Lista iscrizioni anno accademico"""
    model = IscrizioneAnnoAccademico
    template_name = 'iscrizioni/iscrizione_anno_list.html'
    context_object_name = 'iscrizioni'
    paginate_by = 100


class IscrizioneAnnoCreateView(CreateView):
    """Creazione nuova iscrizione anno"""
    model = IscrizioneAnnoAccademico
    form_class = IscrizioneAnnoForm
    template_name = 'iscrizioni/iscrizione_anno_form.html'
    success_url = reverse_lazy('core:iscrizione_anno_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Iscrizione anno creata con successo!')
        return super().form_valid(form)


class IscrizioneCorsoListView(ListView):
    """Lista iscrizioni corsi"""
    model = IscrizioneCorso
    template_name = 'iscrizioni/iscrizione_corso_list.html'
    context_object_name = 'iscrizioni'
    paginate_by = 100


class IscrizioneCorsoCreateView(CreateView):
    """Creazione nuova iscrizione corso"""
    model = IscrizioneCorso
    form_class = IscrizioneCorsoForm
    template_name = 'iscrizioni/iscrizione_corso_form.html'
    success_url = reverse_lazy('core:iscrizione_corso_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Iscrizione corso creata con successo!')
        return super().form_valid(form)


# ============================================================================
# VIEWS PER LEZIONI
# ============================================================================

class LezioneListView(ListView):
    """Lista lezioni"""
    model = Lezione
    template_name = 'lezioni/lezione_list.html'
    context_object_name = 'lezioni'
    paginate_by = 50


class LezioneDetailView(DetailView):
    """Dettaglio lezione"""
    model = Lezione
    template_name = 'lezioni/lezione_detail.html'
    context_object_name = 'lezione'


class LezioneCreateView(CreateView):
    """Creazione nuova lezione"""
    model = Lezione
    form_class = LezioneForm
    template_name = 'lezioni/lezione_form.html'
    success_url = reverse_lazy('core:lezione_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Lezione creata con successo!')
        return super().form_valid(form)


class LezioneUpdateView(UpdateView):
    """Modifica lezione"""
    model = Lezione
    form_class = LezioneForm
    template_name = 'lezioni/lezione_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Lezione modificata con successo!')
        return super().form_valid(form)


def gestione_presenze(request, pk):
    """
    Vista per gestire le presenze a una lezione
    """
    lezione = get_object_or_404(Lezione, pk=pk)
    
    # Ottieni tutti gli iscritti al corso
    iscritti_corso = IscrizioneCorso.objects.filter(
        edizione_corso=lezione.edizione_corso
    ).select_related('iscritto')
    
    # Crea o ottieni le presenze
    for iscrizione in iscritti_corso:
        PresenzaLezione.objects.get_or_create(
            lezione=lezione,
            iscritto=iscrizione.iscritto,
            defaults={'presente': True}
        )
    
    presenze = PresenzaLezione.objects.filter(
        lezione=lezione
    ).select_related('iscritto').order_by('iscritto__nominativo')
    
    if request.method == 'POST':
        # Aggiorna presenze
        for presenza in presenze:
            campo = f'presenza_{presenza.id}'
            presenza.presente = campo in request.POST
            presenza.save()
        
        # Aggiorna conteggio
        lezione.numero_presenti = presenze.filter(presente=True).count()
        lezione.save()
        
        messages.success(request, 'Presenze salvate con successo!')
        return redirect('core:lezione_detail', pk=lezione.pk)
    
    context = {
        'lezione': lezione,
        'presenze': presenze,
    }
    
    return render(request, 'lezioni/gestione_presenze.html', context)


# ============================================================================
# REPORT (Placeholder - da implementare con PDF)
# ============================================================================

def report_menu(request):
    """Menu dei report disponibili"""
    # Ottieni anno dalla sessione
    anno_id = request.session.get('anno_accademico_id')
    anno_attivo = None
    if anno_id:
        anno_attivo = AnnoAccademico.objects.filter(id=anno_id).first()

    # Edizioni dell'anno per i modal
    edizioni = []
    if anno_attivo:
        edizioni = EdizioneCorso.objects.filter(
            anno_accademico=anno_attivo
        ).select_related('corso', 'docente', 'quadrimestre').order_by('corso__nome')

    context = {
        'edizioni': edizioni
    }

    return render(request, 'report/menu.html', context)


def foglio_presenze_pdf(request, edizione_id):
    """Genera foglio presenze PDF"""
    from core.models import EdizioneCorso
    from .reports import foglio_presenze_pdf as genera_pdf

    edizione = get_object_or_404(EdizioneCorso, pk=edizione_id)
    buffer = genera_pdf(edizione)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="presenze_{edizione.corso.nome}.pdf"'
    response.write(buffer.getvalue())

    return response


def elenco_iscritti_pdf(request, edizione_id):
    """Genera elenco iscritti PDF"""
    from core.models import EdizioneCorso
    from .reports import elenco_iscritti_pdf as genera_pdf

    edizione = get_object_or_404(EdizioneCorso, pk=edizione_id)
    buffer = genera_pdf(edizione)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="iscritti_{edizione.corso.nome}.pdf"'
    response.write(buffer.getvalue())

    return response


def elenco_corsi_anno_pdf(request, anno_id):
    """Genera elenco corsi anno PDF"""
    from core.models import AnnoAccademico
    from .reports import elenco_corsi_anno_pdf as genera_pdf

    anno = get_object_or_404(AnnoAccademico, pk=anno_id)
    buffer = genera_pdf(anno)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="corsi_{anno.anno}.pdf"'
    response.write(buffer.getvalue())

    return response


def rubrica_contatti_pdf(request, anno_id):
    """Genera rubrica contatti PDF"""
    from core.models import AnnoAccademico
    from .reports import rubrica_contatti_pdf as genera_pdf

    anno = get_object_or_404(AnnoAccademico, pk=anno_id)
    buffer = genera_pdf(anno)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rubrica_{anno.anno}.pdf"'
    response.write(buffer.getvalue())

    return response


def registro_lezioni_pdf(request, edizione_id):
    """Genera registro lezioni PDF"""
    from core.models import EdizioneCorso
    from .reports import registro_lezioni_pdf as genera_pdf

    edizione = get_object_or_404(EdizioneCorso, pk=edizione_id)
    buffer = genera_pdf(edizione)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="registro_{edizione.corso.nome}.pdf"'
    response.write(buffer.getvalue())

    return response

# ============================================================================
# UTILITÀ
# ============================================================================

def ricerca_globale(request):
    """Ricerca globale nel database"""
    query = request.GET.get('q', '')
    
    risultati = {
        'iscritti': [],
        'docenti': [],
        'corsi': [],
    }
    
    if query:
        risultati['iscritti'] = Iscritto.objects.filter(
            Q(nominativo__icontains=query) |
            Q(codice_fiscale__icontains=query)
        )[:10]
        
        risultati['docenti'] = Docente.objects.filter(
            nome__icontains=query
        )[:10]
        
        risultati['corsi'] = Corso.objects.filter(
            Q(nome__icontains=query) |
            Q(descrizione__icontains=query)
        )[:10]
    
    return render(request, 'ricerca.html', {
        'query': query,
        'risultati': risultati
    })


def cambia_anno_accademico(request):
    """Cambia l'anno accademico nella sessione"""
    if request.method == 'POST':
        anno_id = request.POST.get('anno_id')
        if anno_id:
            try:
                anno = AnnoAccademico.objects.get(pk=anno_id)
                request.session['anno_accademico_id'] = anno.id
                messages.success(request, f'Anno accademico cambiato: {anno.anno}')
            except AnnoAccademico.DoesNotExist:
                messages.error(request, 'Anno accademico non trovato')

    # Redirect alla pagina precedente o home
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/unigest/'))
    return redirect(next_url)


def export_iscritti_excel(request):
    """
    Esporta iscritti in Excel
    """
    from openpyxl import Workbook
    from django.http import HttpResponse

    # Crea workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Iscritti"

    # Header
    headers = ['Matricola', 'Nominativo', 'Sesso', 'Data Nascita',
               'Comune', 'Telefono', 'Cellulare', 'Email']
    ws.append(headers)

    # Dati
    iscritti = Iscritto.objects.all().select_related('comune')
    for iscritto in iscritti:
        ws.append([
            iscritto.matricola,
            iscritto.nominativo,
            iscritto.get_sesso_display(),
            iscritto.data_nascita.strftime('%d/%m/%Y') if iscritto.data_nascita else '',
            str(iscritto.comune) if iscritto.comune else '',
            iscritto.telefono or '',
            iscritto.cellulare or '',
            iscritto.email or ''
        ])

    # Response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=iscritti.xlsx'
    wb.save(response)

    return response

def statistiche_anno(request, anno_id):
    """Mostra statistiche anno accademico"""
    from django.db.models import Count, Avg

    anno = get_object_or_404(AnnoAccademico, pk=anno_id)

    # Statistiche generali
    stats = {
        'anno': anno,
        'totale_iscritti': IscrizioneAnnoAccademico.objects.filter(anno_accademico=anno).count(),
        'totale_edizioni': EdizioneCorso.objects.filter(anno_accademico=anno).count(),
        'totale_iscrizioni_corso': IscrizioneCorso.objects.filter(anno_accademico=anno).count(),
        'totale_lezioni': Lezione.objects.filter(edizione_corso__anno_accademico=anno).count(),
    }

    # Iscrizioni per categoria
    stats['per_categoria'] = EdizioneCorso.objects.filter(
        anno_accademico=anno
    ).values(
        'corso__categoria__nome'
    ).annotate(
        num_edizioni=Count('id'),
        num_iscritti=Count('iscrizioni')
    ).order_by('-num_iscritti')

    # Corsi più frequentati
    stats['top_corsi'] = EdizioneCorso.objects.filter(
        anno_accademico=anno
    ).annotate(
        num_iscritti=Count('iscrizioni')
    ).order_by('-num_iscritti')[:10]

    # Presenze medie
    lezioni_con_presenze = Lezione.objects.filter(
        edizione_corso__anno_accademico=anno,
        numero_presenti__gt=0
    )
    if lezioni_con_presenze.exists():
        stats['presenza_media'] = lezioni_con_presenze.aggregate(
            Avg('numero_presenti')
        )['numero_presenti__avg']
    else:
        stats['presenza_media'] = 0

    return render(request, 'report/statistiche.html', stats)

