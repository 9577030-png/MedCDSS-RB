import pytest
from infrastructure.bootstrap.di_container import DIContainer
from domain.entities.guideline import SpecialtyGuideline


@pytest.mark.integration
def test_guideline_provider_loads_all_guidelines():
    container = DIContainer()
    provider = container.guideline_provider
    guidelines = provider.get_all()

    guideline_ids = [g.id for g in guidelines]

    expected_ids = [
        "iron_deficiency",
        "b12_deficiency",
        "macrocytic_anemia",
        "hypothyroidism",
        "hyperthyroidism",
        "thyroid",
        "hyperkalemia",
        "hypokalemia",
        "hypernatremia",
        "hyponatremia",
        "diabetes_mellitus_type2",
        "prediabetes",
        "metabolic_syndrome",
        "hypercholesterolemia",
        "acute_hepatitis",
        "cholestasis",
        "nonalcoholic_fatty_liver",
        "acute_kidney_injury",
        "chronic_kidney_disease",
        "acute_pancreatitis",
        "inflammatory_bowel_disease",
        "celiac_disease",
        "gout",
        "osteoporosis",
        "folate_deficiency"
    ]

    for expected_id in expected_ids:
        assert expected_id in guideline_ids

    for g in guidelines:
        assert isinstance(g, SpecialtyGuideline)
        assert g.id is not None
        assert isinstance(g.scoring_rules, dict)
        assert isinstance(g.override_thresholds, dict)


@pytest.mark.integration
def test_guideline_provider_applies_overrides():
    container = DIContainer()
    provider = container.guideline_provider
    guidelines = provider.get_all()

    # Проверяем, что override_thresholds загружены для diabetes
    diabetes = next((g for g in guidelines if g.id == "diabetes_mellitus_type2"), None)
    assert diabetes is not None
    assert "glucose" in diabetes.override_thresholds
    assert diabetes.override_thresholds["glucose"]["high"] == 7.0

    # Проверяем hyperkalemia
    hyperkalemia = next((g for g in guidelines if g.id == "hyperkalemia"), None)
    assert hyperkalemia is not None
    assert "potassium" in hyperkalemia.override_thresholds
    assert hyperkalemia.override_thresholds["potassium"]["high"] == 5.5

    # Проверяем iron_deficiency
    iron = next((g for g in guidelines if g.id == "iron_deficiency"), None)
    assert iron is not None
    assert "ferritin" in iron.override_thresholds
    assert iron.override_thresholds["ferritin"]["low"] == 30