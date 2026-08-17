from abc import ABC, abstractmethod
from typing import List
from domain.entities.parameter import Parameter

class ParserInterface(ABC):
    @abstractmethod
    def parse(self, raw_text: str) -> List[Parameter]:
        pass