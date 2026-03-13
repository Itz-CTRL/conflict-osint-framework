"""
config.py

Centralized configuration for API keys and service credentials.
All sensitive data loaded from environment variables for security.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class APIConfig:
    """API configuration with environment variable fallbacks"""
    
    # IntelligenceX (for historical leak data)
    INTELLIGENCEX_API_KEY = os.getenv("INTELLIGENCEX_API_KEY", "")
    INTELLIGENCEX_ENABLED = bool(INTELLIGENCEX_API_KEY)
    
    # Have I Been Pwned (for email breach checking)
    HIBP_API_KEY = os.getenv("HIBP_API_KEY", "")
    HIBP_ENABLED = bool(HIBP_API_KEY)
    
    # Shodan (for device/service discovery)
    SHODAN_API_KEY = os.getenv("SHODAN_API_KEY", "")
    SHODAN_ENABLED = bool(SHODAN_API_KEY)
    
    # Optional: Google API for mentions/posts
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_ENABLED = bool(GOOGLE_API_KEY)
    
    # Request settings
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
    REQUEST_RETRIES = int(os.getenv("REQUEST_RETRIES", "2"))
    REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))
    
    # Feature flags
    DEEP_SCAN_ENABLED = os.getenv("DEEP_SCAN_ENABLED", "true").lower() == "true"
    THREAT_SCORING_ENABLED = os.getenv("THREAT_SCORING_ENABLED", "true").lower() == "true"


# Threat keywords for risk detection
THREAT_KEYWORDS = {
    "violent": [
        "kill", "attack", "bomb", "shoot", "terror", "weapon",
        "violence", "threat", "explode", "hostage", "assassin",
        "poison", "murder", "kidnap", "extort", "ransom",
    ],
    "illegal": [
        "hack", "crack", "malware", "exploit", "inject", "ransomware",
        "ddos", "phishing", "fraud", "scam", "theft", "steal",
    ],
    "extremist": [
        "isis", "terror", "jihad", "radical", "extremist",
    ]
}

# Risk scoring weights
RISK_WEIGHTS = {
    "breach_found": 25,          # Email found in breach
    "multiple_breaches": 35,     # Email in 5+ breaches
    "shodan_devices": 20,        # Devices found on Shodan
    "violent_mentions": 40,      # Posts with violent keywords
    "high_profile": 15,          # High follower count / verified
    "rapid_account_creation": 10, # Multiple accounts created recently
}


def get_enabled_services():
    """Return list of enabled services"""
    services = []
    if INTELLIGENCEX_ENABLED:
        services.append("IntelligenceX")
    if HIBP_ENABLED:
        services.append("HIBP")
    if SHODAN_ENABLED:
        services.append("Shodan")
    if GOOGLE_ENABLED:
        services.append("Google")
    return services
