# DATA_REVIEW_NEEDED.md

## О документе

Этот файл отслеживает известные проблемы в содержимом базы знаний (клинические правила,
интерпретации, конфигурация), в отличие от `AUDIT.md`, который фиксирует архитектурные
находки в коде.

**Важно:** оригинальный файл `docs/DATA_REVIEW_NEEDED.md` пропал из репозитория целиком
(при том что на него ссылаются комментарии в `tests/integration/test_post_processor_combinations.py`
и раздел 6 `HANDOFF.md`). Этот файл — **реконструкция**, собранная из:
- сохранившегося раздела 6 `HANDOFF.md`;
- прямой проверки текущего состояния репозитория (pytest, flake8, systematic-скрипты по
  всей базе, а не выборочные проверки);
- находок новой сессии (2026-09-19).

Оригинальная нумерация разделов (включая «раздел 15», на который ссылались тесты)
восстановить не удалось — используется новая нумерация. Ссылки в тестах на «раздел 15»
теперь описывают пункт из раздела «Исправлено и подтверждено» ниже (septic_syndrome /
hepatorenal_syndrome combinations).

**Методология проверки:** каждая находка в этом файле проверена чтением реального кода/данных
и/или прогоном через реальный пайплайн (pytest с DIContainer, не изолированные моки), а не
по одному примеру — там, где класс ошибки предполагает системность, прогонялся скрипт по
всей базе (243 файла правил / 273 записи интерпретаций / 253 канонических параметра).

---

## Исправлено и подтверждено

Пункты ниже проверены в текущей копии репозитория (не только "предполагается исправленным").

- Пороговые баги в нескольких guideline-файлах (vitamin_b12_deficiency_moderate,
  vitamin_d_deficiency_moderate, thrombocytopenia_moderate, ckd_stage4, критерий нитритов
  в uti_children/acute_pyelonephritis).
- 57 сломанных подключений текста интерпретаций к правилам — устранены через механизм
  `combinations` (54 записи) в `clinical_logic.yaml`.
- `infrastructure/adapters/parsers/regex_parser.py` — переписан заново после регрессии.
- Регистр `AND`/`OR` → `and`/`or` в условиях `iron_deficiency.additional_rules` (2 выражения) —
  **важно:** это работает только вместе с фиксом ниже (баг с именем переменной `value`),
  иначе даже с правильным регистром условие не находило нужную переменную.
- 16 кириллических алиасов лабораторных параметров (СРБ, АЛТ, АСТ, ГГТ, ЛДГ, ТТГ, КФК-МВ,
  ЛПНП, ЛПВП, ОЖСС, ХГЧ, ПСА, ПТГ, ИФР-1, МНО, ЩФ) — подтверждено присутствуют в
  `knowledge/laboratory/aliases.yaml`.
- **[2026-09-19]** Критический баг `datetime.now(timezone.UTC)` в `domain/rule_version.py:61` —
  `timezone.UTC` не существует (правильно `timezone.utc`). Ломал загрузку **абсолютно всех**
  243 файлов правил через `hot_reload()` — вся база знаний не загружалась в проде и в
  большей части тестов, ошибка глушилась `try/except` без видимых последствий. Найден и
  исправлен в этой сессии; ранее нигде не задокументирован.
- **[2026-09-19]** `knowledge/guidelines/cardiology/atherogenic_index_high.yaml`:
  `parameter: hdl` → `hdl_cholesterol` (несоответствие каноническому имени параметра).
- **[2026-09-19]** `clinical_logic.yaml`: комбинации `septic_syndrome` и `hepatorenal_syndrome`
  ссылались на несуществующие id условий (id верхнего уровня файла вместо реального id
  условия в multi-condition файлах: `sepsis`/`systemic_inflammation`/`acute_hepatitis` вместо
  `sepsis_crp`/`systemic_inflammation_esr`/`acute_hepatitis_bilirubin_total`). Плюс exclusion
  `sepsis → systemic_inflammation` гасил `systemic_inflammation_esr` ещё до того, как до него
  доходила комбинация. Оба исправлены и подтверждены тестами
  (`test_combination_septic_syndrome`, `test_combination_hepatorenal_syndrome`).
- **[2026-09-19]** `application/services/interpreter.py::_generate_comment` — баг в передаче
  переменной в `_check_condition` для `additional_rules`: код передавал параметр под его
  собственным именем (`{crit_config['parameter']: value}`), а **все 12 из 12** существующих
  `additional_rules` в базе написаны в расчёте на имя переменной `value`. Проверено скриптом
  по всем additional_rules в файле — 100% используют `value`, 0% используют имя параметра,
  что указывает на баг в коде, а не в данных. Исправлено на `{'value': value}`.
