"""Phone Routes
Handles phone number intelligence lookup (Ghost.py-style).
Returns carrier, country, timezone, social presence, emails found, and network graph nodes.
Supports country detection and searchable country dropdown.
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from database import db
from sqlalchemy.exc import IntegrityError
from models import PhoneIntelligence as PhoneIntelModel, Investigation
from services.phone_intel import PhoneIntelligence as PhoneIntelService
from utils import APIResponse, Validator, generate_case_id
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import re
import uuid
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)

phone_bp = Blueprint('phone', __name__, url_prefix='/api/phone')

# International countries with dial codes (expanded list)
SUPPORTED_COUNTRIES = {
    'US': {'code': '+1', 'name': 'United States', 'flag': '🇺🇸'},
    'CA': {'code': '+1', 'name': 'Canada', 'flag': '🇨🇦'},
    'GB': {'code': '+44', 'name': 'United Kingdom', 'flag': '🇬🇧'},
    'AU': {'code': '+61', 'name': 'Australia', 'flag': '🇦🇺'},
    'DE': {'code': '+49', 'name': 'Germany', 'flag': '🇩🇪'},
    'FR': {'code': '+33', 'name': 'France', 'flag': '🇫🇷'},
    'IN': {'code': '+91', 'name': 'India', 'flag': '🇮🇳'},
    'CN': {'code': '+86', 'name': 'China', 'flag': '🇨🇳'},
    'BR': {'code': '+55', 'name': 'Brazil', 'flag': '🇧🇷'},
    'RU': {'code': '+7', 'name': 'Russia', 'flag': '🇷🇺'},
    'JP': {'code': '+81', 'name': 'Japan', 'flag': '🇯🇵'},
    'KR': {'code': '+82', 'name': 'South Korea', 'flag': '🇰🇷'},
    'ZA': {'code': '+27', 'name': 'South Africa', 'flag': '🇿🇦'},
    'GH': {'code': '+233', 'name': 'Ghana', 'flag': '🇬🇭'},
    'NG': {'code': '+234', 'name': 'Nigeria', 'flag': '🇳🇬'},
    'MX': {'code': '+52', 'name': 'Mexico', 'flag': '🇲🇽'},
    'NL': {'code': '+31', 'name': 'Netherlands', 'flag': '🇳🇱'},
    'SE': {'code': '+46', 'name': 'Sweden', 'flag': '🇸🇪'},
    'SG': {'code': '+65', 'name': 'Singapore', 'flag': '🇸🇬'},
    'AE': {'code': '+971', 'name': 'United Arab Emirates', 'flag': '🇦🇪'},
    'KE': {'code': '+254', 'name': 'Kenya', 'flag': '🇰🇪'},
    'TZ': {'code': '+255', 'name': 'Tanzania', 'flag': '🇹🇿'},
    'UG': {'code': '+256', 'name': 'Uganda', 'flag': '🇺🇬'},
    'PL': {'code': '+48', 'name': 'Poland', 'flag': '🇵🇱'},
    'IT': {'code': '+39', 'name': 'Italy', 'flag': '🇮🇹'},
    'ES': {'code': '+34', 'name': 'Spain', 'flag': '🇪🇸'},
    'TH': {'code': '+66', 'name': 'Thailand', 'flag': '🇹🇭'},
    'PH': {'code': '+63', 'name': 'Philippines', 'flag': '🇵🇭'},
    'VN': {'code': '+84', 'name': 'Vietnam', 'flag': '🇻🇳'},
    'ID': {'code': '+62', 'name': 'Indonesia', 'flag': '🇮🇩'},
    'MY': {'code': '+60', 'name': 'Malaysia', 'flag': '🇲🇾'},
    'BD': {'code': '+880', 'name': 'Bangladesh', 'flag': '🇧🇩'},
    'PK': {'code': '+92', 'name': 'Pakistan', 'flag': '🇵🇰'},
    'PT': {'code': '+351', 'name': 'Portugal', 'flag': '🇵🇹'},
    'CH': {'code': '+41', 'name': 'Switzerland', 'flag': '🇨🇭'},
    'AT': {'code': '+43', 'name': 'Austria', 'flag': '🇦🇹'},
    'GR': {'code': '+30', 'name': 'Greece', 'flag': '🇬🇷'},
    'TR': {'code': '+90', 'name': 'Turkey', 'flag': '🇹🇷'},
    'HK': {'code': '+852', 'name': 'Hong Kong', 'flag': '🇭🇰'},
    'TW': {'code': '+886', 'name': 'Taiwan', 'flag': '🇹🇼'},
    'NZ': {'code': '+64', 'name': 'New Zealand', 'flag': '🇳🇿'},
    'ZW': {'code': '+263', 'name': 'Zimbabwe', 'flag': '🇿🇼'},
    'IL': {'code': '+972', 'name': 'Israel', 'flag': '🇮🇱'},
    'SA': {'code': '+966', 'name': 'Saudi Arabia', 'flag': '🇸🇦'},
    'EG': {'code': '+20', 'name': 'Egypt', 'flag': '🇪🇬'},
    'MA': {'code': '+212', 'name': 'Morocco', 'flag': '🇲🇦'},
}


@phone_bp.route('/countries', methods=['GET'])
def get_countries():
    """
    Get list of supported countries for phone lookups.
    Useful for searchable dropdown in frontend.
    
    Query Parameters:
        search (str): Optional search term to filter countries
    
    Returns:
        List of countries with dial codes
        
    Example:
        GET /api/phone/countries
        Response:
        {
            "status": "success",
            "data": [
                {"code": "US", "dial_code": "+1", "name": "United States", "flag": "🇺🇸"},
                ...
            ]
        }
    """
    try:
        search = request.args.get('search', '').lower()
        
        countries = []
        for code, info in SUPPORTED_COUNTRIES.items():
            country = {
                'code': code,
                'dial_code': info['code'],
                'name': info['name'],
                'flag': info['flag']
            }
            
            # Filter if search provided
            if search:
                if search in code.lower() or search in info['name'].lower() or search in info['code']:
                    countries.append(country)
            else:
                countries.append(country)
        
        # Sort by name
        countries.sort(key=lambda x: x['name'])
        
        response = APIResponse.success(
            None,
            data={
                'countries': countries,
                'count': len(countries),
                'total_supported': len(SUPPORTED_COUNTRIES)
            }
        )
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error getting countries: {str(e)}")
        return jsonify(APIResponse.error(None, f"Server error: {str(e)}")), 500


@phone_bp.route('/detect-country', methods=['POST'])
def detect_country():
    """
    Detect country from phone number (auto-detect country code if missing).
    
    Request body:
    {
        "phone": "2225551234"          # Without country code
    }
    
    Returns:
        Detected country with dial code and region info
        
    Example:
        POST /api/phone/detect-country
        {
            "phone": "2025551234"
        }
        Response:
        {
            "status": "success",
            "data": {
                "phone": "2025551234",
                "detected_country": "US",
                "dial_code": "+1",
                "country_name": "United States",
                "region": "Washington DC"
            }
        }
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        
        if not phone:
            return jsonify(APIResponse.error(None, "Phone number is required")), 400
        
        # Try to parse as international
        detected_country = None
        detected_region = None
        detected_code = None
        
        # Try with each country code
        for country_code_str, country_info in SUPPORTED_COUNTRIES.items():
            try:
                test_number = country_info['code'] + phone.lstrip('+')
                parsed = phonenumbers.parse(test_number, None)
                
                if phonenumbers.is_valid_number(parsed):
                    detected_country = country_code_str
                    detected_code = country_info['code']
                    detected_region = geocoder.region_code_for_number(parsed)
                    break
            except:
                continue
        
        if not detected_country:
            return jsonify(APIResponse.error(None, "Could not detect country for phone number")), 400
        
        country_info = SUPPORTED_COUNTRIES.get(detected_country, {})
        region_name = geocoder.description_for_number(
            phonenumbers.parse(detected_code + phone.lstrip('+'), None),
            'en'
        ) or detected_region
        
        response = APIResponse.success(
            None,
            data={
                'phone': phone,
                'detected_country': detected_country,
                'dial_code': detected_code,
                'country_name': country_info.get('name'),
                'flag': country_info.get('flag'),
                'region': region_name
            }
        )
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error detecting country: {str(e)}")
        return jsonify(APIResponse.error(None, f"Server error: {str(e)}")), 500


