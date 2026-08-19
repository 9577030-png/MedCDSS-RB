import logging
from typing import List, Dict, Set
from domain.rule_version import RuleVersion, RulePriority
from domain.entities.finding import ClinicalFinding

logger = logging.getLogger(__name__)

class ConflictResolver:
    def resolve(self, findings: List[ClinicalFinding], rules: Dict[str, RuleVersion]) -> List[ClinicalFinding]:
        if not findings:
            return []

        conflict_graph: Dict[str, Set[str]] = {}
        for rule_id, rule in rules.items():
            conflict_graph[rule_id] = set(rule.conflicts_with)

        finding_priorities = {}
        for f in findings:
            rule = rules.get(f.id)
            if rule:
                finding_priorities[f.id] = rule.priority
            else:
                finding_priorities[f.id] = RulePriority.MEDIUM

        sorted_findings = sorted(findings, key=lambda f: finding_priorities.get(f.id, RulePriority.MEDIUM), reverse=True)

        kept_ids = set()
        for f in sorted_findings:
            conflict = False
            for kept_id in kept_ids:
                if f.id in conflict_graph.get(kept_id, set()) or kept_id in conflict_graph.get(f.id, set()):
                    conflict = True
                    break
            if not conflict:
                kept_ids.add(f.id)

        result = [f for f in findings if f.id in kept_ids]
        logger.info(f"ConflictResolver: {len(findings)} findings -> {len(result)} after conflict resolution")
        return result