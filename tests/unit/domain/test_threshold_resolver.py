import pytest
from domain.value_objects.unit import Unit
from domain.value_objects.risk_level import RiskLevel
from domain.entities.threshold import Threshold
from domain.logic.threshold_resolver import resolve

def test_resolve_without_overrides():
    """Если overrides пуст, возвращаются те же пороги."""
    global_thresholds = {
        "potassium": Threshold(
            parameter_name="potassium",
            low=3.5,
            high=5.0,
            unit=Unit("mmol/L"),
            risk_level=RiskLevel.HIGH
        ),
        "hemoglobin": Threshold(
            parameter_name="hemoglobin",
            low=120,
            high=160,
            unit=Unit("g/L"),
            risk_level=RiskLevel.HIGH
        )
    }
    result = resolve(global_thresholds, {})
    assert result == global_thresholds

def test_partial_override():
    """Переопределяем только high для potassium, low остаётся из глобального."""
    global_thresholds = {
        "potassium": Threshold(
            parameter_name="potassium",
            low=3.5,
            high=5.0,
            unit=Unit("mmol/L"),
            risk_level=RiskLevel.HIGH
        ),
        "hemoglobin": Threshold(
            parameter_name="hemoglobin",
            low=120,
            high=160,
            unit=Unit("g/L"),
            risk_level=RiskLevel.HIGH
        )
    }
    overrides = {
        "potassium": {"high": 5.5}
    }
    result = resolve(global_thresholds, overrides)
    # Проверяем, что potassium.high стал 5.5, а low остался 3.5
    assert result["potassium"].high == 5.5
    assert result["potassium"].low == 3.5
    # hemoglobin не изменился
    assert result["hemoglobin"] == global_thresholds["hemoglobin"]

def test_full_override():
    """Переопределяем все поля для параметра."""
    global_thresholds = {
        "potassium": Threshold(
            parameter_name="potassium",
            low=3.5,
            high=5.0,
            unit=Unit("mmol/L"),
            risk_level=RiskLevel.HIGH
        )
    }
    overrides = {
        "potassium": {
            "low": 3.0,
            "high": 6.0,
            "unit": Unit("mEq/L"),
            "risk_level": RiskLevel.CRITICAL
        }
    }
    result = resolve(global_thresholds, overrides)
    assert result["potassium"].low == 3.0
    assert result["potassium"].high == 6.0
    assert result["potassium"].unit == Unit("mEq/L")
    assert result["potassium"].risk_level == RiskLevel.CRITICAL