@phone_bp.route('/lookup', methods=['POST'])
def lookup_phone():
    """
    Lookup phone number intelligence with light or deep scan.
    Auto-detects and normalizes phone formats. Never returns 400 for format issues.
    Supports multiple formats: 024XXXXXXX, +233XXXXXXXXX, 233XXXXXXXXX
    
    Request body:
    {
        "phone_number": "+1234567890",     # Required: any format will be normalized
        "country_code": "US",               # Optional: ISO country code or country name
        "scan_type": "light"                # Optional: 'light' or 'deep', default: 'light'
    }
    
    Response:
    {
        "status": "completed",
        "target": "+1234567890",
        "findings": [...],
        "threat_level": 0,
        "network_nodes": [],
        "network_edges": []
    }
    """
    case_id = None
    original_phone = None
    normalized_phone = None
    
    try:
        print(f"\n[PHONE_LOOKUP] ========== LOOKUP STARTED ==========")
        
        # Parse request data
        data = request.get_json()
        print(f"[PHONE_LOOKUP] REQUEST DATA: {data}")
        print(f"[PHONE_LOOKUP] REQUEST HEADERS: {dict(request.headers)}")
        logger.info(f"[PHONE_LOOKUP] REQUEST DATA: {data}")
        
        if not data:
            print("[PHONE_LOOKUP] ERROR: No JSON body provided")
            logger.warning("Phone lookup: No JSON body provided")
            return jsonify(APIResponse.error(None, "Request body is required (JSON)")), 400
        
        original_phone = data.get('phone_number', '').strip() if data.get('phone_number') else None
        country_input = data.get('country_code', '').strip() if data.get('country_code') else None
        scan_type = data.get('scan_type', 'light').lower() if data.get('scan_type') else 'light'
        
        # Log input
        print(f"[PHONE_LOOKUP] INPUT: phone={original_phone}, country={country_input}, scan_type={scan_type}")
        logger.info(f"[PHONE_LOOKUP] Input: phone={original_phone}, country={country_input}, scan_type={scan_type}")
        
        # Validate phone number provided
        if not original_phone:
            print(f"[PHONE_LOOKUP] ERROR: No phone number provided. Available keys: {list(data.keys())}")
            logger.warning("[PHONE_LOOKUP] No phone number provided")
            return jsonify(APIResponse.error(None, "Phone number is required")), 400
        
        # Validate scan type
        print(f"[PHONE_LOOKUP] Validating scan type: {scan_type}")
        is_valid, error = Validator.validate_scan_type(scan_type)
        if not is_valid:
            print(f"[PHONE_LOOKUP] ERROR: Invalid scan type: {scan_type}")
            logger.warning(f"[PHONE_LOOKUP] Invalid scan type: {scan_type}")
            return jsonify(APIResponse.error(None, error)), 400
        
        # Normalize country input (name or code)
        print(f"[PHONE_LOOKUP] Normalizing country: {country_input}")
        country_iso = None
        if country_input:
            try:
                country_info = Validator.normalize_country(country_input)
                if country_info:
                    country_iso = country_info['iso']
                    print(f"[PHONE_LOOKUP] Country normalized: {country_input} -> {country_iso}")
                    logger.info(f"[PHONE_LOOKUP] Country normalized: {country_input} -> {country_iso}")
                else:
                    print(f"[PHONE_LOOKUP] Could not normalize country: {country_input}, will auto-detect")
                    logger.debug(f"[PHONE_LOOKUP] Could not normalize country: {country_input}, will auto-detect")
            except Exception as e:
                print(f"[PHONE_LOOKUP] ERROR normalizing country: {str(e)}")
                logger.error(f"[PHONE_LOOKUP] Error normalizing country: {str(e)}")
        
        # ===== PHONE NORMALIZATION - NEVER FAIL, ALWAYS ATTEMPT =====
        # Try to normalize the phone number - accept any format
        print(f"[PHONE_LOOKUP] NORMALIZING PHONE: {original_phone}")
        logger.debug(f"[PHONE_LOOKUP] Attempting to normalize phone: {original_phone}")
        normalized_phone = Validator.normalize_phone_number(original_phone, country_iso)
        
        if not normalized_phone:
            # Normalization failed, but don't return 400 - try best effort
            print(f"[PHONE_LOOKUP] WARNING: Phone normalization failed for: {original_phone}")
            logger.warning(f"[PHONE_LOOKUP] Phone normalization failed for: {original_phone}")
            # Try to at least parse it with phonenumbers
            try:
                is_valid, error, parsed = Validator.validate_phone(original_phone)
                if is_valid and parsed:
                    normalized_phone = phonenumbers.format_number(
                        parsed,
                        phonenumbers.PhoneNumberFormat.INTERNATIONAL
                    )
                    print(f"[PHONE_LOOKUP] Recovered via fallback: {original_phone} -> {normalized_phone}")
                    logger.info(f"[PHONE_LOOKUP] Recovered via fallback: {original_phone} -> {normalized_phone}")
                else:
                    # Last resort: use original, service will handle
                    normalized_phone = original_phone
                    print(f"[PHONE_LOOKUP] Using original phone (may fail in service): {original_phone}")
                    logger.warning(f"[PHONE_LOOKUP] Using original phone (may fail in service): {original_phone}")
            except Exception as e:
                print(f"[PHONE_LOOKUP] ERROR fallback normalization failed: {str(e)}")
                logger.error(f"[PHONE_LOOKUP] Fallback normalization failed: {str(e)}")
                normalized_phone = original_phone
        
        print(f"[PHONE_LOOKUP] NORMALIZATION RESULT: {original_phone} -> {normalized_phone}")
        logger.info(f"[PHONE_LOOKUP] Normalized: {original_phone} -> {normalized_phone}")
        
        # Auto-detect country if not provided
        if not country_iso:
            print(f"[PHONE_LOOKUP] AUTO-DETECTING COUNTRY from {normalized_phone}...")
            try:
                is_valid, error, parsed = Validator.validate_phone(normalized_phone)
                if parsed:
                    auto_country = phonenumbers.region_code_for_number(parsed)
                    if auto_country:
                        country_iso = auto_country
                        print(f"[PHONE_LOOKUP] AUTO-DETECTED: {country_iso}")
                        logger.info(f"[PHONE_LOOKUP] Auto-detected country: {country_iso}")
            except Exception as e:
                print(f"[PHONE_LOOKUP] Could not auto-detect country: {str(e)}")
                logger.debug(f"[PHONE_LOOKUP] Could not auto-detect country: {str(e)}")
        
        # Perform lookup with specified scan type
        print(f"[PHONE_LOOKUP] STARTING {scan_type.upper()} SCAN: phone={normalized_phone}, country={country_iso}")
        logger.info(f"[PHONE_LOOKUP] Starting {scan_type} scan for {normalized_phone} (country: {country_iso})")
        
        phone_intel_service = PhoneIntelService()
        print(f"[PHONE_LOOKUP] Calling PhoneIntelService.lookup()...")
        result = phone_intel_service.lookup(normalized_phone, country_iso, scan_type=scan_type)
        print(f"[PHONE_LOOKUP] Service returned: {type(result)} = {result is not None}")
        
        # Ensure result has required fields
        if not result:
            print(f"[PHONE_LOOKUP] ERROR: Service returned empty result, creating safe default")
            logger.error(f"[PHONE_LOOKUP] Service returned empty result")
            result = {
                'status': 'success',
                'phone_number': normalized_phone,
                'valid': False,
                'emails_found': [],
                'social_accounts': {},
                'risk_score': 0,
                'risk_factors': []
            }
        
        print(f"[PHONE_LOOKUP] Result received. Status: {result.get('status')}")
        
        # Check if service call succeeded
        is_success = result.get('status') == 'success'
        if not is_success:
            logger.warning(f"[PHONE_LOOKUP] Service error: {result.get('notes', 'Unknown')}")
            # Still return result, don't fail
        
        # Generate unique case ID for this lookup
        case_id = f"phone_{str(uuid.uuid4())[:12]}"
        
        # Build consistent response structure - FLAT for frontend compatibility
        # Frontend expects: data.number, data.country, data.carrier, data.social_presence, etc.
        # NOT nested under 'findings'
        # Determine if any real findings exist
        has_findings = bool(
            result.get('emails_found') or
            (result.get('social_accounts') and len(result.get('social_accounts', {})) > 0) or
            result.get('mentions') or
            result.get('connected_accounts') or
            result.get('is_voip')
        )

        # Normalize threat level: 0 if no real findings, else scale risk_score to 0-100
        raw_risk = result.get('risk_score', 0)
        if not has_findings:
            threat_level = 0
        else:
            try:
                if isinstance(raw_risk, (int, float)):
                    threat_level = int(raw_risk * 100) if raw_risk <= 1 else int(raw_risk)
                else:
                    threat_level = 0
            except Exception:
                threat_level = 0

        # Build social presence list (convert handles to plausible URLs where possible)
        social_presence = []
        social_accounts = result.get('social_accounts') or {}
        for plat, handle in social_accounts.items():
            try:
                h = str(handle)
                if plat.lower() in ['twitter', 'x']:
                    social_presence.append(f"https://twitter.com/{h.lstrip('@')}")
                elif plat.lower() == 'instagram':
                    social_presence.append(f"https://instagram.com/{h.lstrip('@')}")
                elif plat.lower() == 'facebook':
                    social_presence.append(f"https://facebook.com/{h.lstrip('@')}")
                elif plat.lower() == 'github':
                    social_presence.append(f"https://github.com/{h}")
                elif plat.lower() == 'reddit':
                    social_presence.append(f"https://reddit.com/user/{h.lstrip('u/')} ")
                else:
                    social_presence.append(h)
            except Exception:
                continue

        response_data = {
            'status': 'completed',
            'target': normalized_phone,
            'number': result.get('phone_number', normalized_phone),
            'country': result.get('country') or result.get('country_iso') or country_iso,
            'carrier': result.get('carrier'),
            'social_presence': social_presence,
            'emails_found': result.get('emails_found', []),
            'valid': result.get('valid', False),
            'number_type': result.get('number_type'),
            'confidence': result.get('confidence', 0),
            'threat_level': threat_level,
            # Backwards-compatible aliases expected by frontend
            'risk_score': int(threat_level),
            'risk_level': result.get('risk_level') or None,
            'network_nodes': [
                {
                    'id': f"phone_{str(uuid.uuid4())[:8]}",
                    'label': normalized_phone,
                    'type': 'phone',
                    'metadata': {
                        'country': result.get('country'),
                        'carrier': result.get('carrier')
                    }
                }
            ] if result.get('valid') else [],
            'network_edges': []
        }
        
        logger.info(f"[PHONE_LOOKUP] Completed successfully: case={case_id}, threat_level={response_data['threat_level']}")
        
        # Try to save but don't fail if DB error. On unique constraint, perform an update (upsert).
        try:
            phone_intel_record = PhoneIntelModel(
                id=str(uuid.uuid4()),
                phone_number=response_data.get('number'),
                country=response_data.get('country'),
                country_code=result.get('country_iso') or result.get('country_code'),
                region=result.get('region'),
                carrier=response_data.get('carrier'),
                timezone=response_data.get('timezone'),
                valid=response_data.get('valid', False),
                social_presence=response_data.get('social_presence', []),
                emails_found=response_data.get('emails_found', []),
                risk_score=int((result.get('risk_score', 0) * 100)) if isinstance(result.get('risk_score'), (int, float)) else 0,
                confidence=response_data.get('confidence', 0),
                created_at=datetime.utcnow()
            )

            db.session.add(phone_intel_record)
            db.session.commit()
            logger.debug(f"[PHONE_LOOKUP] Saved to database")
        except IntegrityError as ie:
            # Phone already exists — update the existing row instead of failing
            logger.debug(f"[PHONE_LOOKUP] IntegrityError saving phone intel: {ie}")
            db.session.rollback()
            try:
                existing = PhoneIntelModel.query.filter_by(phone_number=response_data.get('number')).first()
                if existing:
                    existing.country = response_data.get('country')
                    existing.country_code = result.get('country_iso') or result.get('country_code')
                    existing.region = result.get('region')
                    existing.carrier = response_data.get('carrier')
                    existing.timezone = response_data.get('timezone')
                    existing.valid = response_data.get('valid', False)
                    existing.social_presence = response_data.get('social_presence', [])
                    existing.emails_found = response_data.get('emails_found', [])
                    existing.risk_score = int((result.get('risk_score', 0) * 100)) if isinstance(result.get('risk_score'), (int, float)) else 0
                    existing.confidence = response_data.get('confidence', 0)
                    existing.updated_at = datetime.utcnow()
                    db.session.commit()
                    logger.debug("[PHONE_LOOKUP] Updated existing phone_intelligence record")
            except Exception as e:
                logger.warning(f"[PHONE_LOOKUP] DB upsert failed (non-critical): {str(e)}")
                db.session.rollback()
        except Exception as e:
            logger.warning(f"[PHONE_LOOKUP] DB save failed (non-critical): {str(e)}")
            db.session.rollback()
        
        # Return 'success' status for compatibility
        response = APIResponse.success(
            case_id,
            data=response_data,
            risk_score=response_data['threat_level'],
            status='success'
        )
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"[PHONE_LOOKUP] Unexpected error: {str(e)}", exc_info=True)
        # Return safe response even on error
        safe_response = APIResponse.success(
            case_id or f"phone_{str(uuid.uuid4())[:12]}",
            data={
                'status': 'completed',
                'number': original_phone or 'unknown',
                'country': None,
                'carrier': None,
                'social_presence': [],
                'emails_found': [],
                'threat_level': 0,
                'network_nodes': [],
                'network_edges': [],
                'error_note': 'Phone lookup encountered an error but returning safe response'
            },
            risk_score=0
        )
        return jsonify(safe_response), 200
        
        # Try to save to database, but don't fail if it doesn't work
        try:
            phone_intel_record = PhoneIntelModel(
                id=str(uuid.uuid4()),
                phone_number=result.get('phone_number', phone),
                country=result.get('country'),
                carrier=result.get('carrier'),
                timezone=result.get('timezone'),
                social_presence=list(result.get('social_accounts', {}).keys()) if result.get('social_accounts') else [],
                emails_found=result.get('emails_found', []) if result.get('emails_found') else [],
                risk_score=int(result.get('risk_score', 0) * 100) if isinstance(result.get('risk_score'), (int, float)) else 0,
                confidence=result.get('confidence', 0),
                data=result,
                created_at=datetime.utcnow()
            )
            
            db.session.add(phone_intel_record)
            db.session.commit()
            logger.info(f"Phone intel record saved to database")
        except Exception as e:
            logger.warning(f"Could not save phone intel to database: {str(e)}")
            db.session.rollback()
            # Don't fail the request - return partial result
        
        response = APIResponse.success(
            case_id,
            data={
                **result,
                'graph_node': graph_node,
                'scan_type': scan_type,
                'case_id': case_id
            },
            risk_score=int(result.get('risk_score', 0) * 100) if isinstance(result.get('risk_score'), (int, float)) else 0
        )
        
        logger.info(f"Phone lookup completed successfully: {case_id}")
        return jsonify(response), 200
    
    except ValueError as e:
        logger.error(f"Validation error in phone lookup: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Validation error: {str(e)}")), 400
    
    except Exception as e:
        logger.error(f"Unexpected error in phone lookup: {str(e)}", exc_info=True)
        return jsonify(APIResponse.error(case_id, f"Lookup error: {str(e)}")), 500


