from typing import Dict, Any
from copy import deepcopy
from domain.entities.threshold import Threshold
from domain.exceptions import ConfigurationError

def resolve(
    global_thresholds: Dict[str, Threshold],
    overrides: Dict[str, Dict[str, Any]]
) -> Dict[str, Threshold]:
    """
    Применяет частичный override к глобальным порогам.
    Для каждого параметра, если есть запись в overrides, заменяются только
    указанные поля (low, high, unit, risk_level). Остальные берутся из глобального.
    """
    if global_thresholds is None:
        raise ConfigurationError("global_thresholds cannot be None")
    if not isinstance(global_thresholds, dict):
        raise ConfigurationError("global_thresholds must be a dict")

    result = {}
    for param_name, base in global_thresholds.items():
        if param_name in overrides:
            override = overrides[param_name]
            if not isinstance(override, dict):
                raise ConfigurationError(f"Override for '{param_name}' must be a dict, got {type(override)}")
            try:
                from dataclasses import replace
                updated = replace(
                    base,
                    low=override.get('low', base.low),
                    high=override.get('high', base.high),
                    unit=override.get('unit', base.unit),
                    risk_level=override.get('risk_level', base.risk_level)
                )
                result[param_name] = updated
            except Exception as e:
                raise ConfigurationError(f"Failed to apply override for '{param_name}': {e}")
        else:
            result[param_name] = base
    return result