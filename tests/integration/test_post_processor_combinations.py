import pytest
from infrastructure.bootstrap.di_container import DIContainer
from domain.entities.finding import ClinicalFinding
from domain.value_objects.risk_level import RiskLevel
from domain.entities.report import AnalysisReport

@pytest.mark.integration
def test_combination_primary_hyperparathyroidism():
    container = DIContainer()
    findings = [
        ClinicalFinding(id="hypercalcemia", title="Hypercalcemia", probability=0.8, risk=RiskLevel.HIGH),
        ClinicalFinding(id="vitamin_d_deficiency", title="Vitamin D deficiency", probability=0.7, risk=RiskLevel.HIGH)
    ]
    report = AnalysisReport(findings=findings, actions=[], explanation="")
    result = container.post_processor.process(report)
    combined = [d for d in result["diagnoses"] if d.get("combined") and d["id"] == "primary_hyperparathyroidism"]
    assert len(combined) == 1

@pytest.mark.integration
def test_combination_hepatorenal_syndrome():
    """
    acute_hepatitis - multi-condition файл (alt/ast/bilirubin_total), поэтому
    finding.id для него - это id конкретного условия (acute_hepatitis_bilirubin_total),
    а не имя файла. acute_kidney_injury - single-condition, id совпадает с именем файла.
    См. combinations в clinical_logic.yaml и DATA_REVIEW_NEEDED.md, раздел 15.
    """
    container = DIContainer()
    findings = [
        ClinicalFinding(id="acute_kidney_injury", title="AKI", probability=0.6, risk=RiskLevel.HIGH),
        ClinicalFinding(id="acute_hepatitis_bilirubin_total", title="Acute hepatitis (bilirubin)", probability=0.6, risk=RiskLevel.HIGH)
    ]
    report = AnalysisReport(findings=findings, actions=[], explanation="")
    result = container.post_processor.process(report)
    combined = [d for d in result["diagnoses"] if d.get("combined") and d["id"] == "hepatorenal_syndrome"]
    assert len(combined) == 1

@pytest.mark.integration
def test_combination_septic_syndrome():
    """
    sepsis и systemic_inflammation - оба multi-condition файлы, finding.id всегда
    с суффиксом параметра (sepsis_crp, systemic_inflammation_esr и т.п.), не имя файла.
    Exclusion 'sepsis -> systemic_inflammation' был убран из clinical_logic.yaml,
    так как он противоречил этой же комбинации (гасил один из компонентов раньше,
    чем комбинация успевала его использовать) - см. DATA_REVIEW_NEEDED.md, раздел 15.
    Комбинация теперь ДОЛЖНА срабатывать при наличии обоих атомарных признаков.
    """
    container = DIContainer()
    findings = [
        ClinicalFinding(id="sepsis_crp", title="Sepsis (CRP)", probability=0.9, risk=RiskLevel.CRITICAL),
        ClinicalFinding(id="systemic_inflammation_esr", title="Systemic inflammation (ESR)", probability=0.7, risk=RiskLevel.HIGH)
    ]
    report = AnalysisReport(findings=findings, actions=[], explanation="")
    result = container.post_processor.process(report)
    combined = [d for d in result["diagnoses"] if d.get("combined") and d["id"] == "septic_syndrome"]
    assert len(combined) == 1

@pytest.mark.integration
def test_combination_metabolic_bone_disease():
    container = DIContainer()
    findings = [
        ClinicalFinding(id="vitamin_d_deficiency", title="Vitamin D deficiency", probability=0.7, risk=RiskLevel.HIGH),
        ClinicalFinding(id="hypercalcemia", title="Hypercalcemia", probability=0.8, risk=RiskLevel.HIGH)
    ]
    report = AnalysisReport(findings=findings, actions=[], explanation="")
    result = container.post_processor.process(report)
    combined = [d for d in result["diagnoses"] if d.get("combined") and d["id"] == "metabolic_bone_disease"]
    assert len(combined) == 1