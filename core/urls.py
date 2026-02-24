"""
UNIGEST - URLs Core App
File: core/urls.py
Descrizione: Configurazione URL per l'applicazione principale
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ========================================================================
    # HOME E DASHBOARD
    # ========================================================================
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ========================================================================
    # ANAGRAFICHE - ISCRITTI
    # ========================================================================
    path('iscritti/', views.IscrittoListView.as_view(), name='iscritto_list'),
    path('iscritti/<int:pk>/', views.IscrittoDetailView.as_view(), name='iscritto_detail'),
    path('iscritti/nuovo/', views.IscrittoCreateView.as_view(), name='iscritto_create'),
    path('iscritti/<int:pk>/modifica/', views.IscrittoUpdateView.as_view(), name='iscritto_update'),
    path('iscritti/<int:pk>/elimina/', views.IscrittoDeleteView.as_view(), name='iscritto_delete'),
    
    # ========================================================================
    # ANAGRAFICHE - DOCENTI
    # ========================================================================
    path('docenti/', views.DocenteListView.as_view(), name='docente_list'),
    path('docenti/<int:pk>/', views.DocenteDetailView.as_view(), name='docente_detail'),
    path('docenti/nuovo/', views.DocenteCreateView.as_view(), name='docente_create'),
    path('docenti/<int:pk>/modifica/', views.DocenteUpdateView.as_view(), name='docente_update'),
    
    # ========================================================================
    # ANAGRAFICHE - AUTORITÀ
    # ========================================================================
    path('autorita/', views.AutoritaListView.as_view(), name='autorita_list'),
    path('autorita/<int:pk>/', views.AutoritaDetailView.as_view(), name='autorita_detail'),
    path('autorita/nuova/', views.AutoritaCreateView.as_view(), name='autorita_create'),
    path('autorita/<int:pk>/modifica/', views.AutoritaUpdateView.as_view(), name='autorita_update'),
    
    # ========================================================================
    # CORSI
    # ========================================================================
    path('corsi/', views.CorsoListView.as_view(), name='corso_list'),
    path('corsi/<int:pk>/', views.CorsoDetailView.as_view(), name='corso_detail'),
    path('corsi/nuovo/', views.CorsoCreateView.as_view(), name='corso_create'),
    path('corsi/<int:pk>/modifica/', views.CorsoUpdateView.as_view(), name='corso_update'),
    
    # ========================================================================
    # EDIZIONI CORSI (Corsi Annuali)
    # ========================================================================
    path('edizioni/', views.EdizioneCorsoListView.as_view(), name='edizione_list'),
    path('edizioni/<int:pk>/', views.EdizioneCorsoDetailView.as_view(), name='edizione_detail'),
    path('edizioni/nuova/', views.EdizioneCorsoCreateView.as_view(), name='edizione_create'),
    path('edizioni/<int:pk>/modifica/', views.EdizioneCorsoUpdateView.as_view(), name='edizione_update'),
    path('edizioni/<int:pk>/iscrizioni/', views.gestione_iscrizioni_corso, name='gestione_iscrizioni'),
    
    # ========================================================================
    # ISCRIZIONI
    # ========================================================================
    path('iscrizioni-anno/', views.IscrizioneAnnoListView.as_view(), name='iscrizione_anno_list'),
    path('iscrizioni-anno/nuova/', views.IscrizioneAnnoCreateView.as_view(), name='iscrizione_anno_create'),
    path('export/iscritti-excel/', views.export_iscritti_excel, name='export_iscritti_excel'),
    path('iscrizioni-corso/', views.IscrizioneCorsoListView.as_view(), name='iscrizione_corso_list'),
    path('iscrizioni-corso/nuova/', views.IscrizioneCorsoCreateView.as_view(), name='iscrizione_corso_create'),
    
    # ========================================================================
    # LEZIONI E PRESENZE
    # ========================================================================
    path('lezioni/', views.LezioneListView.as_view(), name='lezione_list'),
    path('lezioni/<int:pk>/', views.LezioneDetailView.as_view(), name='lezione_detail'),
    path('lezioni/nuova/', views.LezioneCreateView.as_view(), name='lezione_create'),
    path('lezioni/<int:pk>/modifica/', views.LezioneUpdateView.as_view(), name='lezione_update'),
    path('lezioni/<int:pk>/presenze/', views.gestione_presenze, name='gestione_presenze'),
    
    # ========================================================================
    # REPORT
    # ========================================================================
    path('report/', views.report_menu, name='report_menu'),
    path('report/foglio-presenze/<int:edizione_id>/', views.foglio_presenze_pdf, name='foglio_presenze_pdf'),
    path('report/elenco-iscritti/<int:edizione_id>/', views.elenco_iscritti_pdf, name='elenco_iscritti_pdf'),
    path('report/statistiche-anno/<int:anno_id>/', views.statistiche_anno, name='statistiche_anno'),
    path('report/elenco-corsi-anno/<int:anno_id>/', views.elenco_corsi_anno_pdf, name='elenco_corsi_anno_pdf'),
    path('report/rubrica-contatti/<int:anno_id>/', views.rubrica_contatti_pdf, name='rubrica_contatti_pdf'),
    path('report/registro-lezioni/<int:edizione_id>/', views.registro_lezioni_pdf, name='registro_lezioni_pdf'),
    
    # ========================================================================
    # UTILITÀ
    # ========================================================================
    path('cerca/', views.ricerca_globale, name='ricerca_globale'),
    path('anno-accademico/cambia/', views.cambia_anno_accademico, name='cambia_anno_accademico'),
]