- **[2026-09-19]** Несоответствие имён параметров каноническому списку `aliases.yaml`
  (проверено систематическим скриптом по всем `parameter:`-полям базы):
  - `vitamin_d` → `vitamin_d_25oh` (9 мест в `clinical_interpretations.yaml` + 8 guideline-файлов:
    primary/secondary_hyperparathyroidism, osteomalacia, osteoporosis, rickets_risk,
    vitamin_d_deficiency_children, vitamin_d_deficiency_moderate/severe).
  - `hdl` → `hdl_cholesterol` (всего 3 места, не 1 — `atherogenic_index_high.yaml` +
    2 записи в `clinical_interpretations.yaml`: `atherogenic_index_high_cholesterol_total`/
    `atherogenic_index_high_hdl`).
  - `calprotectin` → `fecal_calprotectin` (2 места в `clinical_interpretations.yaml` +
    **сам guideline-файл** `inflammatory_bowel_disease.yaml` — это означало, что диагноз
    ВБК не срабатывал бы вообще на реальных данных, не только текст интерпретации).
  - `erythrocytes` → `rbc`, `hb` → `hemoglobin`, `patient_age` → `age` (нет такого ключа
    в `patient_info`, только `age`), `systolic_bp`/`diastolic_bp` →
    `blood_pressure_systolic`/`blood_pressure_diastolic`.

---

## Открыто (требует решения/внимания)

Пронумеровано заново при реконструкции.

### Из HANDOFF.md (перенесено, статус не менялся в этой сессии)

1. `cushing_disease.yaml` vs `cushing_syndrome.yaml` — дубль, требует объединения/уточнения.
2. `pagets_disease.yaml` vs `paget_disease.yaml` — дубль (различаются только написанием).
3. `systemic_inflammatory_response.yaml` пересекается с `systemic_inflammation` — неясно,
   отдельная это единица или дубль.
4. `sepsis_high_risk_combined.yaml` — дублирует `sepsis.yaml`, нигде не подключён
   (orphan-файл).
5. Кардиология: массовое дублирование между файлами по `troponin_i`, `ck_mb`, `troponin_t`,
   `bnp`/`nt_probnp`.
6. `vasculitis.yaml` не включает критерии по ANCA.
7. 8 межфайловых дублей порогов (например `ckd_stage3` пересекается с `egfr_ranges` и т.п.) —
   список конкретных пар нужно восстанавливать заново, в HANDOFF.md сохранился только счётчик.
8. Педиатрия — пороги во многих файлах не стратифицированы по возрасту.
9. 3 ключа-сироты в интерпретациях (`iron_deficiency`, `metabolic_syndrome`,
   `nonalcoholic_fatty_liver`) — не связаны ни с одним правилом через `combinations` или
   прямое совпадение id.
10. `hyperkalemia`/`hyponatremia`/`hypokalemia`/`hypernatremia` дублируются между
    `knowledge/guidelines/nephrology/` и `knowledge/guidelines/ranges/`.

### Новое, найдено в этой сессии (2026-09-19)

11. **`system_groups` в `clinical_logic.yaml` использует "голые" id вместо реальных id
    условий.** Подтверждено минимум для группы с `sepsis`/`systemic_inflammation` — реальные
    находки (`sepsis_crp` и т.п.) никогда не попадут в группировку «по системам органов» в
    отчёте (`_build_grouped()` в `post_processor.py` делает точное сравнение `f.id in ids`,
    без префиксного совпадения). Диагнозы при этом всё равно появляются в общем списке —
    баг влияет только на группировку по системам, не на сам факт постановки диагноза.
    Нужен систематический скан **всех** групп в `system_groups`, не только этой пары —
    в этой сессии проверена не была.
12. **Два выражения в `differentials` ссылаются на id других правил как на булевы переменные,
    а не на реальные лабораторные параметры** — даже после исправления регистра AND/OR
    работать не будут, нужен содержательный пересмотр условия, не механическая правка:
    - `primary_hyperparathyroidism`: `creatinine_high_male OR creatinine_high_female`
      (ни `creatinine_high_male`, ни `creatinine_high_female` не параметры).
    - `hepatorenal_syndrome`: `acute_hepatitis == true AND acute_kidney_injury == true`
      (`acute_hepatitis`/`acute_kidney_injury` — id других диагнозов, не параметры).
    Не тронуто намеренно — решение об АND/OR-логике конкретных клинических критериев должен
    принимать человек, не ассистент в одностороннем порядке.
