import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def generate_certificate(agent_name: str, topic_name: str, score: float, date_str: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=30,
        textColor=colors.HexColor('#E21B24'),
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CertSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=15,
        textColor=colors.HexColor('#444444'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    name_style = ParagraphStyle(
        'CertName',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#111111'),
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    body_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    content = [
        Spacer(1, 15),
        Paragraph("PATHAO CX ACADEMY", ParagraphStyle('Org', fontName='Helvetica-Bold', fontSize=13, textColor=colors.HexColor('#666666'), alignment=TA_CENTER, spaceAfter=8)),
        Paragraph("CERTIFICATE OF ACHIEVEMENT", title_style),
        Paragraph("This certificate is proudly presented to", subtitle_style),
        Paragraph(f"<u>{agent_name.upper()}</u>", name_style),
        Paragraph(f"for successfully passing the assessment with a score of <b>{score:.1f}%</b> in the training module:", body_style),
        Paragraph(f"<b>{topic_name}</b>", ParagraphStyle('Topic', fontName='Helvetica-Bold', fontSize=20, textColor=colors.HexColor('#E21B24'), alignment=TA_CENTER, spaceAfter=20)),
        Spacer(1, 10),
        Paragraph(f"Completion Date: <b>{date_str}</b> &nbsp;|&nbsp; Verified by Pathao CX Quality & Training Team", ParagraphStyle('Footer', fontName='Helvetica-Oblique', fontSize=10, textColor=colors.HexColor('#777777'), alignment=TA_CENTER)),
        Spacer(1, 15)
    ]
    
    table = Table([[content]], colWidths=[710])
    table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 3, colors.HexColor('#E21B24')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FAFAFA')),
        ('TOPPADDING', (0,0), (-1,-1), 15),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
    ]))
    
    elements = [table]
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
