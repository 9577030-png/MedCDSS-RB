import pytest
import os
from infrastructure.adapters.storage.sql_history_repository import SqlHistoryRepository
from domain.entities.report import AnalysisReport
from domain.entities.finding import ClinicalFinding
from domain.entities.recommendation import Recommendation
from domain.value_objects.risk_level import RiskLevel
from domain.value_objects.severity import Severity

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_history.db")

@pytest.fixture
def repo(db_path):
    return SqlHistoryRepository(db_path)

def test_save_and_load(repo):
    # Создаём тестовый отчёт
    finding = ClinicalFinding(
        id="F1",
        title="Anemia",
        probability=0.9,
        risk=RiskLevel.HIGH,
        doctor_specialty="Hematologist",
        tests=["Iron"],
        evidence=["Low ferritin"],
        excluded_by=[]
    )
    action = Recommendation(
        doctor_specialty="Hematologist",
        urgency=Severity.MODERATE,
        additional_tests=["B12", "Folate"]
    )
    report = AnalysisReport(
        findings=[finding],
        actions=[action],
        explanation="Test explanation"
    )

    # Сохраняем
    repo.save("P123", report)

    # Загружаем
    loaded = repo.load("P123")
    assert loaded is not None
    assert len(loaded.findings) == 1
    assert loaded.findings[0].id == "F1"
    assert loaded.findings[0].risk == RiskLevel.HIGH
    assert loaded.actions[0].urgency == Severity.MODERATE
    assert loaded.explanation == "Test explanation"

    # Проверяем несуществующего пациента
    none_report = repo.load("UNKNOWN")
    assert none_report is None

def test_multiple_saves(repo):
    # Сохраняем два отчёта для одного пациента
    report1 = AnalysisReport(findings=[], actions=[], explanation="First")
    report2 = AnalysisReport(findings=[], actions=[], explanation="Second")
    repo.save("P1", report1)
    repo.save("P1", report2)
    loaded = repo.load("P1")
    assert loaded.explanation == "Second"  # должен загрузиться последний