import pytest
from infrastructure.bootstrap.di_container import DIContainer
from domain.entities.patient import PatientProfile
from domain.entities.parameter import Parameter
from domain.value_objects.unit import Unit
from domain.value_objects.gender import Gender

@pytest.mark.integration
def test_gender_thresholds_creatinine_affects_probability():
    """
    Проверяет, что для мужчины и женщины при одинаковом значении креатинина
    вероятности почечных диагнозов различаются.
    """
    container = DIContainer()
    male = PatientProfile(id="M", gender=Gender.MALE, age=40)
    female = PatientProfile(id="F", gender=Gender.FEMALE, age=40)

    # Для мужчины креатинин 110 – в норме (62-115), для женщины – выше нормы (44-97)
    params = [
        Parameter("creatinine", 110, Unit("umol/L")),
        Parameter("egfr", 45, Unit("mL/min/1.73m2")),  # снижен для обеих стадий
        Parameter("urea", 6, Unit("mmol/L"))
    ]

    findings_male = container.inference_engine.infer(male, params)
    findings_female = container.inference_engine.infer(female, params)

    # Находим все почечные находки (ckd_stage3,4,5, acute_kidney_injury, chronic_kidney_disease)
    kidney_ids = {"ckd_stage3", "ckd_stage4", "ckd_stage5", "acute_kidney_injury", "chronic_kidney_disease"}

    male_kidney = [f for f in findings_male if f.id in kidney_ids and f.probability > 0]
    female_kidney = [f for f in findings_female if f.id in kidney_ids and f.probability > 0]

    # У женщины должно быть больше почечных находок или их вероятности выше
    male_prob_sum = sum(f.probability for f in male_kidney)
    female_prob_sum = sum(f.probability for f in female_kidney)

    assert female_prob_sum > male_prob_sum, "Female should have higher kidney disease probability due to elevated creatinine"

@pytest.mark.integration
def test_gender_thresholds_hemoglobin_no_finding_for_female():
    """
    Проверяет, что при гемоглобине 125 (ниже мужской нормы, но в женской норме)
    у мужчины появляется находка (например, анемия), а у женщины – нет.
    """
    container = DIContainer()
    male = PatientProfile(id="M", gender=Gender.MALE, age=40)
    female = PatientProfile(id="F", gender=Gender.FEMALE, age=40)

    params = [Parameter("hemoglobin", 125, Unit("g/L"))]

    findings_male = container.inference_engine.infer(male, params)
    findings_female = container.inference_engine.infer(female, params)

    # Проверяем, что у мужчины есть хоть какая-то находка с probability > 0
    male_has = any(f.probability > 0 for f in findings_male)
    female_has = any(f.probability > 0 for f in findings_female)

    assert male_has, "Male should have a finding due to low hemoglobin"
    assert not female_has, "Female should have no finding from hemoglobin 125 (within normal range)"