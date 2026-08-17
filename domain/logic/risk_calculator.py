from domain.entities.threshold import Threshold
from domain.value_objects.risk_level import RiskLevel
from domain.value_objects.gender import Gender

def calculate_risk(value: float, threshold: Threshold, gender: Gender = Gender.MALE) -> RiskLevel:
    """
    Вычисляет уровень риска на основе значения и порога.
    Если порог не содержит половой дифференциации, используется переданный threshold.
    """
    if threshold.low is not None and value < threshold.low:
        return threshold.risk_level
    if threshold.high is not None and value > threshold.high:
        return threshold.risk_level
    return RiskLevel.NORMAL