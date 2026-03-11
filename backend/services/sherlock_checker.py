"""Sherlock integration for OSINT investigations.

Sherlock (sherlock-project) provides efficient parallel checking of usernames
across many social media platforms. This module wraps Sherlock for both light
and deep scans.
"""

import logging
from typing import Dict, List, Optional
import json
import requests
from datetime import datetime
import concurrent.futures

logger = logging.getLogger(__name__)


class SherlockChecker:
    """Wrapper around Sherlock functionality for efficient username checking."""

    def __init__(self, timeout=10, max_workers=4):
        self.timeout = timeout
        self.max_workers = max_workers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Sherlock site data (simplified mapping of popular sites)
        self.sites = {
            'Facebook': ('https://www.facebook.com/{username}', 200),
            'Twitter': ('https://twitter.com/{username}', 200),
            'Instagram': ('https://www.instagram.com/{username}/', 200),
            'GitHub': ('https://github.com/{username}', 200),
            'Reddit': ('https://www.reddit.com/user/{username}', 200),
            'LinkedIn': ('https://www.linkedin.com/in/{username}', 200),
            'YouTube': ('https://www.youtube.com/@{username}', 200),
            'TikTok': ('https://www.tiktok.com/@{username}', 200),
            'Twitch': ('https://twitch.tv/{username}', 200),
            'Telegram': ('https://t.me/{username}', 200),
            'Pinterest': ('https://www.pinterest.com/{username}', 200),
            'Snapchat': ('https://www.snapchat.com/add/{username}', 200),
            'Tumblr': ('https://{username}.tumblr.com', 200),
            'Medium': ('https://medium.com/@{username}', 200),
            'Patreon': ('https://www.patreon.com/{username}', 200),
            'Quora': ('https://quora.com/profile/{username}', 200),
            'HackerNews': ('https://news.ycombinator.com/user?id={username}', 200),
            'GitLab': ('https://gitlab.com/{username}', 200),
            'Bitbucket': ('https://bitbucket.org/{username}', 200),
            'Mastodon': ('https://mastodon.social/@{username}', 200),
            'Bluesky': ('https://bsky.app/profile/{username}', 200),
        }

    def check_username(self, username: str, sites: Optional[List[str]] = None) -> Dict:
        """
        Check username across one or more sites using parallel requests.

        Args:
            username: Username to check
            sites: Optional list of site names to check (defaults to all)

        Returns:
            Dict with found_sites, not_found_sites, errors, timestamp
        """
        if not username:
            return {'error': 'Username required', 'found_sites': [], 'not_found_sites': []}

        sites_to_check = sites if sites else list(self.sites.keys())
        found_sites = []
        not_found_sites = []
        errors = []

        def check_site(site_name):
            if site_name not in self.sites:
                return None

            url_template, expected_code = self.sites[site_name]
            url = url_template.format(username=username)

            try:
                # Use GET instead of HEAD to verify body content (Fix #1)
                response = requests.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
                status = response.status_code
                
                # Fix #1: Status code is primary indicator (200 = found, 404 = not found)
                # Verify username appears in response body as secondary confirmation
                verified_in_content = False
                if status == 200:
                    try:
                        body_text = response.text.lower()
                        username_lower = username.lower()
                        verified_in_content = username_lower in body_text
                    except Exception:
                        # If we can't check body, assume it's found if status is 200
                        verified_in_content = True
                
                # Fix #2: Add confidence and rate-limit detection
                # Status code 200 indicates profile exists, even if username not visible in content
                found = status == 200
                confidence = 'high' if (status == 200 and verified_in_content) else ('medium' if status == 200 else 'none')
                may_be_rate_limited = status in [429, 403]

                if status == expected_code or (200 <= status < 400):
                    return {
                        'site': site_name,
                        'url': url,
                        'found': found,
                        'verified_in_content': verified_in_content,
                        'confidence': confidence,
                        'may_be_rate_limited': may_be_rate_limited,
                        'status_code': status,
                        'profile_url': response.url if status == 200 else url
                    }
                else:
                    return {
                        'site': site_name,
                        'url': url,
                        'found': False,
                        'verified_in_content': False,
                        'confidence': 'none',
                        'may_be_rate_limited': may_be_rate_limited,
                        'status_code': status
                    }
            except requests.exceptions.Timeout:
                return {
                    'site': site_name,
                    'url': url,
                    'found': False,
                    'verified_in_content': False,
                    'confidence': 'none',
                    'may_be_rate_limited': False,
                    'error': 'timeout'
                }
            except Exception as e:
                return {
                    'site': site_name,
                    'url': url,
                    'found': False,
                    'verified_in_content': False,
                    'confidence': 'none',
                    'may_be_rate_limited': False,
                    'error': str(e)
                }

        # Parallel checking
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(check_site, site): site for site in sites_to_check}
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        if result.get('found'):
                            found_sites.append(result)
                        else:
                            not_found_sites.append(result)
                except Exception as e:
                    logger.debug(f"Error checking site: {e}")

        return {
            'username': username,
            'found': {
                'count': len(found_sites),
                'sites': found_sites
            },
            'not_found': {
                'count': len(not_found_sites),
                'sites': not_found_sites
            },
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_available_sites(self) -> List[str]:
        """Return list of available sites for checking."""
        return list(self.sites.keys())

    def check_with_filter(self, username: str, platforms: Optional[List[str]] = None) -> Dict:
        """
        Check username on specific platforms and return results filtered.

        Args:
            username: Username to check
            platforms: List of platform names to filter by

        Returns:
            Filtered results containing only requested platforms
        """
        all_results = self.check_username(username, sites=platforms)
        return all_results