13. **`glucocorticoids_use` (differential в `diabetes_mellitus_type_2`) и `baseline`
    (red_flag в `acute_kidney_injury`, `creatinine > baseline * 3`)** — ссылаются на данные,
    которые текущая модель пациента не собирает вообще. `PatientProfile` содержит только
    `id, gender, age, complaints, medications`; `medications` — список строк, но нет логики,
    которая проверяла бы вхождение глюкокортикоидов в этот список и превращала бы это в
    булеву переменную для `_check_condition`. Базового (baseline) креатинина пациента система
    не хранит нигде. Оба условия сейчас гарантированно всегда `False` (не найдена переменная →
    исключение → `except: return False`). Требует архитектурного решения, не просто правки
    yaml.
14. **`glucose_fasting` (red_flag в `diabetes_mellitus_type_2`, `glucose_fasting > 15.0`)** —
    неясно, должен ли это быть просто `glucose` (если в системе "glucose" всегда означает
    "натощак" по умолчанию), или это отдельный, не собираемый сейчас показатель. Не
    переименовано — нужно уточнение.
15. **`reticulocytes` (differential в `iron_deficiency`, `hemoglobin < 100 and reticulocytes < 1`)**
    — канонического параметра с таким именем в `aliases.yaml` нет вообще, и точного
    close-match тоже нет (`reticulocyte_hemoglobin` — другой показатель, содержание Hb в
    ретикулоцитах, а не их количество/доля). Условие сейчас нерабочее по объективной причине
    отсутствия параметра в системе, не из-за опечатки.
16. **`lipase` (red_flag в `acute_pancreatitis`, `lipase > 600`, и сам параметр
    `acute_pancreatitis.yaml`)** — не зарегистрирован в `aliases.yaml` вообще, включая
    кириллические варианты («Липаза» и т.п.). Проверено напрямую через
    `ParameterNormalizer.normalize('Липаза', ...)` — возвращает канонику **`Липаза`**
    (кириллицей, без изменений), которая никогда не совпадёт с `parameter: lipase` в правиле.
    То есть критерий по липазе в `acute_pancreatitis` практически никогда не сработает для
    русскоязычных данных пациента. Оба входа в систему (`/analyze`, `/analyze_structured`)
    идут только через `raw_text` → `regex_parser` → `ParameterNormalizer` → `aliases.yaml`,
    structured JSON-обхода нет — значит это не вспомогательный путь, а единственный.
17. **Ещё 14 параметров используются в правилах базы, но не зарегистрированы в
    `aliases.yaml`** (тот же класс проблемы, что и `lipase`, — не проверялось индивидуально,
    насколько каждый критичен на практике):
    `17_oh_progesterone`, `aldosterone`, `amylase`, `calcitonin`, `glucose_random`,
    `growth_hormone`, `indirect_bilirubin`, `metanephrines`, `normetanephrine`, `renin`,
    `tga_iga`, `total_iga`, `urine_eosinophils`, `waist_circumference`.
    Список получен systematic-скриптом по всем `parameter:`-полям 243 guideline-файлов +
    `clinical_interpretations.yaml` против 253 канонических ключей `aliases.yaml`. Не
    исправлялось намеренно — добавление кириллических синонимов для 14 медицинских терминов
    это content-задача, требующая проверки корректности терминологии, а не техническая правка.
18. **Нулевое тестовое покрытие** для:
    - `ClinicalInterpreter._generate_comment` / `additional_rules` — баг с `value` (см. раздел
      «Исправлено») не был бы обнаружен тестами вообще, если бы не ручная проверка;
    - HTTP-слоя (`api/main.py`) — ни один тест не использует `fastapi.testclient.TestClient`,
      реальные эндпоинты `/analyze`, `/analyze_structured` не прогоняются тестами.

---

## Как проверялось (для следующей сессии)

- `pytest tests/ -q` — 44 passed, 0 failed на момент реконструкции.
- `flake8 . --select=E9,F63,F7,F82` — чисто.
- Tier-статистика: 243 файла, 231 enriched (95%), 12 basic, 0 ошибок загрузки — скрипт
  напрямую вызывает `RuleVersion.from_yaml` + `ClinicalInterpretationMapper`, не моки.
- Систематическая проверка condition-выражений (`differentials`/`red_flags`/`additional_rules`)
  во всём `clinical_interpretations.yaml`: парсинг через `ast.parse` + сverка имён переменных
  против объединения (все канонические ключи `aliases.yaml`) ∪ (`age`, `gender`, `value`).
- Систематическая проверка всех `parameter:`-полей (243 guideline-файла + `clinical_interpretations.yaml`,
  132 уникальных имени) против 253 канонических ключей `aliases.yaml`.

Оба скрипта разовые (писались в `/tmp` в контейнере сессии, не сохранены в репозитории) —
при следующей проверке стоит переписать их как постоянные dev-скрипты или тесты, а не
полагаться на то, что кто-то повторит их вручную.
