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
        self.max_retries = 2
        self.retry_delay = 1  # seconds

    def check_platform(self, platform, url, username):
        """
        Check if a username exists on a given platform.
        Returns data including profile picture if available.
        Includes retry logic for transient failures.
        """
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=8)
                found = response.status_code == 200

                data = {
                    'platform': platform,
                    'username': username,
                    'url': url,
                    'found': found,
                    'status_code': response.status_code,
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

        # Platform URLs to check
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