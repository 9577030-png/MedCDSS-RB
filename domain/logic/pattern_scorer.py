from typing import Dict

def score(parameters: Dict[str, float], rules: Dict[str, float]) -> float:
    """Суммирует веса для параметров, присутствующих в rules."""
    total = 0.0
    for param, weight in rules.items():
        if param in parameters:
            total += weight
    return total