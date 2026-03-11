"""
Routes package for the OSINT Investigation Platform
"""

from .investigation_routes import investigation_bp
from .phone_routes import phone_bp
from .graph_routes import graph_bp
from .report_routes import report_bp
from .profile_routes import profile_bp
from .filter_routes import filter_bp

__all__ = [
    'investigation_bp',
    'phone_bp',
    'graph_bp',
    'report_bp',
    'profile_bp',
    'filter_bp',
]
