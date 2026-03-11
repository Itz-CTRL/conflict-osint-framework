"""AnalyserService wrapper
Provides `light_scan` and `deep_scan` used by the TaskManager.
Uses Sherlock for efficient platform checking, OSINTScraper for details,
BehaviorAnalyzer for risk scoring, and crawlers/email harvesters for deep scans.
"""

from services.scraper import OSINTScraper
from services.analyzer import BehaviorAnalyzer
from services.sherlock_checker import SherlockChecker
from services.crawler import BasicCrawler
from services.email_harvester import EmailHarvester
from database import db
from models import Finding, Investigation
import uuid
import json
import logging
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class AnalyserService:
    def __init__(self, investigation_id=None):
        self.investigation_id = investigation_id
        self.scraper = OSINTScraper()
        self.analyzer = BehaviorAnalyzer()

    def light_scan(self, username, filters=None):
        """Perform a light scan: use Sherlock for efficient parallel platform checking + BehaviorAnalyzer.
        Always checks all platforms regardless of filters.
        """
        try:
            # CRITICAL FIX: Normalize username - remove spaces, convert to valid username
            # "elon musk" -> "elonmusk", handles multi-word input by removing spaces
            username = username.strip().replace(' ', '').lower()
            logger.info(f"AnalyserService: starting light scan for {username} (normalized from user input)")
            
            # Light scan ALWAYS checks all platforms - filters don't restrict platform checking
            # They only control deep scan intensification
            # Use Sherlock for efficient parallel platform checking
            sherlock = SherlockChecker(timeout=8, max_workers=6)
            sherlock_results = sherlock.check_username(username)  # Check all platforms
            logger.info(f"Sherlock check completed: found on {sherlock_results.get('found', {}).get('count', 0)} sites")

            # Map Sherlock results to standard finding format
            platform_results = []
            if sherlock_results.get('found', {}).get('sites'):
                for site in sherlock_results['found']['sites']:
                    platform_results.append({
                        'platform': site['site'],
                        'url': site.get('profile_url') or site.get('url'),
                        'found': True,
                        'status_code': site.get('status_code', 200),
                        'confidence': 0.95
                    })

            results = {
                'username': username,
                'total_checked': len(sherlock.get_available_sites()),
                'found_count': len(platform_results),
                'platforms': platform_results,
                'errors': []
            }

            # Save platform findings to DB under the investigation if provided
            if self.investigation_id and platform_results:
                for p in platform_results:
                    try:
                        finding = Finding(
                            id=str(uuid.uuid4()),
                            investigation_id=self.investigation_id,
                            finding_type='platform',
                            platform=p.get('platform'),
                            found=bool(p.get('found')),
                            source=p.get('url', ''),
                            confidence=float(p.get('confidence', 0.95)),
                            data={
                                'url': p.get('url'), 
                                'platform': p.get('platform'),
                                'username': p.get('username', ''),
                                'profile_picture': p.get('profile_picture'),
                                'page_title': p.get('page_title'),
                                'status_code': p.get('status_code'),
                                'verified': p.get('verified', False)
                            }
                        )
                        db.session.add(finding)
                    except Exception as e:
                        logger.warning(f"Failed to save finding for platform {p.get('platform')}: {e}")
                try:
                    db.session.commit()
                except Exception as e:
                    logger.warning(f"Commit failed saving findings: {e}")
                    db.session.rollback()

            # Run analysis
            analysis = self.analyzer.analyze(username, results)

            return {
                'data': {
                    'username': username,
                    'platforms_checked': results.get('total_checked', 0),
                    'platforms_found': results.get('found_count', 0),
                    'analysis': analysis,
                    'errors': results.get('errors', [])
                },
                'graph': {'nodes': [], 'edges': []},
                'risk_score': float(analysis.get('risk_score', 0))
            }

        except Exception as e:
            logger.error(f"AnalyserService.light_scan error: {e}")
            return {'data': {'username': username, 'analysis': {'risk_score': 0, 'findings': [], 'analysis_error': str(e)}}, 'graph': {'nodes': [], 'edges': []}, 'risk_score': 0}

    def deep_scan(self, username, filters=None):
        """Perform a deep scan: Sherlock for platform detection, then advanced tools for comprehensive enrichment.
        Uses email harvesters, crawlers, spiders, scrapy for deep discovery.
        Finds mentions, related/similar usernames, and phone numbers.
        Filters control intensification, not restriction.
        """
        try:
            # CRITICAL FIX: Normalize username - remove spaces, convert to valid username
            # "elon musk" -> "elonmusk", handles multi-word input by removing spaces
            username = username.strip().replace(' ', '').lower()
            logger.info(f"AnalyserService: starting deep scan for {username} (normalized from user input)")
            
            # Parse filters for intensification (not restriction)
            filter_obj = None
            if filters:
                from services.filter_service import InvestigationFilter
                filter_obj = InvestigationFilter.from_dict(filters) if isinstance(filters, dict) else filters
                if not filter_obj.is_empty():
                    logger.info(f"Filters active for intensification: {filter_obj.to_dict()}")
            
            # ===== DEEP SCAN MAIN FLOW =====
            # PHASE 0: Start with light scan (Sherlock finds all platforms - this is the primary tool)
            result = self.light_scan(username, filters=filters)
            platforms_found = result.get('data', {}).get('analysis', {}).get('platform_presence', {}).get('found_on', [])
            logger.info(f"Sherlock found {len(platforms_found)} platforms for {username}: {platforms_found}")

            # Initialize deep data structure
            deep_data = {
                'emails': [],
                'mentions': [],
                'snippets': [],
                'platform_details': {},
                'crawled_urls': []
            }
            
            # PHASE 1: Platform-specific fetchers (for platforms where API/public data is accessible)
            # Only platforms where we have working fetchers: GitHub, Reddit, Twitter, YouTube, TikTok
            # Facebook, LinkedIn, Instagram are found by Sherlock but not directly scrapeable - they'll be crawled
            platform_fetchers = {
                'Reddit': self.scraper.get_reddit_data,
                'GitHub': self.scraper.get_github_data,
                'Twitter': self.scraper.get_twitter_data,
                'Twitter/X': self.scraper.get_twitter_data,
                'TikTok': self.scraper.get_tiktok_data,
                'YouTube': self.scraper.get_youtube_data,
            }
            
            logger.info(f"Phase 1: Fetching platform-specific data for accessible platforms")
            for platform in platforms_found:
                if platform in platform_fetchers:
                    try:
                        fetcher = platform_fetchers[platform]
                        platform_data = fetcher(username)
                        if platform_data and platform_data.get('found'):
                            deep_data['platform_details'][platform.lower().replace('/', '_')] = platform_data
                            logger.info(f"✓ {platform} detailed data collected")
                        else:
                            logger.debug(f"- {platform} found by Sherlock but no detailed data fetched")
                    except Exception as e:
                        logger.debug(f"✗ {platform} fetch failed (will try crawler): {e}")
                        # Continue to next platform - this is not blocking
                else:
                    # Platform found by Sherlock but no dedicated fetcher
                    # This includes: Facebook, LinkedIn, Instagram, Pinterest, Telegram, etc.
                    logger.info(f"- {platform} found by Sherlock (will be crawled by helper tools)")

            
            # PHASE 2: HELPER 1 - Crawl all profile URLs (Scrapy + BasicCrawler)
            logger.info(f"Phase 2: Crawling discovered profile URLs (Scrapy + BasicCrawler helpers)")
            try:
                # Build profile URLs from Sherlock results
                profile_urls = set()
                for platform in platforms_found:
                    # Construct profile URLs based on platform
                    p_lower = platform.lower().replace('/', '')
                    if 'github' in p_lower:
                        profile_urls.add(f'https://github.com/{username}')
                    elif 'reddit' in p_lower:
                        profile_urls.add(f'https://www.reddit.com/user/{username}')
                    elif 'twitter' in p_lower or 'x' in p_lower:
                        profile_urls.add(f'https://twitter.com/{username}')
                    elif 'instagram' in p_lower:
                        profile_urls.add(f'https://www.instagram.com/{username}')
                    elif 'facebook' in p_lower:
                        profile_urls.add(f'https://www.facebook.com/{username}')
                    elif 'linkedin' in p_lower:
                        profile_urls.add(f'https://www.linkedin.com/in/{username}')
                    elif 'tiktok' in p_lower:
                        profile_urls.add(f'https://www.tiktok.com/@{username}')
                    elif 'youtube' in p_lower:
                        profile_urls.add(f'https://www.youtube.com/@{username}')
                
                profile_urls = list(profile_urls)
                logger.info(f"Starting crawl on {len(profile_urls)} profile URLs")
                
                # Apply filter-based intensification
                crawler_max_pages = 40
                crawler_max_depth = 2
                if filter_obj and not filter_obj.is_empty():
                    intensity = 1.0 + (0.3 * sum([1 for f in [filter_obj.platform, filter_obj.location, filter_obj.account_type] if f]))
                    crawler_max_pages = int(40 * intensity * 2)
                    crawler_max_depth = min(4, int(2 * intensity))
                    logger.info(f"Intensified crawl: {crawler_max_pages} pages, depth {crawler_max_depth}")
                
                crawl_results = {'emails': [], 'mentions': [], 'snippets': [], 'urls_visited': []}
                
                # Helper 1A: Try Scrapy Spider first
                try:
                    from services.scrapy_runner import run_investigation_spider
                    logger.info(f"Using Scrapy Spider helper")
                    spider_results = run_investigation_spider(profile_urls, max_pages=crawler_max_pages)
                    if spider_results:
                        logger.info(f"Scrapy found {len(spider_results)} pages")
                        emails_col = set()
                        mentions_col = set()
                        for r in spider_results:
                            crawl_results['urls_visited'].append(r.get('url'))
                            for e in r.get('emails', []) or []:
                                emails_col.add(e.lower())
                            for m in r.get('mentions', []) or []:
                                mentions_col.add(m)
                        crawl_results['emails'] = list(emails_col)
                        crawl_results['mentions'] = list(mentions_col)
                        logger.info(f"✓ Scrapy: {len(crawl_results['emails'])} emails, {len(crawl_results['mentions'])} mentions")
                except Exception as e:
                    logger.info(f"Scrapy helper unavailable: {e}")
                
                # Helper 1B: Use BasicCrawler as fallback/supplement
                if profile_urls:
                    try:
                        logger.info(f"Using BasicCrawler helper as fallback")
                        crawler = BasicCrawler(max_pages=crawler_max_pages, delay=0.1, allowed_domains=None)
                        basic_results = crawler.crawl(profile_urls, max_depth=crawler_max_depth)
                        # Merge results
                        crawl_results['emails'] = list(set(crawl_results['emails'] + basic_results.get('emails', [])))
                        crawl_results['mentions'] = list(set(crawl_results['mentions'] + basic_results.get('mentions', [])))
                        crawl_results['urls_visited'] = list(set(crawl_results['urls_visited'] + basic_results.get('urls_visited', [])))
                        logger.info(f"✓ BasicCrawler: total {len(crawl_results['emails'])} emails, {len(crawl_results['mentions'])} mentions")
                    except Exception as e:
                        logger.warning(f"BasicCrawler also failed: {e} (continuing with what we have)")
                
                deep_data['emails'].extend(crawl_results.get('emails', []))
                deep_data['mentions'].extend(crawl_results.get('mentions', []))
                deep_data['crawled_urls'].extend(crawl_results.get('urls_visited', []))
                
            except Exception as e:
                logger.warning(f"Crawler phase error: {e} (continuing without crawl results)")
            
            # PHASE 3: HELPER 2 - Email Harvesting from crawled domains
            logger.info(f"Phase 3: Email harvesting helper from discovered domains")
            try:
                harvester = EmailHarvester()
                harvest_urls = deep_data.get('crawled_urls', [])
                
                # Apply filter-based intensification to email harvesting
                email_harvest_limit = 10
                email_intensive = False
                if filter_obj and not filter_obj.is_empty():
                    intensity = 1.0 + (0.3 * sum([1 for f in [filter_obj.platform, filter_obj.location, filter_obj.account_type] if f]))
                    email_harvest_limit = int(15 * intensity)
                    email_intensive = True
                    logger.info(f"Intensified harvest: {email_harvest_limit} domains, intensive={email_intensive}")
                
                harvested_emails = set(deep_data.get('emails', []) or [])
                harvested_count = 0
                
                for url in harvest_urls[:email_harvest_limit]:
                    try:
                        domain = urlparse(url).netloc
                        if domain:
                            result = harvester.harvest_from_domain(domain, intensive=email_intensive)
                            new_emails = result.get('emails', [])
                            harvested_emails.update(new_emails)
                            harvested_count += len(new_emails)
                            if new_emails:
                                logger.debug(f"Harvested {len(new_emails)} emails from {domain}")
                    except Exception as e:
                        logger.debug(f"Email harvest from {url} skipped: {e}")
                        # Continue - don't let one domain failure block others
                        continue
                
                deep_data['emails'] = list(harvested_emails)
                logger.info(f"✓ Email harvester: found {harvested_count} emails across domains")
                    
            except Exception as e:
                logger.warning(f"Email harvesting phase error: {e} (continuing with existing emails)")

            # Enhance analysis with deep_data
            try:
                enhanced = self.analyzer.analyze(username, result['data'].get('analysis', {}), detailed_data=deep_data)
                result['data']['analysis'] = enhanced
                result['risk_score'] = float(enhanced.get('risk_score', result.get('risk_score', 0)))
                logger.info(f"Enhanced analysis complete: risk_score={result['risk_score']}")
            except Exception as e:
                logger.debug(f"Enhancing analysis failed: {e}")

            # Save deep findings (emails/mentions) to DB
            if self.investigation_id:
                try:
                    # Save emails as findings
                    for email in deep_data.get('emails', [])[:40]:
                        try:
                            f = Finding(
                                id=str(uuid.uuid4()),
                                investigation_id=self.investigation_id,
                                finding_type='email',
                                platform='email',
                                found=True,
                                source=email,
                                confidence=0.5,
                                data={'email': email}
                            )
                            db.session.add(f)
                        except Exception:
                            continue

                    # Save mentions as findings
                    for mention in deep_data.get('mentions', [])[:80]:
                        try:
                            f = Finding(
                                id=str(uuid.uuid4()),
                                investigation_id=self.investigation_id,
                                finding_type='mention',
                                platform='web',
                                found=True,
                                source=mention,
                                confidence=0.4,
                                data={'mention': mention}
                            )
                            db.session.add(f)
                        except Exception:
                            continue

                    db.session.commit()
                    logger.info(f"Deep findings saved: {len(deep_data.get('emails', []))} emails, {len(deep_data.get('mentions', []))} mentions")
                except Exception as e:
                    logger.warning(f"Failed to save deep findings: {e}")
                    db.session.rollback()
            
            # Extract related usernames and phone numbers from mentions and deep data
            try:
                logger.info(f"Extracting related usernames and phone numbers for {username}")
                
                # Get all mentions and emails for analysis
                all_text = ' '.join(deep_data.get('mentions', []) + deep_data.get('emails', []) + 
                                   [str(d) for d in deep_data.values() if isinstance(d, (str, dict))])
                
                # Extract phone numbers
                import re
                phone_pattern = re.compile(r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
                phones = list(set(phone_pattern.findall(all_text)))
                
                # Extract mentions of other usernames (@username pattern)
                mention_pattern = re.compile(r'@([A-Za-z0-9_\.-]+)')
                related_usernames = list(set(mention_pattern.findall(all_text)))
                
                # Remove the original username from related usernames
                related_usernames = [u for u in related_usernames if u.lower() != username.lower()]
                
                # Save phone numbers as findings
                for phone in phones[:30]:
                    try:
                        f = Finding(
                            id=str(uuid.uuid4()),
                            investigation_id=self.investigation_id,
                            finding_type='phone',
                            platform='web',
                            found=True,
                            source=phone,
                            confidence=0.3,
                            data={'phone': phone}
                        )
                        db.session.add(f)
                    except Exception:
                        continue
                
                # Save related usernames as findings
                for related in related_usernames[:50]:
                    try:
                        f = Finding(
                            id=str(uuid.uuid4()),
                            investigation_id=self.investigation_id,
                            finding_type='related_username',
                            platform='web',
                            found=True,
                            source=related,
                            confidence=0.3,
                            data={'related_username': related, 'mentioned_in_profiles': True}
                        )
                        db.session.add(f)
                    except Exception:
                        continue
                
                try:
                    db.session.commit()
                    logger.info(f"Extracted {len(phones)} phone numbers and {len(related_usernames)} related usernames")
                except Exception as e:
                    logger.warning(f"Failed to save extracted data: {e}")
                    db.session.rollback()
            
            except Exception as e:
                logger.debug(f"Error extracting usernames/phones: {e}")

            return result

        except Exception as e:
            logger.error(f"AnalyserService.deep_scan error: {e}")
            return {'data': {'username': username, 'analysis': {'risk_score': 0, 'findings': [], 'analysis_error': str(e)}}, 'graph': {'nodes': [], 'edges': []}, 'risk_score': 0}
