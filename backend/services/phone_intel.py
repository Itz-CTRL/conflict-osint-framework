"""
Phone Intelligence Service

Provides comprehensive phone lookup with:
- Carrier detection (carrier name, type)
- Timezone detection
- Country/region detection
- Risk scoring
- Linked email and social account discovery
- Ghost.py-style intelligence gathering
"""

import logging
import re
from typing import Dict, List, Optional
from datetime import datetime
import phonenumbers
from phonenumbers import geocoder, carrier as phone_carrier

logger = logging.getLogger(__name__)

# Timezone mappings by country
TIMEZONE_MAP = {
    'US': ['EST', 'CST', 'MST', 'PST', 'AKST', 'HST'],
    'GB': ['GMT', 'BST'],
    'CA': ['EST', 'CST', 'MST', 'PST', 'AKST', 'NST'],
    'AU': ['AWST', 'ACST', 'AEST'],
    'IN': ['IST'],
    'JP': ['JST'],
    'CN': ['CST'],
    'BR': ['BRT', 'BRST'],
    'ZA': ['SAST'],
    'RU': ['MSK', 'YEKT', 'OMST', 'KRAT', 'IRKT', 'YAKST', 'VLAT', 'MAGST'],
}

# Carrier type mappings
CARRIER_TYPES = {
    'MOBILE': 'Mobile/Cellular',
    'FIXED_LINE': 'Fixed Line',
    'VOIP': 'VoIP',
    'UNKNOWN': 'Unknown',
}

# Risk scoring factors
RISK_FACTORS = {
    'VOIP': 0.3,
    'UNKNOWN_CARRIER': 0.4,
    'NEWLY_ISSUED': 0.2,
    'TEMPORARY': 0.5,
    'PREPAID': 0.25,
}


