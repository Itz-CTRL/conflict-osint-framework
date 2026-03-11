"""Filter Management and Options Routes

Provides endpoints for getting available filter options and
validating filters.
"""

from flask import Blueprint, request, jsonify
import logging
from services.filter_service import InvestigationFilter, Platform
from services.sherlock_checker import SherlockChecker
from utils import APIResponse

logger = logging.getLogger(__name__)

filter_bp = Blueprint('filters', __name__, url_prefix='/api/filters')

@filter_bp.route('/options', methods=['GET'])
def get_filter_options():
    """Get all available filter options (platforms, account types, etc.)"""
    try:
        sherlock = SherlockChecker()
        platforms = sherlock.get_available_sites()
        
        account_types = ['personal', 'business', 'bot', 'unknown']
        
        response_data = {
            'platforms': platforms,
            'account_types': account_types,
            'common_locations': [
                'United States', 'United Kingdom', 'Canada', 'Australia',
                'Germany', 'France', 'India', 'China', 'Brazil', 'Russia',
                'Japan', 'South Korea', 'Nigeria', 'Ghana', 'Kenya',
                'South Africa', 'Mexico', 'Spain', 'Italy', 'Netherlands'
            ],
            'filter_description': {
                'platforms': 'Included: only search these platforms',
                'location': 'Location filter for accounts',
                'account_type': 'Type of account (personal, business, bot)',
                'verified_only': 'Only include verified accounts',
                'minimize_bots': 'Exclude probable bots'
            }
        }
        
        return jsonify(APIResponse.success(None, data=response_data)), 200
    
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        return jsonify(APIResponse.error(None, f"Error: {str(e)}")), 500


@filter_bp.route('/validate', methods=['POST'])
def validate_filters():
    """Validate a filter configuration.
    
    Request body:
    {
        "platforms": ["GitHub", "Twitter"],
        "account_type": ["personal", "business"],
        "verified_only": false,
        "minimize_bots": true
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify(APIResponse.error(None, "Request body required")), 400
        
        try:
            filters = InvestigationFilter.from_dict(data)
            
            # Validate platforms if provided
            if filters.platform:
                sherlock = SherlockChecker()
                available = sherlock.get_available_sites()
                invalid_platforms = [p for p in filters.platform if p not in available]
                if invalid_platforms:
                    return jsonify(APIResponse.error(
                        None,
                        f"Invalid platforms: {', '.join(invalid_platforms)}"
                    )), 400
            
            # Generate description
            description = filters.get_description()
            
            return jsonify(APIResponse.success(None, data={
                'valid': True,
                'filters': {
                    'platforms': filters.platform,
                    'locations': filters.location,
                    'country': filters.country,
                    'account_types': filters.account_type,
                    'verified_only': filters.verified_only,
                    'minimize_bots': filters.minimize_bots
                },
                'description': description
            })), 200
        
        except Exception as e:
            return jsonify(APIResponse.error(None, f"Filter validation error: {str(e)}")), 400
    
    except Exception as e:
        logger.error(f"Error validating filters: {e}")
        return jsonify(APIResponse.error(None, f"Error: {str(e)}")), 500
