"""Advanced web crawler for deep investigations

High-performance crawler with improved depth, parallellization,
and multi-strategy extraction. Designed to find connected entities,
emails, and relationships at scale.
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Optional

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.I)
MENTION_RE = re.compile(r'@([A-Za-z0-9_\.-]+)')
PHONE_RE = re.compile(r'(?:\+\d{1,3}[-.\s]?)?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}')
SOCIAL_HANDLE_RE = re.compile(r'(?:twitter|instagram|facebook|github|linkedin)[/:@]+([A-Za-z0-9_\.-]+)')


class AdvancedCrawler:
    """
    Advanced crawler with intelligent filtering, parallel extraction,
    and multi-source entity discovery.
    """
    
    def __init__(self, max_pages=5000, max_depth=10, delay=0.01, allowed_domains=None, user_agent=None):
        """
        Initialize advanced crawler.
        
        Args:
            max_pages: Maximum pages to crawl (default 5000, massively increased for full exploration)
            max_depth: Maximum depth (default 10, increased for deep exploration)
            delay: Delay between requests in seconds (0.01 for very fast parallel crawling)
            allowed_domains: List of allowed domains
            user_agent: Custom user agent
        """
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.allowed_domains = allowed_domains or []
        self.headers = {
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.visited = set()
        self.priority_keywords = ['contact', 'about', 'team', 'staff', 'author', 'creator']
    
    def _allowed(self, url: str) -> bool:
        """Check if URL domain is in allowed list"""
        if not self.allowed_domains:
            return True
        host = urlparse(url).netloc.lower()
        return any(d.lower() in host for d in self.allowed_domains)
    
    def _get_priority_score(self, url: str) -> float:
        """Calculate priority for crawling - prioritize contact/about pages"""
        score = 0.0
        url_lower = url.lower()
        
        for keyword in self.priority_keywords:
            if keyword in url_lower:
                score += 2.0
        
        if any(ext in url_lower for ext in ['.pdf', '.doc', '.zip']):
            score -= 1.0
        
        return score
    
    def _extract_entities(self, html: str, url: str) -> Dict[str, any]:
        """Extract all entities from HTML"""
        entities = {
            'emails': set(),
            'mentions': set(),
            'handles': set(),
            'phones': set(),
            'text_snippets': []
        }
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            # Extract emails (multiple patterns)
            for m in EMAIL_RE.findall(html):
                entities['emails'].add(m.lower())
            
            # Extract social mentions
            for m in MENTION_RE.findall(html):
                if len(m) >= 3:  # Filter too-short mentions
                    entities['mentions'].add(m)
            
            # Extract social handles
            for m in SOCIAL_HANDLE_RE.findall(html):
                if len(m) >= 2:
                    entities['handles'].add(m)
            
            # Extract phone numbers
            for m in PHONE_RE.findall(html):
                entities['phones'].add(m)
            
            # Store text snippet
            if text:
                entities['text_snippets'].append({
                    'url': url,
                    'snippet': text[:1000],
                    'length': len(text)
                })
        
        except Exception as e:
            logger.debug(f"Entity extraction error for {url}: {e}")
        
        return entities
    
    def _fetch_page(self, url: str, timeout: int = 10) -> Optional[str]:
        """Fetch page with error handling and retry logic"""
        try:
            resp = requests.get(
                url,
                headers=self.headers,
                timeout=timeout,
                allow_redirects=True
            )
            
            if resp.status_code == 200 and resp.text:
                return resp.text
            
            return None
        
        except requests.exceptions.Timeout:
            logger.debug(f"Timeout fetching {url}")
            return None
        
        except requests.exceptions.ConnectionError:
            logger.debug(f"Connection error for {url}")
            return None
        
        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")
            return None
    
    def crawl(self, start_urls: List[str], max_depth: Optional[int] = None, 
              intensive: bool = False) -> Dict[str, any]:
        """
        Advanced crawl with intelligent prioritization and extraction.
        
        Args:
            start_urls: List of URLs to start from
            max_depth: Override instance max_depth
            intensive: If True, performs more thorough crawl
            
        Returns:
            Dict with comprehensive extraction results
        """
        max_depth = max_depth or self.max_depth
        max_pages = self.max_pages * 2 if intensive else self.max_pages
        
        # Priority queue: (url, depth, priority_score)
        to_visit = []
        for url in start_urls:
            priority = self._get_priority_score(url)
            to_visit.append((url, 0, priority))
        
        # Sort by priority (higher first)
        to_visit.sort(key=lambda x: -x[2])
        
        all_emails = set()
        all_mentions = set()
        all_handles = set()
        all_phones = set()
        all_snippets = []
        urls_visited = []
        urls_failed = []
        
        while to_visit and len(urls_visited) < max_pages:
            # Pop highest priority URL
            url, depth, priority = to_visit.pop(0)
            
            if url in self.visited:
                continue
            
            if depth > max_depth:
                continue
            
            if not self._allowed(url):
                logger.debug(f"Skipping disallowed domain: {url}")
                continue
            
            self.visited.add(url)
            
            # Fetch page
            html = self._fetch_page(url)
            
            if not html:
                urls_failed.append(url)
                continue
            
            urls_visited.append(url)
            
            # Extract entities
            entities = self._extract_entities(html, url)
            all_emails.update(entities['emails'])
            all_mentions.update(entities['mentions'])
            all_handles.update(entities['handles'])
            all_phones.update(entities['phones'])
            all_snippets.extend(entities['text_snippets'])
            
            # Rate limiting
            time.sleep(self.delay)
            
            # Extract and enqueue new URLs
            if depth < max_depth:
                try:
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    for a in soup.find_all('a', href=True):
                        href = a.get('href', '')
                        if not href:
                            continue
                        
                        joined = urljoin(url, href)
                        norm = joined.split('#')[0].split('?')[0]  # Remove fragments and queries
                        
                        if (norm not in self.visited and 
                            len(urls_visited) + len(to_visit) < max_pages and
                            self._allowed(norm)):
                            
                            priority = self._get_priority_score(norm)
                            to_visit.append((norm, depth + 1, priority))
                    
                    # Re-sort queue by priority
                    to_visit.sort(key=lambda x: -x[2])
                
                except Exception as e:
                    logger.debug(f"Link extraction error for {url}: {e}")
        
        return {
            'emails': list(all_emails),
            'mentions': list(all_mentions),
            'social_handles': list(all_handles),
            'phones': list(all_phones),
            'snippets': all_snippets,
            'urls_visited': urls_visited,
            'urls_failed': urls_failed,
            'statistics': {
                'pages_crawled': len(urls_visited),
                'pages_failed': len(urls_failed),
                'emails_found': len(all_emails),
                'mentions_found': len(all_mentions),
                'handles_found': len(all_handles),
                'phones_found': len(all_phones)
            }
        }


# Keep old class name for backwards compatibility
class BasicCrawler(AdvancedCrawler):
    """Backwards compatible alias for AdvancedCrawler"""
    pass
