from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.recommendation import Recommendation

class RecommendationProvider(ABC):
    @abstractmethod
    def get_recommendation(self, finding_id: str) -> Optional[Recommendation]:
        pass