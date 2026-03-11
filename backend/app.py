"""OSINT Investigation Platform - Flask Backend
Military-grade intelligence gathering and analysis system.

Uses modular architecture:
- analyzer.py: Risk scoring and behavior analysis
- network_builder.py: Network graph construction
- scraper.py: Lightweight metadata scraping
- routes/: Flask route handlers
- utils/: Validation, response formatting
- workers/: Background task management
- services/: PDF generation, CSV export, email harvesting
"""

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Import configuration
from config import config

# Import database
from database import db, init_db

# Import Celery
from celery_config import celery_app, init_celery

# Import routes
from routes import (
    investigation_bp,
    phone_bp,
    graph_bp,
    report_bp,
    profile_bp,
    filter_bp
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name='development'):
    """
    Application factory function
    
    Args:
        config_name: Configuration environment name ('development', 'production', 'testing')
        
    Returns:
        app: Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    env = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config.get(env, config['development']))
    
    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize database
    init_db(app)
    
    # Initialize Celery
    init_celery(app)
    
    # Register blueprints
    app.register_blueprint(investigation_bp)
    app.register_blueprint(phone_bp)
    app.register_blueprint(graph_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(filter_bp)
    
    # Apply rate limiting to specific routes
    if app.config.get('RATE_LIMIT_ENABLED', True):
        limiter.limit("50 per day")(investigation_bp)
        limiter.limit("100 per hour")(phone_bp)
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        from celery.result import AsyncResult
        celery_ok = False
        try:
            celery_app.control.inspect().active()
            celery_ok = True
        except Exception as e:
            logger.debug(f"Celery not available: {e}")
        
        return jsonify({
            'status': 'online',
            'platform': 'OSINT Investigation Platform',
            'version': '1.0.0',
            'environment': env,
            'features': {
                'pdf_export': app.config.get('PDF_ENABLED', True),
                'csv_export': app.config.get('CSV_EXPORT_ENABLED', True),
                'email_harvesting': app.config.get('EMAIL_HARVESTER_ENABLED', True),
                'rate_limiting': app.config.get('RATE_LIMIT_ENABLED', True),
                'celery_queue': celery_ok
            }
        }), 200
    
    # Task status endpoint
    @app.route('/api/admin/task/<task_id>', methods=['GET'])
    def get_task_status(task_id):
        """Get status of a background task"""
        from celery.result import AsyncResult
        task_result = AsyncResult(task_id, app=celery_app)
        return jsonify({
            'task_id': task_id,
            'status': task_result.status,
            'result': task_result.result if task_result.successful() else None,
            'error': str(task_result.info) if task_result.failed() else None
        }), 200
    
    # Username suggestions endpoint (Fix: missing root-level endpoint)
    @app.route('/api/username_suggestions', methods=['GET'])
    def username_suggestions():
        """
        Get username suggestions using fuzzy matching on investigation history.
        Frontend-facing endpoint at root API level.
        
        Query Parameters:
            q (str): Partial or full username to match (min 2 chars)
            query (str): Alternative parameter name for username query
            limit (int): Maximum suggestions to return (default: 10)
        """
        try:
            from services.suggestion_engine import SuggestionEngine
            
            # Accept both 'q' and 'query' parameter names for flexibility
            query = request.args.get('q') or request.args.get('query', '').strip()
            limit = request.args.get('limit', 10, type=int)
            
            # Validate inputs
            if limit < 1 or limit > 50:
                limit = 10
            
            # Get suggestions
            suggestion_engine = SuggestionEngine()
            suggestions = suggestion_engine.get_username_suggestions(query, limit=limit)
            
            from utils import APIResponse
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
            from utils import APIResponse
            return jsonify(APIResponse.error(None, f"Server error: {str(e)}")), 500
    
    # Username variations endpoint (Fix: missing root-level endpoint)
    @app.route('/api/username_variations', methods=['GET'])
    def username_variations():
        """
        Get common username variations for expanded search.
        Frontend-facing endpoint at root API level.
        
        Query Parameters:
            username (str): Base username to generate variations for
        """
        try:
            from services.suggestion_engine import SuggestionEngine
            
            username = request.args.get('username', '').strip()
            
            if not username or len(username) < 2:
                from utils import APIResponse
                return jsonify(APIResponse.error(None, "Username required (min 2 chars)")), 400
            
            suggestion_engine = SuggestionEngine()
            variations = suggestion_engine.get_common_variations(username)
            
            from utils import APIResponse
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
            from utils import APIResponse
            return jsonify(APIResponse.error(None, f"Server error: {str(e)}")), 500
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint with API information"""
        return jsonify({
            'name': 'OSINT Investigation Platform API',
            'version': '1.0.0',
            'description': 'Military-grade OSINT intelligence gathering system',
            'endpoints': {
                'investigations': '/api/investigation',
                'phone': '/api/phone',
                'graph': '/api/graph',
                'reports': '/api/report',
                'username_suggestions': '/api/username_suggestions',
                'username_variations': '/api/username_variations'
            }
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'status': 'error', 'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"Server error: {str(error)}")
        return jsonify({'status': 'error', 'error': 'Internal server error'}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'status': 'error', 'error': 'Bad request'}), 400
    
    # Request/Response logging
    @app.before_request
    def log_request():
        """Log incoming requests"""
        from flask import request
        logger.debug(f"Request: {request.method} {request.path}")
    
    @app.after_request
    def log_response(response):
        """Log outgoing responses"""
        logger.debug(f"Response: {response.status_code}")
        return response
    
    return app


# Create application instance
app = create_app()


if __name__ == '__main__':
    print("\n" + "="*80)
    print("  OSINT Investigation Platform - Backend Server")
    print("  Military-grade Intelligence Gathering & Analysis System")
    print("  Backend running on http://127.0.0.1:5000")
    print("="*80 + "\n")
    app.run(debug=True, port=5000, host='0.0.0.0')