@phone_bp.route('/infer-country', methods=['POST'])
def infer_country_from_phone():
    """
    Infer country from phone number if not provided.
    
    Request body:
    {
        "phone_number": "2225551234"  # Phone number without country code
    }
    
    Returns:
        Inferred country with dial code
        
    Example:
        POST /api/phone/infer-country
        {
            "phone_number": "2225551234"
        }
        Response:
        {
            "status": "success",
            "data": {
                "country_detected": "United States",
                "country_code": "US",
                "dial_code": "+1"
            }
        }
    """
    try:
        data = request.get_json()
        phone = data.get('phone_number', '').strip()
        
        if not phone:
            return jsonify(APIResponse.error(None, "Phone number is required")), 400
        
        # Try to infer country
        country_info = Validator.infer_country_from_phone(phone)
        
        if not country_info:
            return jsonify(APIResponse.error(
                None, 
                "Could not infer country from phone number. Please provide country code."
            )), 400
        
        response = APIResponse.success(
            None,
            data={
                'country_detected': country_info['name'],
                'country_code': country_info['iso'],
                'dial_code': country_info['code']
            }
        )
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error inferring country: {str(e)}")
        return jsonify(APIResponse.error(None, f"Server error: {str(e)}")), 500


@phone_bp.route('/scan', methods=['POST'])
def scan_phone():
    """Single-button scan endpoint using GhostTR-style quick username probes.

    Request body: { "phone_number": "+123..." }
    Returns a flat `data` object similar to `/phone/lookup` but focused on quick live profile hits.
    """
    try:
        data = request.get_json() or {}
        phone_input = data.get('phone_number') or data.get('phone')
        if not phone_input:
            return jsonify(APIResponse.error(None, 'phone_number is required')), 400

        # Normalize and validate
        normalized = Validator.normalize_phone_number(phone_input, None) or phone_input
        is_valid, err, parsed = Validator.validate_phone(normalized)

        # Prepare defaults
        country = None
        country_iso = None
        carrier_name = None
        valid_flag = False

        if parsed:
            try:
                country = geocoder.country_name_for_number(parsed)
            except Exception:
                country = None
            try:
                country_iso = phonenumbers.region_code_for_number(parsed)
            except Exception:
                country_iso = None
            try:
                carrier_name = carrier.name_for_number(parsed, 'en')
            except Exception:
                carrier_name = None

            try:
                valid_flag = bool(phonenumbers.is_valid_number(parsed))
            except Exception:
                valid_flag = False

        # Run Ghost-style quick scan using phone-derived username
        clean_phone = re.sub(r"\D", '', normalized)
        service = PhoneIntelService()
        try:
            ghost_hits = service._ghost_username_scan(clean_phone)
        except Exception:
            ghost_hits = {}

        social_presence = list(ghost_hits.values()) if ghost_hits else []

        response_data = {
            'status': 'completed',
            'number': normalized,
            'country': country,
            'country_code': country_iso,
            'carrier': carrier_name,
            'social_presence': social_presence,
            'social_accounts': ghost_hits,
            'emails_found': [],
            'valid': valid_flag,
            'threat_level': 0,
            'risk_score': 0,
        }

        return jsonify(APIResponse.success(None, data=response_data, risk_score=0)), 200

    except Exception as e:
        logger.error(f"Error in quick scan: {str(e)}", exc_info=True)
        return jsonify(APIResponse.error(None, f"Scan error: {str(e)}")), 500


