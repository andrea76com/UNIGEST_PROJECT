"""
UNIGEST - Report PDF
File: core/reports.py
Descrizione: Generazione report PDF con ReportLab
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from io import BytesIO
from datetime import date


def crea_header_footer(canvas_obj, doc):
    """
    Crea header e footer per ogni pagina
    """
    canvas_obj.saveState()

    # Header
    canvas_obj.setFont('Helvetica-Bold', 10)
    canvas_obj.drawString(2*cm, A4[1] - 1.5*cm, "UNIVERSITÀ DEGLI ADULTI")
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.drawRightString(
        A4[0] - 2*cm,
        A4[1] - 1.5*cm,
        f"Generato il {date.today().strftime('%d/%m/%Y')}"
    )

    # Footer
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.drawCentredString(
        A4[0] / 2,
        1*cm,
        f"Pagina {doc.page}"
    )

    canvas_obj.restoreState()


def foglio_presenze_pdf(edizione_corso):
    """
    1. FOGLIO PRESENZE - Registro per appello
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2.5*cm,
        bottomMargin=2*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # Stile titolo
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=20,
        alignment=TA_CENTER
    )

    # Titolo
    title = Paragraph(
        f"FOGLIO PRESENZE<br/>{edizione_corso.corso.nome}",
        title_style
    )
    elements.append(title)

    # Info corso
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=20
    )

    info_text = f"""
    <b>Anno Accademico:</b> {edizione_corso.anno_accademico.anno}<br/>
    <b>Quadrimestre:</b> {edizione_corso.quadrimestre}<br/>
    <b>Docente:</b> {edizione_corso.docente.nome}<br/>
    <b>Orario:</b> {edizione_corso.giorni_settimana} -
    {edizione_corso.ora_inizio.strftime('%H:%M')} /
    {edizione_corso.ora_fine.strftime('%H:%M')}
    """

    elements.append(Paragraph(info_text, info_style))
    elements.append(Spacer(1, 10))

    # Tabella iscritti
    iscritti = edizione_corso.iscrizioni.all().select_related('iscritto').order_by('iscritto__nominativo')

    # Header tabella
    data = [
        ['#', 'Nominativo', 'Telefono', 'Firma 1', 'Firma 2', 'Firma 3', 'Firma 4']
    ]

    # Righe iscritti
    for i, iscrizione in enumerate(iscritti, 1):
        row = [
            str(i),
            iscrizione.iscritto.nominativo,
            iscrizione.iscritto.cellulare or iscrizione.iscritto.telefono or '-',
            '',  # Spazio per firma
            '',
            '',
            ''
        ]
        data.append(row)

    # Crea tabella
    table = Table(data, colWidths=[1*cm, 6*cm, 3.5*cm, 2*cm, 2*cm, 2*cm, 2*cm])

    # Stile tabella
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

        # Body
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Nome a sinistra
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))

    elements.append(table)

    # Genera PDF
    doc.build(elements, onFirstPage=crea_header_footer, onLaterPages=crea_header_footer)
    buffer.seek(0)

    return buffer


def elenco_iscritti_pdf(edizione_corso):
    """
    2. ELENCO ISCRITTI - Lista completa con dati anagrafici
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2.5*cm,
        bottomMargin=2*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # Titolo
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#198754'),
        spaceAfter=20,
        alignment=TA_CENTER
    )

    title = Paragraph(
        f"ELENCO ISCRITTI<br/>{edizione_corso.corso.nome}",
        title_style
    )
    elements.append(title)

    # Info corso
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=20
    )

    info_text = f"""
    <b>Anno:</b> {edizione_corso.anno_accademico.anno} |
    <b>Quadrimestre:</b> {edizione_corso.quadrimestre} |
    <b>Docente:</b> {edizione_corso.docente.nome}<br/>
    <b>Totale Iscritti:</b> {edizione_corso.iscrizioni.count()}
    """

    elements.append(Paragraph(info_text, info_style))
    elements.append(Spacer(1, 10))

    # Tabella iscritti
    iscritti = edizione_corso.iscrizioni.all().select_related('iscritto').order_by('iscritto__nominativo')

    data = [['#', 'Nominativo', 'Telefono', 'Cellulare', 'Email']]

    for i, iscrizione in enumerate(iscritti, 1):
        iscr = iscrizione.iscritto
        row = [
            str(i),
            iscr.nominativo,
            iscr.telefono or '-',
            iscr.cellulare or '-',
            Paragraph(iscr.email or '-', styles['Normal'])
        ]
        data.append(row)

    table = Table(data, colWidths=[1*cm, 5*cm, 3*cm, 3*cm, 5*cm])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))

    elements.append(table)

    doc.build(elements, onFirstPage=crea_header_footer, onLaterPages=crea_header_footer)
    buffer.seek(0)

    return buffer

def elenco_corsi_anno_pdf(anno_accademico):
    """
    3. ELENCO CORSI ANNO - Tutti i corsi dell'anno
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),  # Orizzontale
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2.5*cm,
        bottomMargin=2*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # Titolo
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#dc3545'),
        spaceAfter=20,
        alignment=TA_CENTER
    )

    title = Paragraph(
        f"ELENCO CORSI<br/>Anno Accademico {anno_accademico.anno}",
        title_style
    )
    elements.append(title)
    elements.append(Spacer(1, 20))

    # Edizioni per categoria
    from core.models import EdizioneCorso, CategoriaCorso

    categorie = CategoriaCorso.objects.all().order_by('ordine')

    for categoria in categorie:
        edizioni = EdizioneCorso.objects.filter(
            anno_accademico=anno_accademico,
            corso__categoria=categoria
        ).select_related('corso', 'docente', 'quadrimestre').order_by('corso__nome')

        if not edizioni.exists():
            continue

        # Titolo categoria
        cat_style = ParagraphStyle(
            'CategoryStyle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#0d6efd'),
            spaceAfter=10,
            spaceBefore=15
        )
        elements.append(Paragraph(f"<b>{categoria.nome}</b>", cat_style))

        # Tabella corsi
        data = [['Corso', 'Docente', 'Q', 'Giorni', 'Orario', 'Iscritti']]

        for ed in edizioni:
            row = [
                Paragraph(ed.corso.nome, styles['Normal']),
                ed.docente.nome[:30],  # Tronca se troppo lungo
                str(ed.quadrimestre.numero),
                ed.giorni_settimana[:20],
                f"{ed.ora_inizio.strftime('%H:%M')}-{ed.ora_fine.strftime('%H:%M')}",
                str(ed.iscrizioni.count())
            ]
            data.append(row)

        table = Table(data, colWidths=[6*cm, 5*cm, 1*cm, 4*cm, 3*cm, 2*cm])

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Nome corso a sinistra
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

    doc.build(elements, onFirstPage=crea_header_footer, onLaterPages=crea_header_footer)
    buffer.seek(0)

    return buffer


