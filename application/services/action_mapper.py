import logging
from typing import List
from domain.entities.finding import ClinicalFinding
from domain.entities.recommendation import Recommendation
from application.ports.recommendation_provider import RecommendationProvider

logger = logging.getLogger(__name__)

class ActionMapper:
    def __init__(self, recommendation_provider: RecommendationProvider):
        self.recommendation_provider = recommendation_provider
        logger.info("ActionMapper initialized")

    def map_to_actions(self, findings: List[ClinicalFinding]) -> List[Recommendation]:
        logger.info(f"Mapping {len(findings)} findings to actions")
        actions = []
        for finding in findings:
            rec = self.recommendation_provider.get_recommendation(finding.id)
            if rec:
                actions.append(rec)
                logger.debug(f"Added action for finding {finding.id}: {rec.doctor_specialty}")
            else:
                logger.warning(f"No recommendation found for finding {finding.id}")
        logger.info(f"Mapped {len(actions)} actions")
        return actions