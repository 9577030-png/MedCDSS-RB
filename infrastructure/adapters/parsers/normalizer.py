import os
import yaml
import logging
from typing import Dict, Tuple
from domain.value_objects.unit import Unit
from domain.logic.unit_converter import convert
from domain.exceptions import InvalidParameterError, ConfigurationError

logger = logging.getLogger(__name__)

class ParameterNormalizer:
    """Загружает алиасы и единицы, приводит параметры к каноническому виду."""

    def __init__(self):
        self._aliases = self._load_aliases()
        self._units = self._load_units()
        logger.info(f"ParameterNormalizer initialized: {len(self._aliases)} aliases, {len(self._units)} units")

    def _load_aliases(self) -> Dict[str, str]:
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            path = os.path.join(base_dir, "knowledge", "laboratory", "aliases.yaml")
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            alias_map = {}
            for canonical, synonyms in data.get("aliases", {}).items():
                for syn in synonyms:
                    alias_map[syn.lower()] = canonical
            logger.debug(f"Loaded aliases: {alias_map}")
            return alias_map
        except Exception as e:
            logger.error(f"Failed to load aliases: {e}", exc_info=True)
            return {}

    def _load_units(self) -> Dict[str, Dict]:
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            path = os.path.join(base_dir, "knowledge", "laboratory", "units.yaml")
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            units = data.get("units", {})
            logger.debug(f"Loaded units: {list(units.keys())}")
            return units
        except Exception as e:
            logger.error(f"Failed to load units: {e}", exc_info=True)
            return {}

    def normalize(self, raw_name: str, raw_value: float, raw_unit: str) -> Tuple[str, float, Unit]:
        logger.debug(f"Normalizing: {raw_name} {raw_value} {raw_unit}")

        # Проверка значения
        if raw_value < 0:
            raise InvalidParameterError(f"Parameter value cannot be negative: {raw_value} for {raw_name}")

        # Имя
        name_lower = raw_name.strip().lower()
        if not name_lower:
            raise InvalidParameterError("Parameter name cannot be empty")
        canonical = self._aliases.get(name_lower, raw_name.strip())
        logger.debug(f"Canonical name: {canonical}")

        # Единица
        unit_str = raw_unit.strip()
        if not unit_str:
            logger.warning(f"Unit not specified for {canonical}, using as is")
            return canonical, raw_value, Unit("")

        unit_info = self._units.get(unit_str, None)
        if unit_info is None:
            logger.warning(f"Unknown unit '{unit_str}' for {canonical}, using as is")
            return canonical, raw_value, Unit(unit_str)

        base_unit = unit_info["base"]
        factor = unit_info["factor"]
        converted_value = convert(raw_value, factor)
        logger.debug(f"Converted {raw_value} {unit_str} -> {converted_value} {base_unit}")
        return canonical, converted_value, Unit(base_unit)