import os
import yaml
import logging
from typing import Dict, Optional
from config import settings
from domain.entities.threshold import Threshold
from domain.value_objects.unit import Unit
from domain.value_objects.risk_level import RiskLevel
from domain.value_objects.gender import Gender
from application.ports.threshold_provider import ThresholdProvider
from domain.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class YamlThresholdLoader(ThresholdProvider):
    def __init__(self, config_path: str = None):
        if config_path is None:
            base_dir = settings.BASE_DIR
            config_path = os.path.join(base_dir, settings.CONFIGS_DIR, "clinical_thresholds.yaml")
        self.config_path = config_path
        self._thresholds = None
        self._male_thresholds = {}
        self._female_thresholds = {}
        logger.info(f"YamlThresholdLoader initialized with config: {self.config_path}")

    def _load(self) -> None:
        logger.debug(f"Loading thresholds from {self.config_path}")
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        thresholds_data = data.get("thresholds", {})
        for name, params in thresholds_data.items():
            if "male" in params and "female" in params:
                male_params = params["male"]
                female_params = params["female"]
                unit = Unit(params.get("unit", ""))
                risk_level = getattr(RiskLevel, params.get("risk_level", "HIGH"), RiskLevel.HIGH)

                self._male_thresholds[name] = Threshold(
                    parameter_name=name,
                    low=male_params.get("low"),
                    high=male_params.get("high"),
                    unit=unit,
                    risk_level=risk_level
                )
                self._female_thresholds[name] = Threshold(
                    parameter_name=name,
                    low=female_params.get("low"),
                    high=female_params.get("high"),
                    unit=unit,
                    risk_level=risk_level
                )
                logger.debug(f"Loaded gender-specific thresholds for {name}")
            else:
                low = params.get("low")
                high = params.get("high")
                unit = Unit(params.get("unit", ""))
                risk_level = getattr(RiskLevel, params.get("risk_level", "HIGH"), RiskLevel.HIGH)
                threshold = Threshold(
                    parameter_name=name,
                    low=low,
                    high=high,
                    unit=unit,
                    risk_level=risk_level
                )
                self._male_thresholds[name] = threshold
                self._female_thresholds[name] = threshold
                logger.debug(f"Loaded common threshold for {name}")
        logger.info(f"Loaded {len(self._male_thresholds)} thresholds for male and {len(self._female_thresholds)} for female")

    def get_global_thresholds(self) -> Dict[str, Threshold]:
        if self._thresholds is None:
            self._load()
        return self._male_thresholds

    def get_threshold(self, parameter: str, gender: Gender) -> Optional[Threshold]:
        if self._thresholds is None:
            self._load()
        if gender == Gender.MALE:
            return self._male_thresholds.get(parameter)
        elif gender == Gender.FEMALE:
            return self._female_thresholds.get(parameter)
        return self._male_thresholds.get(parameter)

    def reload(self) -> None:
        """Перезагружает пороги из файла."""
        logger.info("Reloading thresholds...")
        self._thresholds = None
        self._male_thresholds = {}
        self._female_thresholds = {}
        self._load()
        logger.info("Thresholds reloaded successfully.")