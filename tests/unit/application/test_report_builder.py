from domain.entities.finding import ClinicalFinding
from domain.entities.recommendation import Recommendation
from domain.value_objects.risk_level import RiskLevel
from domain.value_objects.severity import Severity
from application.services.report_builder import ReportBuilder

def test_report_builder():
    findings = [ClinicalFinding(id="F1", title="Anemia", probability=0.9, risk=RiskLevel.HIGH)]
    actions = [Recommendation(doctor_specialty="Hematologist", additional_tests=["Iron"], urgency=Severity.MODERATE)]
    builder = ReportBuilder()
    report = builder.build(findings, actions)
    assert report.findings == findings
    assert report.actions == actions
    assert "Findings" in report.explanation