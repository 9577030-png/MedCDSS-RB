import logging
import yaml
from pathlib import Path
from typing import List
from domain.rule_version import RuleVersion, RuleTier
from domain.interfaces import RuleRepository
from domain.exceptions import VersionNotFoundError
from application.services.clinical_interpretation_mapper import ClinicalInterpretationMapper

logger = logging.getLogger(__name__)

class VersionManager:
    def __init__(self, rule_repo: RuleRepository, config_dir: str):
        self.rule_repo = rule_repo
        self.config_dir = Path(config_dir)
        self.interpretation_mapper = ClinicalInterpretationMapper()

    def load_from_yaml(self, rule_id: str, yaml_path: Path, created_by: str = "system") -> RuleVersion:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        # Строим правило один раз (это уже выполняет конвертацию старого формата
        # thresholds/scoring -> conditions через RuleVersion.from_yaml), затем
        # пересчитываем tier по РЕАЛЬНЫМ, уже сконвертированным id условий - а не
        # только по ключам сырого YAML. Раньше здесь читался data.get('conditions', [])
        # из сырого файла, что давало ложный 'basic' для любого файла, где conditions
        # появляются только после программной конвертации (thresholds/scoring-схема,
        # например knowledge/guidelines/nephrology/diabetic_nephropathy.yaml) - хотя
        # сам текст интерпретации для этих id уже подключается корректно.
        version = RuleVersion.from_yaml(rule_id, data, created_by, tier=RuleTier.BASIC)
        base_name = yaml_path.stem
        candidate_ids = {base_name} | {c.get("id", base_name) for c in version.conditions}
        version.tier = RuleTier.ENRICHED if any(self.interpretation_mapper.is_enriched(cid) for cid in candidate_ids) else RuleTier.BASIC
        return self.rule_repo.save(version)

    def activate_version(self, rule_id: str, version_id: int) -> None:
        version = self.rule_repo.get_by_id(rule_id, version_id)
        if not version:
            raise VersionNotFoundError(f"Version {version_id} for rule {rule_id} not found")
        self.rule_repo.activate_version(rule_id, version_id)

    def get_history(self, rule_id: str) -> List[RuleVersion]:
        return self.rule_repo.get_version_history(rule_id)

    def hot_reload(self, created_by: str = "system") -> List[RuleVersion]:
        new_versions = []
        for yaml_file in self.config_dir.rglob("*.yaml"):
            # Используем относительный путь как rule_id для сохранения в БД
            rule_id = str(yaml_file.relative_to(self.config_dir)).replace("\\", "/").replace(".yaml", "")
            try:
                version = self.load_from_yaml(rule_id, yaml_file, created_by)
                new_versions.append(version)
                logger.info(f"Loaded {rule_id} (version {version.version_id}, tier={version.tier.value})")
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")
        return new_versions