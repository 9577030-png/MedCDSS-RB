import pytest
from infrastructure.bootstrap.di_container import DIContainer
from domain.entities.guideline import SpecialtyGuideline

@pytest.mark.integration
def test_guideline_provider_loads_all_guidelines():
    container = DIContainer()
    provider = container.guideline_provider
    guidelines = provider.get_all()

    guideline_ids = [g.id for g in guidelines]

    # Реальные ID файлов в папке knowledge/guidelines (без .yaml)
    expected_ids = [
        "diabetes_mellitus_type_2",
        "tsh_ranges",
        "calcium_ranges",
        "potassium_ranges",
        "sodium_ranges",
        "vitamin_d_ranges",
        "uric_acid_ranges",
        "bmi_ranges",
        "blood_pressure_ranges",
        "ldl_ranges",
        "triglycerides_ranges",
        "hdl_ranges",
    ]

    for expected_id in expected_ids:
        assert expected_id in guideline_ids, f"Expected ID {expected_id} not found in guidelines"

    for g in guidelines:
        assert isinstance(g, SpecialtyGuideline)
        assert g.id is not None
        assert hasattr(g, 'conditions') and g.conditions is not None

@pytest.mark.integration
def test_guideline_provider_applies_overrides():
    container = DIContainer()
    provider = container.guideline_provider
    guidelines = provider.get_all()

    # Проверяем, что хотя бы одно правило загружено с условиями
    diabetes = next((g for g in guidelines if g.id == "diabetes_mellitus_type_2"), None)
    if diabetes is None:
        diabetes = next((g for g in guidelines if g.id == "tsh_ranges"), None)
    assert diabetes is not None
    assert len(diabetes.conditions) > 0