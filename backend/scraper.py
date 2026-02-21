import requests
from bs4 import BeautifulSoup  # beautifulsoup4 package required: pip install beautifulsoup4
from datetime import datetime
import json

class OSINTScraper:
    """
    Web scraper for OSINT investigations across social media platforms
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def check_platform(self, platform, url, username):
        """
        Check if a username exists on a given platform
        Returns data including profile picture if available
        """
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
                'profile_picture': None
            }

            if found:
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
                
                print(f"  ✓ Found on {platform}: {url}")
                if profile_pic:
                    print(f"    📸 Profile picture found")
            else:
                print(f"  ✗ Not found on {platform}")

            return data

        except requests.exceptions.Timeout:
            print(f"  ⚠ Timeout on {platform}")
            return {
                'platform': platform,
                'username': username,
                'url': url,
                'found': False,
                'error': 'timeout',
                'profile_picture': None
            }
        except Exception as e:
            print(f"  ⚠ Error on {platform}: {str(e)}")
            return {
                'platform': platform,
                'username': username,
                'url': url,
                'found': False,
                'error': str(e),
                'profile_picture': None
            }

    def search_username(self, username):
        """
        Search for a username across multiple social media platforms
        Returns comprehensive data about where the username exists
        """
        print(f"\n🔍 Searching for username: '{username}'")
        print("=" * 60)

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
            'platforms': []
        }

        for platform, url in platforms:
            result = self.check_platform(platform, url, username)
            results['platforms'].append(result)
            if result.get('found'):
                results['found_count'] += 1

        print(f"\n📊 Results: Found on {results['found_count']}/{results['total_checked']} platforms")
        return results

    def get_reddit_data(self, username):
        """
        Get detailed Reddit profile data using their public JSON API
        """
        print(f"\n📱 Getting detailed Reddit data for: {username}")

        try:
            # Reddit provides free JSON endpoints
            url = f"https://www.reddit.com/user/{username}/about.json"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                return {'found': False, 'error': f'Status {response.status_code}'}

            data = response.json()['data']

            # Get recent posts
            posts_url = f"https://www.reddit.com/user/{username}.json?limit=5"
            posts_response = requests.get(posts_url, headers=self.headers, timeout=10)
            posts = []

            if posts_response.status_code == 200:
                for item in posts_response.json()['data']['children']:
                    p = item['data']
                    posts.append({
                        'content': p.get('title', p.get('body', ''))[:200],
                        'subreddit': p.get('subreddit', 'unknown'),
                        'score': p.get('score', 0),
                        'created': datetime.fromtimestamp(
                            p['created_utc']
                        ).strftime('%Y-%m-%d %H:%M')
                    })

            result = {
                'found': True,
                'platform': 'reddit',
                'username': data.get('name'),
                'account_age': datetime.fromtimestamp(
                    data['created_utc']
                ).strftime('%Y-%m-%d'),
                'karma': data.get('total_karma', 0),
                'verified': data.get('verified', False),
                'recent_posts': posts,
                'profile_picture': data.get('icon_img', '').split('?')[0] if data.get('icon_img') else None
            }

            print(f"  ✓ Reddit data collected")
            return result

        except Exception as e:
            print(f"  ✗ Reddit error: {str(e)}")
            return {'found': False, 'error': str(e)}

    def get_github_data(self, username):
        """
        Get detailed GitHub profile data using their free public API
        """
        print(f"\n💻 Getting detailed GitHub data for: {username}")

        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
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

            print(f"  ✓ GitHub data collected")
            return result

        except Exception as e:
            print(f"  ✗ GitHub error: {str(e)}")
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