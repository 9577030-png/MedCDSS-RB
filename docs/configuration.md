```markdown
# Конфигурация системы

Все конфигурационные файлы находятся в папке `knowledge/`. Редактировать их можно как вручную, так и через веб-интерфейс администратора (раздел «Правила»).

---

## 1. Лабораторные пороги (`clinical_thresholds.yaml`)

**Путь:** `knowledge/configs/clinical_thresholds.yaml`

Определяет нормальные и критические значения для каждого параметра. Поддерживает разделение по полу (ключи `male`/`female`).

**Пример:**

```yaml
thresholds:
  hemoglobin:
    male:
      low: 130
      high: 170
    female:
      low: 120
      high: 150
    unit: "g/L"
    risk_level: HIGH
  glucose:
    low: 3.9
    high: 5.6
    unit: "mmol/L"
    risk_level: HIGH
Поля:

low – нижняя граница нормы (null, если нет)

high – верхняя граница нормы (null, если нет)

unit – единица измерения (должна совпадать с units.yaml)

risk_level – уровень риска (HIGH, MEDIUM, LOW, CRITICAL)

2. Клинические правила (guidelines/)
Путь: knowledge/guidelines/**/*.yaml

Каждое правило описывает диагностический критерий.

Пример (iron_deficiency.yaml):

yaml
id: iron_deficiency
description: "Снижение ферритина, железа и/или повышение MCV указывает на железодефицитную анемию."
scoring:
  hemoglobin: 3
  mcv: 2
  ferritin: 5
override_thresholds:
  ferritin:
    low: 30
    risk_level: HIGH
Поля:

id – уникальный идентификатор

description – текстовое описание для заключения

scoring – веса для каждого параметра (сумма определяет вероятность)

override_thresholds – переопределение глобальных порогов для этого правила

Альтернативный формат (условия):

yaml
id: diabetes_mellitus_type_2
conditions:
  - parameter: glucose
    min: 7.0
    label: "Сахарный диабет 2 типа"
    scoring: 5
    risk: HIGH
    description: "Уровень глюкозы ≥ 7.0 ммоль/л – диабет."
3. Логика постобработки (clinical_logic.yaml)
Путь: knowledge/configs/clinical_logic.yaml

Настройка группировки, исключений, приоритетов, комбинированных диагнозов и маппингов.

Группы и приоритеты
yaml
groups:
  kidney_disease:
    - ckd_stage3
    - ckd_stage4
    - ckd_stage5
    - acute_kidney_injury
    - chronic_kidney_disease

priority:
  kidney_disease:
    - ckd_stage5
    - ckd_stage4
    - ckd_stage3
Исключения
yaml
exclusions:
  - if: ckd_stage5
    then:
      - ckd_stage4
      - ckd_stage3
      - chronic_kidney_disease
Комбинированные диагнозы
yaml
combinations:
  - id: primary_hyperparathyroidism
    label: "Первичный гиперпаратиреоз (предположительно)"
    conditions:
      - hypercalcemia
      - vitamin_d_deficiency
    probability_factor: 0.8
    urgency: high
    doctor_specialty: Endocrinologist
    additional_tests:
      - PTH
      - Calcium 24h urine
      - Parathyroid ultrasound
Маппинги (новые секции)
yaml
# Метки диагнозов для отображения
diagnosis_labels:
  diabetes_mellitus_type_2: "Сахарный диабет 2 типа"
  iron_deficiency: "Железодефицитная анемия"

# Группировка по системам органов
system_groups:
  Эндокринная система:
    - diabetes_mellitus_type_2
    - hypothyroidism
  Гематология:
    - iron_deficiency
    - b12_deficiency

# Белый список основных диагнозов
allowed_primary:
  - diabetes_mellitus_type_2
  - iron_deficiency
  - hypothyroidism
4. Клинические инсайты (clinical_interpretations.yaml)
Путь: knowledge/configs/clinical_interpretations.yaml

Содержит подробные интерпретации для каждого диагноза (шпаргалка для врача).

Пример:

yaml
interpretations:
  diabetes_mellitus_type_2:
    id: diabetes_mellitus_type_2
    label: "Сахарный диабет 2 типа"
    category: "Эндокринология"
    description: "Хроническое метаболическое заболевание..."
    criteria:
      - parameter: glucose
        threshold: 7.0
        unit: "ммоль/л"
        condition: ">="
        comment_template: |
          Критерий выполнен. Уровень {value} ммоль/л превышает порог (≥ 7.0).
    differentials:
      - condition: "age < 45 AND c_peptide < 0.8"
        text: "Заподозрить LADA..."
    red_flags:
      - condition: "hba1c > 9.0"
        text: "**Высокий риск декомпенсации.**"
    treatment_hints:
      - step: "Метформин 500 мг × 2 раза в день"
        note: "Титровать до 2000 мг/сут."
    references:
      - "ADA Standards of Medical Care in Diabetes 2025"
5. Алиасы параметров (aliases.yaml)
Путь: knowledge/laboratory/aliases.yaml

Сопоставляет синонимы с каноническими именами.

yaml
aliases:
  hemoglobin:
    - Hb
    - HGB
    - Гемоглобин
  glucose:
    - Glu
    - Сахар
6. Единицы измерения (units.yaml)
Путь: knowledge/laboratory/units.yaml

Определяет коэффициенты конвертации в базовую единицу.

yaml
units:
  "g/L":
    base: "g/L"
    factor: 1.0
  "mg/dL":
    base: "mmol/L"
    factor: 0.0555
7. Рекомендации врачей (doctor_recommendations.yaml)
Путь: knowledge/configs/doctor_recommendations.yaml

Связывает диагноз с рекомендациями.

yaml
recommendations:
  iron_deficiency:
    doctor_specialty: Hematologist
    urgency: moderate
    additional_tests:
      - Iron
      - TIBC
Изменение конфигурации
Ручное редактирование
После изменения любого YAML-файла нажмите кнопку «Перезагрузить конфигурацию» в админ-интерфейсе или выполните POST /reload_config (только admin). Контейнер перезапускать не нужно.

Через интерфейс администратора
Перейдите в раздел «Администрирование» → «Правила», выберите файл, отредактируйте и сохраните – система автоматически перезагрузит правила.

Через API
bash
curl -X POST http://localhost:8000/reload_config \
  -H "Authorization: Bearer <admin_token>"