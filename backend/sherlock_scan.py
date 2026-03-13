"""
sherlock_scan.py

Sherlock-style username discovery across social platforms.
Light, fast baseline investigation using GET requests (more reliable than HEAD).
"""

import requests
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

# Social media platforms to check (from GhostTR reference)
PLATFORMS = [
    {"name": "Facebook", "url": "https://www.facebook.com/{}"},
    {"name": "Twitter", "url": "https://www.twitter.com/{}"},
    {"name": "Instagram", "url": "https://www.instagram.com/{}/"},
    {"name": "LinkedIn", "url": "https://www.linkedin.com/in/{}/"},
    {"name": "GitHub", "url": "https://www.github.com/{}"},
    {"name": "Pinterest", "url": "https://www.pinterest.com/{}/"},
    {"name": "Tumblr", "url": "https://{}.tumblr.com"},
    {"name": "YouTube", "url": "https://www.youtube.com/@{}"},
    {"name": "SoundCloud", "url": "https://soundcloud.com/{}"},
    {"name": "Snapchat", "url": "https://www.snapchat.com/add/{}"},
    {"name": "TikTok", "url": "https://www.tiktok.com/@{}"},
    {"name": "Behance", "url": "https://www.behance.net/{}"},
    {"name": "Medium", "url": "https://www.medium.com/@{}"},
    {"name": "Quora", "url": "https://www.quora.com/profile/{}"},
    {"name": "Flickr", "url": "https://www.flickr.com/people/{}"},
    {"name": "Periscope", "url": "https://www.periscope.tv/{}"},
    {"name": "Twitch", "url": "https://www.twitch.tv/{}"},
    {"name": "Dribbble", "url": "https://www.dribbble.com/{}"},
    {"name": "StumbleUpon", "url": "https://www.stumbleupon.com/stumbler/{}"},
    {"name": "Ello", "url": "https://www.ello.co/{}"},
    {"name": "Product Hunt", "url": "https://www.producthunt.com/@{}"},
    {"name": "Telegram", "url": "https://www.telegram.me/{}"},
    {"name": "WeHeartIt", "url": "https://www.weheartit.com/{}"},
    {"name": "Reddit", "url": "https://www.reddit.com/user/{}"},
]


def check_username_on_platform(username: str, platform: dict, timeout: int = 6) -> Optional[dict]:
    """
    Check if username exists on a single platform using GET request.
    Uses GET instead of HEAD for better compatibility with all platforms.
    
    Args:
        username: Username to search for
        platform: Platform dict with 'name' and 'url'
        timeout: Request timeout in seconds
    
    Returns:
        dict with platform info if found, None otherwise
    """
    try:
        url = platform["url"].format(username)
        
        # Use GET request with proper headers (more reliable than HEAD)
        response = requests.get(
            url,
            allow_redirects=True,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            stream=True  # Stream to avoid downloading large content
        )
        
        # Check for success status (200-399 range)
        if 200 <= response.status_code < 400:
            return {
                "platform": platform["name"],
                "url": url,
                "found": True,
                "status_code": response.status_code,
            }
        
        return None
        
    except requests.exceptions.Timeout:
        logger.debug(f"Timeout checking {platform['name']} for {username}")
        return None
    except requests.exceptions.ConnectionError:
        logger.debug(f"Connection error checking {platform['name']}")
        return None
    except requests.exceptions.RequestException as e:
        logger.debug(f"Request error on {platform['name']}: {str(e)}")
        return None
    except Exception as e:
        logger.debug(f"Error checking {platform['name']}: {str(e)}")
        return None


def light_scan(username: str) -> dict:
    """
    Perform a light Sherlock-style scan.
    Check username across social platforms in parallel using GET requests.
    
    Args:
        username: Username to scan
    
    Returns:
        dict with success status and discovered profiles
    """
    if not username or len(username.strip()) < 2:
        return {
            "success": False,
            "error": "Username must be at least 2 characters",
            "data": None,
        }
    
    username = username.strip()
    profiles = []
    
    logger.info(f"Starting light scan for username: {username}")
    
    # Check platforms in parallel with increased workers for better throughput
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(check_username_on_platform, username, platform): platform
            for platform in PLATFORMS
        }
        
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    profiles.append(result)
                    logger.info(f"Found profile on {result['platform']}: {result['url']}")
            except Exception as e:
                logger.debug(f"Error processing result: {e}")
    
    return {
        "success": True,
        "data": {
            "username": username,
            "findings": sorted(profiles, key=lambda x: x["platform"]),
            "count": len(profiles),
        }
    }
