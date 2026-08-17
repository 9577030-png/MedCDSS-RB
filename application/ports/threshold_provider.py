from abc import ABC, abstractmethod
from typing import Dict, Optional
from domain.entities.threshold import Threshold
from domain.value_objects.gender import Gender

class ThresholdProvider(ABC):
    @abstractmethod
    def get_global_thresholds(self) -> Dict[str, Threshold]:
        """Возвращает словарь порогов (без учёта пола) — устаревает, используйте get_threshold."""
        pass

    @abstractmethod
    def get_threshold(self, parameter: str, gender: Gender) -> Optional[Threshold]:
        """Возвращает порог для параметра с учётом пола пациента."""
        pass