import logging
from typing import List, Dict, Any, Set
from domain.entities.report import AnalysisReport
from domain.entities.finding import ClinicalFinding
from domain.entities.recommendation import Recommendation
from domain.value_objects.severity import Severity
from infrastructure.adapters.loaders.clinical_logic_loader import ClinicalLogicLoader

logger = logging.getLogger(__name__)

class PostProcessor:
    def __init__(self, logic_loader: ClinicalLogicLoader = None, probability_threshold: float = 0.3):
        self.threshold = probability_threshold
        self.logic_loader = logic_loader or ClinicalLogicLoader()
        self.config = self.logic_loader.get_config()
        self.groups = self.config.get("groups", {})
        self.priority = self.config.get("priority", {})
        self.exclusions = self.config.get("exclusions", [])
        self.combinations = self.config.get("combinations", [])

        # Загружаем маппинги из конфига
        self.diagnosis_labels = self.logic_loader.get_diagnosis_labels()
        self.system_groups = self.logic_loader.get_system_groups()
        self.allowed_primary = self.logic_loader.get_allowed_primary()

        if "probability_threshold" in self.config:
            self.threshold = self.config["probability_threshold"].get("default", self.threshold)

        logger.info(f"PostProcessor initialized with threshold {self.threshold}")
        logger.info(f"Loaded {len(self.diagnosis_labels)} labels, {len(self.system_groups)} system groups, {len(self.allowed_primary)} primary diagnoses")

    def process(self, report: AnalysisReport) -> Dict[str, Any]:
        # 1. Отфильтровываем по порогу
        significant = [f for f in report.findings if f.probability >= self.threshold]
        logger.info(f"Significant findings (raw): {len(significant)}")
        for f in significant:
            logger.info(f"  Finding: {f.id} prob={f.probability} risk={f.risk}")

        # 2. Применяем исключения из clinical_logic.yaml
        significant = self._apply_exclusions(significant)
        logger.info(f"After exclusions: {len(significant)}")

        # 3. Жёсткий фильтр по белому списку – ВРЕМЕННО ОТКЛЮЧЕН
        # Пропускаем все находки без фильтрации
        filtered = significant
        logger.info(f"After white-list filter (disabled): {len(filtered)}")

        # Старый код фильтрации (закомментирован)
        # filtered = []
        # if any(f.id == "diabetes_mellitus_type_2" for f in significant):
        #     allowed = {"diabetes_mellitus_type_2", "severe_hyperglycemia"}
        #     filtered = [f for f in significant if f.id in allowed]
        # elif any(f.id == "iron_deficiency" for f in significant):
        #     allowed = {"iron_deficiency"}
        #     filtered = [f for f in significant if f.id in allowed]
        # else:
        #     filtered = [f for f in significant if f.id in self.allowed_primary]
        # logger.info(f"After white-list filter: {len(filtered)}")

        significant = filtered

        # 4. Группировка по системам (используем загруженный словарь)
        grouped = self._build_grouped(significant)

        # 5. Комбинированные диагнозы
        combined_diagnoses, combined_recommendations = self._apply_combinations(significant)

        # 6. Формируем diagnoses (без probability)
        diagnoses = []
        for f in significant:
            label = self.diagnosis_labels.get(f.id, f.id)
            diagnoses.append({
                "id": f.id,
                "label": label,
                "risk": f.risk.label if hasattr(f.risk, 'label') else str(f.risk),
                "combined": False,
                "description": f.description
            })
        diagnoses.extend(combined_diagnoses)

        # 7. Действия (рекомендации)
        base_actions = report.actions
        combined_actions = self._create_actions_from_combinations(combined_recommendations)
        all_actions = base_actions + combined_actions

        recommendations_by_specialty = {}
        for action in all_actions:
            spec = action.doctor_specialty
            if spec not in recommendations_by_specialty:
                recommendations_by_specialty[spec] = []
            recommendations_by_specialty[spec].append({
                "urgency": action.urgency.value,
                "tests": action.additional_tests
            })

        # 8. Общий уровень риска
        max_risk = max((f.risk for f in significant), key=lambda r: r.value if hasattr(r, 'value') else 0, default=None)
        overall_risk_level = max_risk.label if max_risk and hasattr(max_risk, 'label') else "Норма"

        # 9. Заключение
        conclusion = self._build_conclusion(diagnoses, grouped, recommendations_by_specialty, max_risk)

        return {
            "diagnoses": diagnoses,
            "grouped_findings": grouped,
            "recommendations_by_specialty": recommendations_by_specialty,
            "overall_risk_level": overall_risk_level,
            "conclusion": conclusion,
            "full_report": report
        }

    def _apply_exclusions(self, findings: List[ClinicalFinding]) -> List[ClinicalFinding]:
        ids = {f.id for f in findings}
        to_remove = set()
        for rule in self.exclusions:
            if_condition = rule.get("if")
            if if_condition in ids:
                for excluded in rule.get("then", []):
                    to_remove.add(excluded)
        return [f for f in findings if f.id not in to_remove]

    def _build_grouped(self, findings: List[ClinicalFinding]) -> Dict[str, List[Dict]]:
        grouped = {}
        for system, ids in self.system_groups.items():
            found = [f for f in findings if f.id in ids]
            if found:
                grouped[system] = [
                    {
                        "id": f.id,
                        "title": f.title,
                        "probability": f.probability,
                        "risk": f.risk.label if hasattr(f.risk, 'label') else str(f.risk),
                        "description": f.description,
                        "doctor_specialty": f.doctor_specialty,
                        "tests": f.tests,
                        "evidence": f.evidence
                    }
                    for f in found
                ]
        return grouped

    def _apply_combinations(self, findings: List[ClinicalFinding]) -> tuple:
        findings_dict = {f.id: f for f in findings}
        combined_diagnoses = []
        combined_recommendations = []

        for combo in self.combinations:
            conditions = combo.get("conditions", [])
            if not all(cond in findings_dict for cond in conditions):
                continue

            probs = [findings_dict[cond].probability for cond in conditions]
            avg_prob = sum(probs) / len(probs)
            factor = combo.get("probability_factor", 1.0)
            combo_prob = min(avg_prob * factor, 1.0)

            if combo_prob < self.threshold:
                continue

            combined_diagnoses.append({
                "id": combo["id"],
                "label": combo["label"],
                "risk": "Высокий",
                "combined": True,
                "conditions": conditions,
                "description": combo.get("recommendation") or combo.get("description") or "Комбинированное состояние"
            })

            try:
                urgency_str = combo.get("urgency", "moderate").upper()
                urgency = Severity[urgency_str] if urgency_str in Severity.__members__ else Severity.MODERATE
                rec = Recommendation(
                    doctor_specialty=combo.get("doctor_specialty", "General Practitioner"),
                    urgency=urgency,
                    additional_tests=combo.get("additional_tests", [])
                )
                combined_recommendations.append(rec)
            except Exception as e:
                logger.error(f"Failed to create recommendation for combination {combo['id']}: {e}")

        return combined_diagnoses, combined_recommendations

    def _create_actions_from_combinations(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        return recommendations

    def _build_conclusion(self, diagnoses, grouped, recommendations_by_specialty, max_risk) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("КЛИНИЧЕСКОЕ ЗАКЛЮЧЕНИЕ")
        lines.append("=" * 60)

        if not diagnoses:
            lines.append("Значимых отклонений не обнаружено.")
            return "\n".join(lines)

        lines.append("\n▶ Выявленные состояния:")
        for d in diagnoses:
            label = d.get('label', d['id'])
            risk_label = d['risk']
            desc = d.get('description')
            if desc:
                lines.append(f"  - {label}: {desc}")
            else:
                lines.append(f"  - {label} (риск {risk_label})")
            if d.get("combined", False):
                lines.append("    (комбинированное заключение)")

        lines.append("\n▶ По системам органов:")
        for system, findings in grouped.items():
            lines.append(f"  {system}:")
            for f in findings:
                desc = f.get('description') or f.get('title', f['id'])
                lines.append(f"    - {desc} (риск {f['risk']})")

        lines.append("\n▶ Рекомендации по дополнительному обследованию:")
        if recommendations_by_specialty:
            for spec, recs in recommendations_by_specialty.items():
                lines.append(f"  {spec}:")
                for r in recs:
                    lines.append(f"    - Срочность: {r['urgency']}, тесты: {', '.join(r['tests'])}")
        else:
            lines.append("  Нет дополнительных рекомендаций.")

        if max_risk:
            risk_label = max_risk.label if hasattr(max_risk, 'label') else str(max_risk)
            lines.append(f"\n▶ Общий уровень риска: {risk_label}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)