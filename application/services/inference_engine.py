import logging
from typing import List, Dict, Any
from domain.entities.patient import PatientProfile
from domain.entities.parameter import Parameter
from domain.entities.finding import ClinicalFinding
from domain.value_objects.risk_level import RiskLevel
from domain.interfaces import RuleRepository
from application.services.conflict_resolver import ConflictResolver

logger = logging.getLogger(__name__)

class InferenceEngine:
    def __init__(self, rule_repo: RuleRepository, threshold_provider, guideline_provider):
        self.rule_repo = rule_repo
        self.threshold_provider = threshold_provider
        self.guideline_provider = guideline_provider  # для обратной совместимости
        self.conflict_resolver = ConflictResolver()

    def _evaluate_condition(self, condition: Dict[str, Any], param_dict: Dict[str, float], patient_gender) -> bool:
        if 'parameter' not in condition:
            return False
        if 'gender' in condition:
            required_gender = condition['gender'].lower()
            if hasattr(patient_gender, 'value'):
                current_gender = patient_gender.value.lower()
            else:
                current_gender = str(patient_gender).lower()
            if required_gender != current_gender:
                return False

        param_name = condition['parameter'].lower()
        if param_name not in param_dict:
            return False
        value = param_dict[param_name]
        if 'min' in condition and 'max' in condition:
            return condition['min'] <= value <= condition['max']
        elif 'min' in condition:
            return value >= condition['min']
        elif 'max' in condition:
            return value <= condition['max']
        return False

    def infer(self, patient: PatientProfile, parameters: List[Parameter]) -> List[ClinicalFinding]:
        logger.info(f"Inference for patient {patient.id} (gender={patient.gender.value})")

        param_dict = {p.name.lower(): p.value for p in parameters}
        active_rules = self.rule_repo.get_active_versions()
        rules_dict = {r.rule_id: r for r in active_rules}

        findings = []

        for rule in active_rules:
            for cond in rule.conditions:
                if self._evaluate_condition(cond, param_dict, patient.gender):
                    prob = min(cond.get('scoring', 5) / 10.0, 1.0)
                    risk = RiskLevel.HIGH if prob > 0.5 else RiskLevel.NORMAL
                    if 'risk' in cond:
                        risk_map = {
                            'HIGH': RiskLevel.HIGH,
                            'MEDIUM': RiskLevel.MEDIUM,
                            'NORMAL': RiskLevel.NORMAL,
                            'CRITICAL': RiskLevel.CRITICAL
                        }
                        risk = risk_map.get(cond['risk'].upper(), risk)
                    finding = ClinicalFinding(
                        id=rule.rule_id,
                        title=cond.get('label', rule.name),
                        probability=prob,
                        risk=risk,
                        evidence=cond.get('recommendations', []),
                        description=cond.get('description', rule.comment or '')
                    )
                    findings.append(finding)
                    logger.debug(f"Rule {rule.rule_id} triggered by condition {cond}")

        findings = self.conflict_resolver.resolve(findings, rules_dict)
        logger.info(f"Inference complete: {len(findings)} findings after conflict resolution")
        return findings