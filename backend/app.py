"""OSINT Investigation Platform - Flask Backend
Military-grade intelligence gathering and analysis system.

Uses modular architecture:
- analyzer.py: Risk scoring and behavior analysis
- network_builder.py: Network graph construction
- scraper.py: Lightweight metadata scraping
- routes/: Flask route handlers
- utils/: Validation, response formatting
- workers/: Background task management
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS

# Import configuration
from config import config

# Import database
from database import db, init_db

# Import routes
from routes import (
    investigation_bp,
    phone_bp,
    graph_bp,
    report_bp
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
    
    # Register blueprints
    app.register_blueprint(investigation_bp)
    app.register_blueprint(phone_bp)
    app.register_blueprint(graph_bp)
    app.register_blueprint(report_bp)
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'online',
            'platform': 'OSINT Investigation Platform',
            'version': '1.0.0',
            'environment': env
        }), 200
    
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
                'reports': '/api/report'
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
