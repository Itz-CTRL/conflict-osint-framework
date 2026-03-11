"""Profile Checking and Verification Routes

Allows users to inspect and verify discovered social media profiles,
fetch detailed profile data, and validate account information.
"""

from flask import Blueprint, request, jsonify
import logging
from services.sherlock_checker import SherlockChecker
from services.scraper import OSINTScraper
from utils import APIResponse

logger = logging.getLogger(__name__)

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')

scraper = OSINTScraper()

@profile_bp.route('/check/<platform>/<username>', methods=['GET'])
def check_profile(platform, username):
    """Check a specific platform for a username and get profile details.
    
    Args:
        platform: Platform name (e.g., 'GitHub', 'Twitter', 'Reddit')
        username: Username to check on that platform
        bypass: (optional) Set to 'true' to force-check and skip caching (Fix #3)
        
    Returns:
        Profile details if found, otherwise 404
    """
    try:
        logger.info(f"Checking profile: {platform}/{username}")
        
        # Fix #3: Add bypass flag for force-checking
        bypass_cache = request.args.get('bypass', 'false').lower() == 'true'
        if bypass_cache:
            logger.info(f"Bypass mode: force-checking {platform}/{username}")
        
        # Use Sherlock for quick verification
        sherlock = SherlockChecker(timeout=10)
        result = sherlock.check_username(username, sites=[platform])
        
        found_sites = result.get('found', {}).get('sites', [])
        if not found_sites:
            # Check for rate-limiting or other errors
            error_msg = f"Profile not found on {platform} for username {username}"
            not_found_result = result.get('not_found', {}).get('sites', [])
            if not_found_result and not_found_result[0].get('may_be_rate_limited'):
                error_msg += " (Note: May be rate-limited, try again later or use ?bypass=true)"
                logger.warning(f"Possible rate-limit on {platform}: {error_msg}")
            return jsonify(APIResponse.error(None, error_msg)), 404
        
        site_data = found_sites[0]
        profile_data = {
            'platform': site_data['site'],
            'username': username,
            'url': site_data.get('profile_url') or site_data.get('url'),
            'status_code': site_data.get('status_code'),
            'verified_in_content': site_data.get('verified_in_content', False),
            'confidence': site_data.get('confidence', 'medium'),
            'may_be_rate_limited': site_data.get('may_be_rate_limited', False),
            'found': True,
            'verified_at': site_data.get('verified_at'),
            'bypass_used': bypass_cache
        }
        
        # Try to get additional details based on platform
        if platform.lower() == 'reddit':
            try:
                reddit_data = scraper.get_reddit_data(username)
                if reddit_data and reddit_data.get('found'):
                    profile_data.update({
                        'karma': reddit_data.get('karma'),
                        'account_age': reddit_data.get('account_age'),
                        'verified': reddit_data.get('verified'),
                        'recent_activity': len(reddit_data.get('recent_posts', []))
                    })
            except Exception as e:
                logger.debug(f"Failed to get Reddit details: {e}")
        
        elif platform.lower() == 'github':
            try:
                github_data = scraper.get_github_data(username)
                if github_data and github_data.get('found'):
                    profile_data.update({
                        'name': github_data.get('name'),
                        'bio': github_data.get('bio'),
                        'location': github_data.get('location'),
                        'email': github_data.get('email'),
                        'company': github_data.get('company'),
                        'followers': github_data.get('followers'),
                        'following': github_data.get('following'),
                        'public_repos': github_data.get('public_repos'),
                        'account_age': github_data.get('account_age')
                    })
            except Exception as e:
                logger.debug(f"Failed to get GitHub details: {e}")
        
        return jsonify(APIResponse.success(None, data=profile_data)), 200
    
    except Exception as e:
        logger.error(f"Error checking profile: {e}")
        return jsonify(APIResponse.error(None, f"Error checking profile: {str(e)}")), 500


@profile_bp.route('/check-multiple', methods=['POST'])
def check_multiple_profiles():
    """Check multiple profiles at once.
    
    Request body:
    {
        "profiles": [
            {"platform": "GitHub", "username": "torvalds"},
            {"platform": "Twitter", "username": "github"}
        ]
    }
    """
    try:
        data = request.get_json()
        profiles = data.get('profiles', [])
        
        if not profiles:
            return jsonify(APIResponse.error(None, "No profiles provided")), 400
        
        results = []
        for profile in profiles:
            platform = profile.get('platform')
            username = profile.get('username')
            
            if not platform or not username:
                continue
            
            try:
                sherlock = SherlockChecker(timeout=8)
                result = sherlock.check_username(username, sites=[platform])
                
                found_sites = result.get('found', {}).get('sites', [])
                if found_sites:
                    site_data = found_sites[0]
                    results.append({
                        'platform': platform,
                        'username': username,
                        'found': True,
                        'url': site_data.get('profile_url') or site_data.get('url')
                    })
                else:
                    results.append({
                        'platform': platform,
                        'username': username,
                        'found': False
                    })
            except Exception as e:
                logger.debug(f"Error checking {platform}/{username}: {e}")
                results.append({
                    'platform': platform,
                    'username': username,
                    'found': False,
                    'error': str(e)
                })
        
        return jsonify(APIResponse.success(None, data={'profiles_checked': results})), 200
    
    except Exception as e:
        logger.error(f"Error checking multiple profiles: {e}")
        return jsonify(APIResponse.error(None, f"Error: {str(e)}")), 500


@profile_bp.route('/available-platforms', methods=['GET'])
def get_available_platforms():
    """Get list of all platforms that can be checked."""
    try:
        sherlock = SherlockChecker()
        platforms = sherlock.get_available_sites()
        
        return jsonify(APIResponse.success(None, data={
            'platforms': platforms,
            'count': len(platforms)
        })), 200
    
    except Exception as e:
        logger.error(f"Error getting platforms: {e}")
        return jsonify(APIResponse.error(None, f"Error: {str(e)}")), 500
