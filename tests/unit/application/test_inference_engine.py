import pytest
from unittest.mock import Mock
from domain.entities.patient import PatientProfile
from domain.entities.parameter import Parameter
from domain.entities.guideline import SpecialtyGuideline
from domain.value_objects.unit import Unit
from domain.value_objects.risk_level import RiskLevel
from domain.value_objects.gender import Gender
from application.services.inference_engine import InferenceEngine

def test_inference_engine():
    guideline_provider = Mock()
    threshold_provider = Mock()
    guideline = SpecialtyGuideline(id="G1", scoring_rules={"Hb": 2, "MCV": 1})
    guideline_provider.get_all.return_value = [guideline]
    patient = PatientProfile(id="P1", gender=Gender.MALE, age=30)
    parameters = [Parameter("Hb", 100, Unit("g/L")), Parameter("MCV", 80, Unit("fL"))]
    engine = InferenceEngine(guideline_provider, threshold_provider)
    findings = engine.infer(patient, parameters)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.id == "G1"
    assert finding.risk == RiskLevel.HIGH
    assert finding.probability > 0