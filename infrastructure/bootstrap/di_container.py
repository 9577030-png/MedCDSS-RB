import os
import logging
from config import settings
from infrastructure.adapters.loaders.yaml_threshold_loader import YamlThresholdLoader
from infrastructure.adapters.loaders.yaml_recommendation_loader import YamlRecommendationLoader
from infrastructure.adapters.loaders._merged_guideline_provider import MergedGuidelineProvider
from infrastructure.adapters.loaders.yaml_guideline_provider import YamlGuidelineProvider
from infrastructure.adapters.loaders.clinical_logic_loader import ClinicalLogicLoader
from infrastructure.adapters.parsers.regex_parser import RegexParser
from infrastructure.adapters.renderers.console_renderer import ConsoleRenderer
from infrastructure.adapters.storage.sql_history_repository import SqlHistoryRepository
from infrastructure.adapters.storage.sql_user_repository import SqlUserRepository
from application.services.inference_engine import InferenceEngine
from application.services.action_mapper import ActionMapper
from application.services.report_builder import ReportBuilder
from application.services.analysis_pipeline import AnalysisPipeline
from application.services.post_processor import PostProcessor

logger = logging.getLogger(__name__)

class DIContainer:
    def __init__(self, probability_threshold: float = 0.3):
        logger.info("DIContainer initializing...")

        # Репозитории
        self.user_repo = SqlUserRepository(settings.DB_PATH)

        self.threshold_loader = YamlThresholdLoader()
        self.recommendation_loader = YamlRecommendationLoader()
        self.logic_loader = ClinicalLogicLoader()

        self.merged_guideline_provider = MergedGuidelineProvider(self.threshold_loader)
        self.guideline_provider = YamlGuidelineProvider(self.merged_guideline_provider)

        self.parser = RegexParser()
        self.renderer = ConsoleRenderer()
        self.history_repo = SqlHistoryRepository(settings.DB_PATH)

        self.inference_engine = InferenceEngine(self.guideline_provider, self.threshold_loader)
        self.action_mapper = ActionMapper(self.recommendation_loader)
        self.report_builder = ReportBuilder()

        self.post_processor = PostProcessor(logic_loader=self.logic_loader, probability_threshold=probability_threshold)

        self.pipeline = AnalysisPipeline(
            parser=self.parser,
            inference_engine=self.inference_engine,
            action_mapper=self.action_mapper,
            report_builder=self.report_builder,
            history_repo=self.history_repo,
            renderer=self.renderer,
            post_processor=self.post_processor
        )

        logger.info("DIContainer initialized successfully")

    def reload_configuration(self) -> None:
        logger.info("Reloading all configurations...")
        self.threshold_loader.reload()
        self.recommendation_loader.reload()
        self.logic_loader.reload()
        self.guideline_provider.reload()

        # Обновляем пост-процессор
        self.post_processor = PostProcessor(
            logic_loader=self.logic_loader,
            probability_threshold=self.post_processor.threshold
        )

        # Пересоздаём inference_engine и action_mapper с обновлёнными загрузчиками
        self.inference_engine = InferenceEngine(self.guideline_provider, self.threshold_loader)
        self.action_mapper = ActionMapper(self.recommendation_loader)

        # Пересоздаём pipeline с новыми компонентами
        self.pipeline = AnalysisPipeline(
            parser=self.parser,
            inference_engine=self.inference_engine,
            action_mapper=self.action_mapper,
            report_builder=self.report_builder,
            history_repo=self.history_repo,
            renderer=self.renderer,
            post_processor=self.post_processor
        )

        logger.info("All configurations reloaded successfully.") 