import os
import yaml
import logging
from typing import List
from config import settings
from domain.entities.guideline import SpecialtyGuideline
from application.ports.threshold_provider import ThresholdProvider

logger = logging.getLogger(__name__)

class MergedGuidelineProvider:
    def __init__(self, threshold_provider: ThresholdProvider):
        self.threshold_provider = threshold_provider
        self._guidelines = None

    def _load_guidelines(self) -> List[SpecialtyGuideline]:
        guidelines_dir = os.path.join(settings.BASE_DIR, settings.GUIDELINES_DIR)
        result = []
        for root, dirs, files in os.walk(guidelines_dir):
            for file in files:
                if file.endswith(".yaml"):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    if not data:
                        continue

                    # Если есть conditions, это новое правило с диапазонами
                    if 'conditions' in data:
                        conditions = data['conditions']
                        guideline = SpecialtyGuideline(
                            id=data.get('id', os.path.splitext(file)[0]),
                            scoring_rules={},
                            override_thresholds={},
                            description=data.get('description'),
                            condition='any',
                            recommendations=data.get('recommendations', []),
                            conditions=conditions
                        )
                        result.append(guideline)
                        continue

                    # Старая логика с thresholds или scoring
                    if 'thresholds' in data:
                        scoring_rules = {}
                        override_thresholds = {}
                        for param, condition in data['thresholds'].items():
                            scoring_rules[param] = 5
                            overrides = {}
                            if 'min' in condition:
                                overrides['high'] = condition['min']
                            if 'max' in condition:
                                overrides['low'] = condition['max']
                            if overrides:
                                override_thresholds[param] = overrides
                    else:
                        scoring_rules = data.get('scoring', {})
                        override_thresholds = data.get('override_thresholds', {})

                    condition_type = data.get('condition', 'any')
                    guideline = SpecialtyGuideline(
                        id=data.get('id', os.path.splitext(file)[0]),
                        scoring_rules=scoring_rules,
                        override_thresholds=override_thresholds,
                        description=data.get('description'),
                        condition=condition_type,
                        recommendations=data.get('recommendations', [])
                    )
                    result.append(guideline)
        return result

    def get_all(self) -> List[SpecialtyGuideline]:
        if self._guidelines is None:
            self._guidelines = self._load_guidelines()
        return self._guidelines

    def reload(self) -> None:
        logger.info("Reloading guidelines...")
        self._guidelines = None
        self._guidelines = self._load_guidelines()
        logger.info(f"Guidelines reloaded: {len(self._guidelines)}")