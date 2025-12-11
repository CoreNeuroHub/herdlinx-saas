from datetime import datetime
from collections import defaultdict
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO

def group_cattle_by_color_and_kind(cattle_list):
    """Group cattle by color and breed/kind for manifest description"""
    grouped = defaultdict(lambda: {'count': 0, 'cattle': []})
    
    for cattle in cattle_list:
        color = cattle.get('color', 'Unknown') or 'Unknown'
        breed = cattle.get('breed', 'Unknown') or 'Unknown'
        key = f"{color}_{breed}"
        grouped[key]['count'] += 1
        grouped[key]['cattle'].append(cattle)
        grouped[key]['color'] = color
        grouped[key]['breed'] = breed
    
    return list(grouped.values())

def generate_manifest_data(cattle_list, template_data, feedlot_data, manual_data=None):
    """Generate manifest data structure according to Alberta Livestock Manifest format"""
    
    # Use template data if available, otherwise use manual data
    data = template_data.copy() if template_data else {}
    if manual_data:
        data.update(manual_data)
    
    # Group cattle by color and kind
    grouped_cattle = group_cattle_by_color_and_kind(cattle_list)
    
    # Calculate total head
    total_head = len(cattle_list)
    
    # Build livestock description
    livestock_description = []
    for group in grouped_cattle:
        desc = f"{group['count']} head - {group['color']} {group['breed']}"
        livestock_description.append(desc)
    
    manifest_data = {
        'part_a': {
            'purpose': data.get('purpose', 'transport_only'),
            'transport_for_sale_by': data.get('transport_for_sale_by', 'owner')
        },
        'part_b': {
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'owner_name': data.get('owner_name', ''),
            'owner_phone': data.get('owner_phone', ''),
            'owner_address': data.get('owner_address', ''),
            'dealer_name': data.get('dealer_name', ''),
            'dealer_phone': data.get('dealer_phone', ''),
            'dealer_address': data.get('dealer_address', ''),
            'on_account_of': data.get('on_account_of', ''),
            'location_before': data.get('location_before', feedlot_data.get('name', '')),
            'premises_id_before': data.get('premises_id_before', ''),
            'reason_for_transport': data.get('reason_for_transport', 'transport_to'),
            'destination_name': data.get('destination_name', ''),
            'destination_address': data.get('destination_address', ''),
            'livestock_description': livestock_description,
            'total_head': total_head,
            'grouped_cattle': grouped_cattle,
            'cattle_list': cattle_list
        },
        'part_c': {
            'owner_signature': data.get('owner_signature', ''),
            'owner_signature_date': data.get('owner_signature_date', '')
        },
        'part_d': {
            'inspector_name': data.get('inspector_name', ''),
            'inspector_number': data.get('inspector_number', ''),
            'inspection_date': data.get('inspection_date', ''),
            'inspection_time': data.get('inspection_time', ''),
            'inspection_notes': data.get('inspection_notes', '')
        },
        'part_e': {
            'transporter_name': data.get('transporter_name', ''),
            'transporter_trailer': data.get('transporter_trailer', ''),
            'transporter_phone': data.get('transporter_phone', ''),
            'transporter_signature': data.get('transporter_signature', ''),
            'transporter_signature_date': data.get('transporter_signature_date', '')
        },
        'part_f': {
            'security_interest_declared': data.get('security_interest_declared', False),
            'security_interest_details': data.get('security_interest_details', '')
        },
        'part_g': {
            'destination_name': data.get('destination_name', ''),
            'received_date': data.get('received_date', ''),
            'received_time': data.get('received_time', ''),
            'head_received': data.get('head_received', total_head),
            'receiver_name': data.get('receiver_name', ''),
            'receiver_signature': data.get('receiver_signature', ''),
            'premises_id_destination': data.get('premises_id_destination', '')
        },
        'feedlot': feedlot_data
    }
    
    return manifest_data

