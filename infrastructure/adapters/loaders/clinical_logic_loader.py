import os
import yaml
import logging
from typing import Dict, Any, List
from config import settings

logger = logging.getLogger(__name__)

class ClinicalLogicLoader:
    def __init__(self, config_path: str = None):
        if config_path is None:
            base_dir = settings.BASE_DIR
            config_path = os.path.join(base_dir, settings.CONFIGS_DIR, "clinical_logic.yaml")
        self.config_path = config_path
        self._config = None
        logger.info(f"ClinicalLogicLoader initialized with config: {self.config_path}")

    def _load(self) -> Dict[str, Any]:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        logger.debug(f"Loaded clinical logic config: {list(data.keys())}")
        return data

    def get_config(self) -> Dict[str, Any]:
        if self._config is None:
            self._config = self._load()
        return self._config

    def reload(self) -> None:
        """Перезагружает логику из файла."""
        logger.info("Reloading clinical logic...")
        self._config = None
        self._config = self._load()
        logger.info("Clinical logic reloaded successfully.")

    # ---- Новые методы для получения маппингов ----
    def get_diagnosis_labels(self) -> Dict[str, str]:
        """Возвращает словарь {id: label} для диагнозов."""
        return self.get_config().get("diagnosis_labels", {})

    def get_system_groups(self) -> Dict[str, List[str]]:
        """Возвращает словарь {система: [список id]} для группировки."""
        return self.get_config().get("system_groups", {})

    def get_allowed_primary(self) -> List[str]:
        """Возвращает список id диагнозов, разрешённых для отображения."""
        return self.get_config().get("allowed_primary", [])