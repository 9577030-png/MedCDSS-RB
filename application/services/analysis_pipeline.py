import logging
from typing import List, Union, Dict, Any
from domain.entities.patient import PatientProfile
from domain.entities.parameter import Parameter
from domain.entities.report import AnalysisReport
from application.ports.parser_interface import ParserInterface
from application.ports.history_repository import HistoryRepository
from application.ports.renderer_interface import RendererInterface
from application.services.inference_engine import InferenceEngine
from application.services.action_mapper import ActionMapper
from application.services.report_builder import ReportBuilder
from application.services.post_processor import PostProcessor
from domain.exceptions import MedicalAIError

logger = logging.getLogger(__name__)

class AnalysisPipeline:
    """
    Главный оркестратор анализа. Управляет всем процессом:
    парсинг → вывод → построение действий → постобработка.
    """

    def __init__(
        self,
        parser: ParserInterface,
        inference_engine: InferenceEngine,
        action_mapper: ActionMapper,
        report_builder: ReportBuilder,
        history_repo: HistoryRepository,
        renderer: RendererInterface,
        post_processor: PostProcessor = None
    ):
        self.parser = parser
        self.inference_engine = inference_engine
        self.action_mapper = action_mapper
        self.report_builder = report_builder
        self.history_repo = history_repo
        self.renderer = renderer
        self.post_processor = post_processor or PostProcessor()
        logger.info("AnalysisPipeline initialized with post-processor")

    def run(self, patient: PatientProfile, raw_text: str) -> str:
        """
        Стандартный запуск – возвращает отрендеренный текст (для консоли).
        """
        logger.info(f"Starting standard run for patient {patient.id}")
        report = self._run_core(patient, raw_text)
        rendered = self.renderer.render(report)
        logger.info("Standard run completed")
        return rendered

    def run_structured(self, patient: PatientProfile, raw_text: str) -> AnalysisReport:
        """
        Возвращает объект отчёта без рендеринга (для API).
        """
        logger.info(f"Starting structured run for patient {patient.id}")
        report = self._run_core(patient, raw_text)
        logger.info("Structured run completed")
        return report

    def run_with_postprocessing(self, patient: PatientProfile, raw_text: str) -> Dict[str, Any]:
        """
        Запускает анализ и возвращает структурированное заключение с группировкой,
        диагнозами, рекомендациями и общей оценкой риска.
        """
        logger.info(f"Starting post-processed run for patient {patient.id}")
        report = self._run_core(patient, raw_text)
        result = self.post_processor.process(report)
        logger.info("Post-processed run completed")
        return result

    def _run_core(self, patient: PatientProfile, raw_text: str) -> AnalysisReport:
        """
        Внутренний метод – выполняет основные шаги анализа без постобработки.
        """
        logger.info(f"Core analysis for patient {patient.id}")
        try:
            # 1. Парсинг
            parameters = self.parser.parse(raw_text)
            logger.debug(f"Parsed {len(parameters)} parameters")

            # 2. Вывод (inference) – поиск находок
            findings = self.inference_engine.infer(patient, parameters)
            logger.info(f"Found {len(findings)} findings")

            # 3. Построение действий (рекомендации)
            actions = self.action_mapper.map_to_actions(findings)
            logger.debug(f"Mapped {len(actions)} actions")

            # 4. Сборка отчёта
            report = self.report_builder.build(findings, actions)

            # 5. Сохранение в историю
            self.history_repo.save(patient.id, report)

            logger.info("Core analysis completed successfully")
            return report

        except MedicalAIError as e:
            logger.error(f"Domain error during analysis: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
            raise