"""Services Package - Core business logic for OSINT platform.

This package contains reusable service classes that encapsulate
business logic for analysis, intelligence gathering, and graph operations.

Services:
- PhoneIntelligenceService: Phone number lookup and analysis
- GraphEngineService: Network graph construction and analysis
- BehaviorAnalyzer: Risk scoring and pattern analysis
- NetworkGraphBuilder: Graph building from findings
- OSINTScraper: Lightweight platform verification
"""

"""Services package exports.

Imports are attempted lazily to avoid hard failures when optional
dependencies (e.g., phonenumbers, Scrapy) are not installed in test
environments. Missing services will be None but callers can import
concrete modules directly when running in a fully provisioned env.
"""

try:
    from .phone_intel import PhoneIntelligenceService
except Exception:
    PhoneIntelligenceService = None

try:
    from .graph_engine import GraphEngineService
except Exception:
    GraphEngineService = None

# New wrapper services for task manager compatibility
try:
    from .analyser_service import AnalyserService
except Exception:
    AnalyserService = None

try:
    from .risk_engine import RiskEngine
except Exception:
    RiskEngine = None

try:
    from .graph_engine_wrapper import GraphEngine
except Exception:
    GraphEngine = None

__all__ = [
    'PhoneIntelligenceService',
    'GraphEngineService',
    'AnalyserService',
    'RiskEngine',
    'GraphEngine'
]
