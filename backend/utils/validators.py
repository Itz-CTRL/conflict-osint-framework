"""
Validation utilities for input validation and sanitization
"""

import re
import phonenumbers
import logging
from typing import Optional, Tuple, Dict

logger = logging.getLogger(__name__)

# International country mappings (ISO 3166-1)
COUNTRY_CODES = {
    'US': {'name': 'United States', 'code': '+1', 'iso': 'US'},
    'CA': {'name': 'Canada', 'code': '+1', 'iso': 'CA'},
    'GB': {'name': 'United Kingdom', 'code': '+44', 'iso': 'GB'},
    'AU': {'name': 'Australia', 'code': '+61', 'iso': 'AU'},
    'DE': {'name': 'Germany', 'code': '+49', 'iso': 'DE'},
    'FR': {'name': 'France', 'code': '+33', 'iso': 'FR'},
    'IN': {'name': 'India', 'code': '+91', 'iso': 'IN'},
    'CN': {'name': 'China', 'code': '+86', 'iso': 'CN'},
    'BR': {'name': 'Brazil', 'code': '+55', 'iso': 'BR'},
    'RU': {'name': 'Russia', 'code': '+7', 'iso': 'RU'},
    'JP': {'name': 'Japan', 'code': '+81', 'iso': 'JP'},
    'KR': {'name': 'South Korea', 'code': '+82', 'iso': 'KR'},
    'ZA': {'name': 'South Africa', 'code': '+27', 'iso': 'ZA'},
    'GH': {'name': 'Ghana', 'code': '+233', 'iso': 'GH'},
    'NG': {'name': 'Nigeria', 'code': '+234', 'iso': 'NG'},
    'MX': {'name': 'Mexico', 'code': '+52', 'iso': 'MX'},
    'NL': {'name': 'Netherlands', 'code': '+31', 'iso': 'NL'},
    'SE': {'name': 'Sweden', 'code': '+46', 'iso': 'SE'},
    'SG': {'name': 'Singapore', 'code': '+65', 'iso': 'SG'},
    'UAE': {'name': 'United Arab Emirates', 'code': '+971', 'iso': 'AE'},
    'KE': {'name': 'Kenya', 'code': '+254', 'iso': 'KE'},
    'TZ': {'name': 'Tanzania', 'code': '+255', 'iso': 'TZ'},
    'UG': {'name': 'Uganda', 'code': '+256', 'iso': 'UG'},
    'LV': {'name': 'Latvia', 'code': '+371', 'iso': 'LV'},
    'PL': {'name': 'Poland', 'code': '+48', 'iso': 'PL'},
    'IT': {'name': 'Italy', 'code': '+39', 'iso': 'IT'},
    'ES': {'name': 'Spain', 'code': '+34', 'iso': 'ES'},
    'TH': {'name': 'Thailand', 'code': '+66', 'iso': 'TH'},
    'PH': {'name': 'Philippines', 'code': '+63', 'iso': 'PH'},
    'VN': {'name': 'Vietnam', 'code': '+84', 'iso': 'VN'},
    'ID': {'name': 'Indonesia', 'code': '+62', 'iso': 'ID'},
    'MY': {'name': 'Malaysia', 'code': '+60', 'iso': 'MY'},
    'BD': {'name': 'Bangladesh', 'code': '+880', 'iso': 'BD'},
    'PK': {'name': 'Pakistan', 'code': '+92', 'iso': 'PK'},
    'IM': {'name': 'Isle of Man', 'code': '+44', 'iso': 'IM'},
    'PT': {'name': 'Portugal', 'code': '+351', 'iso': 'PT'},
    'CH': {'name': 'Switzerland', 'code': '+41', 'iso': 'CH'},
    'AT': {'name': 'Austria', 'code': '+43', 'iso': 'AT'},
    'GR': {'name': 'Greece', 'code': '+30', 'iso': 'GR'},
    'TR': {'name': 'Turkey', 'code': '+90', 'iso': 'TR'},
    'SG': {'name': 'Singapore', 'code': '+65', 'iso': 'SG'},
    'HK': {'name': 'Hong Kong', 'code': '+852', 'iso': 'HK'},
    'TW': {'name': 'Taiwan', 'code': '+886', 'iso': 'TW'},
    'NZ': {'name': 'New Zealand', 'code': '+64', 'iso': 'NZ'},
    'ZW': {'name': 'Zimbabwe', 'code': '+263', 'iso': 'ZW'},
    'IL': {'name': 'Israel', 'code': '+972', 'iso': 'IL'},
    'SA': {'name': 'Saudi Arabia', 'code': '+966', 'iso': 'SA'},
    'EG': {'name': 'Egypt', 'code': '+20', 'iso': 'EG'},
    'MA': {'name': 'Morocco', 'code': '+212', 'iso': 'MA'},
}


