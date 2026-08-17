from abc import ABC, abstractmethod
from typing import List
from domain.entities.guideline import SpecialtyGuideline

class GuidelineProvider(ABC):
    @abstractmethod
    def get_all(self) -> List[SpecialtyGuideline]:
        pass