"""Advanced email harvester utilities for investigation deep scans.

Provides multiple email harvesting strategies:
- Regex-based extraction from web content
- Hunter.io API integration (free & paid tiers)
- RocketReach API (optional)
- Website contact page scraping
- Email validation
- Multi-source aggregation

Robust fallback system ensures operation without APIs.
"""

import re
import logging
import requests
from typing import List, Set, Dict, Optional
from urllib.parse import urlparse, urljoin
import time
import os

logger = logging.getLogger(__name__)

# Advanced email regex patterns
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.I)
CONTACT_EMAIL_RE = re.compile(r'(?:contact|info|support|admin|hello|business|sales|hello)@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.I)
HIDDEN_EMAIL_RE = re.compile(r'(?:[a-zA-Z0-9._%+-]+\s*(?:\[at\]|@|\{at\})\s*[a-zA-Z0-9.-]+\s*(?:\[dot\]|\.|\{dot\})\s*[a-zA-Z]{2,})', re.I)


class EmailHarvester:
    """Advanced email harvester with multiple strategies and fallback mechanisms"""
    
    def __init__(self, hunter_api_key=None, rocket_reach_key=None):
        """
        Initialize harvester with optional API keys
        
        Args:
            hunter_api_key: Hunter.io API key (optional)
            rocket_reach_key: RocketReach API key (optional)
        """
        self.hunter_api_key = hunter_api_key or os.environ.get('HUNTER_API_KEY')
        self.rocket_reach_key = rocket_reach_key or os.environ.get('ROCKET_REACH_KEY')
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.timeout = 10
        self.common_contact_pages = [
            '/contact', '/contact-us', '/about', '/team', 
            '/company', '/about-us', '/support', '/help',
            '/careers', '/press', '/contact.html', '/about.html',
            '/people', '/staff', '/founders', '/leadership'
        ]
    
    def harvest_from_text(self, text: str) -> Set[str]:
        """Extract emails from text using multiple patterns"""
        if not text:
            return set()
        
        emails = set()
        
        # Standard email pattern
        for m in EMAIL_RE.findall(text):
            if self._validate_email(m):
                emails.add(m.lower())
        
        # Obfuscated emails (name [at] domain [dot] com)
        try:
            for m in HIDDEN_EMAIL_RE.findall(text):
                # Convert obfuscated to real
                real_email = m.replace('[at]', '@').replace('{at}', '@').replace('[dot]', '.').replace('{dot}', '.')
                if self._validate_email(real_email):
                    emails.add(real_email.lower())
        except Exception:
            pass
        
        # Try BeautifulSoup parsing for HTML attributes
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, 'html.parser')
            for tag in soup.find_all():
                for attr in ['data-email', 'data-contact', 'title', 'alt', 'aria-label']:
                    if tag.get(attr):
                        for m in EMAIL_RE.findall(str(tag.get(attr))):
                            if self._validate_email(m):
                                emails.add(m.lower())
        except Exception:
            pass
        
        return emails
    
    def _validate_email(self, email: str) -> bool:
        """
        Validate email format and reject common false positives
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not email or len(email) < 5 or email.count('@') != 1:
            return False
        
        # Reject placeholder emails
        false_positives = [
            'example@', '@example.', 'test@', '@test.',
            'placeholder@', 'noreply@', 'donotreply@',
            'fake@', '@localhost', '@127.0.0.1'
        ]
        
        email_lower = email.lower()
        for fp in false_positives:
            if fp in email_lower:
                return False
        
        # Basic format check
        username, domain = email.rsplit('@', 1)
        if len(username) < 1 or len(domain) < 3 or '.' not in domain:
            return False
        
        return True
    
    def harvest_from_html(self, html: str) -> Set[str]:
        """Extract emails from HTML with enhanced parsing"""
        return self.harvest_from_text(html)
    
    def harvest_from_url(self, url: str, timeout: Optional[int] = None) -> Set[str]:
        """Fetch URL and extract emails, with retry logic"""
        if not url:
            return set()
        
        timeout = timeout or self.timeout
        
        try:
            resp = requests.get(
                url, 
                timeout=timeout, 
                headers=self.headers,
                allow_redirects=True
            )
            if resp.status_code != 200:
                return set()
            
            return self.harvest_from_html(resp.text)
        
        except requests.exceptions.Timeout:
            logger.debug(f"Timeout harvesting {url}")
            return set()
        
        except requests.exceptions.ConnectionError:
            logger.debug(f"Connection error harvesting {url}")
            return set()
        
        except Exception as e:
            logger.debug(f"Error harvesting {url}: {e}")
            return set()
    
    def harvest_via_hunter_io(self, domain: str) -> Set[str]:
        """
        Use Hunter.io API to find emails
        Currently using free endpoints (email finder, domain search)
        
        Args:
            domain: Domain to search
            
        Returns:
            Set of found emails
        """
        if not domain:
            return set()
        
        try:
            emails = set()
            
            # Hunter.io domain search (free tier limited to 50/month)
            url = 'https://api.hunter.io/v2/domain-search'
            params = {'domain': domain}
            
            if self.hunter_api_key:
                params['domain_key'] = self.hunter_api_key
            
            resp = requests.get(url, params=params, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Extract emails from results
                for item in data.get('data', {}).get('emails', []):
                    email = item.get('value')
                    if email and self._validate_email(email):
                        emails.add(email.lower())
                
                logger.info(f"[HUNTER.IO] Found {len(emails)} emails for {domain}")
            else:
                logger.debug(f"[HUNTER.IO] Error: {resp.status_code}")
            
            return emails
            
        except Exception as e:
            logger.debug(f"Hunter.io harvesting error: {e}")
            return set()
    
    def harvest_via_rocketeach(self, domain: str) -> Set[str]:
        """
        Use RocketReach API for B2B email discovery
        Premium service, requires API key
        
        Args:
            domain: Domain to search
            
        Returns:
            Set of found emails
        """
        if not self.rocket_reach_key or not domain:
            return set()
        
        try:
            emails = set()
            
            url = 'https://api.rocketreach.co/v2/prospects/companies'
            headers = {
                'Authorization': f'Bearer {self.rocket_reach_key}',
                'X-API-Key': self.rocket_reach_key
            }
            params = {'domain': domain, 'limit': 100}
            
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                
                for person in data.get('data', {}).get('people', []):
                    email = person.get('email')
                    if email and self._validate_email(email):
                        emails.add(email.lower())
                
                logger.info(f"[ROCKETREACH] Found {len(emails)} emails for {domain}")
            else:
                logger.debug(f"[ROCKETREACH] Error: {resp.status_code}")
            
            return emails
            
        except Exception as e:
            logger.debug(f"RocketReach harvesting error: {e}")
            return set()
    
    def search_via_duckduckgo(self, domain: str, max_results: int = 50) -> Set[str]:
        """
        Use DuckDuckGo HTML search to find pages with domain emails
        """
        emails = set()
        
        try:
            if not domain:
                return emails
            
            # Multiple search queries for comprehensive coverage
            search_queries = [
                f'site:{domain} email OR mail',
                f'site:{domain} "contact"',
                f'site:{domain} info@ OR contact@ OR admin@',
                f'site:{domain} team OR staff',
            ]
            
            for query in search_queries:
                try:
                    search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
                    
                    resp = requests.get(
                        search_url, 
                        timeout=5, 
                        headers=self.headers
                    )
                    
                    if resp.status_code != 200:
                        continue
                    
                    # Parse results
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # Find links
                    links = set()
                    for a in soup.find_all('a', href=True):
                        href = a.get('href', '')
                        if domain in href and len(links) < 30:
                            links.add(href)
                    
                    # Harvest from found links
                    for link in links:
                        try:
                            found = self.harvest_from_url(link, timeout=3)
                            emails.update(found)
                            time.sleep(0.05)  # Small delay to avoid timeouts
                        except Exception:
                            pass
                
                except Exception:
                    continue
        
        except Exception as e:
            logger.debug(f"DuckDuckGo search error: {e}")
        
        return emails
    
    def harvest_from_common_pages(self, domain: str) -> Set[str]:
        """Check common contact and about pages"""
        emails = set()
        
        base_url = domain if domain.startswith('http') else f'https://{domain}'
        
        for page in self.common_contact_pages:
            try:
                url = f"{base_url.rstrip('/')}{page}"
                found = self.harvest_from_url(url, timeout=3)
                emails.update(found)
                time.sleep(0.01)
            except Exception:
                pass
        
        return emails
    
    def harvest_from_domain(self, domain: str, intensive: bool = False) -> Dict[str, any]:
        """
        Comprehensive domain email harvesting with multiple strategies and API integration
        
        Args:
            domain: Domain to harvest from
            intensive: If True, use all available methods including paid APIs
            
        Returns:
            Dict with results and metadata
        """
        result = {
            'domain': domain,
            'emails': set(),
            'sources': [],
            'count': 0,
            'confidence_scores': {}
        }
        
        if not domain:
            return result
        
        # Strategy 1: API-based harvesting (faster, more reliable)
        try:
            hunter_emails = self.harvest_via_hunter_io(domain)
            if hunter_emails:
                result['emails'].update(hunter_emails)
                result['sources'].append('hunter_io')
                for email in hunter_emails:
                    result['confidence_scores'][email] = 0.9  # High confidence
        except Exception as e:
            logger.debug(f"Hunter.io strategy failed: {e}")
        
        # Strategy 2: RocketReach (if key available and intensive mode)
        if intensive:
            try:
                rr_emails = self.harvest_via_rocketeach(domain)
                if rr_emails:
                    result['emails'].update(rr_emails)
                    result['sources'].append('rocketreach')
                    for email in rr_emails:
                        result['confidence_scores'][email] = 0.85
            except Exception as e:
                logger.debug(f"RocketReach strategy failed: {e}")
        
        # Strategy 3: Check common contact pages
        try:
            common_emails = self.harvest_from_common_pages(domain)
            if common_emails:
                result['emails'].update(common_emails)
                result['sources'].append('common_pages')
                for email in common_emails:
                    result['confidence_scores'].setdefault(email, 0.7)
        except Exception as e:
            logger.debug(f"Common pages harvest failed: {e}")
        
        # Strategy 4: Homepage
        try:
            homepage_url = domain if domain.startswith('http') else f'https://{domain}'
            homepage_emails = self.harvest_from_url(homepage_url)
            if homepage_emails:
                result['emails'].update(homepage_emails)
                result['sources'].append('homepage')
                for email in homepage_emails:
                    result['confidence_scores'].setdefault(email, 0.6)
        except Exception as e:
            logger.debug(f"Homepage harvest failed: {e}")
        
        # Strategy 5: DuckDuckGo search (comprehensive but slower)
        if intensive or len(result['emails']) < 5:
            try:
                search_emails = self.search_via_duckduckgo(domain)
                if search_emails:
                    result['emails'].update(search_emails)
                    result['sources'].append('duckduckgo')
                    for email in search_emails:
                        result['confidence_scores'].setdefault(email, 0.5)
            except Exception as e:
                logger.debug(f"DuckDuckGo harvest failed: {e}")
        
        # Finalize
        sorted_emails = sorted(
            result['emails'],
            key=lambda e: result['confidence_scores'].get(e, 0),
            reverse=True
        )
        result['emails'] = sorted_emails[:50]  # Top 50 emails
        result['count'] = len(result['emails'])
        
        logger.info(f"Harvested {result['count']} emails from {domain} using {len(result['sources'])} sources")
        
        return result

    
    def harvest_from_text(self, text: str) -> Set[str]:
        """Extract emails from text using multiple patterns"""
        if not text:
            return set()
        
        emails = set()
        
        # Standard email pattern
        for m in EMAIL_RE.findall(text):
            emails.add(m.lower())
        
        # Obfuscated emails (name [at] domain [dot] com)
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, 'html.parser')
            # Find common email patterns in HTML attributes
            for tag in soup.find_all():
                for attr in ['data-email', 'data-contact', 'title', 'alt', 'aria-label']:
                    if tag.get(attr):
                        for m in EMAIL_RE.findall(str(tag.get(attr))):
                            emails.add(m.lower())
        except Exception:
            pass
        
        return emails
    
    def harvest_from_html(self, html: str) -> Set[str]:
        """Extract emails from HTML with enhanced parsing"""
        return self.harvest_from_text(html)
    
    def harvest_from_url(self, url: str, timeout: Optional[int] = None) -> Set[str]:
        """Fetch URL and extract emails, with retry logic"""
        if not url:
            return set()
        
        timeout = timeout or self.timeout
        
        try:
            resp = requests.get(
                url, 
                timeout=timeout, 
                headers=self.headers,
                allow_redirects=True
            )
            if resp.status_code != 200:
                return set()
            
            return self.harvest_from_html(resp.text)
        
        except requests.exceptions.Timeout:
            logger.debug(f"Timeout harvesting {url}")
            return set()
        
        except requests.exceptions.ConnectionError:
            logger.debug(f"Connection error harvesting {url}")
            return set()
        
        except Exception as e:
            logger.debug(f"Error harvesting {url}: {e}")
            return set()
    
    def search_via_duckduckgo(self, domain: str, max_results: int = 200) -> Set[str]:
        """Use DuckDuckGo HTML search to find pages with domain emails - massively optimized for comprehensive coverage"""
        emails = set()
        
        try:
            if not domain:
                return emails
            
            # Expanded search queries for comprehensive coverage
            search_queries = [
                f'site:{domain} email OR mail OR contact',
                f'site:{domain} "contact us"',
                f'site:{domain} info@ OR contact@ OR support@ OR admin@ OR hello@',
                f'site:{domain} founder OR author OR created OR owner',
                f'site:{domain} team OR staff OR employees',
                f'site:{domain} business OR sales OR hello',
                f'site:{domain} newsletter OR subscribe',
            ]
            
            for query in search_queries:
                try:
                    search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
                    
                    resp = requests.get(
                        search_url, 
                        timeout=8, 
                        headers=self.headers
                    )
                    
                    if resp.status_code != 200:
                        continue
                    
                    # Parse results
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # Find links - massively increased to 100 for comprehensive search
                    links = set()
                    for a in soup.find_all('a', href=True):
                        href = a.get('href', '')
                        if domain in href and len(links) < 100:
                            links.add(href)
                    
                    # Harvest from found links - much faster with minimal delays
                    for link in links:
                        try:
                            found = self.harvest_from_url(link, timeout=5)
                            emails.update(found)
                            time.sleep(0.01)  # Ultra-minimal delay for fast harvesting
                        except Exception:
                            pass
                
                except Exception:
                    pass
        
        except Exception as e:
            logger.debug(f"DuckDuckGo search error: {e}")
        
        return emails
    
    def harvest_from_common_pages(self, domain: str) -> Set[str]:
        """Check common contact and about pages - massively expanded for better coverage"""
        emails = set()
        
        # Massively expanded list of common pages
        expanded_pages = [
            '/contact', '/contact-us', '/about', '/team', 
            '/company', '/about-us', '/support', '/help',
            '/careers', '/press', '/contact.html', '/about.html',
            '/people', '/staff', '/founders', '/leadership',
            '/contact/team', '/team/contact', '/collaborate',
            '/contributors', '/partners', '/investor',
            '/business', '/sales', '/hello', '/community',
            '/sponsors', '/team-members', '/members',
            '/get-in-touch', '/reach-us', '/connect',
            '/inquiries', '/request', '/feedback',
            '/partners/contact', '/partner-with-us',
            '/team-contact', '/our-team', '/our-staff',
            '/work-with-us', '/join-us', '/hiring'
        ]
        
        base_url = domain if domain.startswith('http') else f'https://{domain}'
        
        for page in expanded_pages:
            try:
                url = f"{base_url.rstrip('/')}{page}"
                found = self.harvest_from_url(url, timeout=5)
                emails.update(found)
                time.sleep(0.01)  # Ultra-minimal delay for fast parallel harvesting
            
            except Exception:
                pass
        
        return emails
    
    def harvest_from_domain(self, domain: str, intensive: bool = False) -> Dict[str, any]:
        """
        Comprehensive domain email harvesting with multiple strategies
        
        Args:
            domain: Domain to harvest from
            intensive: If True, performs more thorough but slower search
            
        Returns:
            Dict with results and metadata
        """
        result = {
            'domain': domain,
            'emails': set(),
            'sources': [],
            'count': 0
        }
        
        if not domain:
            return result
        
        # Strategy 1: Check common contact pages
        try:
            common_emails = self.harvest_from_common_pages(domain)
            if common_emails:
                result['emails'].update(common_emails)
                result['sources'].append('common_pages')
        except Exception as e:
            logger.debug(f"Common pages harvest failed: {e}")
        
        # Strategy 2: Homepage
        try:
            homepage_url = domain if domain.startswith('http') else f'https://{domain}'
            homepage_emails = self.harvest_from_url(homepage_url)
            if homepage_emails:
                result['emails'].update(homepage_emails)
                result['sources'].append('homepage')
        except Exception as e:
            logger.debug(f"Homepage harvest failed: {e}")
        
        # Strategy 3: DuckDuckGo search (if intensive or no results yet)
        if intensive or len(result['emails']) < 3:
            try:
                search_emails = self.search_via_duckduckgo(domain)
                if search_emails:
                    result['emails'].update(search_emails)
                    result['sources'].append('duckduckgo')
            except Exception as e:
                logger.debug(f"DuckDuckGo harvest failed: {e}")
        
        # Filter and count
        result['emails'] = list(result['emails'])
        result['count'] = len(result['emails'])
        
        logger.info(f"Harvested {result['count']} emails from {domain}")
        
        return result
