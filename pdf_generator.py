from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import qrcode
from io import BytesIO


def generate_quote_pdf(quote, output_path):
    """
    Generate PDF quote document

    Args:
        quote: Quote object
        output_path: Path where to save PDF
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                          rightMargin=2*cm, leftMargin=2*cm,
                          topMargin=2*cm, bottomMargin=2*cm)

    # Container for elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#FF6B35'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#004E89'),
        spaceAfter=12
    )

    normal_style = styles['Normal']

    # Header
    header_text = "ALKEMY COMPANY - SUNSET BAR"
    header = Paragraph(header_text, title_style)
    elements.append(header)

    subtitle_text = "Preventivo di Stampa 3D/Laser"
    subtitle = Paragraph(subtitle_text, subtitle_style)
    elements.append(subtitle)

    elements.append(Spacer(1, 0.5*cm))

    # Quote information
    info_data = [
        ['Preventivo N°:', f"#{quote.id}"],
        ['Data:', datetime.utcnow().strftime('%d/%m/%Y')],
        ['Cliente:', quote.customer_name],
        ['Validità:', '30 giorni']
    ]

    info_table = Table(info_data, colWidths=[6*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F0F0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 1*cm))

    # Description
    desc_title = Paragraph("Descrizione Lavoro:", subtitle_style)
    elements.append(desc_title)

    description = Paragraph(quote.description or "Lavoro di stampa personalizzato", normal_style)
    elements.append(description)

    elements.append(Spacer(1, 1*cm))

    # Pricing breakdown
    pricing_title = Paragraph("Dettaglio Costi:", subtitle_style)
    elements.append(pricing_title)

    pricing_data = [
        ['Descrizione', 'Importo'],
        ['Servizio di stampa', f"€ {quote.estimated_price * 0.7:.2f}"],
        ['Materiali', f"€ {quote.estimated_price * 0.2:.2f}"],
        ['Elaborazione e finitura', f"€ {quote.estimated_price * 0.1:.2f}"],
        ['', ''],
        ['TOTALE', f"€ {quote.estimated_price:.2f}"]
    ]

    pricing_table = Table(pricing_data, colWidths=[10*cm, 4*cm])
    pricing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004E89')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFE5D9')),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#FF6B35')),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey)
    ]))

    elements.append(pricing_table)
    elements.append(Spacer(1, 1.5*cm))

    # Terms
    terms_title = Paragraph("Condizioni:", subtitle_style)
    elements.append(terms_title)

    terms = [
        "• Acconto del 50% richiesto per avviare la produzione",
        "• Tempo di consegna: 3-7 giorni lavorativi (salvo diversa indicazione)",
        "• Preventivo valido 30 giorni dalla data di emissione",
        "• Eventuali modifiche al progetto potrebbero comportare variazioni di prezzo"
    ]

    for term in terms:
        elements.append(Paragraph(term, normal_style))
        elements.append(Spacer(1, 0.2*cm))

    elements.append(Spacer(1, 1*cm))

    # Generate QR code for quote acceptance (optional)
    qr = qrcode.QRCode(version=1, box_size=3, border=2)
    qr.add_data(f"QUOTE-{quote.id}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Save QR to BytesIO
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    # Add QR code
    qr_image = Image(qr_buffer, width=3*cm, height=3*cm)
    elements.append(qr_image)

    qr_text = Paragraph("Scansiona per accettare il preventivo", ParagraphStyle(
        'QRText',
        parent=normal_style,
        fontSize=8,
        alignment=TA_CENTER
    ))
    elements.append(qr_text)

    # Build PDF
    doc.build(elements)

    return output_path
