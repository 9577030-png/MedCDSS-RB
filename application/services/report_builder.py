import logging
from typing import List
from domain.entities.finding import ClinicalFinding
from domain.entities.recommendation import Recommendation
from domain.entities.report import AnalysisReport
from domain.logic.explanation_builder import build_explanation

logger = logging.getLogger(__name__)

class ReportBuilder:
    def __init__(self):
        logger.info("ReportBuilder initialized")

    def build(self, findings: List[ClinicalFinding], actions: List[Recommendation]) -> AnalysisReport:
        logger.info(f"Building report with {len(findings)} findings and {len(actions)} actions")
        explanation = build_explanation(findings)
        logger.debug(f"Explanation: {explanation[:100]}...")  # первые 100 символов
        report = AnalysisReport(findings=findings, actions=actions, explanation=explanation)
        logger.info("Report built successfully")
        return report