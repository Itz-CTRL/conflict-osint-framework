"""PDF Report Generator Service
Generates professional PDF reports for investigations.

Features:
- Title page with case ID and metadata
- Executive summary
- Findings table
- Risk analysis
- Network statistics
- Recommendations
"""

import logging
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generate professional PDF investigation reports"""
    
    # Colors
    COLOR_CRITICAL = HexColor('#DC2626')
    COLOR_HIGH = HexColor('#EA580C')
    COLOR_MEDIUM = HexColor('#F59E0B')
    COLOR_LOW = HexColor('#10B981')
    COLOR_MINIMAL = HexColor('#6B7280')
    COLOR_HEADER = HexColor('#1F2937')
    COLOR_LIGHT = HexColor('#F3F4F6')
    
    RISK_COLORS = {
        'CRITICAL': COLOR_CRITICAL,
        'HIGH': COLOR_HIGH,
        'MEDIUM': COLOR_MEDIUM,
        'LOW': COLOR_LOW,
        'MINIMAL': COLOR_MINIMAL,
        'UNKNOWN': COLOR_MINIMAL
    }
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.COLOR_HEADER,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.COLOR_HEADER,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14
        ))
    
    def _get_risk_color(self, risk_level):
        """Get color for risk level"""
        return self.RISK_COLORS.get(risk_level, self.COLOR_MINIMAL)
    
    def _build_title_page(self, investigation_data):
        """Build title page content"""
        elements = []
        
        # Title
        elements.append(Spacer(1, 0.5 * inch))
        title = Paragraph("INVESTIGATION REPORT", self.styles['CustomTitle'])
        elements.append(title)
        
        elements.append(Spacer(1, 0.3 * inch))
        
        # Case information
        case_info = [
            ['Case ID:', investigation_data.get('case_id', 'N/A')],
            ['Target:', investigation_data.get('username', 'N/A')],
            ['Date Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')],
            ['Status:', investigation_data.get('status', 'N/A')],
        ]
        
        if investigation_data.get('email'):
            case_info.append(['Email:', investigation_data['email']])
        if investigation_data.get('phone'):
            case_info.append(['Phone:', investigation_data['phone']])
        
        case_table = Table(case_info, colWidths=[2 * inch, 4 * inch])
        case_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 12),
            ('FONT', (1, 0), (1, -1), 'Helvetica', 11),
            ('TEXTCOLOR', (0, 0), (0, -1), self.COLOR_HEADER),
            ('LINEBELOW', (0, 0), (-1, -1), 1, grey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [white, self.COLOR_LIGHT]),
        ]))
        elements.append(case_table)
        
        elements.append(Spacer(1, 0.5 * inch))
        
        # Risk score prominently displayed
        risk_score = investigation_data.get('risk_score', 0)
        risk_level = investigation_data.get('risk_level', 'UNKNOWN')
        risk_color = self._get_risk_color(risk_level)
        
        risk_text = f'Risk Score: {risk_score}/100'
        elements.append(Paragraph(risk_text, self.styles['CustomHeading']))
        
        risk_level_style = ParagraphStyle(
            name='RiskLevel',
            fontSize=16,
            textColor=risk_color,
            fontName='Helvetica-Bold',
            spaceAfter=12
        )
        elements.append(Paragraph(f'Risk Level: {risk_level}', risk_level_style))
        
        elements.append(PageBreak())
        
        return elements
    
    def _build_executive_summary(self, data):
        """Build executive summary"""
        elements = []
        
        elements.append(Paragraph('Executive Summary', self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1 * inch))
        
        analysis = data.get('analysis', {})
        
        summary_text = f"""
        This investigation examined the digital footprint of <b>{data.get('username', 'N/A')}</b> 
        across {data.get('platforms_checked', 0)} social media platforms. 
        The analysis identified <b>{data.get('platforms_found', 0)} active profiles</b> 
        with an overall risk score of <b>{data.get('risk_score', 0)}/100</b>.
        """
        
        elements.append(Paragraph(summary_text, self.styles['CustomNormal']))
        elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _build_findings_table(self, findings):
        """Build findings table"""
        elements = []
        
        elements.append(Paragraph('Findings', self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1 * inch))
        
        if not findings:
            elements.append(Paragraph('No findings recorded.', self.styles['CustomNormal']))
            return elements
        
        # Prepare table data
        table_data = [['Platform', 'Username', 'Found', 'Confidence', 'URL']]
        
        for finding in findings[:20]:  # Limit to 20 findings per page
            platform = finding.get('platform', 'N/A')
            username = finding.get('username', 'N/A')
            found = 'Yes' if finding.get('found') else 'No'
            confidence = f"{finding.get('confidence', 'N/A').upper()}"
            url = finding.get('url', '')[:50] + '...' if len(finding.get('url', '')) > 50 else finding.get('url', '')
            
            table_data.append([platform, username, found, confidence, url])
        
        findings_table = Table(table_data, colWidths=[1.2 * inch, 1.2 * inch, 0.8 * inch, 1 * inch, 0.8 * inch])
        findings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), self.COLOR_LIGHT),
            ('GRID', (0, 0), (-1, -1), 1, grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(findings_table)
        elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _build_analysis_section(self, analysis):
        """Build analysis section"""
        elements = []
        
        elements.append(Paragraph('Risk Analysis', self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Risk factors
        if analysis.get('behavior_flags'):
            elements.append(Paragraph('<b>Behavior Flags:</b>', self.styles['CustomNormal']))
            for flag in analysis.get('behavior_flags', [])[:10]:
                elements.append(Paragraph(f'• {flag}', self.styles['CustomNormal']))
            elements.append(Spacer(1, 0.1 * inch))
        
        # Keyword hits
        if analysis.get('keyword_hits'):
            elements.append(Paragraph('<b>Keyword Hits:</b>', self.styles['CustomNormal']))
            for hit in analysis.get('keyword_hits', [])[:10]:
                keyword = hit.get('keyword', 'N/A') if isinstance(hit, dict) else hit
                elements.append(Paragraph(f'• {keyword}', self.styles['CustomNormal']))
            elements.append(Spacer(1, 0.1 * inch))
        
        # Platform presence
        presence = analysis.get('platform_presence', {})
        if presence.get('found_on'):
            elements.append(Paragraph(
                f"<b>Active Profiles:</b> Found on {len(presence.get('found_on', []))} platforms",
                self.styles['CustomNormal']
            ))
            for platform in presence.get('found_on', []):
                elements.append(Paragraph(f'• {platform}', self.styles['CustomNormal']))
            elements.append(Spacer(1, 0.1 * inch))
        
        return elements
    
    def _build_recommendations(self, analysis):
        """Build recommendations section"""
        elements = []
        
        elements.append(Paragraph('Recommendations', self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1 * inch))
        
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            for rec in recommendations[:10]:
                elements.append(Paragraph(f'• {rec}', self.styles['CustomNormal']))
        else:
            elements.append(Paragraph('No specific recommendations at this time.', self.styles['CustomNormal']))
        
        elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def generate(self, investigation_data, findings, analysis):
        """
        Generate PDF report
        
        Args:
            investigation_data: Dict with case_id, username, email, phone, status, risk_score, risk_level
            findings: List of finding dicts
            analysis: Analysis dict with flags, keyword_hits, platform_presence, recommendations
            
        Returns:
            BytesIO object containing PDF
        """
        try:
            pdf_buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=letter,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.75 * inch,
                title=f"Investigation Report - {investigation_data.get('case_id', 'Unknown')}"
            )
            
            elements = []
            
            # Title page
            elements.extend(self._build_title_page(investigation_data))
            
            # Executive summary
            elements.extend(self._build_executive_summary(investigation_data))
            
            # Findings
            if findings:
                elements.extend(self._build_findings_table(findings))
            
            # Analysis
            if analysis:
                elements.extend(self._build_analysis_section(analysis))
                elements.extend(self._build_recommendations(analysis))
            
            # Footer with timestamp
            elements.append(Spacer(1, 0.3 * inch))
            footer_text = f"Report generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            elements.append(Paragraph(footer_text, self.styles['Normal']))
            
            # Build PDF
            doc.build(elements)
            pdf_buffer.seek(0)
            
            logger.info(f"PDF report generated successfully for {investigation_data.get('case_id')}")
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise
