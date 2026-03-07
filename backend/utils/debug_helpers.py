"""
Debug utilities for OSINT backend
Provides comprehensive logging and JSON serialization helpers
"""

import json
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

def make_json_serializable(obj, depth=0):
    """
    Recursively convert non-JSON-serializable objects to serializable forms.
    
    Handles:
    - datetime → ISO string
    - set → list
    - Decimal → float
    - bytes → string
    - objects → dict representation
    """
    if depth > 10:  # Prevent infinite recursion
        return str(obj)
    
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {
            str(k): make_json_serializable(v, depth + 1)
            for k, v in obj.items()
        }
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item, depth + 1) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Object - convert via __dict__
        try:
            return make_json_serializable(obj.__dict__, depth + 1)
        except:
            return str(obj)
    else:
        # Last resort
        return str(obj)


def log_scan_step(step, details=None):
    """Log a scan step with consistent formatting"""
    if details:
        print(f"[SCAN] {step}")
        print(f"[SCAN_DETAILS] {details}")
        logger.info(f"[SCAN] {step}")
        logger.info(f"[SCAN_DETAILS] {details}")
    else:
        print(f"[SCAN] {step}")
        logger.info(f"[SCAN] {step}")


def log_phone_step(step, details=None):
    """Log a phone lookup step with consistent formatting"""
    if details:
        print(f"[PHONE_LOOKUP] {step}")
        print(f"[PHONE_LOOKUP_DETAILS] {details}")
        logger.info(f"[PHONE_LOOKUP] {step}")
        logger.info(f"[PHONE_LOOKUP_DETAILS] {details}")
    else:
        print(f"[PHONE_LOOKUP] {step}")
        logger.info(f"[PHONE_LOOKUP] {step}")


def create_safe_response(status, target, findings=None, threat_level=0, network_nodes=None, network_edges=None, error_note=None):
    """
    Create a safe, guaranteed JSON-serializable response.
    
    All values are pre-sanitized and converted to JSON-safe types.
    """
    response = {
        'status': str(status),
        'target': str(target) if target else 'unknown',
        'findings': [] if findings is None else list(findings),
        'threat_level': float(threat_level),
        'network_nodes': [] if network_nodes is None else list(network_nodes),
        'network_edges': [] if network_edges is None else list(network_edges),
    }
    
    if error_note:
        response['error_note'] = str(error_note)
    
    # Ensure everything is JSON-serializable
    response = make_json_serializable(response)
    
    # Verify it can be JSON-encoded
    try:
        json.dumps(response)
        logger.debug(f"[DEBUG] Response is JSON serializable")
    except (TypeError, ValueError) as e:
        logger.error(f"[ERROR] Response not JSON serializable: {str(e)}")
        # Return absolute minimal safe response
        response = {
            'status': 'completed',
            'target': str(target) if target else 'unknown',
            'findings': [],
            'threat_level': 0,
            'network_nodes': [],
            'network_edges': [],
            'error_note': 'Response serialization error'
        }
    
    return response
