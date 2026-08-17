import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from domain.entities.parameter import Parameter
from domain.entities.patient import PatientProfile
from domain.clinical_insights import (
    ClinicalInsights,
    CriterionEvaluation,
    DifferentialSuggestion,
    RedFlag,
    TreatmentHint,
)
from infrastructure.adapters.loaders.medical_reference_loader import MedicalReferenceLoader

class ClinicalInterpreter:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._load_config()
        self.reference_loader = MedicalReferenceLoader()

    def _load_config(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.interpretations = self.config.get('interpretations', {})

    def interpret(self, diagnoses: List[Dict[str, Any]], parameters: List[Parameter], patient: PatientProfile) -> Dict[str, ClinicalInsights]:
        print("\n" + "="*60)
        print("🟢 ВЫЗВАН НОВЫЙ ИНТЕРПРЕТАТОР (ClinicalInterpreter)")
        print(f"Получено диагнозов: {len(diagnoses)}")
        print(f"Получено параметров: {len(parameters)}")
        print("="*60 + "\n")

        param_dict = {p.name: p.value for p in parameters}
        patient_info = {
            'gender': patient.gender.value if hasattr(patient.gender, 'value') else str(patient.gender),
            'age': patient.age,
        }

        result = {}
        for diag in diagnoses:
            diag_id = diag.get('id')
            if not diag_id or diag_id not in self.interpretations:
                print(f"⚠️ Диагноз {diag_id} не найден в интерпретациях")
                continue
            diag_config = self.interpretations[diag_id]
            insights = self._build_insights(diag_config, diag, param_dict, patient_info)
            result[diag_id] = insights
            print(f"✅ Сгенерированы инсайты для {diag_id}")

        print(f"📦 Итого инсайтов: {len(result)}")
        return result

    def _build_insights(self, diag_config: Dict[str, Any], diag: Dict[str, Any], param_dict: Dict[str, float], patient_info: Dict[str, Any]) -> ClinicalInsights:
        insights = ClinicalInsights(
            diagnosis_id=diag.get('id', ''),
            label=diag_config.get('label', diag.get('label', '')),
            category=diag_config.get('category', ''),
            description=diag_config.get('description', diag.get('description')),
            references=diag_config.get('references'),
        )

        for crit in diag_config.get('criteria', []):
            param_name = crit.get('parameter')
            if not param_name:
                continue
            value = param_dict.get(param_name)
            is_optional = crit.get('optional', False)
            if value is None and is_optional:
                continue
            comment = self._generate_comment(crit, value, patient_info)
            evaluation = CriterionEvaluation(
                parameter=param_name,
                value=value,
                unit=crit.get('unit', ''),
                threshold=crit.get('threshold') or crit.get('threshold_low'),
                condition=crit.get('condition'),
                comment=comment,
            )
            insights.criteria.append(evaluation)

        for diff in diag_config.get('differentials', []):
            condition = diff.get('condition', '')
            if self._check_condition(condition, param_dict, patient_info):
                insights.differentials.append(
                    DifferentialSuggestion(condition=condition, text=diff.get('text', ''))
                )

        for rf in diag_config.get('red_flags', []):
            condition = rf.get('condition', '')
            if self._check_condition(condition, param_dict, patient_info):
                insights.red_flags.append(
                    RedFlag(condition=condition, text=rf.get('text', ''))
                )

        for hint in diag_config.get('treatment_hints', []):
            insights.treatment_hints.append(
                TreatmentHint(step=hint.get('step', ''), note=hint.get('note', ''))
            )

        return insights

    def _generate_comment(self, crit_config: Dict[str, Any], value: Optional[float], patient_info: Dict[str, Any]) -> str:
        template = crit_config.get('comment_template', '')
        if not template:
            return ''

        param_name = crit_config.get('parameter')
        gender = patient_info.get('gender', 'male')
        age = patient_info.get('age', 30)
        ref_info = self.reference_loader.get_interpretation(param_name, value, gender, age) if param_name else {}

        context = {
            'value': value if value is not None else 'не указан',
            'gender': gender,
            'age': age,
            'unit': crit_config.get('unit', ref_info.get('unit', '')),
            'threshold': crit_config.get('threshold') or crit_config.get('threshold_low'),
            'severity': self._determine_severity(value, crit_config.get('severity_mapping', [])),
            'additional': '',
            'interpretation': ref_info.get('text', ''),
            'ref_min': ref_info.get('min'),
            'ref_max': ref_info.get('max'),
        }
        if context['ref_min'] is not None and context['ref_max'] is not None:
            context['additional'] += f" Референсный интервал: {context['ref_min']}–{context['ref_max']} {context['unit']}. "

        comment = template.format(**context)

        for rule in crit_config.get('additional_rules', []):
            condition = rule.get('condition', '')
            if self._check_condition(condition, {crit_config['parameter']: value}, patient_info):
                comment += ' ' + rule.get('text', '')

        return comment

    def _determine_severity(self, value: Optional[float], mapping: List[Dict]) -> str:
        if value is None:
            return 'не определено'
        for item in mapping:
            range_str = item.get('range', '')
            try:
                if '>=' in range_str:
                    threshold = float(range_str.split('>=')[1].strip())
                    if value >= threshold:
                        return item.get('label', '')
                elif '-' in range_str:
                    parts = range_str.split('-')
                    low = float(parts[0].strip())
                    high = float(parts[1].strip())
                    if low <= value <= high:
                        return item.get('label', '')
                elif '<' in range_str:
                    threshold = float(range_str.split('<')[1].strip())
                    if value < threshold:
                        return item.get('label', '')
            except:
                continue
        return 'не классифицировано'

    import ast
    import operator
    def _check_condition(self, condition: str, param_dict: Dict[str, float], patient_info: Dict[str, Any]) -> bool:
       if not condition:
           return True

    # Сбор доступных переменных (только числа, строки, булевы)
    allowed_vars = {}
    for k, v in {**param_dict, **patient_info}.items():
        if isinstance(v, (int, float, str, bool)):
            allowed_vars[k] = v

    # Разрешённые операторы
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: operator.and_,
        ast.Or: operator.or_,
        ast.Not: operator.not_,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _eval_node(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            if node.id in allowed_vars:
                return allowed_vars[node.id]
            raise ValueError(f"Unknown variable: {node.id}")
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            op_type = type(node.op)
            if op_type not in operators:
                raise ValueError(f"Unsupported operator: {op_type}")
            return operators[op_type](left, right)
        elif isinstance(node, ast.Compare):
            left = _eval_node(node.left)
            for op, comp in zip(node.ops, node.comparators):
                right = _eval_node(comp)
                op_type = type(op)
                if op_type not in operators:
                    raise ValueError(f"Unsupported comparison: {op_type}")
                if not operators[op_type](left, right):
                    return False
                left = right
            return True
        elif isinstance(node, ast.BoolOp):
            values = [_eval_node(v) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)
            else:
                raise ValueError("Unsupported boolean operator")
        elif isinstance(node, ast.UnaryOp):
            operand = _eval_node(node.operand)
            op_type = type(node.op)
            if op_type not in operators:
                raise ValueError(f"Unsupported unary operator: {op_type}")
            return operators[op_type](operand)
        elif isinstance(node, ast.Attribute):
            # Запрещаем доступ к атрибутам (безопасность)
            raise ValueError("Attribute access not allowed")
        else:
            raise ValueError(f"Unsupported AST node: {type(node).__name__}")

    try:
        parsed = ast.parse(condition, mode='eval')
        return bool(_eval_node(parsed.body))
    except Exception:
        return False