def generate_pdf(manifest_data, output_buffer=None):
    """Generate PDF manifest using reportlab"""
    if output_buffer is None:
        output_buffer = BytesIO()
    
    doc = SimpleDocTemplate(output_buffer, pagesize=letter,
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#0A2540'),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    story.append(Paragraph("Alberta Livestock Manifest", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Part A - Purpose
    part_a_style = ParagraphStyle(
        'PartA',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2D8B8B'),
        spaceAfter=6
    )
    story.append(Paragraph("Part A - Purpose", part_a_style))
    
    purpose = manifest_data['part_a']['purpose']
    purpose_text = {
        'transport_only': 'Transport Only',
        'transport_for_sale_owner': 'Transport for Sale - By Owner',
        'transport_for_sale_dealer': 'Transport for Sale - By Dealer',
        'inspection_only': 'Inspection Only'
    }.get(purpose, 'Transport Only')
    
    # Match HTML format - just show the purpose text without "Purpose:" label
    purpose_style = ParagraphStyle(
        'PurposeText',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=12
    )
    story.append(Paragraph(purpose_text, purpose_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Part B - Transportation and Sale Details
    story.append(Paragraph("Part B - Transportation and Sale Details", part_a_style))
    story.append(Spacer(1, 0.1*inch))
    
    part_b = manifest_data['part_b']
    # Match HTML format - use 2-column grid layout
    # Convert to Paragraph objects to support HTML formatting
    part_b_data = [
        [Paragraph('<b>Date:</b>', styles['Normal']), Paragraph(str(part_b['date']), styles['Normal'])],
        [Paragraph('<b>Owner Name:</b>', styles['Normal']), Paragraph(str(part_b['owner_name']), styles['Normal'])],
        [Paragraph('<b>Owner Phone:</b>', styles['Normal']), Paragraph(str(part_b['owner_phone']), styles['Normal'])],
        [Paragraph('<b>Owner Address:</b>', styles['Normal']), Paragraph(str(part_b['owner_address']), styles['Normal'])],
    ]
    
    if part_b.get('dealer_name'):
        part_b_data.extend([
            [Paragraph('<b>Dealer Name:</b>', styles['Normal']), Paragraph(str(part_b['dealer_name']), styles['Normal'])],
            [Paragraph('<b>Dealer Phone:</b>', styles['Normal']), Paragraph(str(part_b['dealer_phone']), styles['Normal'])],
            [Paragraph('<b>Dealer Address:</b>', styles['Normal']), Paragraph(str(part_b['dealer_address']), styles['Normal'])],
            [Paragraph('<b>On Account Of:</b>', styles['Normal']), Paragraph(str(part_b['on_account_of']), styles['Normal'])],
        ])
    
    part_b_data.extend([
        [Paragraph('<b>Location Before Transport:</b>', styles['Normal']), Paragraph(str(part_b['location_before']), styles['Normal'])],
        [Paragraph('<b>Premises ID (Before):</b>', styles['Normal']), Paragraph(str(part_b['premises_id_before']), styles['Normal'])],
        [Paragraph('<b>Reason for Transport:</b>', styles['Normal']), Paragraph(str(part_b['reason_for_transport']), styles['Normal'])],
        [Paragraph('<b>Destination Name:</b>', styles['Normal']), Paragraph(str(part_b['destination_name']), styles['Normal'])],
        [Paragraph('<b>Destination Address:</b>', styles['Normal']), Paragraph(str(part_b['destination_address']), styles['Normal'])],
    ])
    
    # Use 2-column grid layout matching HTML
    part_b_table = Table(part_b_data, colWidths=[3.25*inch, 3.25*inch])
    part_b_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('RIGHTPADDING', (0, 0), (0, -1), 12),
        ('LEFTPADDING', (1, 0), (1, -1), 0),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))
    story.append(part_b_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Livestock Description
    livestock_heading_style = ParagraphStyle(
        'LivestockHeading',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=6
    )
    story.append(Paragraph("Description of Livestock", livestock_heading_style))
    story.append(Paragraph(f"<b>Total Head:</b> {part_b['total_head']}", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    desc_data = [['Color', 'Kind (Breed)', 'Number of Head']]
    for group in part_b['grouped_cattle']:
        desc_data.append([
            group['color'],
            group['breed'],
            str(group['count'])
        ])
    
    # Match HTML format - gray header background instead of teal
    desc_table = Table(desc_data, colWidths=[2*inch, 2.5*inch, 2*inch])
    desc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),  # Gray background matching HTML bg-gray-200
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#9CA3AF')),  # Gray border matching HTML border-gray-400
    ]))
    story.append(desc_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Part C - Owner Signature
    story.append(Paragraph("Part C - Owner Signature", part_a_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Match HTML format - use 2-column grid layout
    part_c_data = [
        [Paragraph('<b>Signature:</b>', styles['Normal']), Paragraph(str(manifest_data['part_c']['owner_signature']), styles['Normal'])],
        [Paragraph('<b>Date:</b>', styles['Normal']), Paragraph(str(manifest_data['part_c']['owner_signature_date']), styles['Normal'])],
    ]
    
    part_c_table = Table(part_c_data, colWidths=[3.25*inch, 3.25*inch])
    part_c_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('RIGHTPADDING', (0, 0), (0, -1), 12),
        ('LEFTPADDING', (1, 0), (1, -1), 0),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))
    story.append(part_c_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Part E - Transporter
    story.append(Paragraph("Part E - Transporter", part_a_style))
    story.append(Spacer(1, 0.1*inch))
    
    part_e = manifest_data['part_e']
    # Match HTML format - use 2-column grid layout
    part_e_data = [
        [Paragraph('<b>Transporter Name:</b>', styles['Normal']), Paragraph(str(part_e['transporter_name']), styles['Normal'])],
        [Paragraph('<b>Trailer/Conveyance Number:</b>', styles['Normal']), Paragraph(str(part_e['transporter_trailer']), styles['Normal'])],
        [Paragraph('<b>Transporter Phone:</b>', styles['Normal']), Paragraph(str(part_e['transporter_phone']), styles['Normal'])],
        [Paragraph('<b>Signature:</b>', styles['Normal']), Paragraph(str(part_e['transporter_signature']), styles['Normal'])],
        [Paragraph('<b>Date:</b>', styles['Normal']), Paragraph(str(part_e['transporter_signature_date']), styles['Normal'])],
    ]
    
    part_e_table = Table(part_e_data, colWidths=[3.25*inch, 3.25*inch])
    part_e_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('RIGHTPADDING', (0, 0), (0, -1), 12),
        ('LEFTPADDING', (1, 0), (1, -1), 0),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))
    story.append(part_e_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Part G - Destination
    story.append(Paragraph("Part G - Destination/Receiver", part_a_style))
    story.append(Spacer(1, 0.1*inch))
    
    part_g = manifest_data['part_g']
    # Match HTML format - use 2-column grid layout
    part_g_data = [
        [Paragraph('<b>Destination Name:</b>', styles['Normal']), Paragraph(str(part_g['destination_name']), styles['Normal'])],
        [Paragraph('<b>Date Received:</b>', styles['Normal']), Paragraph(str(part_g['received_date']), styles['Normal'])],
        [Paragraph('<b>Time Received:</b>', styles['Normal']), Paragraph(str(part_g['received_time']), styles['Normal'])],
        [Paragraph('<b>Number of Head Received:</b>', styles['Normal']), Paragraph(str(part_g['head_received']), styles['Normal'])],
        [Paragraph('<b>Receiver Name:</b>', styles['Normal']), Paragraph(str(part_g['receiver_name']), styles['Normal'])],
        [Paragraph('<b>Receiver Signature:</b>', styles['Normal']), Paragraph(str(part_g['receiver_signature']), styles['Normal'])],
        [Paragraph('<b>Premises ID (Destination):</b>', styles['Normal']), Paragraph(str(part_g['premises_id_destination']), styles['Normal'])],
    ]
    
    part_g_table = Table(part_g_data, colWidths=[3.25*inch, 3.25*inch])
    part_g_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('RIGHTPADDING', (0, 0), (0, -1), 12),
        ('LEFTPADDING', (1, 0), (1, -1), 0),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))
    story.append(part_g_table)
    
    # Build PDF
    doc.build(story)
    output_buffer.seek(0)
    return output_buffer

