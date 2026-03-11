"""Investigation Routes
Handles investigation case creation, light/deep scan control, status retrieval.
Uses analyzer.py for risk scoring, scraper.py for platform validation, 
network_builder.py for graph construction.
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from models import Investigation, Finding, Entity
from services.analyzer import BehaviorAnalyzer
from services.scraper import OSINTScraper
from services.network_builder import NetworkGraphBuilder
from services.suggestion_engine import SuggestionEngine
from services.filter_service import InvestigationFilter
from utils import APIResponse, Validator, generate_case_id, log_activity
from workers.task_manager import get_task_manager
import uuid
import json

logger = logging.getLogger(__name__)

investigation_bp = Blueprint('investigation', __name__, url_prefix='/api/investigation')

# Initialize services
scraper = OSINTScraper()
analyzer = BehaviorAnalyzer()
graph_builder = NetworkGraphBuilder()
suggestion_engine = SuggestionEngine()


@investigation_bp.route('/username_suggestions', methods=['GET'])
def get_username_suggestions():
    """
    Get username suggestions using fuzzy matching on investigation history.
    
    Query Parameters:
        query (str): Partial or full username to match (min 2 chars)
        limit (int): Maximum suggestions to return (default: 10)
    
    Returns:
        List of suggested usernames with confidence scores and metadata
        
    Example:
        GET /api/investigation/username_suggestions?query=john&limit=10
        Response:
        {
            "status": "success",
            "data": [
                {
                    "username": "johndoe",
                    "confidence": 0.95,
                    "investigation_count": 2,
                    "similarity": 0.92
                },
                ...
            ]
        }
    """
    try:
        query = request.args.get('query', '').strip()
        limit = request.args.get('limit', 10, type=int)
        
        # Validate inputs
        if limit < 1 or limit > 50:
            limit = 10
        
        # Get suggestions
        suggestions = suggestion_engine.get_username_suggestions(query, limit=limit)
        
        response = APIResponse.success(
            None,
            data={
                'query': query,
                'suggestions': suggestions,
                'count': len(suggestions)
            }
        )
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error getting username suggestions: {str(e)}")
        return jsonify(APIResponse.error(None, f"Server error: {str(e)}")), 500


@investigation_bp.route('/username_variations', methods=['GET'])
def get_username_variations():
    """
    Get common username variations for expanded search.
    
    Query Parameters:
        username (str): Base username to generate variations for
    
    Returns:
        List of common variations (underscores, dots, numbers, etc.)
        
    Example:
        GET /api/investigation/username_variations?username=johndoe
        Response:
        {
            "status": "success",
            "data": {
                "base": "johndoe",
                "variations": ["johndoe", "john.doe", "john_doe", "johndoe123", ...]
            }
        }
    """
    try:
        username = request.args.get('username', '').strip()
        
        if not username or len(username) < 2:
            return jsonify(APIResponse.error(None, "Username required (min 2 chars)")), 400
        
        variations = suggestion_engine.get_common_variations(username)
        
        response = APIResponse.success(
            None,
            data={
                'base': username,
                'variations': variations,
                'count': len(variations)
            }
        )
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error generating variations: {str(e)}")
        return jsonify(APIResponse.error(None, f"Server error: {str(e)}")), 500


@investigation_bp.route('/create', methods=['POST'])
def create_investigation():
    """
    Create a new investigation case with optional filters and country.
    Validates all inputs and provides detailed error messages.
    
    Request body:
    {
        "username": "target_username",           # Required
        "email": "optional@email.com",           # Optional: auto-discover if not provided
        "phone": "+1234567890",                  # Optional: auto-discover if not provided
        "country": "Ghana",                      # Optional: country name or code for soft filtering
        "filters": {                             # Optional: if empty, full search performed
            "platform": ["Twitter", "Instagram"],           # Filter by platform(s)
            "location": ["United States", "Canada"],        # Filter by location(s)
            "country": "Ghana",                             # Optional soft filter by country
            "account_type": ["personal", "business"],       # Filter by account type(s)
            "verified_only": false,                         # Include only verified accounts
            "minimize_bots": false                          # Exclude probable bots
        }
    }
    
    Returns:
        Investigation case with ID, status, and filter description
    """
    try:
        data = request.get_json()
        print(f"\n[INVESTIGATION CREATE DEBUG] REQUEST DATA: {data}")
        print(f"[INVESTIGATION CREATE DEBUG] REQUEST HEADERS: {dict(request.headers)}")
        logger.info(f"[INVESTIGATION CREATE DEBUG] REQUEST DATA: {data}")
        
        if not data:
            print("[INVESTIGATION CREATE DEBUG] No JSON body provided")
            return jsonify(APIResponse.error(None, "Request body is required (JSON)")), 400
        
        # Validate required fields
        username = data.get('username', '').strip() if data.get('username') else None
        print(f"[INVESTIGATION CREATE DEBUG] Parsed username={username}, email={data.get('email')}, phone={data.get('phone')}, filters={data.get('filters')}")
        if not username:
            return jsonify(APIResponse.error(None, "Username is required")), 400
        
        # CRITICAL FIX: Normalize username - remove spaces, convert to valid username
        # "elon musk" -> "elonmusk", handles multi-word input by removing spaces
        username = username.replace(' ', '').lower()
        print(f"[INVESTIGATION CREATE DEBUG] Normalized username={username}")
        is_valid, error = Validator.validate_username(username)
        if not is_valid:
            logger.warning(f"Invalid username: {username} - {error}")
            return jsonify(APIResponse.error(None, error)), 400
        
        # Optional fields with validation
        email = None
        phone = None
        country = None
        
        if data.get('email'):
            email = data.get('email', '').strip()
            is_valid, error = Validator.validate_email(email)
            if not is_valid:
                logger.warning(f"Invalid email: {email} - {error}")
                return jsonify(APIResponse.error(None, error)), 400
        
        if data.get('phone'):
            phone = data.get('phone', '').strip()
            is_valid, error, parsed = Validator.validate_phone(phone)
            if not is_valid:
                logger.warning(f"Invalid phone: {phone} - {error}")
                return jsonify(APIResponse.error(None, error)), 400
        
        if data.get('country'):
            country = data.get('country', '').strip()
            # Validate country exists
            country_info = Validator.normalize_country(country)
            if not country_info:
                logger.warning(f"Unknown country: {country}")
                # Don't fail - proceed with country as-is for flexible filtering
        
        logger.info(f"Creating investigation for username: {username}, email: {email}, phone: {phone}, country: {country}")
        
        # Parse filters (optional)
        filters = InvestigationFilter()
        if data.get('filters') and isinstance(data['filters'], dict):
            filter_data = data['filters'].copy()
            # If country provided separately, add to filters
            if country and 'country' not in filter_data:
                filter_data['country'] = country
            try:
                filters = InvestigationFilter.from_dict(filter_data)
            except Exception as e:
                logger.warning(f"Error parsing filters: {str(e)}")
                # Continue with empty filters rather than failing
                filters = InvestigationFilter()
        elif country:
            # If country provided without explicit filters, create filter with just country
            try:
                filters = InvestigationFilter.from_dict({'country': country})
            except Exception as e:
                logger.warning(f"Error creating country filter: {str(e)}")
        
        # Determine scan depth (allow override)
        scan_depth = data.get('scan_depth', 'light') if isinstance(data.get('scan_depth', None), str) else 'light'
        is_valid_depth, depth_error = Validator.validate_scan_depth(scan_depth)
        if not is_valid_depth:
            scan_depth = 'light'

        # Create investigation case
        case_id = generate_case_id()
        investigation = Investigation(
            id=case_id,
            case_type='username',
            primary_entity=username,
            scan_depth=scan_depth,
            status='pending',
            created_at=datetime.utcnow(),
            risk_score=0,
            filters=filters.to_dict() if not filters.is_empty() else {}
        )
        
        # Note: email and phone are stored as Entity objects during scanning, not directly on Investigation
        # They will be discovered and added to entities during the scan process
        
        try:
            db.session.add(investigation)
            db.session.commit()
            
            logger.info(f"Created investigation case {case_id} for username {username}")
            if not filters.is_empty():
                logger.info(f"Filters: {filters.get_description()}")

            # Submit background task via Celery
            try:
                from celery_config import celery_app, run_investigation_scan
                task = run_investigation_scan.apply_async(
                    args=[case_id, username, scan_depth],
                    kwargs={'filters': filters.to_dict() if not filters.is_empty() else {}},
                    task_id=f"inv-{case_id}"
                )
                logger.info(f"Submitted Celery task {task.id} for case {case_id} (scan_depth={scan_depth})")
            except Exception as e:
                logger.warning(f"Failed to submit Celery task for case {case_id}: {e}")
                # Fallback to direct execution if Celery not available
                try:
                    tm = get_task_manager()
                    tm.submit_investigation(case_id, username, scan_depth=scan_depth, 
                                          filters=filters.to_dict() if not filters.is_empty() else {})
                    logger.info(f"Fallback: Submitted task via TaskManager for case {case_id}")
                except Exception as tm_error:
                    logger.warning(f"Fallback also failed: {tm_error}")
        
        except Exception as e:
            logger.error(f"Error saving investigation: {str(e)}")
            db.session.rollback()
            return jsonify(APIResponse.error(
                None,
                f"Error creating investigation: {str(e)}"
            )), 500
        
        response = APIResponse.pending(
            case_id,
            f"Investigation case created for '{username}'. Ready to scan."
        )
        response['data'] = {
            'case_id': case_id,
            'primary_entity': username,
            'case_type': 'username',
            'email': email,
            'phone': phone,
            'country': country,
            'filters_applied': not filters.is_empty(),
            'filter_description': filters.get_description()
        }
        
        return jsonify(response), 201
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify(APIResponse.error(None, f"Validation error: {str(e)}")), 400
    
    except Exception as e:
        logger.error(f"Unexpected error creating investigation: {str(e)}", exc_info=True)
        return jsonify(APIResponse.error(None, f"Server error: {str(e)}")), 500


@investigation_bp.route('/scan/<case_id>/<scan_type>', methods=['POST'])
def start_scan(case_id, scan_type):
    """
    Start investigation scan (light or deep).
    ALWAYS returns valid JSON response. Never returns 500.
    Returns partial results even if somefail.
    
    Args:
        case_id: Investigation ID
        scan_type: 'light' or 'deep'
    
    Response (always this structure):
    {
        "status": "completed",
        "target": "username",
        "findings": [],
        "threat_level": 0,
        "network_nodes": [],
        "network_edges": []
    }
    """
    try:
        print(f"\n[SCAN DEBUG] Received scan request: case_id={case_id}, scan_type={scan_type}")
        logger.info(f"[SCAN DEBUG] Received scan request: case_id={case_id}, scan_type={scan_type}")
        
        # Validate scan type
        if scan_type not in ['light', 'deep']:
            print(f"[SCAN DEBUG] Invalid scan type: {scan_type}")
            logger.warning(f"[SCAN] Invalid scan type: {scan_type}")
            return jsonify({
                'status': 'error',
                'case_id': case_id,
                'error': 'Invalid scan type. Must be light or deep',
                'task_id': None
            }), 400
        
        # Get investigation case
        investigation = None
        try:
            investigation = Investigation.query.get(case_id)
        except Exception as e:
            logger.error(f"[SCAN] DB error getting investigation: {str(e)}")
        
        if not investigation:
            print(f"[SCAN DEBUG] Investigation case not found: {case_id}")
            logger.warning(f"[SCAN] Investigation case not found: {case_id}")
            return jsonify({
                'status': 'error',
                'case_id': case_id,
                'error': 'Investigation case not found',
                'task_id': None
            }), 404
        
        username = investigation.primary_entity
        print(f"[SCAN DEBUG] Investigation found: case={case_id}, username={username}, status={investigation.status}")
        logger.info(f"[SCAN] Starting {scan_type} scan: case={case_id}, username={username}")
        
        if investigation.status not in ['pending', 'running']:
            logger.warning(f"[SCAN] Investigation not ready: status={investigation.status}")
            return jsonify({
                'status': 'error',
                'case_id': case_id,
                'error': f'Investigation status is {investigation.status}. Cannot start scan.',
                'task_id': None
            }), 409
        
        # Update status to running
        try:
            investigation.status = 'running'
            investigation.started_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            logger.error(f"[SCAN] Error updating status: {str(e)}")
            db.session.rollback()
        
        # Submit Celery task
        try:
            from celery_config import celery_app, run_investigation_scan
            task = run_investigation_scan.apply_async(
                args=[case_id, username, scan_type],
                task_id=f"scan-{case_id}-{scan_type}"
            )
            logger.info(f"Submitted Celery task {task.id} for {scan_type} scan on case {case_id}")
            
            return jsonify({
                'status': 'queued',
                'case_id': case_id,
                'scan_type': scan_type,
                'target': username,
                'task_id': task.id,
                'message': f'{scan_type.upper()} scan queued for execution'
            }), 202
        
        except Exception as e:
            logger.warning(f"Failed to submit Celery task for case {case_id}: {e}")
            # Fallback to synchronous execution if Celery not available
            logger.info(f"Fallback: Executing {scan_type} scan synchronously")
            
            result = None
            try:
                if scan_type == 'light':
                    result = _light_scan(investigation)
                else:
                    result = _deep_scan(investigation)
                logger.info(f"[SCAN] Sync scan completed successfully")
            except Exception as sync_error:
                logger.error(f"[SCAN] Sync scan failed: {str(sync_error)}", exc_info=True)
                result = _build_safe_result(username, investigation.id, str(sync_error))
            
            return _format_scan_response(case_id, username, result)
    
    except Exception as e:
        print(f"[SCAN] CRITICAL ERROR at top level: {str(e)}")
        logger.error(f"[SCAN] Unexpected top-level error: {str(e)}", exc_info=True)
        # Return absolute fallback response
        return jsonify({
            'status': 'completed',
            'case_id': case_id,
            'target': 'unknown',
            'findings': [],
            'threat_level': 0,
            'network_nodes': [],
            'network_edges': [],
            'error_note': 'Critical error in scan handler'
        }), 200


@investigation_bp.route('/status/<case_id>', methods=['GET'])
def get_status(case_id):
    """Get investigation status with enhanced progress tracking"""
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation case not found")), 404
        
        # Get findings count
        findings_count = Finding.query.filter_by(investigation_id=case_id).count()
        entities_count = Entity.query.filter_by(investigation_id=case_id).count()
        
        # Calculate time metrics
        time_elapsed = None
        time_remaining = None
        progress_percent = 0
        
        if investigation.started_at:
            time_elapsed = int((datetime.utcnow() - investigation.started_at).total_seconds())
            
            # Estimate remaining time based on status
            if investigation.status == 'running':
                # Light scan: ~10 seconds, Deep scan: ~180 seconds
                total_estimate = 10 if investigation.scan_depth == 'light' else 180
                time_remaining = max(0, total_estimate - time_elapsed)
                progress_percent = min(95, int((time_elapsed / total_estimate) * 100))
            elif investigation.status == 'completed':
                progress_percent = 100
                time_remaining = 0
        
        if investigation.completed_at and investigation.started_at:
            total_duration = int((investigation.completed_at - investigation.started_at).total_seconds())
        else:
            total_duration = None
        
        response = APIResponse.success(
            case_id,
            data={
                'username': investigation.primary_entity,
                'status': investigation.status,
                'risk_score': investigation.risk_score,
                'findings_count': findings_count,
                'entities_count': entities_count,
                'progress_percent': progress_percent,
                'time_elapsed_seconds': time_elapsed,
                'time_remaining_seconds': time_remaining,
                'total_duration_seconds': total_duration,
                'current_task': f"Scanning {investigation.primary_entity}...",
                'created_at': investigation.created_at.isoformat(),
                'started_at': investigation.started_at.isoformat() if investigation.started_at else None,
                'completed_at': investigation.completed_at.isoformat() if investigation.completed_at else None,
                'export_available': investigation.status == 'completed'
            },
            risk_score=investigation.risk_score,
            status=investigation.status
        )
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Server error: {str(e)}")), 500


@investigation_bp.route('/export/<case_id>/pdf', methods=['GET'])
def export_pdf(case_id):
    """Export investigation as PDF report"""
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        if investigation.status != 'completed':
            return jsonify(APIResponse.error(case_id, "Investigation not completed yet")), 400
        
        # Get findings
        findings = Finding.query.filter_by(investigation_id=case_id).all()
        findings_data = [json.loads(f.data) if isinstance(f.data, str) else f.data for f in findings]
        
        # Get entities
        entities = Entity.query.filter_by(investigation_id=case_id).all()
        
        # Prepare investigation data
        investigation_data = {
            'case_id': case_id,
            'username': investigation.primary_entity,
            'email': getattr(investigation, 'email', None),
            'phone': getattr(investigation, 'phone', None),
            'status': investigation.status,
            'risk_score': investigation.risk_score,
            'risk_level': 'CRITICAL' if investigation.risk_score >= 75 else ('HIGH' if investigation.risk_score >= 50 else ('MEDIUM' if investigation.risk_score >= 25 else 'LOW')),
            'platforms_checked': 20,
            'platforms_found': len(findings_data),
            'created_at': investigation.created_at.isoformat(),
            'completed_at': investigation.completed_at.isoformat() if investigation.completed_at else None
        }
        
        # Prepare analysis data
        analysis = {
            'risk_score': investigation.risk_score,
            'behavior_flags': [],
            'keyword_hits': [],
            'platform_presence': {'found_on': [f.get('platform', 'Unknown') for f in findings_data]},
            'recommendations': [
                'Continue monitoring account activity',
                'Cross-reference with known threat databases',
                'Archive profile content for evidence'
            ]
        }
        
        # Generate PDF
        from services.pdf_generator import PDFReportGenerator
        generator = PDFReportGenerator()
        pdf_buffer = generator.generate(investigation_data, findings_data, analysis)
        
        # Send file
        from flask import send_file
        filename = f"investigation_{case_id}.pdf"
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting PDF: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"PDF generation failed: {str(e)}")), 500


@investigation_bp.route('/export/<case_id>/csv', methods=['GET'])
def export_csv(case_id):
    """Export investigation findings as CSV"""
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        if investigation.status != 'completed':
            return jsonify(APIResponse.error(case_id, "Investigation not completed yet")), 400
        
        # Get findings
        findings = Finding.query.filter_by(investigation_id=case_id).all()
        findings_data = []
        
        for f in findings:
            data = json.loads(f.data) if isinstance(f.data, str) else f.data
            findings_data.append({
                'platform': data.get('platform', ''),
                'username': data.get('username', ''),
                'found': data.get('found', False),
                'confidence': data.get('confidence', 'unknown'),
                'verified_in_content': data.get('verified_in_content', False),
                'status_code': data.get('status_code', 0),
                'url': data.get('url', ''),
                'may_be_rate_limited': data.get('may_be_rate_limited', False)
            })
        
        # Generate CSV
        from services.csv_exporter import CSVExporter
        csv_data = CSVExporter.export_findings(case_id, findings_data)
        
        # Send file
        from flask import send_file
        from io import BytesIO
        csv_buffer = BytesIO(csv_data.encode('utf-8'))
        filename = f"investigation_{case_id}.csv"
        
        return send_file(
            csv_buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"CSV export failed: {str(e)}")), 500


@investigation_bp.route('/result/<case_id>', methods=['GET'])
def get_result(case_id):
    """Get complete investigation result"""
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation case not found")), 404
        
        if investigation.status != 'completed':
            return jsonify(APIResponse.error(case_id, "Investigation still running or failed")), 400
        
        # Get all findings
        findings = Finding.query.filter_by(investigation_id=case_id).all()
        findings_data = [f.to_dict() for f in findings]
        
        # Build graph from findings
        graph_data = graph_builder.build_from_investigation(
            {'username': investigation.primary_entity, 'id': case_id},
            [json.loads(f.data) if isinstance(f.data, str) else f.data for f in findings]
        )
        
        response = APIResponse.success(
            case_id,
            data={
                'username': investigation.primary_entity,
                'status': investigation.status,
                'findings': findings_data
            },
            graph=graph_data,
            risk_score=investigation.risk_score,
            status='completed'
        )
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error getting result: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Server error: {str(e)}")), 500


@investigation_bp.route('/list', methods=['GET'])
def list_investigations():
    """List all investigations (paginated)"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        status_filter = request.args.get('status')
        
        query = Investigation.query
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        paginated = query.order_by(Investigation.created_at.desc()).paginate(
            page=page, per_page=limit, error_out=False
        )
        
        investigations = []
        for inv in paginated.items:
            try:
                # Use model's primary_entity and compute risk level from analyzer
                risk_level = analyzer.get_risk_category(inv.risk_score) if hasattr(analyzer, 'get_risk_category') else 'UNKNOWN'
            except Exception:
                risk_level = 'UNKNOWN'

            investigations.append({
                'id': inv.id,
                'username': getattr(inv, 'primary_entity', None),
                'status': inv.status,
                'risk_score': inv.risk_score,
                'risk_level': risk_level,
                'created_at': inv.created_at.isoformat() if inv.created_at else None
            })
        
        return jsonify({
            'status': 'success',
            'data': investigations,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': paginated.total,
                'pages': paginated.pages
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing investigations: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@investigation_bp.route('/delete/<case_id>', methods=['DELETE'])
def delete_investigation(case_id):
    """Delete an investigation and all related data"""
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation case not found")), 404
        
        # Delete all findings
        Finding.query.filter_by(investigation_id=case_id).delete()
        # Delete investigation
        db.session.delete(investigation)
        db.session.commit()
        
        logger.info(f"Deleted investigation case {case_id}")
        
        return jsonify({'status': 'success', 'message': 'Investigation deleted'}), 200
    
    except Exception as e:
        logger.error(f"Error deleting investigation: {str(e)}")
        db.session.rollback()
        return jsonify(APIResponse.error(case_id, f"Deletion error: {str(e)}")), 500


# ==================== Private Helper Functions ====================

def _light_scan(investigation):
    """
    Light scan: Quick username validation across platforms using Sherlock.
    Uses scraper.py for platform checking.
    Returns partial results even if some platforms fail.
    
    Returns: {data, graph, risk_score}
    """
    try:
        username = investigation.primary_entity
        print(f"\n[SCAN] ========== LIGHT SCAN STARTED ==========")
        print(f"[SCAN] Username: {username}")
        print(f"[SCAN] Investigation ID: {investigation.id}")
        logger.info(f"[SCAN] ========== LIGHT SCAN STARTED ==========")
        logger.info(f"[SCAN] Username: {username}")
        
        # Platform list for Sherlock validation
        print(f"[SCAN] Initializing Sherlock platform list...")
        platforms = [
            ('Facebook', f'https://www.facebook.com/{username}'),
            ('Instagram', f'https://www.instagram.com/{username}'),
            ('Twitter', f'https://twitter.com/{username}'),
            ('TikTok', f'https://www.tiktok.com/@{username}'),
            ('YouTube', f'https://www.youtube.com/@{username}'),
            ('GitHub', f'https://github.com/{username}'),
            ('Reddit', f'https://reddit.com/u/{username}'),
            ('LinkedIn', f'https://www.linkedin.com/in/{username}'),
        ]
        print(f"[SCAN] Platform count: {len(platforms)}")
        logger.info(f"[SCAN] Platform count: {len(platforms)}")
        
        # Check platforms with error handling for individual failures
        platform_results = {
            'platforms': [],
            'total_checked': len(platforms),
            'found_count': 0,
            'failed_count': 0,
            'errors': []
        }
        
        print(f"[SCAN] Starting Sherlock platform check...")
        for platform_name, url in platforms:
            try:
                print(f"[SCAN] Checking {platform_name}...")
                logger.debug(f"[SCAN] Checking {platform_name} for {username}")
                result = scraper.check_platform(platform_name, url, username)
                
                if not result:
                    print(f"[SCAN] No result from {platform_name}")
                    logger.warning(f"[SCAN] No result from {platform_name}")
                    platform_results['failed_count'] += 1
                    platform_results['errors'].append({
                        'platform': platform_name,
                        'error': 'No result returned'
                    })
                    continue
                
                platform_results['platforms'].append(result)
                
                if result.get('found'):
                    platform_results['found_count'] += 1
                    print(f"[SCAN] ✓ FOUND on {platform_name} - Result: {result}")
                    logger.info(f"[SCAN] ✓ FOUND {username} on {platform_name} (result={result})")
                    
                    try:
                        # Save finding to DB
                        print(f"[SCAN] Saving finding for {platform_name}...")
                        
                        # FIX: Convert confidence string to float (0-1 scale)
                        # scraper returns: 'high', 'medium', 'unknown', 'none'
                        confidence_str = result.get('confidence', 'none')
                        confidence_map = {
                            'high': 0.95,
                            'medium': 0.7,
                            'unknown': 0.5,
                            'none': 0.0
                        }
                        confidence_float = confidence_map.get(confidence_str, 0.0)
                        
                        finding = Finding(
                            id=str(uuid.uuid4()),
                            investigation_id=investigation.id,
                            finding_type='platform',
                            platform=platform_name,
                            found=bool(result.get('found')),
                            source=url,
                            confidence=confidence_float,  # Now a float!
                            data=result if isinstance(result, dict) else json.loads(result) if isinstance(result, str) else {}
                        )
                        db.session.add(finding)
                        db.session.flush()  # Flush but don't commit yet
                        print(f"[SCAN] Finding saved for {platform_name}")
                    except Exception as e:
                        print(f"[SCAN] ERROR saving finding for {platform_name}: {str(e)}")
                        logger.error(f"[SCAN] Error saving finding for {platform_name}: {str(e)}")
                        db.session.rollback()
                        # Continue with other platforms
                else:
                    print(f"[SCAN] ✗ Not found on {platform_name}")
                    logger.debug(f"[SCAN] Not found on {platform_name}")
                
                # Check for errors in the result
                if result.get('error'):
                    platform_results['errors'].append({
                        'platform': platform_name,
                        'error': result['error']
                    })
            
            except Exception as e:
                print(f"[SCAN] ERROR checking {platform_name}: {str(e)}")
                logger.error(f"[SCAN] Error checking {platform_name}: {str(e)}")
                platform_results['failed_count'] += 1
                platform_results['errors'].append({
                    'platform': platform_name,
                    'error': str(e)
                })
        
        print(f"[SCAN] Platform check complete. Found: {platform_results['found_count']}/{len(platforms)}")
        logger.info(f"[SCAN] Platform check complete. Found: {platform_results['found_count']}/{len(platforms)}")
        
        try:
            print(f"[SCAN] Committing findings to database...")
            db.session.commit()
            print(f"[SCAN] Findings committed successfully")
            logger.info(f"[SCAN] Findings committed successfully")
        except Exception as e:
            print(f"[SCAN] ERROR committing findings: {str(e)}")
            logger.error(f"[SCAN] Error committing findings: {str(e)}")
            db.session.rollback()
        
        # Apply filters to platform results if configured
        print(f"[SCAN] Applying filters to results...")
        if investigation.filters:
            try:
                from services.filter_service import InvestigationFilter
                filters = InvestigationFilter.from_dict(investigation.filters)
                if not filters.is_empty():
                    print(f"[SCAN] Filters active: {filters.get_description()}")
                    original_count = len(platform_results['platforms'])
                    platform_results['platforms'] = filters.apply_to_findings(platform_results['platforms'])
                    filtered_count = len(platform_results['platforms'])
                    print(f"[SCAN] Filter results: {original_count} platforms → {filtered_count} platforms")
                    logger.info(f"[SCAN] Filtered: {original_count} platforms → {filtered_count}")
                    platform_results['found_count'] = len([p for p in platform_results['platforms'] if p.get('found')])
            except Exception as e:
                print(f"[SCAN] ERROR applying filters: {str(e)}")
                logger.debug(f"[SCAN] Filter error (continuing): {str(e)}")
        
        # Run basic analysis on available data
        print(f"[SCAN] Running behavior analysis...")
        analysis = {}
        try:
            analysis = analyzer.analyze(username, platform_results)
            print(f"[SCAN] Analysis completed. Risk score: {analysis.get('risk_score', 0)}")
            print(f"[SCAN] Analysis findings count: {len(analysis.get('findings', []))}")
            print(f"[SCAN] Analysis findings: {analysis.get('findings', [])}")
            logger.info(f"[SCAN] Analysis completed for {username}")
        except Exception as e:
            print(f"[SCAN] ERROR in analysis: {str(e)}")
            logger.error(f"[SCAN] Analysis failed: {str(e)}")
            analysis = {
                'username': username,
                'risk_score': 0,
                'risk_level': 'UNKNOWN',
                'findings': [],
                'analysis_error': str(e)
            }
        
        risk_score = analysis.get('risk_score', 0)
        
        # Build graph - handle empty findings gracefully
        print(f"[SCAN] Building network graph...")
        graph_data = {'nodes': [], 'edges': []}
        try:
            graph_data = graph_builder.build_from_investigation(
                {'username': username, 'id': investigation.id},
                platform_results.get('platforms', [])
            ) or {'nodes': [], 'edges': []}
            print(f"[SCAN] Graph built. Nodes: {len(graph_data.get('nodes', []))} Edges: {len(graph_data.get('edges', []))}")
            logger.info(f"[SCAN] Graph built successfully")
        except Exception as e:
            print(f"[SCAN] ERROR building graph: {str(e)}")
            logger.error(f"[SCAN] Error building graph: {str(e)}")
            graph_data = {'nodes': [], 'edges': []}
        
        # Prepare result - ensure JSON-serializable
        from utils.debug_helpers import make_json_serializable
        result = {
            'data': {
                'username': username,
                'platforms_checked': platform_results['total_checked'],
                'platforms_found': platform_results['found_count'],
                'platforms_failed': platform_results['failed_count'],
                'analysis': analysis,
                'errors': platform_results.get('errors', [])
            },
            'graph': graph_data,
            'risk_score': float(risk_score)
        }
        
        # Serialize to ensure JSON compatibility
        result = make_json_serializable(result)
        
        print(f"[SCAN] Result prepared. JSON serializable: Yes")
        print(f"[SCAN] ========== LIGHT SCAN COMPLETED ==========")
        logger.info(f"[SCAN] ========== LIGHT SCAN COMPLETED ==========")
        
        return result
        
    except Exception as e:
        print(f"[SCAN] CRITICAL ERROR in _light_scan: {str(e)}")
        logger.error(f"[SCAN] CRITICAL ERROR in _light_scan: {str(e)}", exc_info=True)
        # Return safe fallback result
        return {
            'data': {
                'username': investigation.primary_entity,
                'platforms_checked': 0,
                'platforms_found': 0,
                'platforms_failed': 0,
                'analysis': {
                    'username': investigation.primary_entity,
                    'risk_score': 0,
                    'risk_level': 'UNKNOWN',
                    'findings': [],
                    'error': str(e)
                },
                'errors': [{'error': str(e)}]
            },
            'graph': {'nodes': [], 'edges': []},
            'risk_score': 0
        }


def _deep_scan(investigation):
    """
    Deep scan: Full analysis with email harvesting, mentions, network graph.
    Uses analyzer.py + network_builder.py.
    Returns partial results even if some data sources fail.
    
    Returns: {data, graph, risk_score}
    """
    logger.info(f"Executing deep scan for {investigation.primary_entity}")
    
    # Start with light scan
    result = _light_scan(investigation)
    
    # Try to get deeper data from specific platforms
    deep_data = {
        'reddit': None,
        'github': None,
        'errors': []
    }
    
    try:
        logger.debug(f"Attempting Reddit deep dive for {investigation.primary_entity}")
        reddit_data = scraper.get_reddit_data(investigation.primary_entity)
        if reddit_data and reddit_data.get('found'):
            deep_data['reddit'] = reddit_data
            logger.info(f"Reddit data acquired for {investigation.primary_entity}")
    except Exception as e:
        logger.error(f"Reddit deep dive failed: {str(e)}")
        deep_data['errors'].append({'source': 'reddit', 'error': str(e)})
    
    try:
        logger.debug(f"Attempting GitHub deep dive for {investigation.primary_entity}")
        github_data = scraper.get_github_data(investigation.primary_entity)
        if github_data and github_data.get('found'):
            deep_data['github'] = github_data
            logger.info(f"GitHub data acquired for {investigation.primary_entity}")
    except Exception as e:
        logger.error(f"GitHub deep dive failed: {str(e)}")
        deep_data['errors'].append({'source': 'github', 'error': str(e)})
    
    # Merge deep data into analysis if available
    if deep_data['reddit'] or deep_data['github']:
        try:
            enhanced_analysis = analyzer.analyze(
                investigation.primary_entity,
                result['data'].get('analysis', {}),
                detailed_data=deep_data
            )
            result['data']['analysis'] = enhanced_analysis
            result['risk_score'] = enhanced_analysis.get('risk_score', result['risk_score'])
            logger.info(f"Analysis enhanced with deep data for {investigation.primary_entity}")
        except Exception as e:
            logger.error(f"Error enhancing analysis with deep data: {str(e)}")
            # Keep original analysis
    
    # Add deep data errors to result
    if deep_data['errors']:
        if 'errors' not in result['data']:
            result['data']['errors'] = []
        result['data']['errors'].extend(deep_data['errors'])
    
    # Add deep data to findings
    if deep_data['reddit'] or deep_data['github']:
        try:
            if deep_data['reddit'] and deep_data['reddit'].get('found'):
                # Deep data findings get high confidence since they're verified
                confidence_str = deep_data['reddit'].get('confidence', 'high') if isinstance(deep_data['reddit'], dict) else 'high'
                confidence_map = {'high': 0.95, 'medium': 0.7, 'unknown': 0.5, 'none': 0.0}
                confidence_float = confidence_map.get(confidence_str, 0.95)
                finding = Finding(
                    id=str(uuid.uuid4()),
                    investigation_id=investigation.id,
                    finding_type='platform',
                    platform='Reddit',
                    found=True,
                    source=f"https://reddit.com/user/{investigation.primary_entity}",
                    confidence=confidence_float,
                    data=deep_data['reddit'] if isinstance(deep_data['reddit'], dict) else {}
                )
                db.session.add(finding)
            
            if deep_data['github'] and deep_data['github'].get('found'):
                # Deep data findings get high confidence since they're verified
                confidence_str = deep_data['github'].get('confidence', 'high') if isinstance(deep_data['github'], dict) else 'high'
                confidence_map = {'high': 0.95, 'medium': 0.7, 'unknown': 0.5, 'none': 0.0}
                confidence_float = confidence_map.get(confidence_str, 0.95)
                finding = Finding(
                    id=str(uuid.uuid4()),
                    investigation_id=investigation.id,
                    finding_type='platform',
                    platform='GitHub',
                    found=True,
                    source=f"https://github.com/{investigation.primary_entity}",
                    confidence=confidence_float,
                    data=deep_data['github'] if isinstance(deep_data['github'], dict) else {}
                )
                db.session.add(finding)
            
            db.session.commit()
            logger.info(f"Deep data findings saved for {investigation.primary_entity}")
        except Exception as e:
            logger.error(f"Error saving deep data findings: {str(e)}")
            db.session.rollback()
    
    # Email harvesting integration - SKIPPED in deep scan (takes too long, do asynchronously)
    # For now, return response immediately without waiting for email harvest
    logger.info(f"Deep scan completed for {investigation.primary_entity} - skipping email harvest to return response quickly")
    
    # Rebuild graph with all available data
    try:
        all_findings = Finding.query.filter_by(investigation_id=investigation.id).all()
        findings_data = [json.loads(f.data) if isinstance(f.data, str) else f.data for f in all_findings]
        
        # Apply filters before building graph
        if investigation.filters:
            try:
                from services.filter_service import InvestigationFilter
                filters = InvestigationFilter.from_dict(investigation.filters)
                if not filters.is_empty():
                    original_count = len(findings_data)
                    findings_data = filters.apply_to_findings(findings_data)
                    filtered_count = len(findings_data)
                    logger.info(f"Deep scan filtered findings: {original_count} → {filtered_count}")
            except Exception as e:
                logger.debug(f"Filter error in deep_scan (continuing): {str(e)}")
        
        graph_data = graph_builder.build_from_investigation(
            {'username': investigation.primary_entity, 'id': investigation.id},
            findings_data
        ) or {'nodes': [], 'edges': []}
        result['graph'] = graph_data
        logger.info(f"Graph rebuilt with deep scan findings")
    except Exception as e:
        logger.error(f"Error rebuilding graph: {str(e)}")
        # Keep existing graph
    
    logger.info(f"Deep scan completed for {investigation.primary_entity}")
    return result


def _build_safe_result(username, investigation_id, error_msg=''):
    """Build a safe empty result for error cases"""
    return {
        'data': {
            'username': username,
            'platforms_checked': 0,
            'platforms_found': 0,
            'analysis': {
                'username': username,
                'risk_score': 0,
                'risk_level': 'UNKNOWN',
                'findings': [],
                'analysis_notes': [f'Scan error: {error_msg}'] if error_msg else []
            },
            'errors': [error_msg] if error_msg else []
        },
        'graph': {'nodes': [], 'edges': []},
        'risk_score': 0
    }


def _format_scan_response(case_id, username, result):
    """Format scan result into response JSON"""
    print(f"\n[RESPONSE] ========== FORMATTING RESPONSE ==========")
    print(f"[RESPONSE] Case ID: {case_id}, Username: {username}")
    print(f"[RESPONSE] Result type: {type(result)}")
    logger.info(f"[RESPONSE] Starting response formatting for case {case_id}")
    
    try:
        data = result.get('data', {})
        graph = result.get('graph', {'nodes': [], 'edges': []})
        risk_score = float(result.get('risk_score', 0))
        analysis = data.get('analysis', {})
        
        print(f"[RESPONSE] Data keys: {list(data.keys())}")
        print(f"[RESPONSE] Graph nodes: {len(graph.get('nodes', []))}, edges: {len(graph.get('edges', []))}")
        print(f"[RESPONSE] Analysis findings: {len(analysis.get('findings', []))}")
        print(f"[RESPONSE] Risk score: {risk_score}")
        logger.info(f"[RESPONSE] Formatting response: findings={len(analysis.get('findings', []))}, threat_level={risk_score}")
        
        # Update database
        try:
            investigation = Investigation.query.get(case_id)
            if investigation:
                investigation.status = 'completed'
                investigation.completed_at = datetime.utcnow()
                investigation.risk_score = float(risk_score)
                db.session.commit()
                print(f"[RESPONSE] Investigation {case_id} updated in DB: status=completed, risk_score={risk_score}")
                logger.info(f"[RESPONSE] Updated investigation {case_id}: status=completed, risk_score={risk_score}")
        except Exception as e:
            print(f"[RESPONSE] Error updating investigation: {str(e)}")
            logger.error(f"[RESPONSE] Error updating investigation in _format_scan_response: {str(e)}")
            db.session.rollback()
        
        response = {
            'status': 'completed',
            'case_id': case_id,
            'target': username,
            'findings': list(analysis.get('findings', [])),
            'threat_level': float(risk_score),
            'network_nodes': list(graph.get('nodes', [])) if graph.get('nodes') else [],
            'network_edges': list(graph.get('edges', [])) if graph.get('edges') else [],
            'risk_level': str(analysis.get('risk_level', 'UNKNOWN')),
        }
        
        print(f"[RESPONSE] Response constructed successfully")
        print(f"[RESPONSE] Final findings count: {len(response['findings'])}")
        logger.info(f"[RESPONSE] Response ready: findings={len(response['findings'])}, threat_level={response['threat_level']}")
        
        result_tuple = jsonify(response), 200
        print(f"[RESPONSE] Returning response tuple: {type(result_tuple)}")
        logger.info(f"[RESPONSE] Returning formatted response")
        return result_tuple
    except Exception as e:
        print(f"[RESPONSE] CRITICAL ERROR in _format_scan_response: {str(e)}")
        logger.error(f"[RESPONSE] Error in _format_scan_response: {str(e)}", exc_info=True)
        # Return fallback response
        fallback = {
            'status': 'completed',
            'case_id': case_id,
            'target': username,
            'findings': [],
            'threat_level': 0,
            'network_nodes': [],
            'network_edges': [],
            'risk_level': 'UNKNOWN',
            'error_note': f'Response formatting error: {str(e)}'
        }
        print(f"[RESPONSE] Returning fallback response due to error")
        return jsonify(fallback), 200

