"""
Digital Battery Passport Certificate Generator
Creates PDF and JSON certificates for individual batteries
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


class CertificateGenerator:
    """
    Generates Digital Battery Passports in PDF and JSON formats.
    """
    
    GRADE_COLORS = {
        'Grade A': colors.HexColor('#27AE60'),  # Green
        'Grade B': colors.HexColor('#F39C12'),  # Orange
        'Grade C': colors.HexColor('#E74C3C'),  # Red
    }
    
    GRADE_ICONS = {
        'Grade A': '✓ CERTIFIED',
        'Grade B': '⚠ CONDITIONAL',
        'Grade C': '♻ RECYCLING',
    }
    
    def __init__(self, output_dir: str = 'certificates'):
        """Initialize certificate generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_json_certificate(self, battery_data: Dict, filename: str = None) -> str:
        """
        Generate a JSON certificate for a battery.
        
        Args:
            battery_data: Dictionary with battery assessment results
            filename: Optional custom filename (defaults to battery_id)
            
        Returns:
            Path to generated JSON file
        """
        if filename is None:
            filename = f"{battery_data['Battery_ID']}_certificate.json"
        
        output_path = self.output_dir / filename
        
        # Enrich data with additional metadata
        certificate = {
            'certificate_type': 'Digital Battery Passport',
            'issue_date': datetime.now().isoformat(),
            'version': '1.0',
            'battery_info': {
                'battery_id': battery_data['Battery_ID'],
                'predicted_rul_cycles': battery_data['Predicted_RUL'],
                'average_operating_temp_c': battery_data['Avg_Operating_Temp'],
            },
            'health_assessment': {
                'health_score_percent': battery_data['Health_Score_%'],
                'grade': battery_data['Grade'],
                'category': battery_data['Category'],
                'certified_applications': battery_data['Applications'].split(', '),
            },
            'thermal_audit': {
                'temperature_penalty_factor': battery_data['Temperature_Penalty_Factor'],
                'assessment': battery_data['Temperature_Assessment'],
            },
            'valuation': {
                'residual_value_inr': battery_data['Residual_Value_INR'],
                'currency': 'INR',
                'blue_book_value': f"₹{battery_data['Residual_Value_INR']:,.2f}",
            },
            'metadata': {
                'assessment_timestamp': battery_data['Assessment_Date'],
                'certification_authority': 'Endur-Cert Engine',
            }
        }
        
        # Write to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(certificate, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def generate_pdf_certificate(self, battery_data: Dict, filename: str = None) -> str:
        """
        Generate a professional PDF certificate for a battery.
        
        Args:
            battery_data: Dictionary with battery assessment results
            filename: Optional custom filename (defaults to battery_id)
            
        Returns:
            Path to generated PDF file
        """
        if filename is None:
            filename = f"{battery_data['Battery_ID']}_certificate.pdf"
        
        output_path = self.output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch,
        )
        
        # Container for PDF objects
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        grade = battery_data['Grade']
        grade_color = self.GRADE_COLORS[grade]
        grade_icon = self.GRADE_ICONS[grade]
        
        # Title
        elements.append(Paragraph("ENDUR-CERT", title_style))
        elements.append(Paragraph("Digital Battery Passport", styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Issue date
        elements.append(Paragraph(
            f"<i>Certificate issued on {datetime.now().strftime('%d %B %Y')}</i>",
            styles['Normal']
        ))
        elements.append(Spacer(1, 0.2*inch))
        
        # Grade badge table
        grade_data = [
            [Paragraph(f"<b>{grade_icon}</b>", styles['Normal'])],
        ]
        grade_table = Table(grade_data, colWidths=[2*inch])
        grade_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), grade_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('PADDING', (0, 0), (-1, -1), 15),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [grade_color]),
        ]))
        elements.append(grade_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Battery Information Section
        elements.append(Paragraph("BATTERY INFORMATION", heading_style))
        
        battery_info = [
            ['Battery ID', battery_data['Battery_ID']],
            ['Predicted RUL (Cycles)', f"{battery_data['Predicted_RUL']:.0f}"],
            ['Average Operating Temperature', f"{battery_data['Avg_Operating_Temp']:.1f}°C"],
        ]
        
        battery_table = Table(battery_info, colWidths=[2*inch, 3*inch])
        battery_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(battery_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Health Assessment Section
        elements.append(Paragraph("HEALTH ASSESSMENT", heading_style))
        
        health_info = [
            ['Health Score (SoH)', f"{battery_data['Health_Score_%']:.1f}%"],
            ['Grade Classification', f"{grade} - {battery_data['Category']}"],
            ['Certified Applications', battery_data['Applications']],
        ]
        
        health_table = Table(health_info, colWidths=[2*inch, 3*inch])
        health_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(health_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Thermal Audit Section
        elements.append(Paragraph("THERMAL AUDIT", heading_style))
        
        thermal_info = [
            ['Temperature Assessment', battery_data['Temperature_Assessment']],
            ['Thermal Penalty Factor', f"{battery_data['Temperature_Penalty_Factor']:.3f}"],
        ]
        
        thermal_table = Table(thermal_info, colWidths=[2*inch, 3*inch])
        thermal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(thermal_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Blue Book Valuation
        elements.append(Paragraph("BLUE BOOK VALUATION", heading_style))
        
        value_style = ParagraphStyle(
            'ValueStyle',
            parent=styles['Normal'],
            fontSize=20,
            textColor=colors.HexColor('#27AE60'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph(
            f"₹ {battery_data['Residual_Value_INR']:,.2f}",
            value_style
        ))
        elements.append(Paragraph(
            "Residual Market Value (Fair Buyback Quote)",
            styles['Normal']
        ))
        elements.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph(
            f"<i>Certified by Endur-Cert Engine | Assessment: {battery_data['Assessment_Date']}</i>",
            footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        
        return str(output_path)
    
    def generate_batch_certificates(self, assessed_df: pd.DataFrame, 
                                   format: str = 'both') -> Dict[str, list]:
        """
        Generate certificates for all batteries in a fleet.
        
        Args:
            assessed_df: DataFrame with assessment results
            format: 'pdf', 'json', or 'both'
            
        Returns:
            Dictionary with lists of generated file paths
        """
        results = {'json': [], 'pdf': []}
        
        for idx, row in assessed_df.iterrows():
            battery_data = row.to_dict()
            
            if format in ['json', 'both']:
                json_path = self.generate_json_certificate(battery_data)
                results['json'].append(json_path)
            
            if format in ['pdf', 'both']:
                pdf_path = self.generate_pdf_certificate(battery_data)
                results['pdf'].append(pdf_path)
        
        return results
