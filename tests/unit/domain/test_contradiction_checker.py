from domain.entities.finding import ClinicalFinding
from domain.logic.contradiction_checker import filter_contradictions
from domain.value_objects.risk_level import RiskLevel

def test_filter_contradictions():
    f1 = ClinicalFinding(id="A", title="A", probability=0.8, risk=RiskLevel.HIGH, excluded_by=[])
    f2 = ClinicalFinding(id="B", title="B", probability=0.9, risk=RiskLevel.HIGH, excluded_by=["A"])
    f3 = ClinicalFinding(id="C", title="C", probability=0.5, risk=RiskLevel.LOW, excluded_by=[])
    result = filter_contradictions([f1, f2, f3])
    # f2 исключена, потому что excluded_by содержит "A"
    assert result == [f1, f3]