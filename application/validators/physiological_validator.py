import yaml
from typing import List, Dict, Any

class PhysiologicalValidator:
    def __init__(self, config_path: str):
        # Открываем с явной кодировкой UTF-8
        with open(config_path, 'r', encoding='utf-8') as f:
            self.ranges = yaml.safe_load(f).get('physiological_ranges', {})

    def validate(self, parameters: List[Dict[str, Any]]) -> List[str]:
        errors = []
        for param in parameters:
            name = param.get('name')
            value = param.get('value')
            if name in self.ranges:
                lo, hi = self.ranges[name]
                if not (lo <= value <= hi):
                    errors.append(f"Parameter {name} value {value} outside physiological range [{lo}, {hi}]")
        return errors