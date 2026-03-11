"""RiskEngine wrapper to calculate risk score for TaskManager"""

from services.analyzer import BehaviorAnalyzer
from database import db
from models import Investigation, Finding
import logging

logger = logging.getLogger(__name__)


class RiskEngine:
    def __init__(self, investigation_id):
        self.investigation_id = investigation_id
        self.analyzer = BehaviorAnalyzer()

    def calculate_risk_score(self):
        try:
            inv = Investigation.query.get(self.investigation_id)
            if not inv:
                logger.warning(f"RiskEngine: investigation {self.investigation_id} not found")
                return 0

            # Gather findings and build platform results summary
            findings = Finding.query.filter_by(investigation_id=self.investigation_id).all()
            platforms = []
            for f in findings:
                try:
                    data = f.data if isinstance(f.data, dict) else (json.loads(f.data) if isinstance(f.data, str) else {})
                except Exception:
                    data = {}
                platforms.append({'platform': f.platform, 'found': f.found, 'metadata': data})

            platform_results = {
                'platforms': platforms,
                'total_checked': len(platforms),
                'found_count': sum(1 for p in platforms if p.get('found'))
            }

            # Run analyzer on aggregated data
            report = self.analyzer.analyze(inv.primary_entity, platform_results)
            score = report.get('risk_score', 0)

            # Persist to investigation record
            try:
                inv.risk_score = float(score)
                db.session.commit()
            except Exception as e:
                logger.warning(f"RiskEngine: failed to persist risk_score: {e}")
                db.session.rollback()

            return float(score)

        except Exception as e:
            logger.error(f"RiskEngine.calculate_risk_score error: {e}")
            return 0
