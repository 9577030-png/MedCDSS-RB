from dataclasses import dataclass, field
from typing import List, Optional
from domain.value_objects.gender import Gender
from domain.exceptions import InvalidPatientDataError


@dataclass(frozen=True)
class PatientProfile:
    id: str
    gender: Gender
    age: int
    complaints: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Валидация данных пациента."""
        if not self.id or not self.id.strip():
            raise InvalidPatientDataError("Patient ID cannot be empty")
        if self.age < 0:
            raise InvalidPatientDataError(f"Invalid age: {self.age}. Age must be >= 0")
        if self.age > 150:
            raise InvalidPatientDataError(f"Invalid age: {self.age}. Age must be <= 150")
        # complaints и medications могут быть пустыми, это нормально
        if not isinstance(self.gender, Gender):
            raise InvalidPatientDataError(f"Invalid gender: {self.gender}")