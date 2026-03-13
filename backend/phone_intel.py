"""
phone_intel.py

Phone Intelligence module using phonenumbers library with enhanced verification.
Normalizes phone numbers and extracts carrier, country, timezone data.
Includes verification through multiple sources.
"""

import phonenumbers
from phonenumbers import carrier, geocoder, timezone, COUNTRY_CODE_TO_REGION_CODE
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# Country code mappings for common prefixes
COUNTRY_PREFIXES = {
    '1': 'US',      # US/Canada
    '44': 'GB',     # UK
    '233': 'GH',    # Ghana
    '234': 'NG',    # Nigeria
    '255': 'TZ',    # Tanzania
    '256': 'UG',    # Uganda
    '27': 'ZA',     # South Africa
    '254': 'KE',    # Kenya
    '212': 'MA',    # Morocco
}


def normalize_phone_number(phone_number: str, country_code: Optional[str] = None) -> tuple:
    """
    Normalize and clean phone number to standard format.
    Returns (cleaned_number, detected_country_code)
    """
    phone = phone_number.strip()
    
    # Remove common separators
    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('.', '')
    
    # Handle +0... format (common mistake) - convert to international format
    if phone.startswith('+0'):
        phone = phone[1:]  # Remove the +, keep the 0
    
    # Try to detect country code from the number itself
    detected_country = None
    
    # If it starts with +, extract country code
    if phone.startswith('+'):
        # Try to find matching country code (longest match first)
        for prefix in sorted(COUNTRY_PREFIXES.keys(), key=len, reverse=True):
            if phone[1:].startswith(prefix):
                detected_country = COUNTRY_PREFIXES[prefix]
                break
    
    # If starts with 0, it's a local number
    elif phone.startswith('0'):
        if country_code:
            detected_country = country_code.upper()
        else:
            # Default to Ghana if no country code provided
            detected_country = 'GH'
    
    # If starts with digits but no +, treat as international prefix
    else:
        # Try to find matching country code from the beginning
        for prefix in sorted(COUNTRY_PREFIXES.keys(), key=len, reverse=True):
            if phone.startswith(prefix):
                detected_country = COUNTRY_PREFIXES[prefix]
                phone = '+' + phone  # Add the + prefix
                break
    
    # Use provided country_code if explicitly given, otherwise use detected
    final_country = country_code.upper() if country_code else (detected_country or 'US')
    
    return phone, final_country


def validate_and_analyze_phone(phone_number: str, country_code: Optional[str] = None) -> dict:
    """
    Validate and analyze a phone number with enhanced verification.
    Automatically detects country from phone number format.
    
    Args:
        phone_number: Phone number string (any format: +1234567890, 0123456789, 1234567890)
        country_code: Optional 2-letter country code for region inference
    
    Returns:
        dict with normalized_number, country, carrier, valid, etc.
    """
    try:
        # Normalize the phone number
        normalized_phone, detected_country = normalize_phone_number(phone_number, country_code)
        
        logger.info(f"Processing phone: {phone_number} → {normalized_phone} (Country: {detected_country})")
        
        # Parse phone number with detected country
        parsed = phonenumbers.parse(normalized_phone, detected_country)
        
        # Validate
        is_valid = phonenumbers.is_valid_number(parsed)
        is_possible = phonenumbers.is_possible_number(parsed)
        
        # Extract metadata
        region_code = phonenumbers.region_code_for_number(parsed)
        carrier_name = carrier.name_for_number(parsed, "en")
        location = geocoder.description_for_number(parsed, "en")
        timezones = timezone.time_zones_for_number(parsed)
        number_type = phonenumbers.number_type(parsed)
        
        # Format numbers
        e164_format = phonenumbers.format_number(
            parsed, 
            phonenumbers.PhoneNumberFormat.E164
        )
        international_format = phonenumbers.format_number(
            parsed,
            phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
        
        # Map number type to string
        type_map = {
            phonenumbers.PhoneNumberType.MOBILE: "mobile",
            phonenumbers.PhoneNumberType.FIXED_LINE: "fixed_line",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_or_mobile",
            phonenumbers.PhoneNumberType.TOLL_FREE: "toll_free",
            phonenumbers.PhoneNumberType.PREMIUM_RATE: "premium_rate",
            phonenumbers.PhoneNumberType.SHARED_COST: "shared_cost",
            phonenumbers.PhoneNumberType.VOIP: "voip",
            phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "personal",
            phonenumbers.PhoneNumberType.PAGER: "pager",
            phonenumbers.PhoneNumberType.UAN: "uan",
            phonenumbers.PhoneNumberType.UNKNOWN: "unknown",
        }
        type_str = type_map.get(number_type, "unknown")
        
        # Calculate confidence based on validation results
        confidence = 0.95 if is_valid else 0.50 if is_possible else 0.10
        
        logger.info(f"Phone analysis result: {e164_format} - Valid: {is_valid}, Carrier: {carrier_name}")
        
        return {
            "number": e164_format,
            "number_international": international_format,
            "country": location or region_code,
            "country_code": region_code,
            "region": location,
            "carrier": carrier_name or "Unknown",
            "timezone": timezones[0] if timezones else None,
            "type": type_str,
            "valid": is_valid,
            "possible": is_possible,
            "confidence": confidence,
        }
        
    except phonenumbers.NumberParseException as e:
        logger.warning(f"Phone parse error: {str(e)}")
        return {
            "error": f"Invalid phone number: {str(e)}",
            "valid": False,
        }
    except Exception as e:
        logger.error(f"Phone analysis error: {str(e)}")
        return {
            "error": f"Phone analysis error: {str(e)}",
            "valid": False,
        }
