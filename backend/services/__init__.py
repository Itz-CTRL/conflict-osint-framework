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

from .phone_intel import PhoneIntelligenceService
from .graph_engine import GraphEngineService

__all__ = [
    'PhoneIntelligenceService',
    'GraphEngineService',
]