@phone_bp.route('/batch', methods=['POST'])
def batch_lookup():
    """
    Batch lookup multiple phone numbers
    
    Request body:
    {
        "phones": ["+1234567890", "+0987654321"]
    }
    """
    try:
        data = request.get_json()
        phones = data.get('phones', [])
        
        if not phones or not isinstance(phones, list):
            return jsonify(APIResponse.error(None, "phones must be a non-empty list")), 400
        
        if len(phones) > 100:
            return jsonify(APIResponse.error(None, "Maximum 100 phones per batch")), 400
        
        results = []
        
        for phone in phones:
            phone = phone.strip()
            is_valid, error, parsed = Validator.validate_phone(phone)
            
            if not is_valid:
                results.append({
                    'phone': phone,
                    'valid': False,
                    'error': error
                })
                continue
            
            try:
                valid = phonenumbers.is_valid_number(parsed) if parsed else False

                
                if valid:
                    result = _extract_phone_intelligence(phone, parsed)
                    results.append(result)
                else:
                    results.append({
                        'phone': phone,
                        'valid': False,
                        'error': 'Invalid phone number'
                    })
            except Exception as e:
                results.append({
                    'phone': phone,
                    'valid': False,
                    'error': str(e)
                })
        
        # Calculate average risk score
        valid_results = [r for r in results if r.get('valid', False)]
        avg_risk = sum([r['risk_score'] for r in valid_results]) / len(valid_results) if valid_results else 0
        
        return jsonify({
            'status': 'success',
            'data': results,
            'summary': {
                'total': len(phones),
                'valid': len(valid_results),
                'average_risk_score': round(avg_risk, 2)
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error in batch lookup: {str(e)}")
        return jsonify(APIResponse.error(None, f"Batch error: {str(e)}")), 500


@phone_bp.route('/case', methods=['POST'])
def create_phone_case():
    """Create an investigation case from phone number"""
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        
        if not phone:
            return jsonify(APIResponse.error(None, "Phone number is required")), 400
        
        # Validate and lookup phone
        is_valid, error, parsed = Validator.validate_phone(phone)
        if not is_valid:
            return jsonify(APIResponse.error(None, error)), 400
        
        try:
            valid = phonenumbers.is_valid_number(parsed) if parsed else False
            if not valid:
                return jsonify(APIResponse.error(None, "Invalid phone number")), 400
        except:
            return jsonify(APIResponse.error(None, "Cannot parse phone number")), 400
        
        # Extract intelligence
        result = _extract_phone_intelligence(phone, parsed)
        
        # Create investigation case
        case_id = generate_case_id()
        investigation = Investigation(
            id=case_id,
            primary_entity=f"phone_{phone.replace('+', '')}",
            case_type='phone',
            scan_depth='light',
            status='completed',
            created_at=datetime.utcnow(),
            risk_score=result['risk_score']
        )
        
        db.session.add(investigation)
        db.session.commit()
        
        response = APIResponse.success(
            case_id,
            data={
                'phone_number': phone,
                'intelligence': result,
                'case_created': True
            },
            risk_score=result['risk_score']
        )
        
        return jsonify(response), 201
    
    except Exception as e:
        logger.error(f"Error creating phone case: {str(e)}")
        db.session.rollback()
        return jsonify(APIResponse.error(None, f"Error: {str(e)}")), 500


@phone_bp.route('/history', methods=['GET'])
def get_phone_history():
    """Get phone lookup history"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        paginated = PhoneIntelModel.query.order_by(
            PhoneIntelModel.created_at.desc()
        ).paginate(page=page, per_page=limit, error_out=False)
        
        data = [
            {
                'id': pi.id,
                'phone_number': pi.phone_number,
                'country': pi.country,
                'carrier': pi.carrier,
                'risk_score': pi.risk_score,
                'created_at': pi.created_at.isoformat()
            } for pi in paginated.items
        ]
        
        return jsonify({
            'status': 'success',
            'data': data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': paginated.total,
                'pages': paginated.pages
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting phone history: {str(e)}")
        return jsonify(APIResponse.error(None, f"Error: {str(e)}")), 500


# ==================== Private Helper Functions ====================

def _extract_phone_intelligence(phone_number, parsed_phone):
    """
    Extract intelligence from phone number using phonenumbers library.
    Returns dict with country, carrier, timezone, social_presence, risk_score, etc.
    """
    try:
        # Get country
        country = geocoder.country_name_for_number(parsed_phone)
        country_code = phonenumbers.region_code_for_number(parsed_phone)
        region = geocoder.region_name_for_number(parsed_phone, 'en_US')
        
        # Get carrier
        carrier_name = carrier.name_for_number(parsed_phone, 'en_US')
        
        # Get timezone
        tz_list = timezone.time_zones_for_number(parsed_phone)
        tz = tz_list[0] if tz_list else 'Unknown'
        
        # Simulate social presence check
        social_presence = _check_social_presence(phone_number)
        
        # Simulate email finding
        emails_found = _find_associated_emails(phone_number)
        
        # Calculate risk score based on:
        # - VoIP detection (high risk)
        # - Country (some countries higher risk)
        # - Social presence (more presence = more data exposed)
        # - Associated emails
        risk_score = _calculate_phone_risk_score(
            phone_number,
            carrier_name,
            country_code,
            social_presence,
            emails_found
        )
        
        # Confidence score (how much data we found)
        confidence = (len(social_presence) * 0.2 + len(emails_found) * 0.3 + 0.5)
        confidence = min(confidence, 1.0)
        
        return {
            'valid': True,
            'number': phone_number,
            'country': country,
            'country_code': country_code,
            'region': region if region else 'Unknown',
            'carrier': carrier_name if carrier_name else 'Unknown',
            'timezone': tz,
            'social_presence': social_presence,
            'emails_found': emails_found,
            'risk_score': round(risk_score, 2),
            'confidence': round(confidence, 2)
        }
    
    except Exception as e:
        logger.error(f"Error extracting phone intelligence: {str(e)}")
        return {
            'valid': False,
            'number': phone_number,
            'error': str(e),
            'risk_score': 0,
            'confidence': 0
        }


def _check_social_presence(phone_number):
    """
    Simulate checking if phone number is registered on social platforms.
    In production, would use APIs like Truecaller, HLR lookups, etc.
    """
    # Remove formatting
    clean_phone = re.sub(r'\D', '', phone_number)
    
    # Simulate based on phone hash
    social = []
    hash_val = sum([ord(c) for c in clean_phone])
    
    # Pseudo-random assignment
    if hash_val % 3 == 0:
        social.append('WhatsApp')
    if hash_val % 5 == 0:
        social.append('Telegram')
    if hash_val % 7 == 0:
        social.append('Signal')
    if hash_val % 11 == 0:
        social.append('Viber')
    
    return social


def _find_associated_emails(phone_number):
    """
    Simulate finding emails associated with phone number.
    In production, would use data breach APIs, reverse lookup services.
    """
    # Placeholder - would integrate with breach databases
    return []


def _calculate_phone_risk_score(phone_number, carrier_name, country_code, social_presence, emails_found):
    """
    Calculate risk score based on multiple factors.
    Score 0-100: 0 (safe) to 100 (dangerous)
    """
    score = 20  # Base risk
    
    # High risk carriers/VoIP
    voip_carriers = ['VOIPNow', 'MagicJack', 'Google Voice', 'Skype']
    if carrier_name and any(v in carrier_name for v in voip_carriers):
        score += 25
    
    # Country risk
    high_risk_countries = ['KP', 'IR', 'SY']  # North Korea, Iran, Syria
    if country_code in high_risk_countries:
        score += 20
    
    # Social presence increases exposure risk
    score += len(social_presence) * 8
    
    # Associated emails increase risk
    score += len(emails_found) * 5
    
    return min(score, 100)
