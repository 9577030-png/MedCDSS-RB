import pytest
from infrastructure.adapters.loaders.yaml_threshold_loader import YamlThresholdLoader
from domain.entities.threshold import Threshold
from domain.value_objects.unit import Unit
from domain.value_objects.risk_level import RiskLevel


@pytest.mark.integration
def test_load_global_thresholds():
    loader = YamlThresholdLoader()
    thresholds = loader.get_global_thresholds()

    # Проверяем наличие ключей из вашего файла
    assert "Hb" in thresholds
    assert "MCV" in thresholds
    assert "Ferritin" in thresholds

    hb = thresholds["Hb"]
    assert isinstance(hb, Threshold)
    assert hb.parameter_name == "Hb"
    assert hb.low == 120
    assert hb.high == 160
    assert hb.unit == Unit("g/L")
    assert hb.risk_level == RiskLevel.HIGH

    mcv = thresholds["MCV"]
    assert mcv.low == 80
    assert mcv.high == 100
    assert mcv.unit == Unit("fL")

    ferritin = thresholds["Ferritin"]
    assert ferritin.low == 30
    assert ferritin.high == 300
    assert ferritin.unit == Unit("ug/L")


@pytest.mark.integration
def test_threshold_loader_returns_dict():
    loader = YamlThresholdLoader()
    thresholds = loader.get_global_thresholds()
    assert isinstance(thresholds, dict)
    for key, value in thresholds.items():
        assert isinstance(key, str)
        assert isinstance(value, Threshold)