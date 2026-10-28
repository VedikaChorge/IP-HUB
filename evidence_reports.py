"""
Evidence Pack Generator Service
Generates professional, printable PDF evidence reports using ReportLab.
Includes cryptographic hashes, registration timestamps, metadata,
gap checklist audit, and verification QR code.
"""

import os
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

def generate_evidence_pdf(record, gap_data, qr_image_path, output_pdf_path):
    """
    Generate an official evidence report PDF.
    Returns:
        success (bool)
        filepath (str or None)
        message (str)
    """
    if not HAS_REPORTLAB:
        return False, None, "ReportLab is not installed in the environment."

    try:
        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=12
        )
        section_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor('#1e3a8a'),
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155')
        )
        hash_style = ParagraphStyle(
            'HashText',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#0f172a')
        )
        disclaimer_style = ParagraphStyle(
            'DisclaimerText',
            parent=styles['Normal'],
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#475569')
        )

        elements = []

        # 1. Header Banner
        elements.append(Paragraph("IP EVIDENCE HUB &bull; EVIDENCE AUDIT REPORT", title_style))
        elements.append(Paragraph(
            "Cryptographic Digital Asset Provenance & Evidence Verification Record &bull; Savitribai Phule Pune University",
            subtitle_style
        ))
        elements.append(Spacer(1, 8))

        # 2. Key Summary Table
        summary_data = [
            [
                Paragraph("<b>Evidence ID:</b>", body_style),
                Paragraph(f"<b>{record['evidence_id']}</b>", body_style),
                Paragraph("<b>Report Date:</b>", body_style),
                Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"), body_style)
            ],
            [
                Paragraph("<b>Asset Title:</b>", body_style),
                Paragraph(record['title'], body_style),
                Paragraph("<b>Category:</b>", body_style),
                Paragraph(record.get('category', 'Digital Asset') or 'Digital Asset', body_style)
            ],
            [
                Paragraph("<b>Creator / Registrant:</b>", body_style),
                Paragraph(record['creator_name'], body_style),
                Paragraph("<b>Registration Time:</b>", body_style),
                Paragraph(str(record['created_at']).replace('T', ' ')[:19], body_style)
            ]
        ]
        summary_table = Table(summary_data, colWidths=[1.3*inch, 2.3*inch, 1.3*inch, 2.3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 12))

        # 3. Cryptographic Hashes Section
        elements.append(Paragraph("1. CRYPTOGRAPHIC PROOF OF EXISTENCE (SHA-256)", section_style))
        hash_rows = [
            [
                Paragraph("<b>Primary File Hash:</b>", body_style),
                Paragraph(record['sha256_hash'], hash_style)
            ],
            [
                Paragraph("<b>Original Filename:</b>", body_style),
                Paragraph(f"{record['original_filename']} ({round(record['file_size']/1024, 2)} KB, {record['mime_type']})", body_style)
            ]
        ]
        if record['watermark_enabled'] and record.get('watermark_sha256'):
            hash_rows.append([
                Paragraph("<b>Watermarked Copy Hash:</b>", body_style),
                Paragraph(record['watermark_sha256'], hash_style)
            ])
            hash_rows.append([
                Paragraph("<b>Steganography:</b>", body_style),
                Paragraph("LSB (Least Significant Bit) Invisible Watermark embedded with Evidence ID.", body_style)
            ])

        hash_table = Table(hash_rows, colWidths=[1.8*inch, 5.4*inch])
        hash_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#93c5fd')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e0f2fe')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(hash_table)
        elements.append(Spacer(1, 10))

        # 4. Smart Evidence Gap Analysis Checklist
        elements.append(Paragraph("2. SUPPORTING EVIDENCE AUDIT TRAIL (GAP CHECK)", section_style))
        gap_score = gap_data['score_percent'] if gap_data else 14
        
        def check_icon(val):
            return "PRESENT (Confirmed)" if val else "MISSING (Recommended to collect)"

        gap_rows = [
            [Paragraph("<b>Evidence Category</b>", body_style), Paragraph("<b>Audit Status</b>", body_style)],
            [Paragraph("1. Original Master Asset File", body_style), Paragraph(check_icon(gap_data.get('has_original_file', 1) if gap_data else 1), body_style)],
            [Paragraph("2. Early Drafts, Sketches & Iterations", body_style), Paragraph(check_icon(gap_data.get('has_drafts', 0) if gap_data else 0), body_style)],
            [Paragraph("3. Creation Notes & Time-stamped Logs", body_style), Paragraph(check_icon(gap_data.get('has_creation_notes', 0) if gap_data else 0), body_style)],
            [Paragraph("4. Native Working / Project Files", body_style), Paragraph(check_icon(gap_data.get('has_working_files', 0) if gap_data else 0), body_style)],
            [Paragraph("5. Client / Collaborator Correspondence", body_style), Paragraph(check_icon(gap_data.get('has_correspondence', 0) if gap_data else 0), body_style)],
            [Paragraph("6. Publication & Public Release Records", body_style), Paragraph(check_icon(gap_data.get('has_publication_records', 0) if gap_data else 0), body_style)],
            [Paragraph("7. Identity & Creator Verification Proof", body_style), Paragraph(check_icon(gap_data.get('has_identity_proof', 0) if gap_data else 0), body_style)],
            [Paragraph("<b>Overall Evidence Completeness:</b>", body_style), Paragraph(f"<b>{gap_score}% Documented</b>", body_style)]
        ]
        gap_table = Table(gap_rows, colWidths=[3.6*inch, 3.6*inch])
        gap_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#f1f5f9')),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(gap_table)
        elements.append(Spacer(1, 10))

        # 5. Blockchain Notarization & QR Verification Section
        elements.append(Paragraph("3. BLOCKCHAIN REGISTRATION & QR AUDIT VERIFICATION", section_style))
        bc_status = record.get('blockchain_status', 'NOT_REGISTERED')
        bc_tx = record.get('blockchain_tx_hash') or 'Off-chain local record (Not yet anchored to Ethereum testnet)'
        bc_network = record.get('blockchain_network') or 'Off-chain SQLite Evidence Vault'

        bc_rows = [
            [
                Paragraph("<b>Blockchain Status:</b>", body_style),
                Paragraph(f"<b>{bc_status}</b>", body_style)
            ],
            [
                Paragraph("<b>Network:</b>", body_style),
                Paragraph(bc_network, body_style)
            ],
            [
                Paragraph("<b>Transaction Hash:</b>", body_style),
                Paragraph(bc_tx, hash_style)
            ]
        ]
        bc_table = Table(bc_rows, colWidths=[1.8*inch, 5.4*inch])
        bc_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#faf5ff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#d8b4fe')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#f3e8ff')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(bc_table)
        elements.append(Spacer(1, 10))

        # 6. QR Code & Disclaimer in two columns
        qr_flowable = Paragraph("QR verification unavailable", body_style)
        if qr_image_path and os.path.exists(qr_image_path):
            qr_flowable = RLImage(qr_image_path, width=1.1*inch, height=1.1*inch)

        disclaimer_text = (
            "<b>IMPORTANT LEGAL & FORENSIC NOTICE:</b><br/>"
            "This report is generated by IP Evidence Hub, a blockchain intellectual property evidence platform prototype "
            "developed at Savitribai Phule Pune University. This document attests that the specified SHA-256 digital fingerprint "
            "was submitted and recorded at the indicated timestamp. This report serves as an organized, chronological proof-of-possession "
            "trail to assist creators in defending against claims of unauthorized derivation. It does NOT automatically confer statutory "
            "legal copyright ownership, which is governed by national copyright registries and judicial proceedings."
        )

        bottom_table = Table([[
            qr_flowable,
            Paragraph(disclaimer_text, disclaimer_style)
        ]], colWidths=[1.3*inch, 5.9*inch])
        bottom_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(bottom_table)

        doc.build(elements)
        return True, output_pdf_path, "PDF evidence report generated successfully."

    except Exception as e:
        return False, None, f"PDF generation error: {str(e)}"
