"""
Investigation Filter Service

Provides filtering capabilities for investigations based on:
- Platform (Twitter, Instagram, Facebook, LinkedIn, etc.)
- Location / Country
- Account Type (personal, business, bot)
- Verified status
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AccountType(Enum):
    """Account classification types"""
    PERSONAL = "personal"
    BUSINESS = "business"
    BOT = "bot"
    UNKNOWN = "unknown"


class Platform(Enum):
    """Supported social media platforms"""
    FACEBOOK = "Facebook"
    TWITTER = "Twitter"
    INSTAGRAM = "Instagram"
    LINKEDIN = "LinkedIn"
    GITHUB = "GitHub"
    TIKTOK = "TikTok"
    YOUTUBE = "YouTube"
    REDDIT = "Reddit"
    TELEGRAM = "Telegram"
    TWITCH = "Twitch"
    SNAPCHAT = "Snapchat"
    PINTEREST = "Pinterest"
    TUMBLR = "Tumblr"


class InvestigationFilter:
    """
    Filter OSINT investigation results by multiple criteria.
    
    Filters are optional - if empty, backend performs full search.
    """
    
    def __init__(self):
        """Initialize filter with empty parameters"""
        self.platform: Optional[List[str]] = None
        self.location: Optional[List[str]] = None
        self.country: Optional[str] = None  # Soft filter - optional country bias
        self.account_type: Optional[List[str]] = None
        self.verified_only: Optional[bool] = None
        self.minimize_bots: bool = False
    
    @staticmethod
    def from_dict(filter_dict: Dict[str, Any]) -> 'InvestigationFilter':
        """
        Create filter from dictionary (typically from API request).
        
        Args:
            filter_dict: Dictionary with optional keys:
                - platform: str or list of platform names
                - location: str or list of countries
                - country: str - country name or code (soft filter, optional)
                - account_type: str or list of account types
                - verified_only: bool
                - minimize_bots: bool
                
        Returns:
            InvestigationFilter instance
            
        Example:
            >>> filters = InvestigationFilter.from_dict({
            ...     "platform": ["Twitter", "Instagram"],
            ...     "location": ["United States", "Canada"],
            ...     "country": "Ghana",
            ...     "account_type": "personal",
            ...     "verified_only": True
            ... })
        """
        filters = InvestigationFilter()
        
        # Platform filter
        if 'platform' in filter_dict and filter_dict['platform']:
            platform = filter_dict['platform']
            filters.platform = platform if isinstance(platform, list) else [platform]
        
        # Location filter
        if 'location' in filter_dict and filter_dict['location']:
            location = filter_dict['location']
            filters.location = location if isinstance(location, list) else [location]
        
        # Country filter (soft filter - only bias, doesn't block results)
        if 'country' in filter_dict and filter_dict['country']:
            filters.country = str(filter_dict['country']).strip()
        
        # Account type filter
        if 'account_type' in filter_dict and filter_dict['account_type']:
            account_type = filter_dict['account_type']
            filters.account_type = account_type if isinstance(account_type, list) else [account_type]
        
        # Verified status filter
        if 'verified_only' in filter_dict:
            filters.verified_only = bool(filter_dict['verified_only'])
        
        # Minimize bots
        if 'minimize_bots' in filter_dict:
            filters.minimize_bots = bool(filter_dict['minimize_bots'])
        
        return filters
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert filter to dictionary.
        
        Returns:
            Dictionary representation of active filters
        """
        return {
            'platform': self.platform,
            'location': self.location,
            'country': self.country,
            'account_type': self.account_type,
            'verified_only': self.verified_only,
            'minimize_bots': self.minimize_bots
        }
    
    def is_empty(self) -> bool:
        """Check if all filters are empty (no filtering applied)"""
        return (
            self.platform is None and
            self.location is None and
            self.country is None and
            self.account_type is None and
            self.verified_only is None and
            self.minimize_bots is False
        )
    
    def apply_to_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter findings list based on active filters.
        
        Args:
            findings: List of finding dictionaries from investigation
            
        Returns:
            Filtered findings list
        """
        if self.is_empty():
            # No filtering
            return findings
        
        filtered = findings
        
        # Filter by platform
        if self.platform:
            filtered = [
                f for f in filtered
                if f.get('platform') in [p for p in self.platform]
            ]
        
        # Filter by location (check metadata)
        if self.location:
            filtered = [
                f for f in filtered
                if self._check_location(f, self.location)
            ]
        
        # Filter by account type (check metadata)
        if self.account_type:
            filtered = [
                f for f in filtered
                if self._check_account_type(f, self.account_type)
            ]
        
        # Filter by verified status
        if self.verified_only is not None:
            filtered = [
                f for f in filtered
                if f.get('verified', False) == self.verified_only
            ]
        
        # Minimize bots
        if self.minimize_bots:
            filtered = [
                f for f in filtered
                if not self._is_bot(f)
            ]
        
        return filtered
    
    @staticmethod
    def _check_location(finding: Dict[str, Any], locations: List[str]) -> bool:
        """Check if finding matches any location filter"""
        metadata = finding.get('metadata', {})
        finding_location = metadata.get('location') or metadata.get('country')
        
        if not finding_location:
            return True  # Include if location not specified
        
        return finding_location.lower() in [loc.lower() for loc in locations]
    
    @staticmethod
    def _check_account_type(finding: Dict[str, Any], account_types: List[str]) -> bool:
        """Check if finding matches any account type filter"""
        metadata = finding.get('metadata', {})
        finding_type = metadata.get('account_type', 'unknown').lower()
        
        return finding_type in [t.lower() for t in account_types]
    
    @staticmethod
    def _is_bot(finding: Dict[str, Any]) -> bool:
        """Detect if account appears to be a bot"""
        metadata = finding.get('metadata', {})
        
        # Red flags for bots
        bot_indicators = [
            metadata.get('account_type', '').lower() == 'bot',
            'bot' in metadata.get('username', '').lower(),
            'automated' in metadata.get('bio', '').lower(),
            metadata.get('is_bot', False),
            metadata.get('is_automated', False),
            'spam' in metadata.get('category', '').lower(),
        ]
        
        # Count indicators
        return sum(bot_indicators) >= 2
    
    def get_description(self) -> str:
        """
        Get human-readable description of active filters.
        
        Returns:
            String describing the filters applied
            
        Example:
            >>> filters = InvestigationFilter.from_dict({
            ...     "platform": ["Twitter", "Instagram"],
            ...     "country": "Ghana",
            ...     "verified_only": True
            ... })
            >>> description = filters.get_description()
            >>> # Returns: "Platforms: Twitter, Instagram | Country: Ghana | Verified Only"
        """
        active_filters = []
        
        if self.platform:
            active_filters.append(f"Platforms: {', '.join(self.platform)}")
        
        if self.location:
            active_filters.append(f"Locations: {', '.join(self.location)}")
        
        if self.country:
            active_filters.append(f"Country: {self.country}")
        
        if self.account_type:
            active_filters.append(f"Account Types: {', '.join(self.account_type)}")
        
        if self.verified_only:
            active_filters.append("Verified Only")
        
        if self.minimize_bots:
            active_filters.append("No Bots")
        
        return " | ".join(active_filters) if active_filters else "No filters applied"
    
    def get_search_parameters(self) -> Dict[str, Any]:
        """
        Convert filters to search parameters for intensified searching.
        
        When filters are applied, searches should be narrowed and intensified
        in those specific areas rather than searching broadly.
        
        Returns:
            Dict with search intensity parameters for services
        """
        params = {
            'narrow_search': not self.is_empty(),  # Narrow if any filter applied
            'intensity': 1.0,  # Base intensity
            'platforms': self.platform,
            'locations': self.location,
            'require_country': self.country,
            'crawler_depth': 2,  # Normal depth
            'crawler_max_pages': 50,  # Normal pages
        }
        
        # Increase intensity and depth based on filters
        active_filter_count = sum([
            bool(self.platform),
            bool(self.location),
            bool(self.country),
            bool(self.account_type),
            bool(self.verified_only),
            self.minimize_bots
        ])
        
        if active_filter_count > 0:
            # More filters = more intense focused search
            params['intensity'] = 1.0 + (active_filter_count * 0.3)
            params['crawler_depth'] = 3  # Deeper crawl for filtered searches
            params['crawler_max_pages'] = 100  # More pages for focused search
            params['email_harvester_intensive'] = True
            params['scraper_retry_attempts'] = 3
            params['search_strategy'] = 'narrowed_and_intensified'
        else:
            params['search_strategy'] = 'broad'
        
        return params
    
    def should_intensify_for_platforms(self) -> bool:
        """Check if search should be intensified for platform filters"""
        return bool(self.platform) and len(self.platform) <= 3
    
    def should_intensify_for_location(self) -> bool:
        """Check if search should be intensified for location filters"""
        return bool(self.location) and len(self.location) <= 2


# Supported countries for location filter
SUPPORTED_COUNTRIES = [
    "United States",
    "United Kingdom",
    "Canada",
    "Australia",
    "India",
    "Brazil",
    "Mexico",
    "Germany",
    "France",
    "China",
    "Japan",
    "South Korea",
    "Russia",
    "Saudi Arabia",
    "United Arab Emirates",
    "Singapore",
    "Malaysia",
    "Indonesia",
    "Thailand",
    "Vietnam",
    "Philippines",
    "Pakistan",
    "Nigeria",
    "Kenya",
    "South Africa",
    # Add more as needed
]

# Supported account types
SUPPORTED_ACCOUNT_TYPES = [
    "personal",
    "business",
    "bot",
    "verified",
    "celebrity",
    "influencer",
    "organization",
    "government",
]
