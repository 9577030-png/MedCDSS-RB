import logging
from typing import List
from application.ports.guideline_provider import GuidelineProvider
from domain.entities.guideline import SpecialtyGuideline
from infrastructure.adapters.loaders._merged_guideline_provider import MergedGuidelineProvider

logger = logging.getLogger(__name__)

class YamlGuidelineProvider(GuidelineProvider):
    def __init__(self, merged_provider: MergedGuidelineProvider):
        self._merged = merged_provider
        logger.info("YamlGuidelineProvider initialized with merged_provider")

    def get_all(self) -> List[SpecialtyGuideline]:
        logger.debug("Fetching all guidelines via merged provider")
        guidelines = self._merged.get_all()
        logger.info(f"Returning {len(guidelines)} guidelines")
        return guidelines

    def reload(self) -> None:
        """Перезагружает guidelines через merged provider."""
        logger.info("Reloading guidelines via merged provider...")
        self._merged.reload()
        logger.info("Guidelines reloaded.")