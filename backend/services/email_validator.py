"""Email validation and verification service

Provides multiple email validation strategies:
- Syntax validation (RFC 5322 compliant)
- MX record checking
- SMTP verification (connect to server without sending)
- External API validation (when available)
- Disposable email detection
- Corporate email verification

Multi-strategy approach with fallback mechanisms.
"""

import re
import logging
import socket
import smtplib
import requests
from typing import Dict, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Extended RFC 5322 email regex
RFC5322_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)

# Common disposable email domains
DISPOSABLE_DOMAINS = {
    'tempmail.com', 'throwaway.email', '10minutemail.com',
    'mailinator.com', 'maildrop.cc', 'temp-mail.org',
    'yopmail.com', 'trashmail.com', 'fake-mail.com',
    'spam4.me', 'temp.email', 'tempemailaddress.com'
}


class EmailValidator:
    """Comprehensive email validation with multiple strategies"""
    
    def __init__(self, api_key=None):
        """
        Initialize email validator
        
        Args:
            api_key: Optional external API key for advanced validation
        """
        self.api_key = api_key
        self.timeout = 5
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def validate_syntax(self, email: str) -> Dict[str, any]:
        """
        Validate email syntax against RFC 5322
        
        Args:
            email: Email address to validate
            
        Returns:
            Dict with validation result and details
        """
        result = {
            'email': email,
            'valid': False,
            'reason': '',
            'checks': {}
        }
        
        if not email or not isinstance(email, str):
            result['reason'] = 'Email is empty or not a string'
            return result
        
        email = email.strip().lower()
        result['email'] = email
        
        # Basic checks
        if len(email) > 254:
            result['reason'] = 'Email exceeds maximum length (254 characters)'
            result['checks']['length'] = False
            return result
        
        result['checks']['length'] = True
        
        # Check for valid characters and format
        if not RFC5322_REGEX.match(email):
            result['reason'] = 'Email format does not match RFC 5322'
            result['checks']['format'] = False
            return result
        
        result['checks']['format'] = True
        
        # Check for consecutive dots
        if '..' in email:
            result['reason'] = 'Email contains consecutive dots'
            result['checks']['consecutive_dots'] = False
            return result
        
        result['checks']['consecutive_dots'] = True
        
        # Check if starts/ends with dot
        local_part = email.split('@')[0]
        if local_part.startswith('.') or local_part.endswith('.'):
            result['reason'] = 'Local part starts or ends with dot'
            result['checks']['dot_position'] = False
            return result
        
        result['checks']['dot_position'] = True
        result['valid'] = True
        result['reason'] = 'Syntax validation passed'
        
        return result
    
    def check_mx_record(self, email: str) -> Dict[str, any]:
        """
        Check if domain has valid MX records
        
        Args:
            email: Email address to check
            
        Returns:
            Dict with MX check result
        """
        result = {
            'email': email,
            'has_mx': False,
            'records': [],
            'error': None
        }
        
        try:
            domain = email.split('@')[1]
            
            # Try to get MX records
            import dns.resolver
            
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                result['has_mx'] = True
                result['records'] = [str(mx) for mx in mx_records]
                logger.info(f"MX records found for {domain}: {len(result['records'])} records")
            except Exception as e:
                result['error'] = f"MX lookup failed: {str(e)}"
                logger.debug(f"MX lookup error for {domain}: {e}")
        
        except Exception as e:
            result['error'] = f"Error checking MX: {str(e)}"
            logger.debug(f"MX check error: {e}")
        
        return result
    
    def smtp_verify(self, email: str) -> Dict[str, any]:
        """
        Attempt SMTP verification without sending email
        WARNING: Some servers may flag this as suspicious, use cautiously
        
        Args:
            email: Email address to verify
            
        Returns:
            Dict with SMTP verification result
        """
        result = {
            'email': email,
            'smtp_valid': False,
            'error': None
        }
        
        try:
            # Extract domain
            domain = email.split('@')[1]
            
            # Get MX records
            import dns.resolver
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                if not mx_records:
                    result['error'] = 'No MX records found'
                    return result
            except Exception as e:
                result['error'] = f"MX lookup failed: {str(e)}"
                return result
            
            # Try SMTP verification on first MX server
            mx_server = str(mx_records[0].exchange)
            
            try:
                server = smtplib.SMTP(mx_server, timeout=self.timeout)
                server.ehlo()
                
                # Try to verify
                code, msg = server.verify(email)
                
                if code == 250:
                    result['smtp_valid'] = True
                    logger.info(f"SMTP verification succeeded for {email}")
                else:
                    result['error'] = f"SMTP verification returned code {code}"
                
                server.quit()
            
            except smtplib.SMTPServerDisconnected:
                result['error'] = 'SMTP server disconnected'
            except smtplib.SMTPException as e:
                result['error'] = f"SMTP error: {str(e)}"
            except socket.timeout:
                result['error'] = 'SMTP timeout'
            except Exception as e:
                result['error'] = f"SMTP verification error: {str(e)}"
        
        except Exception as e:
            result['error'] = f"Error in SMTP verification: {str(e)}"
        
        return result
    
    def check_disposable(self, email: str) -> Dict[str, any]:
        """
        Check if email uses a disposable/temporary service
        
        Args:
            email: Email address to check
            
        Returns:
            Dict with disposable status
        """
        result = {
            'email': email,
            'is_disposable': False,
            'domain': '',
            'type': None
        }
        
        try:
            domain = email.split('@')[1].lower()
            result['domain'] = domain
            
            # Check against known disposable domains
            if domain in DISPOSABLE_DOMAINS:
                result['is_disposable'] = True
                result['type'] = 'known_disposable'
                logger.debug(f"Email {email} uses known disposable domain")
                return result
            
            # Check common patterns
            suspicious_patterns = [
                'temp', 'trash', 'fake', 'test', 'spam',
                'random', 'throw', 'mail', 'catch'
            ]
            
            for pattern in suspicious_patterns:
                if pattern in domain:
                    result['is_disposable'] = True
                    result['type'] = 'suspected_disposable'
                    logger.debug(f"Email {email} may use disposable-like domain")
                    break
        
        except Exception as e:
            logger.debug(f"Disposable check error: {e}")
        
        return result
    
    def validate_comprehensive(self, email: str, use_smtp=False) -> Dict[str, any]:
        """
        Comprehensive email validation using multiple strategies
        
        Args:
            email: Email to validate
            use_smtp: Whether to attempt SMTP verification (risky, use cautiously)
            
        Returns:
            Dict with comprehensive validation result and confidence score
        """
        result = {
            'email': email,
            'valid': False,
            'confidence': 0.0,
            'details': {},
            'verification_passed': 0,
            'total_checks': 0
        }
        
        try:
            # 1. Syntax validation
            syntax_result = self.validate_syntax(email)
            result['details']['syntax'] = syntax_result
            result['total_checks'] += 1
            if syntax_result['valid']:
                result['verification_passed'] += 1
            
            # 2. Disposable check
            disposable_result = self.check_disposable(email)
            result['details']['disposable'] = disposable_result
            result['total_checks'] += 1
            if not disposable_result['is_disposable']:
                result['verification_passed'] += 1
            
            # 3. MX record check
            mx_result = self.check_mx_record(email)
            result['details']['mx_check'] = mx_result
            result['total_checks'] += 1
            if mx_result['has_mx']:
                result['verification_passed'] += 1
            
            # 4. Optional SMTP verification
            if use_smtp:
                smtp_result = self.smtp_verify(email)
                result['details']['smtp'] = smtp_result
                result['total_checks'] += 1
                if smtp_result['smtp_valid']:
                    result['verification_passed'] += 1
            
            # Calculate confidence score
            result['confidence'] = result['verification_passed'] / result['total_checks'] if result['total_checks'] > 0 else 0.0
            result['valid'] = result['confidence'] >= 0.7  # 70% threshold
            
            logger.info(f"Email validation complete for {email}: confidence={result['confidence']:.2%}")
            
        except Exception as e:
            logger.error(f"Error in comprehensive validation: {e}")
            result['error'] = str(e)
        
        return result
    
    def batch_validate(self, emails: list, use_smtp=False) -> Dict[str, any]:
        """
        Validate multiple emails efficiently
        
        Args:
            emails: List of email addresses
            use_smtp: Whether to use SMTP verification
            
        Returns:
            Dict with batch validation results
        """
        result = {
            'total': len(emails),
            'valid': [],
            'invalid': [],
            'suspended': []
        }
        
        for email in emails:
            try:
                val_result = self.validate_comprehensive(email, use_smtp=use_smtp)
                
                if val_result['valid']:
                    result['valid'].append({
                        'email': email,
                        'confidence': val_result['confidence'],
                        'details': val_result['details']
                    })
                else:
                    if val_result['details'].get('smtp', {}).get('error', '').lower().count('suspended') > 0:
                        result['suspended'].append({
                            'email': email,
                            'reason': 'SMTP indicated suspended'
                        })
                    else:
                        result['invalid'].append({
                            'email': email,
                            'reason': val_result['details'].get('syntax', {}).get('reason', 'Unknown'),
                            'confidence': val_result['confidence']
                        })
            
            except Exception as e:
                logger.error(f"Error validating {email}: {e}")
                result['invalid'].append({
                    'email': email,
                    'reason': f'Error: {str(e)}'
                })
        
        result['valid_count'] = len(result['valid'])
        result['invalid_count'] = len(result['invalid'])
        result['suspended_count'] = len(result['suspended'])
        
        return result
