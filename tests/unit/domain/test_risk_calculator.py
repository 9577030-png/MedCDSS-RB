import pytest
from domain.value_objects.unit import Unit
from domain.value_objects.risk_level import RiskLevel
from domain.entities.threshold import Threshold
from domain.logic.risk_calculator import calculate_risk

def test_risk_calculator_normal():
    threshold = Threshold("potassium", low=3.5, high=5.0, unit=Unit("mmol/L"), risk_level=RiskLevel.HIGH)
    assert calculate_risk(4.0, threshold) == RiskLevel.NORMAL

def test_risk_calculator_low():
    threshold = Threshold("potassium", low=3.5, high=5.0, unit=Unit("mmol/L"), risk_level=RiskLevel.HIGH)
    assert calculate_risk(3.0, threshold) == RiskLevel.HIGH

def test_risk_calculator_high():
    threshold = Threshold("potassium", low=3.5, high=5.0, unit=Unit("mmol/L"), risk_level=RiskLevel.HIGH)
    assert calculate_risk(5.5, threshold) == RiskLevel.HIGH

def test_risk_calculator_no_low():
    threshold = Threshold("glucose", low=None, high=6.0, unit=Unit("mmol/L"), risk_level=RiskLevel.CRITICAL)
    assert calculate_risk(5.0, threshold) == RiskLevel.NORMAL
    assert calculate_risk(7.0, threshold) == RiskLevel.CRITICAL