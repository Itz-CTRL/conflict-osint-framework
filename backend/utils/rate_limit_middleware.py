"""
Flask middleware and decorators for rate limiting integration

Provides decorators for protecting routes with rate limiting
and utilities for extracting client identifiers.
"""

import logging
from functools import wraps
from flask import request, jsonify
from services.rate_limiter import global_rate_limiter
from utils import APIResponse

logger = logging.getLogger(__name__)


def get_client_identifier():
    """Extract client identifier from request (IP or user ID)"""
    # Try to get user ID if authenticated
    if hasattr(request, 'user_id') and request.user_id:
        return request.user_id
    
    # Fallback to IP address
    return request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')


def rate_limit_check(limit_type='user', action=None):
    """
    Decorator for rate limiting routes.
    
    Args:
        limit_type: Type of limit ('user', 'ip', 'deep_scan', 'phone_lookup', etc.)
        action: Optional specific action identifier
    
    Usage:
        @investigation_bp.route('/deep-scan', methods=['POST'])
        @rate_limit_check(limit_type='deep_scan')
        def deep_scan():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_id = get_client_identifier()
            
            # Check rate limit
            is_allowed, limit_info = global_rate_limiter.check_limit(
                key=client_id,
                limit_type=limit_type,
                action=action
            )
            
            # Add rate limit info to response headers
            # This will be available for the frontend
            @wraps(func)
            def inner_wrapper(*args, **kwargs):
                response = func(*args, **kwargs)
                
                # Extract dict if tuple (response, status_code)
                if isinstance(response, tuple):
                    data, status_code = response[0], response[1]
                    # Add rate limit info
                    if isinstance(data, dict):
                        data['_rate_limit'] = limit_info
                    return data, status_code
                else:
                    # If returning jsonify, try to add headers
                    if hasattr(response, 'headers'):
                        response.headers['X-RateLimit-Limit'] = str(limit_info['limit'])
                        response.headers['X-RateLimit-Remaining'] = str(limit_info['remaining'])
                        response.headers['X-RateLimit-Reset'] = str(limit_info['reset_in'])
                    return response
            
            if not is_allowed:
                # Rate limit exceeded
                logger.warning(f"Rate limit exceeded for {client_id} ({limit_type})")
                error_response = {
                    'status': 'error',
                    'message': limit_info['message'],
                    'error': 'rate_limit_exceeded',
                    '_rate_limit': limit_info
                }
                return jsonify(error_response), 429  # Too Many Requests
            
            # Call original function with rate limit info attached to request
            request.rate_limit_info = limit_info
            
            return inner_wrapper(*args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit_warn(limit_type='user'):
    """
    Decorator for soft rate limiting - warns but doesn't block.
    Used for informational warnings about approaching limits.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_id = get_client_identifier()
            
            # Check rate limit
            is_allowed, limit_info = global_rate_limiter.check_limit(
                key=client_id,
                limit_type=limit_type
            )
            
            # Attach to request for endpoint to use
            request.rate_limit_info = limit_info
            request.rate_limit_warning = (limit_info['status'] == 'warning')
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
