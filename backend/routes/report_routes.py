"""Report Routes
Handles PDF/Text/JSON report generation and retrieval.
Uses BehaviorAnalyzer for risk scoring and NetworkGraphBuilder for graph data.
"""

from flask import Blueprint, request, jsonify
import logging
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from models import Investigation, Report, Entity, Finding, NetworkEdge
from utils import APIResponse, generate_report_id
from services.analyzer import BehaviorAnalyzer
from services.network_builder import NetworkGraphBuilder
import json

logger = logging.getLogger(__name__)

report_bp = Blueprint('report', __name__, url_prefix='/api/report')

# Initialize services
analyzer = BehaviorAnalyzer()
graph_builder = NetworkGraphBuilder()


@report_bp.route('/<case_id>/generate', methods=['POST'])
def generate_report(case_id):
    """
    Generate PDF report for an investigation
    
    Request body:
    {
        "include_graph": true,
        "include_evidence": true,
        "include_timeline": true
    }
    """
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        if investigation.status != 'completed':
            return jsonify(APIResponse.error(case_id, "Investigation must be completed first")), 400
        
        include_graph = request.json.get('include_graph', True) if request.json else True
        include_evidence = request.json.get('include_evidence', True) if request.json else True
        include_timeline = request.json.get('include_timeline', True) if request.json else True
        
        # Generate PDF content
        pdf_content = _generate_pdf_content(
            investigation,
            include_graph=include_graph,
            include_evidence=include_evidence,
            include_timeline=include_timeline
        )
        
        # Save report to database
        report_id = generate_report_id()
        report = Report(
            id=report_id,
            investigation_id=case_id,
            report_type='pdf',
            title=f"OSINT Investigation Report - {investigation.primary_entity}",
            summary=f"Investigation case {case_id} for {investigation.primary_entity}",
            chain_of_custody=json.dumps(_generate_chain_of_custody(investigation))
        )
        
        db.session.add(report)
        db.session.commit()
        
        logger.info(f"Generated PDF report {report_id} for case {case_id}")
        
        return jsonify({
            'status': 'success',
            'case_id': case_id,
            'report_id': report_id,
            'report_type': 'pdf',
            'title': report.title,
            'created_at': datetime.utcnow().isoformat()
        }), 201
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Report generation error: {str(e)}")), 500


