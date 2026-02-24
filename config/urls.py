"""
UNIGEST - URL Configuration
File: config/urls.py
Descrizione: Configurazione URL principali del progetto
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

# Personalizzazione intestazioni Admin
admin.site.site_header = "UNIGEST - Amministrazione"
admin.site.site_title = "UNIGEST Admin"
admin.site.index_title = "Benvenuto nel pannello di amministrazione UNIGEST"

urlpatterns = [
    # URL Admin Django
    path('admin/', admin.site.urls),
    
    # Redirect dalla root alla home dell'applicazione
    path('', RedirectView.as_view(url='/unigest/', permanent=False)),
    
    # URL dell'applicazione principale UNIGEST
    path('unigest/', include('core.urls', namespace='core')),
]

# Aggiungi URL per file media in sviluppo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Aggiungi Django Debug Toolbar in sviluppo
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
