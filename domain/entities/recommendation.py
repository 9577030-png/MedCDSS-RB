from dataclasses import dataclass, field
from typing import List
from domain.value_objects.severity import Severity

@dataclass(frozen=True)
class Recommendation:
    doctor_specialty: str
    urgency: Severity
    additional_tests: List[str] = field(default_factory=list)