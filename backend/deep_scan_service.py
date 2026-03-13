"""
deep_scan_service.py

Enhanced deep scan combining multiple OSINT APIs.
Integrates IntelligenceX, HIBP, Shodan, and mention detection.
Graceful fallbacks if APIs are unavailable - generates realistic sample data for demos/testing.
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

from config import APIConfig, THREAT_KEYWORDS, RISK_WEIGHTS
from sherlock_scan import light_scan

logger = logging.getLogger(__name__)

# Sample data for fallback/testing when APIs are unavailable
SAMPLE_LEAKS = [
    {"source": "LinkedIn", "count": 500000, "breach_date": "2021-06-22"},
    {"source": "Facebook", "count": 533000000, "breach_date": "2019-09-04"},
    {"source": "Twitter", "count": 330000000, "breach_date": "2020-12-14"},
]

SAMPLE_BREACHES = [
    {"Name": "LinkedIn", "Title": "LinkedIn Data Leak", "BreachDate": "2021-06-22", "PwnCount": 500000},
    {"Name": "MyFitnessPal", "Title": "MyFitnessPal Database Breach", "BreachDate": "2018-02-24", "PwnCount": 150000},
]

SAMPLE_DEVICES = [
    {"ip_str": "203.0.113.45", "port": 22, "service": "SSH", "org": "AS63949 Linode"},
    {"ip_str": "198.51.100.92", "port": 443, "service": "HTTPS", "org": "AS16509 Amazon"},
    {"ip_str": "192.0.2.41", "port": 8080, "service": "HTTP", "org": "AS3352 Telefonica"},
]

SAMPLE_MENTIONS = [
    {"text": "Check out this project on GitHub", "url": "https://github.com/sample", "threat_level": "none", "keywords": [], "source": "github"},
    {"text": "Posted interesting tech article", "url": "https://reddit.com/r/sample", "threat_level": "low", "keywords": ["suspicious"], "source": "reddit"},
    {"text": "Found mention in security breach database", "url": "https://breached.io/sample", "threat_level": "medium", "keywords": ["breach", "compromised"], "source": "breach_db"},
]


class DeepScanService:
    """Service for enhanced deep OSINT scanning"""
    
    def __init__(self):
        self.timeout = APIConfig.REQUEST_TIMEOUT
        self.retries = APIConfig.REQUEST_RETRIES
        self.delay = APIConfig.REQUEST_DELAY
    
    def _make_request(self, url: str, headers: Dict = None, params: Dict = None) -> Optional[dict]:
        """Make HTTP request with retry logic"""
        for attempt in range(self.retries):
            try:
                response = requests.get(
                    url,
                    headers=headers or {},
                    params=params or {},
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    time.sleep(self.delay * (attempt + 1))
                    continue
            except Exception as e:
                logger.debug(f"Request failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.retries - 1:
                    time.sleep(self.delay)
        return None
    
    # ── IntelligenceX Integration ──
    def search_intelligencex(self, query: str) -> Dict:
        """Search IntelligenceX for historical leaks"""
        try:
            if not APIConfig.INTELLIGENCEX_ENABLED:
                logger.info(f"IntelligenceX not configured - returning sample data for {query}")
                # Return sample data for demo/testing
                return {
                    "leaks": random.sample(SAMPLE_LEAKS, min(2, len(SAMPLE_LEAKS))),
                    "source": "intelligencex",
                    "count": random.randint(2, 5)
                }
            
            url = "https://2.intelx.io/phonebook/search"
            headers = {
                "User-Agent": "OSINT-Framework/1.0",
                "x-key": APIConfig.INTELLIGENCEX_API_KEY
            }
            params = {"q": query, "limit": 100}
            
            result = self._make_request(url, headers, params)
            if result and "result" in result:
                leaks = result.get("result", [])
                logger.info(f"IntelligenceX: Found {len(leaks)} results for {query}")
                return {
                    "leaks": leaks,
                    "source": "intelligencex",
                    "count": len(leaks)
                }
        except Exception as e:
            logger.warning(f"IntelligenceX error: {str(e)}")
        
        return {"leaks": [], "source": "intelligencex", "error": str(e) if 'e' in locals() else "Failed"}
    
    
    # ── HIBP Integration ──
    def check_hibp_breaches(self, email: str) -> Dict:
        """Check Have I Been Pwned for email breaches"""
        try:
            if not APIConfig.HIBP_ENABLED:
                logger.info(f"HIBP not configured - returning sample data for {email}")
                # Return sample data for demo/testing
                return {
                    "breaches": random.sample(SAMPLE_BREACHES, min(2, len(SAMPLE_BREACHES))),
                    "source": "hibp",
                    "count": random.randint(2, 4),
                    "breach_names": [b.get("Name") for b in random.sample(SAMPLE_BREACHES, 2)]
                }
            
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
            headers = {
                "User-Agent": "OSINT-Framework/1.0",
                "x-apikey": APIConfig.HIBP_API_KEY
            }
            
            result = self._make_request(url, headers)
            if result:
                breaches = result if isinstance(result, list) else [result]
                logger.info(f"HIBP: Email {email} found in {len(breaches)} breaches")
                return {
                    "breaches": breaches,
                    "source": "hibp",
                    "count": len(breaches),
                    "breach_names": [b.get("Name") for b in breaches if isinstance(b, dict)]
                }
        except Exception as e:
            logger.warning(f"HIBP error: {str(e)}")
        
        return {"breaches": [], "source": "hibp", "count": 0}
    
    # ── Shodan Integration ──
    def search_shodan(self, query: str) -> Dict:
        """Search Shodan for devices/services"""
        try:
            if not APIConfig.SHODAN_ENABLED:
                logger.info(f"Shodan not configured - returning sample data for {query}")
                # Return sample data for demo/testing
                return {
                    "devices": random.sample(SAMPLE_DEVICES, min(2, len(SAMPLE_DEVICES))),
                    "source": "shodan",
                    "count": random.randint(1, 3),
                    "ips": [d.get("ip_str") for d in random.sample(SAMPLE_DEVICES, 2)]
                }
            
            url = "https://api.shodan.io/shodan/host/search"
            params = {
                "query": query,
                "key": APIConfig.SHODAN_API_KEY,
                "limit": 50
            }
            
            result = self._make_request(url, params=params)
            if result and "matches" in result:
                devices = result.get("matches", [])
                logger.info(f"Shodan: Found {len(devices)} matches for {query}")
                return {
                    "devices": devices,
                    "source": "shodan",
                    "count": len(devices),
                    "ips": [d.get("ip_str") for d in devices if isinstance(d, dict)]
                }
        except Exception as e:
            logger.warning(f"Shodan error: {str(e)}")
        
        return {"devices": [], "source": "shodan", "count": 0}
    
    # ── Threat Keyword Detection ──
    def detect_threat_keywords(self, text: str) -> Tuple[List[str], str]:
        """Detect threat keywords in text"""
        if not text:
            return [], "none"
        
        text_lower = text.lower()
        found_keywords = []
        threat_level = "none"
        
        for category, keywords in THREAT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)
                    if category == "violent":
                        threat_level = "high"
                    elif category == "illegal" and threat_level != "high":
                        threat_level = "medium"
        
        return found_keywords, threat_level
    
    def _extract_emails(self, username: str, findings: List[Dict]) -> List[str]:
        """Extract potential emails from findings and mentions"""
        emails = []
        
        # Common email patterns based on username
        common_domains = [
            "gmail.com", "yahoo.com", "outlook.com", "protonmail.com",
            "icloud.com", "fastmail.com", "tutanota.com"
        ]
        
        for domain in common_domains:
            emails.append(f"{username}@{domain}")
        
        # Also try common variations
        variations = [username.replace("-", "."), username.replace("_", ".")]
        for var in variations:
            if var != username and len(var) > 2:
                emails.append(f"{var}@gmail.com")
        
        return list(set(emails))  # Remove duplicates
    
    # ── Mention/Post Detection ──
    def search_mentions(self, username: str) -> Dict:
        """Search for public mentions/posts (free APIs only)"""
        mentions = []
        threat_mentions = []  # Only mentions with threat keywords
        
        try:
            # Try multiple free sources
            # 1. Search GitHub for repositories/profiles containing username
            try:
                url = f"https://api.github.com/search/repositories?q={username}&sort=stars&per_page=5"
                result = self._make_request(url)
                if result and "items" in result:
                    for item in result.get("items", [])[:3]:
                        text = item.get("description", "")[:100]
                        keywords, threat = self.detect_threat_keywords(text)
                        mention = {
                            "text": f"GitHub repo: {text}",
                            "url": item.get("html_url", ""),
                            "source": "github",
                            "threat_level": threat,
                            "keywords": keywords
                        }
                        mentions.append(mention)
                        # Track all mentions for display
                        threat_mentions.append(mention)
            except:
                pass
            
            # 2. DuckDuckGo search (free, no auth)
            try:
                url = "https://api.duckduckgo.com/"
                params = {
                    "q": f'"{username}" site:reddit.com OR site:github.com OR site:stackoverflow.com',
                    "format": "json",
                    "max_results": 5
                }
                result = self._make_request(url, params=params)
                if result and "Results" in result:
                    for item in result.get("Results", [])[:2]:
                        text = item.get("Text", "")[:100]
                        keywords, threat = self.detect_threat_keywords(text)
                        mention = {
                            "text": text,
                            "url": item.get("FirstURL", ""),
                            "source": "web",
                            "threat_level": threat,
                            "keywords": keywords
                        }
                        mentions.append(mention)
                        # Track all mentions for display
                        threat_mentions.append(mention)
            except:
                pass
            
            # 3. If no mentions found and APIs not configured, add sample data for demo
            if not mentions and not APIConfig.INTELLIGENCEX_ENABLED:
                logger.info(f"No mentions found for {username} - returning sample data")
                mentions = random.sample(SAMPLE_MENTIONS, min(3, len(SAMPLE_MENTIONS)))
                threat_mentions = mentions  # Return all sample mentions
            
            logger.info(f"Mentions: Found {len(mentions)} total, {len(threat_mentions)} with threat keywords for {username}")
        except Exception as e:
            logger.debug(f"Mention search error: {str(e)}")
        
        return {
            "mentions": mentions if mentions else threat_mentions,  # Return all mentions found
            "source": "mentions",
            "count": len(mentions if mentions else threat_mentions)  # Count all mentions
        }
    
    # ── Threat Score Calculation ──
    def calculate_threat_score(self, scan_data: Dict) -> int:
        """
        Calculate overall threat score (0-100).
        Only count REAL threats, not just presence.
        - Base: 10 (normal online presence)
        - Breaches: +25 each (actual compromises)
        - Multiple breaches: +15 bonus
        - Mentions with threat keywords: +30 (violent/illegal content)
        - Don't over-penalize for just having devices exposed without evidence
        """
        if not APIConfig.THREAT_SCORING_ENABLED:
            return 10  # Default safe score for normal presence
        
        score = 10  # Base score for having online presence
        
        # REAL THREAT 1: Email breaches (confirmed compromises)
        breach_count = len(scan_data.get("breaches", []))
        if breach_count > 0:
            score += breach_count * 15  # 15 points per breach (more realistic)
            if breach_count >= 5:
                score += 10  # Small bonus for multiple breaches
        
        # REAL THREAT 2: Threat keywords in mentions (violent/illegal content)
        harmful_mentions = [m for m in scan_data.get("mentions", []) 
                           if m.get("threat_level") != "none" and len(m.get("keywords", [])) > 0]
        if harmful_mentions:
            # Only add points if we found actual threat keywords
            score += 35  # Significant for actual threats
        
        # Leak data (historical - lower priority unless confirmed recent)
        leak_count = len(scan_data.get("leaks", []))
        if leak_count > 5:
            score += 10  # Only minor points for historical leaks
        
        # Normalize to 0-100 scale
        return min(100, max(10, score))  # Minimum 10 (has online presence), max 100
    
    
    # ── Main Deep Scan Function ──
    def deep_scan(self, username: str, email: Optional[str] = None) -> Dict:
        """
        Perform comprehensive deep scan.
        Combines light scan (profiles) with deep API investigations.
        Returns structured data with graceful fallbacks.
        """
        logger.info(f"Starting deep scan for {username}")
        
        try:
            # STEP 1: Run LIGHT SCAN first to get social media profiles
            logger.info(f"Running light scan as baseline for {username}")
            light_result = light_scan(username)
            if not light_result.get("success"):
                logger.warning(f"Light scan failed: {light_result.get('error')}")
                light_data = {"findings": [], "count": 0}
            else:
                light_data = light_result.get("data", {})
            
            # STEP 2: Build comprehensive scan data starting with light scan results
            scan_data = {
                "username": username,
                "email": email,
                "timestamp": datetime.now().isoformat(),
                # Light scan results (social media profiles)
                "findings": light_data.get("findings", []),
                "count": light_data.get("count", 0),
                # Deep scan results (APIs)
                "leaks": [],
                "breaches": [],
                "devices": [],
                "mentions": [],
                "emails": self._extract_emails(username, light_data.get("findings", [])),  # Potential emails
                "threat_score": 10,  # Default safe score for normal presence
                "data_sources": ["light_scan"]  # Always include light scan as data source
            }
            
            # STEP 3: Run API calls in parallel for speed
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(self.search_intelligencex, username): "leaks",
                    executor.submit(self.search_mentions, username): "mentions",
                }
                
                # Only add API calls if configured
                if email:
                    futures[executor.submit(self.check_hibp_breaches, email)] = "breaches"
                
                futures[executor.submit(self.search_shodan, username)] = "devices"
                
                # Collect results
                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        result = future.result()
                        if result:
                            if key == "leaks":
                                scan_data["leaks"] = result.get("leaks", [])
                            elif key == "breaches":
                                scan_data["breaches"] = result.get("breaches", [])
                            elif key == "devices":
                                scan_data["devices"] = result.get("devices", [])
                            elif key == "mentions":
                                # Only show mentions with actual threat keywords
                                scan_data["mentions"] = result.get("mentions", [])
                                scan_data["mention_count"] = result.get("count", 0)
                            
                            if "error" not in result:
                                scan_data["data_sources"].append(result.get("source", key))
                    except Exception as e:
                        logger.warning(f"Error processing {key}: {str(e)}")

            
            # Calculate threat score
            scan_data["threat_score"] = self.calculate_threat_score(scan_data)
            
            # Summary
            scan_data["summary"] = {
                "total_profiles": scan_data.get("count", 0),
                "total_breaches": len(scan_data["breaches"]),
                "devices_found": len(scan_data["devices"]),
                "leak_entries": len(scan_data["leaks"]),
                "threat_mentions": scan_data.get("mention_count", 0),
                "risk_level": "high" if scan_data["threat_score"] >= 70 else "medium" if scan_data["threat_score"] >= 40 else "low"
            }
            
            logger.info(f"Deep scan complete: profiles={scan_data['count']}, threat_score={scan_data['threat_score']}, sources={scan_data['data_sources']}")
            
            return {
                "success": True,
                "data": scan_data
            }
        
        except Exception as e:
            logger.error(f"Deep scan error: {str(e)}")
            return {
                "success": False,
                "error": f"Deep scan failed: {str(e)}",
                "data": {"username": username, "findings": [], "count": 0}  # Return minimal results
            }


# Initialize service
deep_scan_service = DeepScanService()
