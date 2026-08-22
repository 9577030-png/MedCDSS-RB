import logging
from typing import List, Dict, Set
from domain.rule_version import RuleVersion, RulePriority
from domain.entities.finding import ClinicalFinding

logger = logging.getLogger(__name__)

class ConflictResolver:
    def resolve(self, findings: List[ClinicalFinding], rules: Dict[str, RuleVersion]) -> List[ClinicalFinding]:
        if not findings:
            return []

        # finding.id - это id КОНКРЕТНОГО condition внутри правила (например
        # "diabetes_glucose" или "ckd_stage5_egfr"), а не id самого правила
        # ("diabetes", "ckd_stage5"). При этом conflicts_with/priority описаны
        # в YAML на уровне ПРАВИЛА. Восстанавливаем связь finding.id -> rule_id
        # через реальный список conditions каждого правила (а не угадыванием
        # по префиксу строки, как пришлось делать в PostProcessor - тут у нас
        # есть доступ к самим правилам, поэтому можно точно).
        finding_id_to_rule_id: Dict[str, str] = {}
        for rule_id, rule in rules.items():
            finding_id_to_rule_id[rule_id] = rule_id  # правило само может быть id находки (один параметр)
            for cond in rule.conditions:
                cond_id = cond.get('id', rule_id)
                finding_id_to_rule_id[cond_id] = rule_id

        def rule_of(finding_id: str) -> str:
            return finding_id_to_rule_id.get(finding_id, finding_id)

        conflict_graph: Dict[str, Set[str]] = {}
        for rule_id, rule in rules.items():
            conflict_graph[rule_id] = set(rule.conflicts_with)

        finding_priorities = {}
        for f in findings:
            rule = rules.get(rule_of(f.id))
            finding_priorities[f.id] = rule.priority if rule else RulePriority.MEDIUM

        sorted_findings = sorted(findings, key=lambda f: finding_priorities.get(f.id, RulePriority.MEDIUM), reverse=True)

        kept_ids = set()
        for f in sorted_findings:
            f_rule = rule_of(f.id)
            conflict = False
            for kept_id in kept_ids:
                kept_rule = rule_of(kept_id)
                if f_rule in conflict_graph.get(kept_rule, set()) or kept_rule in conflict_graph.get(f_rule, set()):
                    conflict = True
                    break
            if not conflict:
                kept_ids.add(f.id)

        # dict вместо списка на выходе - защита от дублей по id, даже если
        # апстрим когда-нибудь снова случайно породит два finding'а с одним id
        result = list({f.id: f for f in findings if f.id in kept_ids}.values())
        logger.info(f"ConflictResolver: {len(findings)} findings -> {len(result)} after conflict resolution")
        return result