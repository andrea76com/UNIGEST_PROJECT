"""
UNIGEST - Report PDF
File: core/reports.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from io import BytesIO

def foglio_presenze_pdf(edizione_corso):
    """
    Genera PDF foglio presenze per un corso
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Titolo
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=30,
    )

    title = Paragraph(
        f"FOGLIO PRESENZE - {edizione_corso.corso.nome}",
        title_style
    )
    elements.append(title)

    # Info corso
    info = f"""
    <b>Anno Accademico:</b> {edizione_corso.anno_accademico.anno}<br/>
    <b>Quadrimestre:</b> {edizione_corso.quadrimestre}<br/>
    <b>Docente:</b> {edizione_corso.docente.nome}<br/>
    <b>Orario:</b> {edizione_corso.giorni_settimana} - {edizione_corso.ora_inizio.strftime('%H:%M')} / {edizione_corso.ora_fine.strftime('%H:%M')}
    """
    elements.append(Paragraph(info, styles['Normal']))
    elements.append(Spacer(1, 20))

    # Tabella iscritti
    iscritti = edizione_corso.iscrizioni.all().select_related('iscritto')
    lezioni = edizione_corso.lezioni.all().order_by('data_lezione')

    # Header tabella
    data = [['#', 'Nominativo', 'Telefono'] + [l.data_lezione.strftime('%d/%m') for l in lezioni]]

    # Righe iscritti
    for i, iscrizione in enumerate(iscritti, 1):
        row = [
            str(i),
            iscrizione.iscritto.nominativo,
            iscrizione.iscritto.cellulare or '-'
        ]
        # Aggiungi celle per presenze (da compilare a mano o prendere dal DB)
        for lezione in lezioni:
            presenza = lezione.presenze.filter(iscritto=iscrizione.iscritto).first()
            row.append('✓' if presenza and presenza.presente else '')
        data.append(row)

    # Stile tabella
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)

    # Genera PDF
    doc.build(elements)
    buffer.seek(0)

    return buffer


def genera_pdf_foglio_presenze(request, edizione_id):
    """
    Vista per generare il PDF
    """
    from core.models import EdizioneCorso
    edizione = EdizioneCorso.objects.get(pk=edizione_id)

    buffer = foglio_presenze_pdf(edizione)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="presenze_{edizione.corso.nome}.pdf"'
    response.write(buffer.getvalue())

    return response
