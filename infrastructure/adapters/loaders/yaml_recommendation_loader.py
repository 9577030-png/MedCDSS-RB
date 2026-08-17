import os
import yaml
import logging
from typing import Optional
from config import settings
from domain.entities.recommendation import Recommendation
from domain.value_objects.severity import Severity
from application.ports.recommendation_provider import RecommendationProvider

logger = logging.getLogger(__name__)

class YamlRecommendationLoader(RecommendationProvider):
    def __init__(self, config_path: str = None):
        if config_path is None:
            base_dir = settings.BASE_DIR
            config_path = os.path.join(base_dir, settings.CONFIGS_DIR, "doctor_recommendations.yaml")
        self.config_path = config_path
        self._recommendations = None
        logger.info(f"YamlRecommendationLoader initialized with config: {self.config_path}")

    def _load(self) -> dict:
        logger.debug(f"Loading recommendations from {self.config_path}")
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        recs = data.get("recommendations", {})
        logger.info(f"Loaded {len(recs)} recommendations")
        return recs

    def get_recommendation(self, finding_id: str) -> Optional[Recommendation]:
        if self._recommendations is None:
            self._recommendations = self._load()
        data = self._recommendations.get(finding_id)
        if not data:
            logger.warning(f"No recommendation found for finding {finding_id}")
            return None
        urgency = getattr(Severity, data.get("urgency", "moderate").upper(), Severity.MODERATE)
        rec = Recommendation(
            doctor_specialty=data["doctor_specialty"],
            urgency=urgency,
            additional_tests=data.get("additional_tests", [])
        )
        logger.debug(f"Returning recommendation for {finding_id}")
        return rec

    def reload(self) -> None:
        """Перезагружает рекомендации из файла."""
        logger.info("Reloading recommendations...")
        self._recommendations = None
        self._recommendations = self._load()
        logger.info("Recommendations reloaded successfully.")    