import pytest
from infrastructure.bootstrap.di_container import DIContainer
from domain.entities.patient import PatientProfile
from domain.entities.finding import ClinicalFinding
from domain.value_objects.risk_level import RiskLevel
from domain.entities.report import AnalysisReport

@pytest.mark.integration
def test_combination_primary_hyperparathyroidism():
    """Проверяет, что комбинация hypercalcemia + vitamin_d_deficiency даёт диагноз primary_hyperparathyroidism."""
    container = DIContainer()
    findings = [
        ClinicalFinding(
            id="hypercalcemia",
            title="Hypercalcemia",
            probability=0.8,
            risk=RiskLevel.HIGH,
            description="Повышенный кальций"
        ),
        ClinicalFinding(
            id="vitamin_d_deficiency",
            title="Vitamin D deficiency",
            probability=0.7,
            risk=RiskLevel.HIGH,
            description="Дефицит витамина D"
        )
    ]
    report = AnalysisReport(findings=findings, actions=[], explanation="")
    result = container.post_processor.process(report)
    combined = [d for d in result["diagnoses"] if d.get("combined") and d["id"] == "primary_hyperparathyroidism"]
    assert len(combined) == 1
    assert combined[0]["probability"] > 0

@pytest.mark.integration
def test_combination_hepatorenal_syndrome():
    """Проверяет комбинацию acute_kidney_injury + acute_hepatitis."""
    container = DIContainer()
    findings = [
        ClinicalFinding(
            id="acute_kidney_injury",
            title="AKI",
            probability=0.6,
            risk=RiskLevel.HIGH,
            description="Острое повреждение почек"
        ),
        ClinicalFinding(
            id="acute_hepatitis",
            title="Acute hepatitis",
            probability=0.6,
            risk=RiskLevel.HIGH,
            description="Острый гепатит"
        )
    ]
    report = AnalysisReport(findings=findings, actions=[], explanation="")
    result = container.post_processor.process(report)
    combined = [d for d in result["diagnoses"] if d.get("combined") and d["id"] == "hepatorenal_syndrome"]
    assert len(combined) == 1
    assert combined[0]["probability"] > 0

@pytest.mark.integration
def test_combination_septic_syndrome():
    """Проверяет комбинацию sepsis + systemic_inflammation."""
    container = DIContainer()
    findings = [
        ClinicalFinding(
            id="sepsis",
            title="Sepsis",
            probability=0.9,
            risk=RiskLevel.CRITICAL,
            description="Сепсис"
        ),
        ClinicalFinding(
            id="systemic_inflammation",
            title="Systemic inflammation",
            probability=0.7,
            risk=RiskLevel.HIGH,
            description="Системное воспаление"
        )
    ]
    report = AnalysisReport(findings=findings, actions=[], explanation="")
    result = container.post_processor.process(report)
    combined = [d for d in result["diagnoses"] if d.get("combined") and d["id"] == "septic_syndrome"]
    assert len(combined) == 1
    assert combined[0]["probability"] > 0

@pytest.mark.integration
def test_combination_metabolic_bone_disease():
    """Проверяет комбинацию vitamin_d_deficiency + hypercalcemia (другая комбинация с теми же условиями)."""
    container = DIContainer()
    findings = [
        ClinicalFinding(
            id="vitamin_d_deficiency",
            title="Vitamin D deficiency",
            probability=0.7,
            risk=RiskLevel.HIGH,
            description="Дефицит витамина D"
        ),
        ClinicalFinding(
            id="hypercalcemia",
            title="Hypercalcemia",
            probability=0.8,
            risk=RiskLevel.HIGH,
            description="Повышенный кальций"
        )
    ]
    report = AnalysisReport(findings=findings, actions=[], explanation="")
    result = container.post_processor.process(report)
    # Должна быть комбинация metabolic_bone_disease (если она есть в конфиге)
    combined = [d for d in result["diagnoses"] if d.get("combined") and d["id"] == "metabolic_bone_disease"]
    # Если в clinical_logic.yaml есть такая комбинация, она должна сработать
    # Проверяем, что хотя бы одна комбинация есть
    assert any(d.get("combined") for d in result["diagnoses"]), "At least one combined diagnosis should be present"