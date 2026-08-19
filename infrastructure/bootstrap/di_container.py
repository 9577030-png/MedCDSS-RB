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

# Новые импорты
from domain.interfaces import RuleRepository
from infrastructure.repositories.sqlalchemy_rule_repository import SQLAlchemyRuleRepository
from infrastructure.repositories.audit_repository import AuditRepository
from infrastructure.cache.redis_cache import RedisCache
from application.validators.physiological_validator import PhysiologicalValidator
from application.services.version_manager import VersionManager

logger = logging.getLogger(__name__)

class DIContainer:
    def __init__(self, probability_threshold: float = 0.3):
        logger.info("DIContainer initializing...")

        # --- Существующие компоненты ---
        self.user_repo = SqlUserRepository(settings.DB_PATH)
        self.threshold_loader = YamlThresholdLoader()
        self.recommendation_loader = YamlRecommendationLoader()
        self.logic_loader = ClinicalLogicLoader()
        self.merged_guideline_provider = MergedGuidelineProvider(self.threshold_loader)
        self.guideline_provider = YamlGuidelineProvider(self.merged_guideline_provider)
        self.parser = RegexParser()
        self.renderer = ConsoleRenderer()
        self.history_repo = SqlHistoryRepository(settings.DB_PATH)

        # --- НОВЫЕ КОМПОНЕНТЫ (улучшенный движок) ---

        # 1. Репозиторий правил (SQLAlchemy)
        self.rule_repo = SQLAlchemyRuleRepository(settings.DATABASE_URL)

        # 2. Репозиторий аудита
        self.audit_repo = AuditRepository(settings.DATABASE_URL)

        # 3. Кэш Redis – инициализируем только если URL задан и соединение успешно
        self.cache = None
        if settings.REDIS_URL:
            try:
                cache = RedisCache(settings.REDIS_URL)
                # Проверяем соединение
                cache.client.ping()
                self.cache = cache
                logger.info("Redis cache enabled")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Cache disabled.")
                self.cache = None

               # 4. Валидатор физиологических диапазонов (если файл существует)
        config_dir = os.path.join(settings.BASE_DIR, settings.KNOWLEDGE_DIR, "configs")
        physiological_ranges_path = os.path.join(config_dir, "physiological_ranges.yaml")
        if os.path.exists(physiological_ranges_path):
            try:
                self.validator = PhysiologicalValidator(physiological_ranges_path)
                logger.info("Physiological validator enabled")
            except Exception as e:
                logger.warning(f"Failed to load physiological validator: {e}. Validator disabled.")
                self.validator = None
        else:
            logger.warning(f"Physiological ranges file not found: {physiological_ranges_path}. Validator disabled.")
            self.validator = None

        # 5. Менеджер версий правил
        guidelines_dir = os.path.join(settings.BASE_DIR, settings.GUIDELINES_DIR)
        self.version_manager = VersionManager(self.rule_repo, guidelines_dir)
         # Загружаем все правила из YAML в БД и активируем их
        try:
            logger.info("Loading rules from YAML into database...")
            new_versions = self.version_manager.hot_reload(created_by="system")
            # Активируем все загруженные версии
            for version in new_versions:
                self.version_manager.activate_version(version.rule_id, version.version_id)
            logger.info(f"Activated {len(new_versions)} rule versions")
        except Exception as e:
            logger.error(f"Failed to load rules: {e}", exc_info=True)

        # --- Движок вывода с новыми зависимостями ---
        self.inference_engine = InferenceEngine(
            rule_repo=self.rule_repo,
            threshold_provider=self.threshold_loader,
            guideline_provider=self.guideline_provider
        )

        self.action_mapper = ActionMapper(self.recommendation_loader)
        self.report_builder = ReportBuilder()

        self.post_processor = PostProcessor(
            logic_loader=self.logic_loader,
            probability_threshold=probability_threshold
        )

        # --- Главный пайплайн с опциональными улучшениями ---
        self.pipeline = AnalysisPipeline(
            parser=self.parser,
            inference_engine=self.inference_engine,
            action_mapper=self.action_mapper,
            report_builder=self.report_builder,
            history_repo=self.history_repo,
            renderer=self.renderer,
            post_processor=self.post_processor,
            cache=self.cache,                 # может быть None
            audit_repo=self.audit_repo,       # всегда есть
            rule_repo=self.rule_repo,         # всегда есть
            validator=self.validator          # может быть None
        )

        logger.info("DIContainer initialized successfully")

    def reload_configuration(self) -> None:
        logger.info("Reloading all configurations...")
        self.threshold_loader.reload()
        self.recommendation_loader.reload()
        self.logic_loader.reload()
        self.guideline_provider.reload()

        self.post_processor = PostProcessor(
            logic_loader=self.logic_loader,
            probability_threshold=self.post_processor.threshold
        )

        self.inference_engine = InferenceEngine(
            rule_repo=self.rule_repo,
            threshold_provider=self.threshold_loader,
            guideline_provider=self.guideline_provider
        )
        self.action_mapper = ActionMapper(self.recommendation_loader)

        self.pipeline = AnalysisPipeline(
            parser=self.parser,
            inference_engine=self.inference_engine,
            action_mapper=self.action_mapper,
            report_builder=self.report_builder,
            history_repo=self.history_repo,
            renderer=self.renderer,
            post_processor=self.post_processor,
            cache=self.cache,
            audit_repo=self.audit_repo,
            rule_repo=self.rule_repo,
            validator=self.validator
        )

        logger.info("All configurations reloaded successfully.")