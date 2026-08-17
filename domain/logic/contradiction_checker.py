from typing import List
from domain.entities.finding import ClinicalFinding

def filter_contradictions(findings: List[ClinicalFinding]) -> List[ClinicalFinding]:
    """
    Удаляет находки, которые помечены как исключённые (поле excluded_by не пусто).
    """
    return [f for f in findings if not f.excluded_by]