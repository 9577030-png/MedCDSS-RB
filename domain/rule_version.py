from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import IntEnum

class RulePriority(IntEnum):
    LOW = 10
    MEDIUM = 50
    HIGH = 100
    CRITICAL = 200

@dataclass
class RuleVersion:
    # Обязательные поля (без значений по умолчанию) — идут первыми
    rule_id: str
    name: str
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    created_at: datetime
    created_by: str

    # Необязательные поля (со значениями по умолчанию)
    version_id: int = 0
    priority: RulePriority = RulePriority.MEDIUM
    conflicts_with: List[str] = field(default_factory=list)
    supports: List[str] = field(default_factory=list)
    is_active: bool = False
    comment: Optional[str] = None

    @classmethod
    def from_yaml(cls, rule_id: str, yaml_data: Dict[str, Any], created_by: str = "system") -> "RuleVersion":
        """Создать версию из YAML-словаря."""
        return cls(
            version_id=0,
            rule_id=rule_id,
            name=yaml_data.get("name", rule_id),
            conditions=yaml_data.get("conditions", []),
            actions=yaml_data.get("actions", []),
            priority=RulePriority[yaml_data.get("priority", "MEDIUM").upper()],
            conflicts_with=yaml_data.get("conflicts_with", []),
            supports=yaml_data.get("supports", []),
            created_at=datetime.utcnow(),
            created_by=created_by,
            is_active=False,
            comment=yaml_data.get("comment")
        )