@report_bp.route('/<case_id>/text', methods=['GET'])
def get_text_report(case_id):
    """
    Get report as formatted text
    
    Returns structured text report with all findings
    """
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        # Build text report
        text_report = _build_text_report(investigation)
        
        return jsonify({
            'status': 'success',
            'case_id': case_id,
            'report': text_report
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting text report: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Server error: {str(e)}")), 500


@report_bp.route('/<case_id>/json', methods=['GET'])
def get_json_report(case_id):
    """
    Get complete investigation as JSON
    
    Returns all data in structured JSON format
    """
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        # Get all related data
        entities = Entity.query.filter_by(investigation_id=case_id).all()
        edges = NetworkEdge.query.filter_by(investigation_id=case_id).all()
        findings = Finding.query.filter_by(investigation_id=case_id).all()
        
        # Build graph
        findings_data = [
            json.loads(f.data) if isinstance(f.data, str) else f.data 
            for f in findings
        ]
        graph = graph_builder.build_from_investigation(
            {'username': investigation.primary_entity, 'id': case_id},
            findings_data
        )
        
        json_report = {
            'investigation': {
                'id': investigation.id,
                'username': investigation.primary_entity,
                'email': investigation.email,
                'phone': investigation.phone,
                'status': investigation.status,
                'risk_score': investigation.risk_score,
                'risk_level': investigation.risk_level,
                'created_at': investigation.created_at.isoformat(),
                'completed_at': investigation.completed_at.isoformat() if investigation.completed_at else None
            },
            'entities': [e.to_dict() for e in entities],
            'edges': [e.to_dict() for e in edges],
            'findings': [f.to_dict() for f in findings],
            'graph': graph,
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'entity_count': len(entities),
                'edge_count': len(edges),
                'finding_count': len(findings),
            }
        }
        
        return jsonify({
            'status': 'success',
            'case_id': case_id,
            'report': json_report
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting JSON report: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Server error: {str(e)}")), 500


@report_bp.route('/<case_id>/list', methods=['GET'])
def list_reports(case_id):
    """
    List all reports for an investigation
    """
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        paginated = Report.query.filter_by(investigation_id=case_id).order_by(
            Report.created_at.desc()
        ).paginate(page=page, per_page=limit, error_out=False)
        
        reports_data = [
            {
                'id': r.id,
                'report_type': r.report_type,
                'title': r.title,
                'created_at': r.created_at.isoformat()
            } for r in paginated.items
        ]
        
        return jsonify({
            'status': 'success',
            'case_id': case_id,
            'reports': reports_data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': paginated.total,
                'pages': paginated.pages
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Server error: {str(e)}")), 500


def _generate_pdf_content(investigation, include_graph=True, include_evidence=True, include_timeline=True):
    """
    Generate PDF content
    
    This is a placeholder. In production, use reportlab or similar
    """
    try:
        # Try importing reportlab
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from io import BytesIO
        
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, f"OSINT Investigation Report")
        
        # Case information
        c.setFont("Helvetica", 10)
        c.drawString(50, 720, f"Case ID: {investigation.id}")
        c.drawString(50, 700, f"Target: {investigation.primary_entity}")
        c.drawString(50, 680, f"Risk Score: {investigation.risk_score} ({investigation.risk_level})")
        
        # Draw some content
        y = 640
        if include_evidence:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Findings")
            y -= 20
            
            findings = Finding.query.filter_by(investigation_id=investigation.id).limit(10).all()
            c.setFont("Helvetica", 9)
            for finding in findings:
                if y < 50:
                    c.showPage()
                    y = 750
                c.drawString(50, y, f"- {finding.platform or 'N/A'}: Found={finding.found}")
                y -= 15
        
        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    except ImportError:
        logger.warning("reportlab not installed, using text placeholder")
        return _build_text_report(investigation).encode('utf-8')


def _build_text_report(investigation):
    """Build text report"""
    report = []
    report.append("=" * 80)
    report.append("OSINT INVESTIGATION REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Case Overview
    report.append("CASE OVERVIEW")
    report.append("-" * 40)
    report.append(f"Case ID: {investigation.id}")
    report.append(f"Target Username: {investigation.primary_entity}")
    report.append(f"Email: {investigation.email or 'N/A'}")
    report.append(f"Phone: {investigation.phone or 'N/A'}")
    report.append(f"Status: {investigation.status}")
    report.append(f"Risk Score: {investigation.risk_score}")
    report.append(f"Risk Level: {investigation.risk_level}")
    report.append(f"Created: {investigation.created_at}")
    report.append(f"Completed: {investigation.completed_at}")
    report.append("")
    
    # Entities Found
    entities = Entity.query.filter_by(investigation_id=investigation.id).all()
    if entities:
        report.append("ENTITIES FOUND")
        report.append("-" * 40)
        for entity in entities:
            report.append(f"Type: {entity.entity_type}")
            report.append(f"  Value: {entity.entity_value}")
            report.append(f"  Platform: {entity.platform or 'N/A'}")
            report.append("")
    
    # Findings
    findings = Finding.query.filter_by(investigation_id=investigation.id).all()
    if findings:
        report.append("FINDINGS")
        report.append("-" * 40)
        for finding in findings:
            try:
                finding_username = None
                if finding.data and isinstance(finding.data, dict):
                    finding_username = finding.data.get('username') or finding.data.get('user')
            except Exception:
                finding_username = None

            report.append(f"Platform: {finding.platform or 'N/A'}")
            report.append(f"  Username: {finding_username or 'N/A'}")
            report.append(f"  Found: {finding.found}")
            report.append("")
    
    report.append("=" * 80)
    return "\n".join(report)


def _generate_chain_of_custody(investigation):
    """Generate chain of custody log"""
    log = []
    
    log.append({
        'timestamp': investigation.created_at.isoformat(),
        'action': 'Case Created',
        'entity': investigation.primary_entity,
        'details': f'Investigation case created'
    })
    
    if investigation.started_at:
        log.append({
            'timestamp': investigation.started_at.isoformat(),
            'action': 'Scan Started',
            'entity': investigation.primary_entity,
            'details': 'Investigation scan initiated'
        })
    
    if investigation.completed_at:
        log.append({
            'timestamp': investigation.completed_at.isoformat(),
            'action': 'Scan Completed',
            'entity': investigation.primary_entity,
            'details': f'Investigation completed with risk score {investigation.risk_score}'
        })
    
    # Add entity discovery logs
    entities = Entity.query.filter_by(investigation_id=investigation.id).all()
    for entity in entities:
        log.append({
            'timestamp': entity.created_at.isoformat() if hasattr(entity, 'created_at') else datetime.utcnow().isoformat(),
            'action': 'Entity Discovered',
            'entity': entity.entity_value,
            'details': f'{entity.entity_type}: {entity.entity_value}'
        })
    
    return log
