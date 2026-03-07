"""
Utility helper functions
"""

import uuid
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


def generate_case_id():
    """Generate a unique case ID"""
    return str(uuid.uuid4())


def generate_entity_id():
    """Generate a unique entity ID"""
    return str(uuid.uuid4())


def generate_edge_id():
    """Generate a unique edge ID"""
    return str(uuid.uuid4())


def generate_report_id():
    """Generate a unique report ID"""
    return str(uuid.uuid4())


def to_json_safe(obj):
    """Convert objects to JSON-safe format"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_json_safe(v) for v in obj]
    return obj


def calculate_confidence(sources_count, verification_status=False):
    """
    Calculate confidence score based on evidence count
    
    Args:
        sources_count (int): Number of sources confirming the finding
        verification_status (bool): Whether manually verified
        
    Returns:
        float: Confidence score (0-1)
    """
    base_confidence = min(sources_count * 0.15, 0.85)
    if verification_status:
        base_confidence = min(base_confidence + 0.15, 1.0)
    return base_confidence


def format_timestamp(dt):
    """Format datetime object to ISO string"""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return dt


def log_activity(message, level='info', investigation_id=None):
    """Log an activity"""
    timestamp = datetime.utcnow().isoformat()
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message,
    }
    if investigation_id:
        log_entry['investigation_id'] = investigation_id
    
    logger.log(getattr(logging, level.upper(), logging.INFO), message)
    return log_entry
