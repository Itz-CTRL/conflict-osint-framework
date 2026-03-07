"""
Configuration module for the OSINT Investigation Platform
Handles environment-based settings and feature toggles
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///osint_platform.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Configuration
    API_TITLE = 'OSINT Investigation Platform'
    API_VERSION = 'v1.0'
    
    # Task Management
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    TASK_TIMEOUT = 3600  # 1 hour max task time
    
    # Caching
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Risk Scoring Weights (configurable)
    RISK_WEIGHTS = {
        'scam_keywords': 0.25,
        'spam_reports': 0.20,
        'multi_platform': 0.20,
        'dangerous_keywords': 0.25,
        'account_age': 0.10,  # Newer accounts = higher risk
    }
    
    # Scam/Risk Keywords
    SCAM_KEYWORDS = [
        'lottery', 'prize', 'verify account', 'claim reward',
        'urgent', 'act now', 'limited time', 'confirm identity',
        'update payment', 'suspicious activity', 'bitcoin', 'crypto',
        'money transfer', 'western union', 'gift card'
    ]
    
    # Dangerous Keyword Clusters
    DANGEROUS_KEYWORDS = [
        'exploit', 'ransomware', 'malware', 'payload',
        'ddos', 'botnet', 'zero-day', 'vulnerability',
        'credential', 'password', 'banking', 'carder'
    ]
    
    # Social Media Platforms (for username scanning)
    PLATFORMS = {
        'facebook': {'url': 'https://www.facebook.com/{}', 'method': 'content'},
        'twitter': {'url': 'https://twitter.com/{}', 'method': 'content'},
        'instagram': {'url': 'https://www.instagram.com/{}/', 'method': 'content'},
        'linkedin': {'url': 'https://www.linkedin.com/in/{}', 'method': 'content'},
        'github': {'url': 'https://github.com/{}', 'method': 'content'},
        'tiktok': {'url': 'https://www.tiktok.com/@{}', 'method': 'content'},
        'youtube': {'url': 'https://www.youtube.com/user/{}', 'method': 'content'},
        'twitch': {'url': 'https://twitch.tv/{}', 'method': 'content'},
        'reddit': {'url': 'https://reddit.com/u/{}', 'method': 'content'},
        'telegram': {'url': 'https://t.me/{}', 'method': 'content'},
    }
    
    # Scrapy Configuration
    SCRAPY_ENABLED = True
    SCRAPY_TIMEOUT = 300
    SCRAPY_MAX_DEPTH = 3
    
    # PDF Report Configuration
    PDF_ENABLED = True
    PDF_FONT = 'Helvetica'
    PDF_AUTHOR = 'OSINT Investigation Platform'
    

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Override with environment variables for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost/osint_db')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