class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_username(username):
        """
        Validate username format
        
        Args:
            username (str): Username to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not username:
            return False, "Username is required"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(username) > 255:
            return False, "Username is too long (max 255 characters)"
        
        # Allow alphanumeric, dots, dashes, underscores
        if not re.match(r'^[a-zA-Z0-9._-]+$', username):
            return False, "Username contains invalid characters"
        
        return True, None
    
    @staticmethod
    def validate_email(email):
        """
        Validate email format
        
        Args:
            email (str): Email to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        
        return True, None
    
    @staticmethod
    def normalize_phone_number(phone_number: str, country_code: Optional[str] = None) -> Optional[str]:
        """
        Normalize phone number to international format.
        Handles multiple input formats: 024XXXXXXX, +233XXXXXXXXX, 233XXXXXXXXX
        Never fails - returns best effort normalized number or original.
        
        Args:
            phone_number: Phone number in any format
            country_code: Optional ISO country code for context
            
        Returns:
            Normalized phone number in international format, or None if unrecoverable
        """
        if not phone_number:
            return None
        
        phone_number = phone_number.strip()
        logger.debug(f"Normalizing phone: {phone_number} with country: {country_code}")
        
        try:
            # Try direct parsing first (handles +233XXXXXXXXX format)
            try:
                parsed = phonenumbers.parse(phone_number, None)
                if phonenumbers.is_valid_number(parsed):
                    normalized = phonenumbers.format_number(
                        parsed,
                        phonenumbers.PhoneNumberFormat.INTERNATIONAL
                    )
                    logger.debug(f"Normalized via direct parse: {phone_number} -> {normalized}")
                    return normalized
            except phonenumbers.NumberParseException:
                pass
            
            # Try with explicit country code if provided
            if country_code:
                try:
                    parsed = phonenumbers.parse(phone_number, country_code)
                    if phonenumbers.is_valid_number(parsed):
                        normalized = phonenumbers.format_number(
                            parsed,
                            phonenumbers.PhoneNumberFormat.INTERNATIONAL
                        )
                        logger.debug(f"Normalized via country {country_code}: {phone_number} -> {normalized}")
                        return normalized
                except phonenumbers.NumberParseException:
                    pass
            
            # Try adding + prefix if missing (handles 233XXXXXXXXX format)
            if not phone_number.startswith('+'):
                try:
                    parsed = phonenumbers.parse('+' + phone_number, None)
                    if phonenumbers.is_valid_number(parsed):
                        normalized = phonenumbers.format_number(
                            parsed,
                            phonenumbers.PhoneNumberFormat.INTERNATIONAL
                        )
                        logger.debug(f"Normalized with prefix: {phone_number} -> {normalized}")
                        return normalized
                except phonenumbers.NumberParseException:
                    pass
            
            # Try common regions (handles 024XXXXXXX for Ghana format)
            common_regions = ['GH', 'US', 'GB', 'IN', 'BR', 'RU', 'DE', 'FR', 'ID', 'CN', 'JP']
            if country_code:
                common_regions.insert(0, country_code)
            
            for region in common_regions:
                try:
                    parsed = phonenumbers.parse(phone_number, region)
                    if phonenumbers.is_valid_number(parsed):
                        normalized = phonenumbers.format_number(
                            parsed,
                            phonenumbers.PhoneNumberFormat.INTERNATIONAL
                        )
                        logger.debug(f"Normalized via region {region}: {phone_number} -> {normalized}")
                        return normalized
                except phonenumbers.NumberParseException:
                    continue
            
            # Last resort: if phone is all digits, try to construct international format
            clean_phone = re.sub(r'\D', '', phone_number)
            if clean_phone:
                if len(clean_phone) >= 10:
                    # Try as-is
                    for region in common_regions:
                        try:
                            parsed = phonenumbers.parse(clean_phone, region)
                            if phonenumbers.is_valid_number(parsed):
                                normalized = phonenumbers.format_number(
                                    parsed,
                                    phonenumbers.PhoneNumberFormat.INTERNATIONAL
                                )
                                logger.debug(f"Normalized cleaned digits: {phone_number} -> {normalized}")
                                return normalized
                        except phonenumbers.NumberParseException:
                            continue
            
            logger.warning(f"Could not normalize phone number: {phone_number}")
            return None
            
        except Exception as e:
            logger.error(f"Error normalizing phone number: {str(e)}")
            return None
    
    @staticmethod
    def validate_phone(phone_number):
        """
        Validate phone number using phonenumbers library.
        No longer returns 400 errors - always attempts normalization.
        
        Args:
            phone_number (str): Phone number to validate
            
        Returns:
            tuple: (is_valid, error_message, parsed_number or None)
        """
        if not phone_number:
            return False, "Phone number is required", None
        
        try:
            # Try parsing with common regions first
            parsed = None
            for region in ['US', 'ID', 'GB', 'IN', 'BR', 'RU']:
                try:
                    parsed = phonenumbers.parse(phone_number, region)
                    if phonenumbers.is_valid_number(parsed):
                        break
                except:
                    continue
            
            if not parsed:
                return False, "Invalid phone number format", None
            
            if not phonenumbers.is_valid_number(parsed):
                return False, "Phone number is not valid", None
            
            return True, None, parsed
        
        except Exception as e:
            return False, f"Phone validation error: {str(e)}", None
    
    @staticmethod
    def validate_scan_depth(depth):
        """
        Validate scan depth parameter
        
        Args:
            depth (str): Scan depth ('light' or 'deep')
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if depth not in ['light', 'deep']:
            return False, "Scan depth must be 'light' or 'deep'"
        
        return True, None
    
    @staticmethod
    def sanitize_input(value):
        """
        Sanitize user input
        
        Args:
            value (str): Input to sanitize
            
        Returns:
            str: Sanitized input
        """
        if isinstance(value, str):
            # Remove leading/trailing whitespace
            value = value.strip()
            # Remove null bytes
            value = value.replace('\x00', '')
        return value
    
    @staticmethod
    def normalize_country(country_input: Optional[str]) -> Optional[Dict[str, str]]:
        """
        Normalize country input (name or code) to standard format.
        
        Args:
            country_input: Country name (e.g., "Ghana") or ISO code (e.g., "GH")
            
        Returns:
            Dict with 'name', 'code', 'iso' keys, or None if not found
            
        Examples:
            normalize_country("Ghana") → {'iso': 'GH', 'name': 'Ghana', 'code': '+233'}
            normalize_country("GH") → {'iso': 'GH', 'name': 'Ghana', 'code': '+233'}
            normalize_country("United States") → {'iso': 'US', 'name': 'United States', 'code': '+1'}
        """
        if not country_input:
            return None
        
        country_input = country_input.strip().upper()
        
        # Try direct ISO code match
        if country_input in COUNTRY_CODES:
            return COUNTRY_CODES[country_input]
        
        # Try country name match (case-insensitive)
        country_input_lower = country_input.lower()
        for iso, info in COUNTRY_CODES.items():
            if info['name'].lower() == country_input_lower:
                return info
        
        # Partial match for common variations
        for iso, info in COUNTRY_CODES.items():
            if country_input_lower in info['name'].lower() or info['name'].lower() in country_input_lower:
                return info
        
        # Return None if not found - let caller decide whether to accept it
        logger.debug(f"Country '{country_input}' not found in standard mappings")
        return None
    
    @staticmethod
    def infer_country_from_phone(phone_number: str) -> Optional[Dict[str, str]]:
        """
        Attempt to infer country from phone number prefix.
        
        Args:
            phone_number: Phone number string (with or without +)
            
        Returns:
            Dict with country info if found, else None
        """
        if not phone_number:
            return None
        
        try:
            # Extract country code from phone number
            parsed = phonenumbers.parse(phone_number, None)
            country_code = phonenumbers.region_code_for_number(parsed)
            
            if country_code and country_code in COUNTRY_CODES:
                return COUNTRY_CODES[country_code]
        except Exception as e:
            logger.debug(f"Could not infer country from phone: {str(e)}")
        
        return None
    
    @staticmethod
    def validate_scan_type(scan_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate scan type parameter.
        
        Args:
            scan_type: 'light' or 'deep'
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not scan_type:
            return False, "Scan type is required"
        
        if scan_type.lower() not in ['light', 'deep']:
            return False, "Scan type must be 'light' or 'deep'"
        
        return True, None
