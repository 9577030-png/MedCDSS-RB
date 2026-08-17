import logging
from typing import List, Dict, Any
from domain.entities.patient import PatientProfile
from domain.entities.parameter import Parameter
from domain.entities.finding import ClinicalFinding
from domain.entities.guideline import SpecialtyGuideline
from domain.value_objects.risk_level import RiskLevel
from domain.logic.contradiction_checker import filter_contradictions
from application.ports.guideline_provider import GuidelineProvider
from application.ports.threshold_provider import ThresholdProvider

logger = logging.getLogger(__name__)

class InferenceEngine:
    def __init__(self, guideline_provider: GuidelineProvider, threshold_provider: ThresholdProvider):
        self.guideline_provider = guideline_provider
        self.threshold_provider = threshold_provider
        logger.info("InferenceEngine initialized")

    def _is_out_of_range(self, value: float, param_name: str, patient_gender, guideline_override_thresholds: dict) -> bool:
        if param_name in guideline_override_thresholds:
            overrides = guideline_override_thresholds[param_name]
            if 'high' in overrides and value > overrides['high']:
                return True
            if 'low' in overrides and value < overrides['low']:
                return True
            return False
        threshold = self.threshold_provider.get_threshold(param_name, patient_gender)
        if threshold is None:
            return False
        if threshold.low is not None and value < threshold.low:
            return True
        if threshold.high is not None and value > threshold.high:
            return True
        return False

    def _evaluate_condition(self, condition: Dict[str, Any], param_dict: Dict[str, float], patient_gender) -> bool:
        if 'parameter' not in condition:
            return False
        
        # Проверка пола (если указано в условии)
        if 'gender' in condition:
            required_gender = condition['gender'].lower()
            # patient_gender может быть объектом Gender или строкой
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
        guidelines = self.guideline_provider.get_all()
        findings = []

        for guideline in guidelines:
            # Новые правила с conditions
            if guideline.conditions:
                for cond in guideline.conditions:
                    if self._evaluate_condition(cond, param_dict, patient.gender):
                        cond_id = cond.get('id', f"{guideline.id}_{len(findings)}")
                        label = cond.get('label', cond_id)
                        scoring = cond.get('scoring', 5)
                        probability = min(scoring / 10.0, 1.0)
                        risk = RiskLevel.HIGH if probability > 0.5 else RiskLevel.NORMAL
                        if 'risk' in cond:
                            risk_map = {
                                'HIGH': RiskLevel.HIGH,
                                'MEDIUM': RiskLevel.MEDIUM,
                                'NORMAL': RiskLevel.NORMAL,
                                'CRITICAL': RiskLevel.CRITICAL
                            }
                            risk = risk_map.get(cond['risk'].upper(), risk)
                        recommendations = cond.get('recommendations', guideline.recommendations)
                        finding = ClinicalFinding(
                            id=cond_id,
                            title=label,
                            probability=probability,
                            risk=risk,
                            evidence=recommendations,
                            description=cond.get('description', guideline.description)
                        )
                        findings.append(finding)
                        logger.info(f"Condition triggered: {cond_id} (value={param_dict.get(cond['parameter'].lower())}, score={scoring})")
                continue

            # Старая логика (scoring / thresholds)
            total_score = 0.0
            all_present = True
            all_out_of_range = True

            for param_name in guideline.scoring_rules.keys():
                param_lower = param_name.lower()
                if param_lower not in param_dict:
                    all_present = False
                    break

            condition_type = getattr(guideline, 'condition', 'any')

            for param_name, weight in guideline.scoring_rules.items():
                param_lower = param_name.lower()
                if param_lower not in param_dict:
                    continue
                value = param_dict[param_lower]
                if self._is_out_of_range(value, param_lower, patient.gender, guideline.override_thresholds):
                    total_score += weight
                else:
                    all_out_of_range = False

            if condition_type == 'any':
                condition_met = (total_score > 0)
            else:
                condition_met = all_present and (total_score > 0) and all_out_of_range

            if condition_met:
                probability = min(total_score / 10.0, 1.0) if condition_type == 'any' else 1.0
                risk = RiskLevel.HIGH if probability > 0.5 else RiskLevel.NORMAL
                finding = ClinicalFinding(
                    id=guideline.id,
                    title=f"Guideline {guideline.id}",
                    probability=probability,
                    risk=risk,
                    evidence=guideline.recommendations,
                    description=guideline.description
                )
                findings.append(finding)
                logger.debug(f"Rule {guideline.id} triggered (condition={condition_type}, score={total_score})")

        filtered = filter_contradictions(findings)
        logger.info(f"Inference complete: {len(findings)} raw, {len(filtered)} after contradiction filter")
        return filtered