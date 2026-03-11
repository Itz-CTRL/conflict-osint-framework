"""OSINT Scraper Service
Lightweight web scraper for OSINT investigations across social media platforms.
Checks username presence and extracts metadata.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import logging
import time
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class OSINTScraper:
    """
    Web scraper for OSINT investigations across social media platforms.
    Light scraping for verification and metadata extraction.
    Includes retry logic for temporary failures.
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.max_retries = 3  # Increased from 2 for better resilience
        self.retry_delay = 0.1  # Reduced from 1 second for fast retries

    def check_platform(self, platform, url, username):
        """
        Check if a username exists on a given platform.
        Returns data including profile picture if available.
        Includes retry logic for transient failures.
        Now includes body content verification to prevent false positives.
        """
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=8)
                status_code = response.status_code
                
                # Fix #1: Check status code as primary indicator (200 = found, 404 = not found)
                # Also verify username appears in response for additional confirmation
                verified_in_content = False
                if status_code == 200:
                    try:
                        body_text = response.text.lower()
                        username_lower = username.lower()
                        # Check if username appears in page content
                        # This is a secondary check - status code is primary
                        verified_in_content = username_lower in body_text
                    except Exception as e:
                        logger.debug(f"Error checking body content for {username}: {str(e)}")
                        # If we can't check body, assume it's found if status is 200
                        verified_in_content = True
                
                # Status code is primary indicator of existence
                # 200 = profile exists (found)
                # 404 = profile not found
                # 403, 429 = rate limited (could exist)
                found = status_code == 200
                
                # Fix #2: Add confidence level and not-found confirmation
                if found and verified_in_content:
                    confidence = 'high'
                elif found and not verified_in_content:
                    confidence = 'medium'  # Found by status code but not verified in content
                elif status_code in [429, 403]:
                    confidence = 'unknown'  # Rate limited or forbidden
                else:
                    confidence = 'none'  # Profile not found
                
                may_be_rate_limited = status_code in [429, 403]

                data = {
                    'platform': platform,
                    'username': username,
                    'url': url,
                    'found': found,
                    'status_code': status_code,
                    'verified_in_content': verified_in_content,
                    'confidence': confidence,
                    'may_be_rate_limited': may_be_rate_limited,
                    'checked_at': datetime.now().isoformat(),
                    'profile_picture': None,
                    'error': None
                }

                if found:
                    try:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        title = soup.title.string if soup.title else 'No title'
                        data['page_title'] = title

                        # Try to get profile picture
                        profile_pic = None
                        
                        if platform == 'GitHub':
                            img = soup.find('img', {'class': 'avatar'})
                            if img and img.get('src'):
                                profile_pic = img['src']
                        
                        # Try generic Open Graph meta tag (works for many platforms)
                        if not profile_pic:
                            meta_image = soup.find('meta', property='og:image')
                            if meta_image and meta_image.get('content'):
                                profile_pic = meta_image['content']
                        
                        data['profile_picture'] = profile_pic
                        
                        logger.info(f"✓ Found {username} on {platform}")
                    except Exception as e:
                        logger.warning(f"Error parsing {platform} page: {str(e)}")
                        data['parse_error'] = str(e)
                else:
                    logger.debug(f"✗ Not found on {platform}")

                return data

            except requests.exceptions.Timeout:
                error_msg = f"Timeout on {platform} (attempt {attempt + 1}/{self.max_retries + 1})"
                logger.warning(error_msg)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                return {
                    'platform': platform,
                    'username': username,
                    'url': url,
                    'found': False,
                    'error': 'timeout',
                    'checked_at': datetime.now().isoformat(),
                    'profile_picture': None
                }
            
            except requests.exceptions.ConnectionError:
                error_msg = f"Connection error on {platform} (attempt {attempt + 1}/{self.max_retries + 1})"
                logger.warning(error_msg)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                return {
                    'platform': platform,
                    'username': username,
                    'url': url,
                    'found': False,
                    'error': 'connection_error',
                    'checked_at': datetime.now().isoformat(),
                    'profile_picture': None
                }
            
            except requests.exceptions.HTTPError as e:
                # Don't retry on HTTP errors like 404, 403
                status_code = e.response.status_code if hasattr(e, 'response') else None
                logger.debug(f"HTTP error {status_code} on {platform}: {str(e)}")
                return {
                    'platform': platform,
                    'username': username,
                    'url': url,
                    'found': False,
                    'status_code': status_code,
                    'error': f'http_error_{status_code}',
                    'checked_at': datetime.now().isoformat(),
                    'profile_picture': None
                }
            
            except Exception as e:
                error_msg = f"Error on {platform}: {str(e)} (attempt {attempt + 1}/{self.max_retries + 1})"
                logger.warning(error_msg)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                return {
                    'platform': platform,
                    'username': username,
                    'url': url,
                    'found': False,
                    'error': str(e),
                    'checked_at': datetime.now().isoformat(),
                    'profile_picture': None
                }

    def search_username(self, username):
        """
        Search for a username across multiple social media platforms.
        Returns comprehensive data about where the username exists.
        Returns partial results even if some platform checks fail.
        """
        logger.info(f"Starting username search for: {username}")

        # Core platform URLs to check - specified OSINT platforms
        platforms = [
            ('Facebook', f'https://www.facebook.com/{username}'),
            ('Instagram', f'https://www.instagram.com/{username}'),
            ('Twitter/X', f'https://twitter.com/{username}'),
            ('TikTok', f'https://www.tiktok.com/@{username}'),
            ('YouTube', f'https://www.youtube.com/@{username}'),
            ('GitHub', f'https://github.com/{username}'),
            ('Reddit', f'https://www.reddit.com/user/{username}'),
            ('LinkedIn', f'https://www.linkedin.com/in/{username}'),
            ('Pinterest', f'https://www.pinterest.com/{username}'),
            ('Telegram', f'https://t.me/{username}'),
        ]

        results = {
            'username': username,
            'searched_at': datetime.now().isoformat(),
            'total_checked': len(platforms),
            'found_count': 0,
            'platforms': [],
            'errors': []
        }

        for platform_name, url in platforms:
            try:
                result = self.check_platform(platform_name, url, username)
                results['platforms'].append(result)
                
                if result.get('found'):
                    results['found_count'] += 1
                    logger.info(f"Found {username} on {platform_name}")
                
                if result.get('error'):
                    results['errors'].append({
                        'platform': platform_name,
                        'error': result['error']
                    })
            except Exception as e:
                logger.error(f"Unexpected error checking {platform_name}: {str(e)}")
                results['platforms'].append({
                    'platform': platform_name,
                    'username': username,
                    'url': url,
                    'found': False,
                    'error': str(e),
                    'checked_at': datetime.now().isoformat()
                })
                results['errors'].append({
                    'platform': platform_name,
                    'error': str(e)
                })

        logger.info(f"Username search completed: Found on {results['found_count']}/{results['total_checked']} platforms")
        return results
    
    def format_findings_for_ui(self, search_results: Dict) -> Dict:
        """
        Format search results for frontend display with clickable links.
        
        Returns findings with:
        - Clickable profile URLs
        - Verification status
        - Verified badges
        - Risk indicators
        """
        socials = {
            'found': [],
            'not_found': [],
            'errors': []
        }
        
        # Categorize by platform
        for platform_result in search_results.get('platforms', []):
            platform = platform_result.get('platform', 'Unknown')
            found = platform_result.get('found', False)
            url = platform_result.get('url') or platform_result.get('profile_url', '')
            
            finding = {
                'platform': platform,
                'username': platform_result.get('username', ''),
                'url': url,
                'found': found,
                'verified': platform_result.get('verified', False),
                'profile_picture': platform_result.get('profile_picture'),
                'status_code': platform_result.get('status_code'),
                'verified_at': platform_result.get('checked_at'),
                'clickable': True,  # Indicates URL is clickable
                'risk_indicators': {
                    'spam_reported': platform_result.get('spam_reported', False),
                    'dangerous': platform_result.get('dangerous', False)
                }
            }
            
            if found:
                socials['found'].append(finding)
            elif not platform_result.get('error'):
                socials['not_found'].append(finding)
            else:
                socials['errors'].append({
                    'platform': platform,
                    'error': platform_result.get('error'),
                    'error_details': str(platform_result)
                })
        
        socials['summary'] = {
            'total_checked': len(search_results.get('platforms', [])),
            'found_count': len(socials['found']),
            'not_found_count': len(socials['not_found']),
            'error_count': len(socials['errors'])
        }
        
        return socials

    def get_reddit_data(self, username):
        """
        Get detailed Reddit profile data using their public JSON API.
        Returns partial data even if some requests fail.
        """
        logger.info(f"Fetching detailed Reddit data for: {username}")

        try:
            # Reddit provides free JSON endpoints
            url = f"https://www.reddit.com/user/{username}/about.json"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                logger.error(f"Reddit API returned status {response.status_code}")
                return {'found': False, 'error': f'Status {response.status_code}'}

            data = response.json().get('data', {})

            # Get recent posts (continue even if this fails)
            posts = []
            try:
                posts_url = f"https://www.reddit.com/user/{username}.json?limit=5"
                posts_response = requests.get(posts_url, headers=self.headers, timeout=10)
                
                if posts_response.status_code == 200:
                    for item in posts_response.json().get('data', {}).get('children', []):
                        p = item.get('data', {})
                        posts.append({
                            'content': p.get('title', p.get('body', ''))[:200],
                            'subreddit': p.get('subreddit', 'unknown'),
                            'score': p.get('score', 0),
                            'created': datetime.fromtimestamp(
                                p.get('created_utc', 0)
                            ).strftime('%Y-%m-%d %H:%M')
                        })
                else:
                    logger.warning(f"Could not fetch Reddit posts: status {posts_response.status_code}")
            except Exception as e:
                logger.warning(f"Error fetching Reddit posts: {str(e)}")

            result = {
                'found': True,
                'platform': 'reddit',
                'username': data.get('name'),
                'account_age': datetime.fromtimestamp(
                    data.get('created_utc', 0)
                ).strftime('%Y-%m-%d') if data.get('created_utc') else None,
                'karma': data.get('total_karma', 0),
                'verified': data.get('verified', False),
                'recent_posts': posts,
                'profile_picture': data.get('icon_img', '').split('?')[0] if data.get('icon_img') else None
            }

            logger.info(f"Reddit data collected for {username}")
            return result

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching Reddit data for {username}")
            return {'found': False, 'error': 'timeout'}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching Reddit data: {str(e)}")
            return {'found': False, 'error': str(e)}
        
        except Exception as e:
            logger.error(f"Unexpected error fetching Reddit data: {str(e)}")
            return {'found': False, 'error': str(e)}

    def get_github_data(self, username):
        """
        Get detailed GitHub profile data using their free public API.
        Returns partial data even if some requests fail.
        """
        logger.info(f"Fetching detailed GitHub data for: {username}")

        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                logger.error(f"GitHub API returned status {response.status_code}")
                return {'found': False, 'error': f'Status {response.status_code}'}

            data = response.json()

            result = {
                'found': True,
                'platform': 'github',
                'username': data.get('login'),
                'name': data.get('name'),
                'bio': data.get('bio'),
                'location': data.get('location'),
                'email': data.get('email'),
                'company': data.get('company'),
                'followers': data.get('followers', 0),
                'following': data.get('following', 0),
                'public_repos': data.get('public_repos', 0),
                'account_age': data.get('created_at', '')[:10],
                'twitter_linked': data.get('twitter_username'),
                'profile_picture': data.get('avatar_url')
            }

            logger.info(f"GitHub data collected for {username}")
            return result

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching GitHub data for {username}")
            return {'found': False, 'error': 'timeout'}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching GitHub data: {str(e)}")
            return {'found': False, 'error': str(e)}
        
        except Exception as e:
            logger.error(f"Unexpected error fetching GitHub data: {str(e)}")
            return {'found': False, 'error': str(e)}

    def get_twitter_data(self, username):
        """Fetch detailed Twitter/X data from API or page parsing"""
        logger.info(f"Fetching detailed Twitter data for: {username}")
        try:
            # Try using nitter (privacy-focused Twitter frontend) for public data
            url = f"https://nitter.net/{username}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                try:
                    profile_card = soup.find('div', class_='profile-card')
                    
                    result = {
                        'found': True,
                        'platform': 'twitter',
                        'username': username,
                        'verified': bool(soup.find('svg', class_='icon-verified')),
                        'followers': 'N/A',  # Nitter doesn't expose follower counts easily due to JS
                        'location': 'N/A',
                        'bio': 'N/A',
                        'profile_picture': None
                    }
                    
                    # Try to extract profile picture
                    img = soup.find('img', class_='profile-pic')
                    if img and img.get('src'):
                        result['profile_picture'] = img['src']
                    
                    logger.info(f"Twitter data collected for {username}")
                    return result
                except Exception:
                    return {'found': response.status_code == 200, 'platform': 'twitter', 'username': username}
            else:
                return {'found': False, 'platform': 'twitter', 'username': username}
        
        except Exception as e:
            logger.debug(f"Twitter data fetch failed: {e}")
            return {'found': False, 'platform': 'twitter', 'username': username, 'error': str(e)}

    def get_instagram_data(self, username):
        """Fetch Instagram profile metadata from public graph endpoint"""
        logger.info(f"Fetching detailed Instagram data for: {username}")
        try:
            # Instagram public API endpoint for basic profile info
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('data', {}).get('user', {})
                
                result = {
                    'found': True,
                    'platform': 'instagram',
                    'username': user_data.get('username', username),
                    'name': user_data.get('full_name'),
                    'bio': user_data.get('biography'),
                    'followers': user_data.get('edge_followed_by', {}).get('count', 0),
                    'following': user_data.get('edge_follow', {}).get('count', 0),
                    'verified': user_data.get('is_verified', False),
                    'website': user_data.get('external_url'),
                    'profile_picture': user_data.get('profile_pic_url_hd'),
                    'public_email': user_data.get('public_email')
                }
                
                logger.info(f"Instagram data collected for {username}")
                return result
            
            return {'found': response.status_code == 200, 'platform': 'instagram', 'username': username}
        
        except Exception as e:
            logger.debug(f"Instagram data fetch failed: {e}")
            return {'found': False, 'platform': 'instagram', 'username': username, 'error': str(e)}

    def get_linkedin_data(self, username):
        """Fetch LinkedIn profile data from public profile page"""
        logger.info(f"Fetching detailed LinkedIn data for: {username}")
        try:
            url = f"https://www.linkedin.com/in/{username}/"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                try:
                    # Extract from JSON-LD structured data
                    script = soup.find('script', {'type': 'application/ld+json'})
                    if script:
                        profile_data = json.loads(script.string)
                        
                        result = {
                            'found': True,
                            'platform': 'linkedin',
                            'username': username,
                            'name': profile_data.get('name'),
                            'headline': profile_data.get('jobTitle'),
                            'location': profile_data.get('address', {}).get('addressCountry'),
                            'profile_picture': profile_data.get('image'),
                            'description': profile_data.get('description')
                        }
                        
                        logger.info(f"LinkedIn data collected for {username}")
                        return result
                except Exception:
                    pass
                
                return {'found': True, 'platform': 'linkedin', 'username': username}
            
            return {'found': False, 'platform': 'linkedin', 'username': username}
        
        except Exception as e:
            logger.debug(f"LinkedIn data fetch failed: {e}")
            return {'found': False, 'platform': 'linkedin', 'username': username, 'error': str(e)}

    def get_tiktok_data(self, username):
        """Fetch TikTok profile metadata"""
        logger.info(f"Fetching detailed TikTok data for: {username}")
        try:
            # Use TikTok's public API endpoint
            url = f"https://api.tiktok.com/v1/user/@{username}/"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('user', {})
                
                result = {
                    'found': True,
                    'platform': 'tiktok',
                    'username': user_data.get('uniqueId', username),
                    'name': user_data.get('nickname'),
                    'bio': user_data.get('signature'),
                    'followers': user_data.get('followerCount', 0),
                    'following': user_data.get('followingCount', 0),
                    'verified': user_data.get('verified', False),
                    'video_count': user_data.get('videoCount', 0),
                    'profile_picture': user_data.get('avatarLarger'),
                    'website': user_data.get('webcast')
                }
                
                logger.info(f"TikTok data collected for {username}")
                return result
            
            return {'found': response.status_code == 200, 'platform': 'tiktok', 'username': username}
        
        except Exception as e:
            logger.debug(f"TikTok data fetch failed: {e}")
            return {'found': False, 'platform': 'tiktok', 'username': username, 'error': str(e)}

    def get_youtube_data(self, username):
        """Fetch YouTube channel data"""
        logger.info(f"Fetching detailed YouTube data for: {username}")
        try:
            # YouTube's public data endpoint
            url = f"https://www.youtube.com/@{username}/about"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract channel info from meta tags
                result = {
                    'found': True,
                    'platform': 'youtube',
                    'username': username,
                    'verified': False
                }
                
                # Try to get channel title from OG tags
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    result['name'] = og_title.get('content')
                
                og_image = soup.find('meta', property='og:image')
                if og_image:
                    result['profile_picture'] = og_image.get('content')
                
                og_desc = soup.find('meta', property='og:description')
                if og_desc:
                    result['description'] = og_desc.get('content')
                
                logger.info(f"YouTube data collected for {username}")
                return result
            
            return {'found': response.status_code == 200, 'platform': 'youtube', 'username': username}
        
        except Exception as e:
            logger.debug(f"YouTube data fetch failed: {e}")
            return {'found': False, 'platform': 'youtube', 'username': username, 'error': str(e)}


# Test mode
if __name__ == '__main__':
    scraper = OSINTScraper()
    
    # Test with a known username
    results = scraper.search_username('elonmusk')
    print("\n" + "="*60)
    print("PLATFORM SEARCH RESULTS:")
    print(json.dumps(results, indent=2))
    
    # Test detailed data gathering
    reddit_data = scraper.get_reddit_data('spez')
    github_data = scraper.get_github_data('torvalds')
    
    print("\n" + "="*60)
    print("DETAILED DATA SAMPLES:")
    print("\nReddit:", json.dumps(reddit_data, indent=2))
    print("\nGitHub:", json.dumps(github_data, indent=2))