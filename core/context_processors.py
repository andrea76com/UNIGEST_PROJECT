"""
UNIGEST - Context Processors
File: core/context_processors.py
Descrizione: Fornisce dati globali a tutti i template
"""

from core.models import AnnoAccademico
from datetime import date

def calcola_anno_corrente():
    """
    Calcola l'anno accademico corrente in base alla data odierna.
    Logica: Se mese >= Agosto (8), siamo nel nuovo anno accademico
    Esempio:
    - 14/04/2025 -> Anno 2024-2025
    - 01/08/2025 -> Anno 2025-2026
    - 25/11/2025 -> Anno 2025-2026
    """
    oggi = date.today()

    # Se siamo da Agosto in poi, l'anno accademico inizia quest'anno
    if oggi.month >= 8:
        anno_inizio = oggi.year
    else:
        # Altrimenti siamo ancora nell'anno accademico precedente
        anno_inizio = oggi.year - 1

    anno_fine = anno_inizio + 1
    anno_str = f"{anno_inizio}-{anno_fine}"

    return anno_str


def anno_accademico_corrente(request):
    """
    Fornisce l'anno accademico selezionato a tutti i template
    """
    # Ottieni anno dalla sessione
    anno_id = request.session.get('anno_accademico_id')

    if anno_id:
        anno_attivo = AnnoAccademico.objects.filter(id=anno_id).first()
    else:
        # Se non c'è nella sessione, calcola l'anno corrente
        anno_corrente_str = calcola_anno_corrente()
        anno_attivo = AnnoAccademico.objects.filter(anno=anno_corrente_str).first()

        # Se non esiste quell'anno, prendi l'anno marcato come attivo
        if not anno_attivo:
            anno_attivo = AnnoAccademico.objects.filter(attivo=True).first()

        # Se ancora non c'è, prendi il più recente
        if not anno_attivo:
            anno_attivo = AnnoAccademico.objects.order_by('-anno').first()

    # Salva in sessione
    if anno_attivo:
        request.session['anno_accademico_id'] = anno_attivo.id

    # Lista di tutti gli anni per il selettore
    anni_disponibili = AnnoAccademico.objects.all().order_by('-anno')

    return {
        'anno_attivo': anno_attivo,
        'anni_disponibili': anni_disponibili,
        'anno_corrente_calcolato': calcola_anno_corrente(),  # Per debug
    }
