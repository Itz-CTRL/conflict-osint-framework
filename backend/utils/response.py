"""
Response formatting utility for consistent API responses
"""

import json
from datetime import datetime


class APIResponse:
    """Standardized API response formatter"""
    
    @staticmethod
    def success(case_id, data=None, graph=None, risk_score=0, logs=None, status='completed'):
        """
        Create a successful response
        
        Returns:
            dict: Standardized success response
        """
        response = {
            'status': status,
            'case_id': case_id,
            'data': data or {},
            'graph': graph or {'nodes': [], 'edges': []},
            'risk_score': risk_score,
            'logs': logs or []
        }
        return response
    
    @staticmethod
    def pending(case_id, message='Investigation started', logs=None):
        """Create a pending/running response"""
        return {
            'status': 'running',
            'case_id': case_id,
            'data': {},
            'graph': {'nodes': [], 'edges': []},
            'risk_score': 0,
            'logs': logs or [{'timestamp': datetime.utcnow().isoformat(), 'message': message}]
        }
    
    @staticmethod
    def error(case_id, error_message, logs=None):
        """Create an error response"""
        return {
            'status': 'failed',
            'case_id': case_id,
            'data': {},
            'graph': {'nodes': [], 'edges': []},
            'risk_score': 0,
            'logs': logs or [{'timestamp': datetime.utcnow().isoformat(), 'error': error_message}]
        }
    
    @staticmethod
    def add_log(response, message=None, error=None, level='info'):
        """Add a log entry to response"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level
        }
        if message:
            log_entry['message'] = message
        if error:
            log_entry['error'] = error
        
        if 'logs' not in response:
            response['logs'] = []
        response['logs'].append(log_entry)
        return response
