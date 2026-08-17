from typing import List
from domain.entities.finding import ClinicalFinding

def build_explanation(findings: List[ClinicalFinding]) -> str:
    """Генерирует простой текст объяснения."""
    if not findings:
        return "No significant findings."
    parts = [f"- {f.title} (probability {f.probability:.0%}, risk {f.risk.label})" for f in findings]
    return "Findings:\n" + "\n".join(parts)