"""GraphEngine wrapper expected by TaskManager
Provides `add_central_node` and `build_graph_json` to match TaskManager usage.
"""

from services.graph_engine import GraphEngineService
import logging

logger = logging.getLogger(__name__)


class GraphEngine:
    def __init__(self, investigation_id=None):
        self.case_id = investigation_id
        self.engine = GraphEngineService(case_id=investigation_id)

    def add_central_node(self, node_type, username):
        # GraphEngineService expects an investigation dict; provide minimal structure
        try:
            self.engine._add_central_node({'username': username, 'id': self.case_id, 'email': None, 'phone': None, 'risk_score': 0})
        except Exception as e:
            logger.debug(f"GraphEngine.add_central_node error: {e}")

    def build_graph_json(self):
        try:
            return self.engine.export_json()
        except Exception as e:
            logger.error(f"GraphEngine.build_graph_json error: {e}")
            return {'nodes': [], 'edges': [], 'metadata': {}, 'statistics': {}}