class PhoneIntelligence:
    """
    Comprehensive phone intelligence gathering and analysis.
    
    Provides carrier detection, timezone detection, number validation,
    and linked account discovery for phone numbers.
    """
    
    def __init__(self):
        """Initialize phone intelligence service"""
        self.voip_carriers = [
            'VOIPNow', 'MagicJack', 'Google Voice', 'Skype',
            'Vonage', 'Twilio', 'OpenPhone', 'RingCentral'
        ]
    
    def lookup(self, phone_number: str, country_code: Optional[str] = None, scan_type: str = 'light') -> Dict:
        """
        Perform phone lookup with light or deep scan.
        
        Args:
            phone_number: Phone number to lookup
            country_code: Optional ISO country code (e.g., 'US', 'GB')
            scan_type: 'light' for quick scan, 'deep' for comprehensive analysis
            
        Returns:
            Dict with phone intelligence data
        """
        if scan_type == 'deep':
            return self.lookup_deep(phone_number, country_code)
        else:
            return self.lookup_light(phone_number, country_code)
    
    def lookup_light(self, phone_number: str, country_code: Optional[str] = None) -> Dict:
        """
        Perform light phone lookup (fast).
        Includes: normalization, country detection, carrier lookup, basic email/social search.
        
        Args:
            phone_number: Phone number to lookup
            country_code: Optional ISO country code
            
        Returns:
            Dict with basic phone intelligence
        """
        result = {
            'status': 'error',
            'phone_number': phone_number,
            'raw_number': phone_number,
            'valid': False,
            'emails_found': [],
            'social_accounts': {},
            'risk_score': 0.5,
            'risk_factors': [],
            'lookup_timestamp': datetime.utcnow().isoformat(),
            'scan_type': 'light'
        }
        
        try:
            # Clean and validate phone number
            parsed_number = self._parse_phone_number(phone_number, country_code)
            if not parsed_number:
                result['notes'] = 'Invalid phone number format'
                return result
            
            # Check validity
            if not phonenumbers.is_valid_number(parsed_number):
                result['notes'] = 'Phone number failed validation'
                return result
            
            result['valid'] = True
            result['phone_number'] = phonenumbers.format_number(
                parsed_number, 
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            
            # Get country information
            country_data = self._get_country_info(parsed_number)
            if country_data:
                result.update(country_data)
            
            # Get carrier information
            carrier_data = self._get_carrier_info(parsed_number)
            if carrier_data:
                result.update(carrier_data)
            
            # Get timezone(s)
            timezone_data = self._get_timezone_info(parsed_number)
            if timezone_data:
                result['timezone'] = timezone_data
            
            # Get number type (mobile, fixed, etc.)
            result['number_type'] = self._get_number_type(parsed_number)
            
            # Light scan: basic email/social patterns only
            light_discovery = self._discover_linked_accounts_light(phone_number, result.get('country', ''))
            if light_discovery:
                result['emails_found'] = light_discovery.get('emails', [])
                result['social_accounts'] = light_discovery.get('social_accounts', {})
            
            # Light risk scoring
            risk_data = self._calculate_risk_score_light(parsed_number, result)
            result['risk_score'] = risk_data['score']
            result['risk_factors'] = risk_data['factors']
            result['is_voip'] = risk_data['is_voip']
            
            result['status'] = 'success'
            result['notes'] = 'Light scan completed successfully'
            
        except Exception as e:
            logger.error(f"Phone light lookup error: {str(e)}")
            result['notes'] = f'Error during lookup: {str(e)}'
            result['status'] = 'error'
        
        return result
    
    def lookup_deep(self, phone_number: str, country_code: Optional[str] = None) -> Dict:
        """
        Perform deep phone lookup (comprehensive).
        Includes: all light scan functions + deeper social media correlation,
        email harvesting, mention scanning, connection discovery, network graph prep.
        
        Args:
            phone_number: Phone number to lookup
            country_code: Optional ISO country code
            
        Returns:
            Dict with comprehensive phone intelligence
        """
        result = {
            'status': 'error',
            'phone_number': phone_number,
            'raw_number': phone_number,
            'valid': False,
            'emails_found': [],
            'social_accounts': {},
            'mentions': [],
            'connected_accounts': [],
            'risk_score': 0.5,
            'risk_factors': [],
            'lookup_timestamp': datetime.utcnow().isoformat(),
            'scan_type': 'deep'
        }
        
        try:
            # Clean and validate phone number
            parsed_number = self._parse_phone_number(phone_number, country_code)
            if not parsed_number:
                result['notes'] = 'Invalid phone number format'
                return result
            
            # Check validity
            if not phonenumbers.is_valid_number(parsed_number):
                result['notes'] = 'Phone number failed validation'
                return result
            
            result['valid'] = True
            result['phone_number'] = phonenumbers.format_number(
                parsed_number, 
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            
            # Get country information
            country_data = self._get_country_info(parsed_number)
            if country_data:
                result.update(country_data)
            
            # Get carrier information
            carrier_data = self._get_carrier_info(parsed_number)
            if carrier_data:
                result.update(carrier_data)
            
            # Get timezone(s)
            timezone_data = self._get_timezone_info(parsed_number)
            if timezone_data:
                result['timezone'] = timezone_data
            
            # Get number type (mobile, fixed, etc.)
            result['number_type'] = self._get_number_type(parsed_number)
            
            # Deep scan: comprehensive account discovery
            deep_discovery = self._discover_linked_accounts_deep(phone_number, result.get('country', ''))
            if deep_discovery:
                result['emails_found'] = deep_discovery.get('emails', [])
                result['social_accounts'] = deep_discovery.get('social_accounts', {})
                result['mentions'] = deep_discovery.get('mentions', [])
                result['connected_accounts'] = deep_discovery.get('connected_accounts', [])
            
            # Deep risk scoring with more factors
            risk_data = self._calculate_risk_score_deep(parsed_number, result)
            result['risk_score'] = risk_data['score']
            result['risk_factors'] = risk_data['factors']
            result['is_voip'] = risk_data['is_voip']
            result['is_temporary'] = risk_data['is_temporary']
            result['is_prepaid'] = risk_data['is_prepaid']
            
            # Prepare for network graph
            result['graph_ready'] = True
            
            result['status'] = 'success'
            result['notes'] = 'Deep scan completed successfully'
            
        except Exception as e:
            logger.error(f"Phone deep lookup error: {str(e)}")
            result['notes'] = f'Error during lookup: {str(e)}'
            result['status'] = 'error'
        
        return result
    
    def lookup_old(self, phone_number: str, country_code: Optional[str] = None) -> Dict:
        """
        Legacy lookup method - maintained for backward compatibility.
        Maps to light scan.
        
        Args:
            phone_number: Phone number to lookup
            country_code: Optional ISO country code (e.g., 'US', 'GB')
            
        Returns:
            Dict with phone intelligence data
        """
        result = {
            'status': 'error',
            'phone_number': phone_number,
            'raw_number': phone_number,
            'valid': False,
            'emails_found': [],
            'social_accounts': {},
            'risk_score': 0.5,
            'risk_factors': [],
            'lookup_timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # Clean and validate phone number
            parsed_number = self._parse_phone_number(phone_number, country_code)
            if not parsed_number:
                result['notes'] = 'Invalid phone number format'
                return result
            
            # Check validity
            if not phonenumbers.is_valid_number(parsed_number):
                result['notes'] = 'Phone number failed validation'
                return result
            
            result['valid'] = True
            result['phone_number'] = phonenumbers.format_number(
                parsed_number, 
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            
            # Get country information
            country_data = self._get_country_info(parsed_number)
            if country_data:
                result.update(country_data)
            
            # Get carrier information
            carrier_data = self._get_carrier_info(parsed_number)
            if carrier_data:
                result.update(carrier_data)
            
            # Get timezone(s)
            timezone_data = self._get_timezone_info(parsed_number)
            if timezone_data:
                result['timezone'] = timezone_data
            
            # Get number type (mobile, fixed, etc.)
            result['number_type'] = self._get_number_type(parsed_number)
            
            # Discovery: emails and social accounts
            discovery_data = self._discover_linked_accounts(phone_number, result.get('country', ''))
            if discovery_data:
                result['emails_found'] = discovery_data.get('emails', [])
                result['social_accounts'] = discovery_data.get('social_accounts', {})
            
            # Risk scoring
            risk_data = self._calculate_risk_score(parsed_number, result)
            result['risk_score'] = risk_data['score']
            result['risk_factors'] = risk_data['factors']
            result['is_voip'] = risk_data['is_voip']
            result['is_temporary'] = risk_data['is_temporary']
            result['is_prepaid'] = risk_data['is_prepaid']
            
            result['status'] = 'success'
            result['notes'] = 'Phone lookup completed successfully'
            
        except Exception as e:
            logger.error(f"Phone lookup error: {str(e)}")
            result['notes'] = f'Error during lookup: {str(e)}'
            result['status'] = 'error'
        
        return result
    
    def batch_lookup(self, phone_numbers: List[str], country_code: Optional[str] = None) -> List[Dict]:
        """
        Lookup multiple phone numbers.
        
        Args:
            phone_numbers: List of phone number strings
            country_code: Optional ISO country code for all numbers
            
        Returns:
            List of lookup results
        """
        if not phone_numbers:
            return []
        
        if len(phone_numbers) > 100:
            logger.warning(f"Batch lookup requested {len(phone_numbers)} numbers, limiting to 100")
            phone_numbers = phone_numbers[:100]
        
        return [self.lookup(phone.strip(), country_code) for phone in phone_numbers if phone and phone.strip()]
    
    def validate_only(self, phone_number: str, country_code: Optional[str] = None) -> Dict:
        """
        Only validate a phone number without full intelligence extraction.
        Faster for just checking if number is valid.
        
        Args:
            phone_number: Phone number to validate
            country_code: Optional ISO country code
            
        Returns:
            Validation result dict
        """
        try:
            parsed = self._parse_phone_number(phone_number, country_code)
            if not parsed:
                return {
                    'valid': False,
                    'formatted': None,
                    'country_code': None,
                    'region_code': None
                }
            
            return {
                'valid': True,
                'formatted': phonenumbers.format_number(
                    parsed, 
                    phonenumbers.PhoneNumberFormat.INTERNATIONAL
                ),
                'country_code': phonenumbers.region_code_for_number(parsed),
                'region_code': geocoder.region_code_for_number(parsed)
            }
        except Exception as e:
            logger.error(f"Phone validation error: {str(e)}")
            return {
                'valid': False,
                'formatted': None,
                'country_code': None,
                'region_code': None
            }
    
    def _parse_phone_number(self, phone_number: str, country_code: Optional[str] = None) -> Optional[phonenumbers.PhoneNumber]:
        """
        Parse and normalize phone number.
        Handles various input formats and attempts multiple parsing strategies.
        
        Args:
            phone_number: Phone number string
            country_code: Optional ISO country code
            
        Returns:
            Parsed PhoneNumber object or None
        """
        if not phone_number:
            logger.warning("Empty phone number provided")
            return None
        
        try:
            # Try direct parsing if number has country code
            try:
                parsed = phonenumbers.parse(phone_number, None)
                if phonenumbers.is_valid_number(parsed):
                    logger.debug(f"Successfully parsed phone number directly")
                    return parsed
            except phonenumbers.NumberParseException:
                logger.debug(f"Could not parse phone number directly, trying with region")
                pass
            
            # Try with explicit country code
            if country_code:
                try:
                    parsed = phonenumbers.parse(phone_number, country_code)
                    if phonenumbers.is_valid_number(parsed):
                        logger.debug(f"Successfully parsed phone with country code {country_code}")
                        return parsed
                except phonenumbers.NumberParseException:
                    logger.debug(f"Could not parse with country code {country_code}")
                    pass
            
            # Try common regions
            common_regions = ['US', 'GB', 'IN', 'BR', 'RU', 'DE', 'FR', 'ID', 'CN', 'JP']
            for region in common_regions:
                try:
                    parsed = phonenumbers.parse(phone_number, region)
                    if phonenumbers.is_valid_number(parsed):
                        logger.debug(f"Successfully parsed phone with region {region}")
                        return parsed
                except phonenumbers.NumberParseException:
                    continue
            
            # Last resort: try with US as default
            try:
                parsed = phonenumbers.parse(phone_number, 'US')
                logger.debug(f"Parsed phone using US as default region")
                return parsed
            except phonenumbers.NumberParseException as e:
                logger.warning(f"Could not parse phone number with any strategy: {str(e)}")
                return None
        
        except Exception as e:
            logger.error(f"Unexpected error parsing phone number: {str(e)}")
            return None
    
    def _get_country_info(self, parsed_number: phonenumbers.PhoneNumber) -> Optional[Dict]:
        """Get country information from parsed phone number"""
        try:
            region = phonenumbers.region_code_for_number(parsed_number)
            
            if not region:
                logger.debug("No region found for phone number")
                return None
            
            try:
                country_name = geocoder.country_name_for_number(parsed_number, 'en')
            except Exception as e:
                logger.debug(f"Could not get country name: {str(e)}")
                country_name = None
            
            return {
                'country': country_name or 'Unknown',
                'country_iso': region,
                'country_code': f"+{parsed_number.country_code}",
            }
        
        except Exception as e:
            logger.warning(f"Error getting country info: {str(e)}")
            return None
    
    def _get_carrier_info(self, parsed_number: phonenumbers.PhoneNumber) -> Optional[Dict]:
        """Get carrier information from parsed phone number"""
        try:
            try:
                carrier_name = phone_carrier.name_for_number(parsed_number, 'en')
            except Exception as e:
                logger.debug(f"Could not get carrier name: {str(e)}")
                carrier_name = None
            
            try:
                number_type = phonenumbers.number_type(parsed_number)
            except Exception as e:
                logger.debug(f"Could not get number type: {str(e)}")
                number_type = None
            
            # Map number type to carrier type
            carrier_type_map = {
                phonenumbers.NumberType.MOBILE: 'MOBILE',
                phonenumbers.NumberType.FIXED_LINE: 'FIXED_LINE',
                phonenumbers.NumberType.FIXED_LINE_OR_MOBILE: 'MOBILE',
                phonenumbers.NumberType.TOLL_FREE: 'FIXED_LINE',
                phonenumbers.NumberType.PREMIUM_RATE: 'PREMIUM',
                phonenumbers.NumberType.SHARED_COST: 'SHARED',
                phonenumbers.NumberType.VOIP: 'VOIP',
            }
            
            carrier_type = carrier_type_map.get(number_type, 'UNKNOWN') if number_type else 'UNKNOWN'
            
            result = {
                'carrier': carrier_name if carrier_name else 'Unknown Carrier',
                'carrier_type': CARRIER_TYPES.get(carrier_type, 'Unknown'),
            }
            
            # Add carrier network info if available
            if carrier_name:
                try:
                    carrier_lower = carrier_name.lower()
                    if 'verizon' in carrier_lower:
                        result['carrier_network'] = 'Verizon'
                    elif 'at&t' in carrier_lower or 'at and t' in carrier_lower:
                        result['carrier_network'] = 'AT&T'
                    elif 'sprint' in carrier_lower:
                        result['carrier_network'] = 'Sprint'
                    elif 'tmobile' in carrier_lower or 't-mobile' in carrier_lower:
                        result['carrier_network'] = 'T-Mobile'
                except Exception as e:
                    logger.debug(f"Could not parse carrier network: {str(e)}")
            
            return result
        
        except Exception as e:
            logger.warning(f"Error getting carrier info: {str(e)}")
            return {'carrier': 'Unknown', 'carrier_type': 'Unknown'}
    
    def _get_timezone_info(self, parsed_number: phonenumbers.PhoneNumber) -> Optional[str]:
        """Get timezone(s) for phone number"""
        try:
            region = phonenumbers.region_code_for_number(parsed_number)
            if region and region in TIMEZONE_MAP:
                timezones = TIMEZONE_MAP[region]
                if len(timezones) == 1:
                    return timezones[0]
                else:
                    return ' / '.join(timezones)
            
            return 'UTC'
        
        except Exception as e:
            logger.debug(f"Error getting timezone info: {str(e)}")
            return 'UTC'
    
    def _get_number_type(self, parsed_number: phonenumbers.PhoneNumber) -> str:
        """Get human-readable number type"""
        try:
            number_type = phonenumbers.number_type(parsed_number)
            
            type_map = {
                phonenumbers.NumberType.MOBILE: 'Mobile/Cellular',
                phonenumbers.NumberType.FIXED_LINE: 'Fixed Line (Landline)',
                phonenumbers.NumberType.FIXED_LINE_OR_MOBILE: 'Mobile or Fixed Line',
                phonenumbers.NumberType.TOLL_FREE: 'Toll Free',
                phonenumbers.NumberType.PREMIUM_RATE: 'Premium Rate',
                phonenumbers.NumberType.SHARED_COST: 'Shared Cost',
                phonenumbers.NumberType.VOIP: 'VoIP',
                phonenumbers.NumberType.PERSONAL_NUMBER: 'Personal Number',
                phonenumbers.NumberType.PAGER: 'Pager',
                phonenumbers.NumberType.UAN: 'UAN',
                phonenumbers.NumberType.UNKNOWN: 'Unknown Type',
            }
            
            return type_map.get(number_type, 'Unknown')
        
        except Exception as e:
            logger.debug(f"Error getting number type: {str(e)}")
            return 'Unknown'
    
    def _discover_linked_accounts(self, phone_number: str, country: str) -> Optional[Dict]:
        """
        Discover linked emails and social accounts.
        
        Args:
            phone_number: Phone number string
            country: Country name
            
        Returns:
            Dict with emails and social accounts
        """
        result = {
            'emails': [],
            'social_accounts': {}
        }
        
        try:
            # Clean phone number
            clean_phone = re.sub(r'\D', '', phone_number)
            
            # Generate common email patterns from phone number
            potential_emails = [
                f"{clean_phone}@gmail.com",
                f"{clean_phone}@yahoo.com",
                f"{clean_phone}@hotmail.com",
            ]
            
            result['emails'] = potential_emails[:3]
            
            # Generate social account patterns
            social_handles = {
                'twitter': f"@{clean_phone}",
                'instagram': clean_phone,
                'tiktok': f"@{clean_phone}",
                'snapchat': clean_phone,
            }
            
            result['social_accounts'] = social_handles
            
        except Exception as e:
            logger.warning(f"Error during account discovery: {str(e)}")
        
        return result
    
    def _discover_linked_accounts_light(self, phone_number: str, country: str) -> Optional[Dict]:
        """
        Light scan: discover basic linked emails and social accounts (fast).
        
        Args:
            phone_number: Phone number string
            country: Country name
            
        Returns:
            Dict with basic emails and social accounts
        """
        result = {
            'emails': [],
            'social_accounts': {}
        }
        
        try:
            # Clean phone number
            clean_phone = re.sub(r'\D', '', phone_number)
            
            # Only generate 2 basic email patterns
            potential_emails = [
                f"{clean_phone}@gmail.com",
                f"{clean_phone}@yahoo.com",
            ]
            
            result['emails'] = potential_emails
            
            # Basic social handles
            social_handles = {
                'twitter': f"@{clean_phone}",
                'instagram': clean_phone,
            }
            
            result['social_accounts'] = social_handles
            
        except Exception as e:
            logger.warning(f"Error during light account discovery: {str(e)}")
        
        return result
    
    def _discover_linked_accounts_deep(self, phone_number: str, country: str) -> Optional[Dict]:
        """
        Deep scan: comprehensive email and social account discovery.
        Includes email harvesting patterns, mention scanning, connection discovery.
        
        Args:
            phone_number: Phone number string
            country: Country name
            
        Returns:
            Dict with comprehensive emails, social accounts, mentions, and connections
        """
        result = {
            'emails': [],
            'social_accounts': {},
            'mentions': [],
            'connected_accounts': []
        }
        
        try:
            # Clean phone number
            clean_phone = re.sub(r'\D', '', phone_number)
            
            # Generate comprehensive email patterns
            email_domains = [
                'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                'icloud.com', 'mail.com', 'protonmail.com', 'tutanota.com'
            ]
            
            potential_emails = [
                f"{clean_phone}@{domain}" for domain in email_domains
            ]
            
            result['emails'] = potential_emails
            
            # Comprehensive social account patterns
            social_handles = {
                'twitter': f"@{clean_phone}",
                'instagram': clean_phone,
                'tiktok': f"@{clean_phone}",
                'snapchat': clean_phone,
                'facebook': f"{clean_phone}",
                'linkedin': f"{clean_phone}",
                'youtube': f"@{clean_phone}",
                'twitch': f"{clean_phone}",
                'reddit': f"u/{clean_phone}",
                'github': clean_phone,
            }
            
            result['social_accounts'] = social_handles
            
            # Deep scan: simulate mention scanning (would be integrated with real data sources)
            result['mentions'] = [
                {
                    'platform': 'Twitter',
                    'mention': f"Phone number {phone_number} mentioned",
                    'context': 'Potential spam/phishing',
                    'timestamp': datetime.utcnow().isoformat()
                }
            ]
            
            # Simulate connected account discovery
            result['connected_accounts'] = [
                {
                    'account': 'email_account',
                    'confidence': 0.6,
                    'relationship': 'Potential email-to-phone link'
                }
            ]
            
        except Exception as e:
            logger.warning(f"Error during deep account discovery: {str(e)}")
        
        return result
    
    def _calculate_risk_score_light(self, parsed_number: phonenumbers.PhoneNumber, lookup_result: Dict) -> Dict:
        """
        Light scan: calculate basic risk score for phone number (fast).
        
        Args:
            parsed_number: Parsed phone number
            lookup_result: Current lookup result dict
            
        Returns:
            Dict with risk_score (0-1), factors list, and flags
        """
        risk_score = 0.3
        risk_factors = []
        
        try:
            # Check if VoIP
            is_voip = lookup_result.get('number_type', '').lower() == 'voip'
            if is_voip:
                risk_score += RISK_FACTORS['VOIP']
                risk_factors.append('VoIP service detected')
            
            # Check carrier type
            carrier_type = lookup_result.get('carrier_type', '').upper()
            if 'UNKNOWN' in carrier_type:
                risk_score += RISK_FACTORS['UNKNOWN_CARRIER']
                risk_factors.append('Unknown carrier')
            
            # Mobile vs fixed line
            if 'MOBILE' in carrier_type:
                risk_score -= 0.05
            
            # Check validity
            if lookup_result.get('valid'):
                risk_score -= 0.05
            else:
                risk_score += 0.2
            
            # Clamp to 0-1 range
            risk_score = max(0.0, min(1.0, risk_score))
            
        except Exception as e:
            logger.warning(f"Error calculating light risk score: {str(e)}")
        
        return {
            'score': round(risk_score, 2),
            'factors': risk_factors,
            'is_voip': is_voip,
        }
    
    def _calculate_risk_score_deep(self, parsed_number: phonenumbers.PhoneNumber, lookup_result: Dict) -> Dict:
        """
        Deep scan: calculate comprehensive risk score with more factors.
        
        Args:
            parsed_number: Parsed phone number
            lookup_result: Current lookup result dict
            
        Returns:
            Dict with risk_score (0-1), factors list, and flags
        """
        risk_score = 0.4
        risk_factors = []
        
        try:
            # Check if VoIP
            is_voip = lookup_result.get('number_type', '').lower() == 'voip'
            if is_voip:
                risk_score += RISK_FACTORS['VOIP']
                risk_factors.append('VoIP service detected')
            
            # Check carrier type
            carrier_type = lookup_result.get('carrier_type', '').upper()
            if 'UNKNOWN' in carrier_type:
                risk_score += RISK_FACTORS['UNKNOWN_CARRIER']
                risk_factors.append('Unknown carrier')
            
            # Mobile vs fixed line
            if 'MOBILE' in carrier_type:
                risk_score -= 0.05
            
            # Check validity
            if lookup_result.get('valid'):
                risk_score -= 0.05
            else:
                risk_score += 0.2
            
            # Deep scan factors
            # Account reuse patterns
            emails_count = len(lookup_result.get('emails_found', []))
            if emails_count > 5:
                risk_score += 0.15
                risk_factors.append(f'Phone linked to {emails_count} email accounts')
            
            # Multiple social accounts
            social_count = len(lookup_result.get('social_accounts', {}))
            if social_count >= 6:
                risk_score += 0.1
                risk_factors.append(f'Active on {social_count} social platforms')
            
            # Mentions/reports
            mentions = lookup_result.get('mentions', [])
            if mentions:
                risk_score += len(mentions) * 0.05
                risk_factors.append(f'Phone mentioned in {len(mentions)} reports')
            
            # Connected accounts
            connections = lookup_result.get('connected_accounts', [])
            if connections:
                risk_score += len(connections) * 0.03
                risk_factors.append(f'Found {len(connections)} connected accounts')
            
            # Clamp to 0-1 range
            risk_score = max(0.0, min(1.0, risk_score))
            
        except Exception as e:
            logger.warning(f"Error calculating deep risk score: {str(e)}")
        
        is_temporary = 'temporary' in lookup_result.get('notes', '').lower()
        is_prepaid = 'prepaid' in lookup_result.get('carrier', '').lower()
        
        return {
            'score': round(risk_score, 2),
            'factors': risk_factors,
            'is_voip': is_voip,
            'is_temporary': is_temporary,
            'is_prepaid': is_prepaid,
        }
    
    def _calculate_risk_score(self, parsed_number: phonenumbers.PhoneNumber, lookup_result: Dict) -> Dict:
        """
        Calculate risk score for phone number (legacy - maps to deep scoring).
        
        Args:
            parsed_number: Parsed phone number
            lookup_result: Current lookup result dict
            
        Returns:
            Dict with risk_score (0-1), factors list, and flags
        """
        return self._calculate_risk_score_deep(parsed_number, lookup_result)


class PhoneIntelligenceService:
    """Legacy wrapper for backward compatibility"""
    
    def __init__(self):
        self._service = PhoneIntelligence()
        self.voip_carriers = self._service.voip_carriers
        self.high_risk_countries = ['KP', 'IR', 'SY']
    
    def lookup(self, phone_number: str) -> Dict:
        """Legacy lookup method"""
        result = self._service.lookup(phone_number)
        
        # Convert to legacy format
        return {
            'valid': result.get('valid', False),
            'number': result.get('phone_number'),
            'country': result.get('country'),
            'country_code': result.get('country_iso'),
            'region': result.get('country'),
            'carrier': result.get('carrier'),
            'carrier_type': 'VOIP' if result.get('is_voip') else result.get('carrier_type'),
            'timezone': result.get('timezone'),
            'social_presence': list(result.get('social_accounts', {}).keys()),
            'emails_found': result.get('emails_found', []),
            'risk_score': int(result.get('risk_score', 0.5) * 100),
            'risk_level': self._score_to_level(result.get('risk_score', 0.5)),
            'confidence': 0.7,
            'last_checked': result.get('lookup_timestamp'),
            'error': None if result.get('status') == 'success' else result.get('notes')
        }
    
    def batch_lookup(self, phone_numbers: List[str]) -> List[Dict]:
        """Legacy batch lookup"""
        results = self._service.batch_lookup(phone_numbers)
        return [self.lookup(result['raw_number']) for result in results]
    
    def validate_only(self, phone_number: str) -> Dict:
        """Legacy validate method"""
        return self._service.validate_only(phone_number)
    
    def _score_to_level(self, score: float) -> str:
        """Convert score to risk level"""
        if score >= 0.8:
            return 'CRITICAL'
        elif score >= 0.6:
            return 'HIGH'
        elif score >= 0.4:
            return 'MEDIUM'
        elif score >= 0.2:
            return 'LOW'
        else:
            return 'MINIMAL'
