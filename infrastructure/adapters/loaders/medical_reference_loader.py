import json
import os
import logging
from typing import Optional, Tuple, Dict, Any
from config import settings

logger = logging.getLogger(__name__)

class MedicalReferenceLoader:
    """Загрузчик референсных значений и интерпретаций из medical_data.json."""

    def __init__(self):
        self.data = self._load()
        self.norms = self.data.get("norms", {})
        self.groups = self.data.get("groups", {})
        self.metadata = self.data.get("metadata", {})
        logger.info(f"MedicalReferenceLoader initialized: {len(self.norms)} parameters")

    def _load(self) -> Dict:
        path = os.path.join(settings.BASE_DIR, settings.KNOWLEDGE_DIR, "configs", "medical_data.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"medical_data.json not found at {path}")
            return {"norms": {}, "groups": {}}

    def get_norm(self, param_name: str, gender: str, age: int) -> Tuple[Optional[float], Optional[float]]:
        """Возвращает (min, max) для параметра с учётом пола и возраста."""
        param = self.norms.get(param_name)
        if not param:
            return None, None
        # Ищем подходящую норму
        for rule in param.get("norms", []):
            if "gender" in rule and rule["gender"] != gender:
                continue
            if "age_min" in rule and age < rule["age_min"]:
                continue
            if "age_max" in rule and age > rule["age_max"]:
                continue
            return rule.get("min"), rule.get("max")
        # Если нет специфичной, берём base_min/base_max
        return param.get("base_min"), param.get("base_max")

    def get_unit(self, param_name: str) -> str:
        param = self.norms.get(param_name)
        return param.get("unit", "") if param else ""

    def get_name(self, param_name: str) -> str:
        param = self.norms.get(param_name)
        return param.get("name", param_name) if param else param_name

    def get_interpretation(self, param_name: str, value: float, gender: str, age: int) -> Dict[str, Any]:
        """
        Возвращает статус ('low', 'normal', 'high', 'unknown') и соответствующий текст.
        """
        param = self.norms.get(param_name)
        if not param:
            return {"status": "unknown", "text": "Нет данных", "unit": ""}
        min_val, max_val = self.get_norm(param_name, gender, age)
        unit = param.get("unit", "")
        if min_val is None or max_val is None:
            return {"status": "unknown", "text": "Нет референсов", "unit": unit}
        if value < min_val:
            return {
                "status": "low",
                "text": param.get("low", f"Значение ниже нормы (< {min_val} {unit})"),
                "unit": unit,
                "min": min_val,
                "max": max_val
            }
        elif value > max_val:
            return {
                "status": "high",
                "text": param.get("high", f"Значение выше нормы (> {max_val} {unit})"),
                "unit": unit,
                "min": min_val,
                "max": max_val
            }
        else:
            return {
                "status": "normal",
                "text": "В норме",
                "unit": unit,
                "min": min_val,
                "max": max_val
            }

    def get_group(self, param_name: str) -> str:
        param = self.norms.get(param_name)
        if not param:
            return ""
        group_key = param.get("group")
        return self.groups.get(group_key, group_key)

    def get_all_params(self) -> Dict[str, Dict]:
        """Возвращает все параметры с их данными."""
        return self.norms

    def get_groups(self) -> Dict[str, str]:
        return self.groups