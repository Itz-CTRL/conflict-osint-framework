"""
Country Code Utilities

Provides country code mappings, detection, and formatting utilities
for phone number intelligence and location-based filtering.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Comprehensive country database with phone codes and info
COUNTRIES = {
    'US': {'name': 'United States', 'code': '+1', 'iso': 'US', 'region': 'North America'},
    'CA': {'name': 'Canada', 'code': '+1', 'iso': 'CA', 'region': 'North America'},
    'UK': {'name': 'United Kingdom', 'code': '+44', 'iso': 'GB', 'region': 'Europe'},
    'GB': {'name': 'United Kingdom', 'code': '+44', 'iso': 'GB', 'region': 'Europe'},
    'AU': {'name': 'Australia', 'code': '+61', 'iso': 'AU', 'region': 'Oceania'},
    'NZ': {'name': 'New Zealand', 'code': '+64', 'iso': 'NZ', 'region': 'Oceania'},
    'DE': {'name': 'Germany', 'code': '+49', 'iso': 'DE', 'region': 'Europe'},
    'FR': {'name': 'France', 'code': '+33', 'iso': 'FR', 'region': 'Europe'},
    'IT': {'name': 'Italy', 'code': '+39', 'iso': 'IT', 'region': 'Europe'},
    'ES': {'name': 'Spain', 'code': '+34', 'iso': 'ES', 'region': 'Europe'},
    'NL': {'name': 'Netherlands', 'code': '+31', 'iso': 'NL', 'region': 'Europe'},
    'BE': {'name': 'Belgium', 'code': '+32', 'iso': 'BE', 'region': 'Europe'},
    'CH': {'name': 'Switzerland', 'code': '+41', 'iso': 'CH', 'region': 'Europe'},
    'AT': {'name': 'Austria', 'code': '+43', 'iso': 'AT', 'region': 'Europe'},
    'SE': {'name': 'Sweden', 'code': '+46', 'iso': 'SE', 'region': 'Europe'},
    'NO': {'name': 'Norway', 'code': '+47', 'iso': 'NO', 'region': 'Europe'},
    'DK': {'name': 'Denmark', 'code': '+45', 'iso': 'DK', 'region': 'Europe'},
    'FI': {'name': 'Finland', 'code': '+358', 'iso': 'FI', 'region': 'Europe'},
    'PL': {'name': 'Poland', 'code': '+48', 'iso': 'PL', 'region': 'Europe'},
    'CZ': {'name': 'Czech Republic', 'code': '+420', 'iso': 'CZ', 'region': 'Europe'},
    'SK': {'name': 'Slovakia', 'code': '+421', 'iso': 'SK', 'region': 'Europe'},
    'HU': {'name': 'Hungary', 'code': '+36', 'iso': 'HU', 'region': 'Europe'},
    'RO': {'name': 'Romania', 'code': '+40', 'iso': 'RO', 'region': 'Europe'},
    'BG': {'name': 'Bulgaria', 'code': '+359', 'iso': 'BG', 'region': 'Europe'},
    'GR': {'name': 'Greece', 'code': '+30', 'iso': 'GR', 'region': 'Europe'},
    'PT': {'name': 'Portugal', 'code': '+351', 'iso': 'PT', 'region': 'Europe'},
    'IE': {'name': 'Ireland', 'code': '+353', 'iso': 'IE', 'region': 'Europe'},
    'RU': {'name': 'Russia', 'code': '+7', 'iso': 'RU', 'region': 'Europe/Asia'},
    'UA': {'name': 'Ukraine', 'code': '+380', 'iso': 'UA', 'region': 'Europe'},
    'KZ': {'name': 'Kazakhstan', 'code': '+7', 'iso': 'KZ', 'region': 'Asia'},
    'IN': {'name': 'India', 'code': '+91', 'iso': 'IN', 'region': 'Asia'},
    'PK': {'name': 'Pakistan', 'code': '+92', 'iso': 'PK', 'region': 'Asia'},
    'BD': {'name': 'Bangladesh', 'code': '+880', 'iso': 'BD', 'region': 'Asia'},
    'LK': {'name': 'Sri Lanka', 'code': '+94', 'iso': 'LK', 'region': 'Asia'},
    'NP': {'name': 'Nepal', 'code': '+977', 'iso': 'NP', 'region': 'Asia'},
    'JP': {'name': 'Japan', 'code': '+81', 'iso': 'JP', 'region': 'Asia'},
    'KR': {'name': 'South Korea', 'code': '+82', 'iso': 'KR', 'region': 'Asia'},
    'CN': {'name': 'China', 'code': '+86', 'iso': 'CN', 'region': 'Asia'},
    'TW': {'name': 'Taiwan', 'code': '+886', 'iso': 'TW', 'region': 'Asia'},
    'HK': {'name': 'Hong Kong', 'code': '+852', 'iso': 'HK', 'region': 'Asia'},
    'SG': {'name': 'Singapore', 'code': '+65', 'iso': 'SG', 'region': 'Asia'},
    'MY': {'name': 'Malaysia', 'code': '+60', 'iso': 'MY', 'region': 'Asia'},
    'TH': {'name': 'Thailand', 'code': '+66', 'iso': 'TH', 'region': 'Asia'},
    'VN': {'name': 'Vietnam', 'code': '+84', 'iso': 'VN', 'region': 'Asia'},
    'PH': {'name': 'Philippines', 'code': '+63', 'iso': 'PH', 'region': 'Asia'},
    'ID': {'name': 'Indonesia', 'code': '+62', 'iso': 'ID', 'region': 'Asia'},
    'BR': {'name': 'Brazil', 'code': '+55', 'iso': 'BR', 'region': 'South America'},
    'AR': {'name': 'Argentina', 'code': '+54', 'iso': 'AR', 'region': 'South America'},
    'CL': {'name': 'Chile', 'code': '+56', 'iso': 'CL', 'region': 'South America'},
    'CO': {'name': 'Colombia', 'code': '+57', 'iso': 'CO', 'region': 'South America'},
    'PE': {'name': 'Peru', 'code': '+51', 'iso': 'PE', 'region': 'South America'},
    'VE': {'name': 'Venezuela', 'code': '+58', 'iso': 'VE', 'region': 'South America'},
    'MX': {'name': 'Mexico', 'code': '+52', 'iso': 'MX', 'region': 'North America'},
    'ZA': {'name': 'South Africa', 'code': '+27', 'iso': 'ZA', 'region': 'Africa'},
    'EG': {'name': 'Egypt', 'code': '+20', 'iso': 'EG', 'region': 'Africa'},
    'NG': {'name': 'Nigeria', 'code': '+234', 'iso': 'NG', 'region': 'Africa'},
    'GH': {'name': 'Ghana', 'code': '+233', 'iso': 'GH', 'region': 'Africa'},
    'KE': {'name': 'Kenya', 'code': '+254', 'iso': 'KE', 'region': 'Africa'},
    'ET': {'name': 'Ethiopia', 'code': '+251', 'iso': 'ET', 'region': 'Africa'},
    'UG': {'name': 'Uganda', 'code': '+256', 'iso': 'UG', 'region': 'Africa'},
    'TZ': {'name': 'Tanzania', 'code': '+255', 'iso': 'TZ', 'region': 'Africa'},
    'ZM': {'name': 'Zambia', 'code': '+260', 'iso': 'ZM', 'region': 'Africa'},
    'ZW': {'name': 'Zimbabwe', 'code': '+263', 'iso': 'ZW', 'region': 'Africa'},
    'AO': {'name': 'Angola', 'code': '+244', 'iso': 'AO', 'region': 'Africa'},
    'CM': {'name': 'Cameroon', 'code': '+237', 'iso': 'CM', 'region': 'Africa'},
    'CI': {'name': 'Côte d\'Ivoire', 'code': '+225', 'iso': 'CI', 'region': 'Africa'},
    'SN': {'name': 'Senegal', 'code': '+221', 'iso': 'SN', 'region': 'Africa'},
    'MA': {'name': 'Morocco', 'code': '+212', 'iso': 'MA', 'region': 'Africa'},
    'TN': {'name': 'Tunisia', 'code': '+216', 'iso': 'TN', 'region': 'Africa'},
    'DZ': {'name': 'Algeria', 'code': '+213', 'iso': 'DZ', 'region': 'Africa'},
    'LY': {'name': 'Libya', 'code': '+218', 'iso': 'LY', 'region': 'Africa'},
    'SD': {'name': 'Sudan', 'code': '+249', 'iso': 'SD', 'region': 'Africa'},
    'MW': {'name': 'Malawi', 'code': '+265', 'iso': 'MW', 'region': 'Africa'},
    'MZ': {'name': 'Mozambique', 'code': '+258', 'iso': 'MZ', 'region': 'Africa'},
    'SL': {'name': 'Sierra Leone', 'code': '+232', 'iso': 'SL', 'region': 'Africa'},
    'LR': {'name': 'Liberia', 'code': '+231', 'iso': 'LR', 'region': 'Africa'},
    'GN': {'name': 'Guinea', 'code': '+224', 'iso': 'GN', 'region': 'Africa'},
    'GA': {'name': 'Gabon', 'code': '+241', 'iso': 'GA', 'region': 'Africa'},
    'CG': {'name': 'Congo', 'code': '+242', 'iso': 'CG', 'region': 'Africa'},
    'CD': {'name': 'Democratic Republic of Congo', 'code': '+243', 'iso': 'CD', 'region': 'Africa'},
    'RW': {'name': 'Rwanda', 'code': '+250', 'iso': 'RW', 'region': 'Africa'},
    'BI': {'name': 'Burundi', 'code': '+257', 'iso': 'BI', 'region': 'Africa'},
    'SA': {'name': 'Saudi Arabia', 'code': '+966', 'iso': 'SA', 'region': 'Middle East'},
    'AE': {'name': 'United Arab Emirates', 'code': '+971', 'iso': 'AE', 'region': 'Middle East'},
    'QA': {'name': 'Qatar', 'code': '+974', 'iso': 'QA', 'region': 'Middle East'},
    'KW': {'name': 'Kuwait', 'code': '+965', 'iso': 'KW', 'region': 'Middle East'},
    'BH': {'name': 'Bahrain', 'code': '+973', 'iso': 'BH', 'region': 'Middle East'},
    'OM': {'name': 'Oman', 'code': '+968', 'iso': 'OM', 'region': 'Middle East'},
    'YE': {'name': 'Yemen', 'code': '+967', 'iso': 'YE', 'region': 'Middle East'},
    'AE': {'name': 'United Arab Emirates', 'code': '+971', 'iso': 'AE', 'region': 'Middle East'},
    'IL': {'name': 'Israel', 'code': '+972', 'iso': 'IL', 'region': 'Middle East'},
    'JO': {'name': 'Jordan', 'code': '+962', 'iso': 'JO', 'region': 'Middle East'},
    'LB': {'name': 'Lebanon', 'code': '+961', 'iso': 'LB', 'region': 'Middle East'},
    'SY': {'name': 'Syria', 'code': '+963', 'iso': 'SY', 'region': 'Middle East'},
    'IQ': {'name': 'Iraq', 'code': '+964', 'iso': 'IQ', 'region': 'Middle East'},
    'IR': {'name': 'Iran', 'code': '+98', 'iso': 'IR', 'region': 'Middle East'},
    'AF': {'name': 'Afghanistan', 'code': '+93', 'iso': 'AF', 'region': 'Asia'},
    'TJ': {'name': 'Tajikistan', 'code': '+992', 'iso': 'TJ', 'region': 'Asia'},
    'UZ': {'name': 'Uzbekistan', 'code': '+998', 'iso': 'UZ', 'region': 'Asia'},
    'TM': {'name': 'Turkmenistan', 'code': '+993', 'iso': 'TM', 'region': 'Asia'},
    'KG': {'name': 'Kyrgyzstan', 'code': '+996', 'iso': 'KG', 'region': 'Asia'},
}


class CountryCodeDetector:
    """Detect and validate country codes from phone numbers"""
    
    @staticmethod
    def get_by_code_prefix(phone: str) -> Optional[Dict[str, str]]:
        """
        Detect country by international phone prefix.
        
        Args:
            phone: Phone number string (with or without +)
            
        Returns:
            Country dict or None if not detected
        """
        # Remove non-digits, keep +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        
        # Try to match prefixes (longest first)
        phone_codes_sorted = sorted(
            [(v['code'], k, v) for k, v in COUNTRIES.items()],
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for prefix, country_key, country_data in phone_codes_sorted:
            if cleaned.startswith(prefix):
                return {
                    'code': country_data['code'],
                    'iso': country_data['iso'],
                    'name': country_data['name'],
                    'region': country_data['region']
                }
        
        return None
    
    @staticmethod
    def get_by_iso(iso_code: str) -> Optional[Dict[str, str]]:
        """
        Get country info by ISO code.
        
        Args:
            iso_code: ISO 2-letter country code (e.g., 'US', 'GB')
            
        Returns:
            Country dict or None
        """
        iso_upper = iso_code.upper()
        
        # Direct lookup
        if iso_upper in COUNTRIES:
            country = COUNTRIES[iso_upper]
            return {
                'code': country['code'],
                'iso': country['iso'],
                'name': country['name'],
                'region': country['region']
            }
        
        # Search by ISO field
        for key, country in COUNTRIES.items():
            if country['iso'] == iso_upper:
                return {
                    'code': country['code'],
                    'iso': country['iso'],
                    'name': country['name'],
                    'region': country['region']
                }
        
        return None
    
    @staticmethod
    def get_by_name(name: str) -> Optional[Dict[str, str]]:
        """
        Get country info by country name (case-insensitive).
        
        Args:
            name: Country name
            
        Returns:
            Country dict or None
        """
        name_lower = name.lower().strip()
        
        for key, country in COUNTRIES.items():
            if country['name'].lower() == name_lower:
                return {
                    'code': country['code'],
                    'iso': country['iso'],
                    'name': country['name'],
                    'region': country['region']
                }
        
        return None
    
    @staticmethod
    def search_countries(query: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Search for countries by partial name or code.
        
        Args:
            query: Search string
            limit: Maximum results
            
        Returns:
            List of matching countries
        """
        query_lower = query.lower().strip()
        matches = []
        
        for key, country in COUNTRIES.items():
            if (query_lower in country['name'].lower() or
                query_lower in country['code'] or
                query_lower in country['iso'].lower() or
                query_lower in country['region'].lower()):
                
                matches.append({
                    'code': country['code'],
                    'iso': country['iso'],
                    'name': country['name'],
                    'region': country['region'],
                    'country_key': key
                })
        
        return matches[:limit]
    
    @staticmethod
    def get_all_countries() -> List[Dict[str, str]]:
        """
        Get all countries sorted by name.
        
        Returns:
            List of all country dicts sorted by name
        """
        all_countries = []
        for key, country in COUNTRIES.items():
            all_countries.append({
                'code': country['code'],
                'iso': country['iso'],
                'name': country['name'],
                'region': country['region'],
                'country_key': key
            })
        
        return sorted(all_countries, key=lambda x: x['name'])
    
    @staticmethod
    def get_countries_by_region(region: str) -> List[Dict[str, str]]:
        """
        Get all countries in a specific region.
        
        Args:
            region: Region name (e.g., 'Africa', 'Europe', 'Asia')
            
        Returns:
            List of countries in that region
        """
        region_lower = region.lower()
        matches = []
        
        for key, country in COUNTRIES.items():
            if region_lower in country['region'].lower():
                matches.append({
                    'code': country['code'],
                    'iso': country['iso'],
                    'name': country['name'],
                    'region': country['region']
                })
        
        return sorted(matches, key=lambda x: x['name'])