def rubrica_contatti_pdf(anno_accademico):
    """
    4. RUBRICA CONTATTI - Elenco telefonico iscritti
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2.5*cm,
        bottomMargin=2*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # Titolo
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#6f42c1'),
        spaceAfter=20,
        alignment=TA_CENTER
    )

    title = Paragraph(
        f"RUBRICA CONTATTI<br/>Anno Accademico {anno_accademico.anno}",
        title_style
    )
    elements.append(title)
    elements.append(Spacer(1, 20))

    # Prendi tutti gli iscritti dell'anno
    from core.models import IscrizioneAnnoAccademico

    iscrizioni_anno = IscrizioneAnnoAccademico.objects.filter(
        anno_accademico=anno_accademico
    ).select_related('iscritto').order_by('iscritto__nominativo')

    data = [['Nominativo', 'Telefono', 'Cellulare', 'Email']]

    for iscrizione in iscrizioni_anno:
        iscr = iscrizione.iscritto
        row = [
            iscr.nominativo,
            iscr.telefono or '-',
            iscr.cellulare or '-',
            Paragraph(iscr.email or '-', styles['Normal'])
        ]
        data.append(row)

    table = Table(data, colWidths=[5*cm, 3*cm, 3*cm, 6*cm])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6f42c1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))

    elements.append(table)

    doc.build(elements, onFirstPage=crea_header_footer, onLaterPages=crea_header_footer)
    buffer.seek(0)

    return buffer


def registro_lezioni_pdf(edizione_corso):
    """
    5. REGISTRO LEZIONI - Elenco lezioni effettuate
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2.5*cm,
        bottomMargin=2*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # Titolo
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#fd7e14'),
        spaceAfter=20,
        alignment=TA_CENTER
    )

    title = Paragraph(
        f"REGISTRO LEZIONI<br/>{edizione_corso.corso.nome}",
        title_style
    )
    elements.append(title)

    # Info
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=20
    )

    lezioni = edizione_corso.lezioni.all().order_by('data_lezione')
    totale_ore = sum([l.ore_lezione for l in lezioni])

    info_text = f"""
    <b>Anno:</b> {edizione_corso.anno_accademico.anno} |
    <b>Docente:</b> {edizione_corso.docente.nome}<br/>
    <b>Totale Lezioni:</b> {lezioni.count()} |
    <b>Totale Ore:</b> {totale_ore}
    """

    elements.append(Paragraph(info_text, info_style))
    elements.append(Spacer(1, 10))

    # Tabella lezioni
    data = [['#', 'Data', 'Argomento', 'Docente', 'Ore', 'Presenti']]

    for i, lezione in enumerate(lezioni, 1):
        row = [
            str(i),
            lezione.data_lezione.strftime('%d/%m/%Y'),
            Paragraph(lezione.descrizione[:50] or '-', styles['Normal']),
            lezione.docente.nome[:25],
            str(lezione.ore_lezione),
            str(lezione.numero_presenti)
        ]
        data.append(row)

    table = Table(data, colWidths=[1*cm, 2.5*cm, 7*cm, 4*cm, 1.5*cm, 2*cm])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fd7e14')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),  # Argomento a sinistra
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))

    elements.append(table)

    doc.build(elements, onFirstPage=crea_header_footer, onLaterPages=crea_header_footer)
    buffer.seek(0)

    return buffer

