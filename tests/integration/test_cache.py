import pytest
from unittest.mock import MagicMock
from domain.entities.patient import PatientProfile
from domain.entities.parameter import Parameter
from domain.entities.finding import ClinicalFinding
from domain.entities.report import AnalysisReport
from domain.value_objects.gender import Gender
from domain.value_objects.unit import Unit
from domain.value_objects.risk_level import RiskLevel
from infrastructure.cache.redis_cache import RedisCache
from infrastructure.repositories.audit_repository import AuditRepository
from domain.interfaces import RuleRepository
from application.validators.physiological_validator import PhysiologicalValidator
from application.services.inference_engine import InferenceEngine
from application.services.action_mapper import ActionMapper
from application.services.report_builder import ReportBuilder
from application.services.post_processor import PostProcessor
from application.services.analysis_pipeline import AnalysisPipeline
from application.ports.parser_interface import ParserInterface
from application.ports.history_repository import HistoryRepository
from application.ports.renderer_interface import RendererInterface

@pytest.mark.integration
def test_cache_hit_does_not_raise_name_error():
    # Мокаем все зависимости
    parser = MagicMock(spec=ParserInterface)
    parser.parse.return_value = [Parameter("glucose", 10.0, Unit("mmol/L"))]

    inference_engine = MagicMock(spec=InferenceEngine)
    inference_engine.infer.return_value = []

    action_mapper = MagicMock(spec=ActionMapper)
    action_mapper.map_to_actions.return_value = []

    report_builder = MagicMock(spec=ReportBuilder)
    report_builder.build.return_value = AnalysisReport(findings=[], actions=[], explanation="Test")

    history_repo = MagicMock(spec=HistoryRepository)
    renderer = MagicMock(spec=RendererInterface)
    post_processor = MagicMock(spec=PostProcessor)
    post_processor.process.return_value = {"diagnoses": []}

    # Мокаем кэш – возвращаем закэшированный результат
    cache = MagicMock(spec=RedisCache)
    cache.get.return_value = {
        "findings": [{"id": "F1", "title": "Test", "probability": 0.9, "risk": 3, "evidence": [], "description": ""}],
        "actions": [{"doctor_specialty": "Hematologist", "urgency": "moderate", "additional_tests": []}],
        "explanation": "Cached explanation"
    }

    audit_repo = MagicMock(spec=AuditRepository)
    rule_repo = MagicMock(spec=RuleRepository)
    validator = MagicMock(spec=PhysiologicalValidator)
    validator.validate.return_value = []

    pipeline = AnalysisPipeline(
        parser=parser,
        inference_engine=inference_engine,
        action_mapper=action_mapper,
        report_builder=report_builder,
        history_repo=history_repo,
        renderer=renderer,
        post_processor=post_processor,
        cache=cache,
        audit_repo=audit_repo,
        rule_repo=rule_repo,
        validator=validator
    )

    patient = PatientProfile(id="P1", gender=Gender.MALE, age=30)
    report = pipeline.run_structured(patient, "glucose 10.0", user_id=1)

    # Проверяем, что отчёт собран из кэша без ошибок
    assert report.explanation == "Cached explanation"
    assert len(report.findings) == 1
    assert report.findings[0].id == "F1"
    # Убеждаемся, что методы, которые не должны вызываться, не вызваны
    inference_engine.infer.assert_not_called()