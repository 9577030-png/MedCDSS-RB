from abc import ABC, abstractmethod
from typing import Optional, List
from domain.rule_version import RuleVersion

class RuleRepository(ABC):
    @abstractmethod
    def save(self, rule_version: RuleVersion) -> RuleVersion:
        """Сохранить новую версию правила."""
        pass

    @abstractmethod
    def get_active_versions(self) -> List[RuleVersion]:
        """Получить все активные версии правил."""
        pass

    @abstractmethod
    def get_by_id(self, rule_id: str, version_id: Optional[int] = None) -> Optional[RuleVersion]:
        """Получить конкретную версию правила. Если version_id не указан – активную."""
        pass

    @abstractmethod
    def activate_version(self, rule_id: str, version_id: int) -> None:
        """Активировать указанную версию (деактивировать предыдущие)."""
        pass

    @abstractmethod
    def get_version_history(self, rule_id: str) -> List[RuleVersion]:
        """Получить всю историю версий правила."""
        pass