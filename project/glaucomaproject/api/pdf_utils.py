import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from django.conf import settings
import os

def generate_glaucoma_report(diagnosis):
    """
    Generates a professional PDF report for a given Diagnosis object.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                            rightMargin=72, leftMargin=72, 
                            topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#2C3E50"),
        alignment=1, # Center
        spaceAfter=20
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#2980B9"),
        spaceBefore=15,
        spaceAfter=10,
        borderPadding=5,
        borderWidth=0,
        borderColor=colors.lightgrey,
        backColor=colors.HexColor("#F8F9FA")
    )

    story = []

    # --- Header ---
    story.append(Paragraph("GLAUCOMA DIAGNOSTIC REPORT", title_style))
    story.append(Paragraph(f"Date: {diagnosis.created_at.strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Paragraph(f"Report ID: #DIAG-{diagnosis.id:04d}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))

    # --- Patient Information ---
    story.append(Paragraph("Patient Information", section_header_style))
    patient_data = [
        ["Patient Name:", diagnosis.patient_name],
        ["Status:", "Evaluation Complete"]
    ]
    t_patient = Table(patient_data, colWidths=[1.5 * inch, 4 * inch])
    t_patient.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_patient)

    # --- AI Analysis Summary ---
    story.append(Paragraph("AI Analysis Results", section_header_style))
    
    # Highlight prediction with color
    pred_color = "#E74C3C" if diagnosis.prediction.lower() == "glaucoma" else "#27AE60"
    pred_html = f'<font color="{pred_color}"><b>{diagnosis.prediction.upper()}</b></font>'
    
    model_display = "Vision Transformer (ViT) ⚡" if getattr(diagnosis, 'model_used', 'ViT') == 'ViT' else "ResNet CNN 🧠"
    
    analysis_data = [
        ["AI Classification Engine:", model_display],
        ["AI Prediction:", Paragraph(pred_html, styles['Normal'])],
        ["Confidence Score:", f"{diagnosis.confidence:.2f}%"],
        ["Glaucoma Probability:", f"{diagnosis.glaucoma_prob:.2f}%"],
        ["Normal Probability:", f"{diagnosis.normal_prob:.2f}%"]
    ]
    t_analysis = Table(analysis_data, colWidths=[2 * inch, 3.5 * inch])
    t_analysis.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1,1), (1,1), colors.HexColor(pred_color)),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_analysis)

    # --- Retinal Image ---
    story.append(Paragraph("Retinal Fundus Image", section_header_style))
    if diagnosis.image:
        img_path = diagnosis.image.path
        if os.path.exists(img_path):
            img = Image(img_path, width=3.5 * inch, height=3.5 * inch)
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Paragraph("<i>Scan Image provided for clinical review</i>", styles['Italic']))
        else:
            story.append(Paragraph("[Image file missing from server]", styles['Normal']))
    
    # --- Doctor's Notes & Recommendations ---
    story.append(Paragraph("Doctor's Clinical Notes", section_header_style))
    notes = diagnosis.doctor_notes if diagnosis.doctor_notes else "No specific notes provided."
    story.append(Paragraph(notes, styles['Normal']))

    story.append(Paragraph("Clinical Recommendations", section_header_style))
    recs = diagnosis.recommendations if diagnosis.recommendations else "Standard follow-up as per clinical protocol."
    story.append(Paragraph(recs, styles['Normal']))

    # --- Footer ---
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("-" * 80, styles['Normal']))
    story.append(Paragraph("<b>Disclaimer:</b> This AI-generated report is for screening assistance only. Final diagnosis must be confirmed by a licensed ophthalmologist.", styles['Italic']))

    # Build PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer
