import os
import yaml
import logging
from typing import Dict, Set
from config import settings

logger = logging.getLogger(__name__)

class ClinicalInterpretationMapper:
    """
    Загружает clinical_interpretations.yaml и предоставляет метод для проверки,
    есть ли для данного rule_id полноценная запись (enriched).
    """
    def __init__(self):
        self._enriched_ids: Set[str] = set()
        self._load_interpretations()

    def _load_interpretations(self):
        config_path = os.path.join(settings.BASE_DIR, settings.KNOWLEDGE_DIR, "configs", "clinical_interpretations.yaml")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            interpretations = data.get("interpretations", {})
            # Все ключи верхнего уровня в interpretations считаем обогащёнными
            self._enriched_ids = set(interpretations.keys())
            logger.info(f"Loaded {len(self._enriched_ids)} enriched interpretation IDs")
        except Exception as e:
            logger.error(f"Failed to load clinical_interpretations.yaml: {e}")
            self._enriched_ids = set()

    def is_enriched(self, rule_id: str) -> bool:
        """
        Возвращает True, если для данного rule_id есть полноценная интерпретация.
        """
        return rule_id in self._enriched_ids

    def get_enriched_ids(self) -> Set[str]:
        return self._enriched_ids.copy()