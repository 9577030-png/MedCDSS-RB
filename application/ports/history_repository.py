from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.report import AnalysisReport

class HistoryRepository(ABC):
    @abstractmethod
    def save(self, patient_id: str, report: AnalysisReport) -> None:
        pass

    @abstractmethod
    def load(self, patient_id: str) -> Optional[AnalysisReport]:
        pass