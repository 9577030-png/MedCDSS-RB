import logging
import yaml
from pathlib import Path
from typing import List
from domain.rule_version import RuleVersion
from domain.interfaces import RuleRepository
from domain.exceptions import MedicalAIError, VersionNotFoundError

logger = logging.getLogger(__name__)

class VersionManager:
    def __init__(self, rule_repo: RuleRepository, config_dir: str):
        self.rule_repo = rule_repo
        self.config_dir = Path(config_dir)

    def load_from_yaml(self, rule_id: str, yaml_path: Path, created_by: str = "system") -> RuleVersion:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        version = RuleVersion.from_yaml(rule_id, data, created_by)
        return self.rule_repo.save(version)

    def activate_version(self, rule_id: str, version_id: int) -> None:
        version = self.rule_repo.get_by_id(rule_id, version_id)
        if not version:
            raise VersionNotFoundError(f"Version {version_id} for rule {rule_id} not found")
        self.rule_repo.activate_version(rule_id, version_id)

    def get_history(self, rule_id: str) -> List[RuleVersion]:
        return self.rule_repo.get_version_history(rule_id)

    def hot_reload(self, created_by: str = "system") -> List[RuleVersion]:
        """Обновить все правила из YAML-файлов (рекурсивно по всем подпапкам)."""
        new_versions = []
        for yaml_file in self.config_dir.rglob("*.yaml"):   # рекурсивный обход
            # Используем относительный путь как rule_id, чтобы избежать коллизий
            rule_id = str(yaml_file.relative_to(self.config_dir)).replace("\\", "/").replace(".yaml", "")
            try:
                version = self.load_from_yaml(rule_id, yaml_file, created_by)
                new_versions.append(version)
                logger.info(f"Loaded new version for {rule_id} (version {version.version_id})")
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")
        return new_versions