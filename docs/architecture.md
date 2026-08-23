# Архитектура системы

## Общая структура

```
MedCDSS-RB/
├── domain/                 # Чистое ядро (сущности, value objects, логика)
│   ├── entities/            # PatientProfile, Parameter, ClinicalFinding, Recommendation, Report
│   ├── value_objects/        # Gender, RiskLevel, Unit
│   └── rule_version.py        # RuleVersion, RuleTier, RulePriority
├── application/              # Сценарии использования и порты
│   ├── ports/                  # Интерфейсы (ParserInterface, HistoryRepository...)
│   └── services/                # InferenceEngine, ActionMapper, ReportBuilder,
│                                  # AnalysisPipeline, PostProcessor, ClinicalInterpreter,
│                                  # ConflictResolver, VersionManager
├── infrastructure/            # Адаптеры
│   ├── adapters/
│   │   ├── loaders/              # YAML/JSON-загрузчики (пороги, правила, референсы)
│   │   ├── parsers/               # RegexParser (токенизирующий) + ParameterNormalizer
│   │   ├── renderers/              # ConsoleRenderer
│   │   └── storage/                # SqlHistoryRepository, SqlUserRepository
│   ├── bootstrap/                    # DIContainer (сборка всех зависимостей)
│   └── repositories/                  # SqlAlchemyRuleRepository (версии правил)
├── api/                        # FastAPI + JWT-аутентификация
│   ├── main.py                   # Все эндпоинты
│   └── auth_config.py              # Хеширование паролей, создание токенов
├── knowledge/                   # Конфигурации в YAML
│   ├── configs/
│   │   ├── clinical_thresholds.yaml       # Пороги для ~6 параметров с богатыми интерпретациями
│   │   ├── clinical_logic.yaml             # Группировка, исключения, комбинации, метки
│   │   ├── clinical_interpretations.yaml    # Клинические инсайты (enriched-уровень)
│   │   ├── doctor_recommendations.yaml       # Рекомендации врачей по специальности
│   │   └── medical_data.json                  # Референсные интервалы для текстовых интерпретаций
│   └── guidelines/                              # 243 файла правил (можно добавлять новые)
├── tests/                       # Юнит- и интеграционные тесты (44 теста)
├── docs/                         # Документация
├── fonts/                         # Шрифты для PDF
└── streamlit_app.py                 # Веб-интерфейс (Streamlit)
```

## Принципы архитектуры

- **Чистая архитектура** — ядро (`domain/`) не зависит от внешних деталей (БД, фреймворков, форматов файлов)
- **Инверсия зависимостей** — `application/` использует порты (интерфейсы), `infrastructure/` их реализует
- **Внешняя конфигурация** — правила и пороги хранятся в YAML/JSON, не в коде
- **Единый DI-контейнер** (`infrastructure/bootstrap/di_container.py`) — все компоненты собираются в одном месте

## Поток данных

1. **Вход** — данные пациента + сырой текст лабораторных показателей
2. **Парсинг** — `RegexParser` токенизирует строку (учитывает референсные интервалы в скобках, составные имена вроде `HbA1c`, запятую как десятичный разделитель), `ParameterNormalizer` приводит имена к каноническому виду через таблицу алиасов (640 алиасов, 52 единицы измерения)
3. **Загрузка правил** — `VersionManager.hot_reload()` читает все YAML из `knowledge/guidelines/**` через `RuleVersion.from_yaml()`. Если файл уже в формате `conditions: [...]` — используется как есть; если в старом формате (`thresholds:`/`scoring:`) — конвертируется на лету через `_convert_old_format()`. Каждому правилу присваивается `tier` (`enriched`/`basic`) на основе того, есть ли для него запись в `clinical_interpretations.yaml`
4. **Вывод (inference)** — `InferenceEngine` проверяет каждое условие каждого активного правила против параметров пациента (с учётом пола, где задано), формирует находки (`ClinicalFinding`)
5. **Разрешение конфликтов** — `ConflictResolver` убирает дубли по id и разрешает конфликты между правилами, объявившими друг друга через `conflicts_with`, с учётом приоритета (`RulePriority`)
6. **Действия** — `ActionMapper` подбирает рекомендации врачей на основе `doctor_recommendations.yaml`
7. **Постобработка** — `PostProcessor`:
   - фильтрует по порогу вероятности
   - применяет исключения из `clinical_logic.yaml` (`_apply_exclusions`, понимает и id правила, и id отдельного условия внутри него)
   - группирует низкоспецифичные находки по общему лабораторному параметру, если их 3 и более (`_group_low_specificity_by_parameter`) — иначе, например, один повышенный креатинин мог бы выдать 20+ равноправных диагнозов одновременно
   - группирует по системам органов, формирует комбинированные диагнозы (`combinations` в `clinical_logic.yaml`)
8. **Интерпретация** — `ClinicalInterpreter` для enriched-правил генерирует развёрнутые инсайты (критерии, дифдиагноз, красные флаги, тактику), используя референсы из `medical_data.json`
9. **Ответ** — структурированное заключение (JSON) или PDF/текст

## Компоненты

### Domain (ядро)

| Компонент | Описание |
|-----------|----------|
| `PatientProfile` | Данные пациента (id, пол, возраст) |
| `Parameter` | Лабораторный параметр (название, значение, единица) |
| `ClinicalFinding` | Находка с вероятностью, уровнем риска и id исходного параметра |
| `Recommendation` | Рекомендация (специальность, срочность, тесты) |
| `AnalysisReport` | Отчёт (находки, действия, объяснение) |
| `RuleVersion` | Версия правила с условиями, приоритетом, `conflicts_with`, `tier` |
| `User` | Пользователь (id, логин, хеш пароля, роль) |

### Application (сервисы)

| Сервис | Описание |
|--------|----------|
| `VersionManager` | Загрузка и горячая перезагрузка правил из YAML |
| `InferenceEngine` | Применяет правила к параметрам, вычисляет находки |
| `ConflictResolver` | Дедупликация и разрешение конфликтов между находками |
| `ActionMapper` | Сопоставляет находки с рекомендациями |
| `ReportBuilder` | Собирает отчёт из находок и действий |
| `AnalysisPipeline` | Оркестратор всего процесса анализа, кэш, аудит |
| `PostProcessor` | Фильтрация, исключения, группировка, комбинации |
| `ClinicalInterpreter` | Генерация клинических инсайтов для enriched-правил |
| `ClinicalInterpretationMapper` | Определяет, есть ли для правила enriched-запись |

### Infrastructure (адаптеры)

| Адаптер | Описание |
|---------|----------|
| `RegexParser` | Токенизирующий парсер лабораторного текста |
| `ParameterNormalizer` | Нормализация имён параметров и единиц измерения |
| `MedicalReferenceLoader` | Референсные интервалы для текстовых интерпретаций (`medical_data.json`) |
| `SqlHistoryRepository` | Хранение истории отчётов в SQLite |
| `SqlUserRepository` | Хранение пользователей, генерация случайных паролей при первом запуске |
| `SqlAlchemyRuleRepository` | Хранение версий правил |
| `DIContainer` | Сборка всех зависимостей |

### API (FastAPI)

| Эндпоинт | Метод | Описание | Доступ |
|----------|-------|----------|--------|
| `/token` | POST | Получение JWT-токена | Публичный |
| `/register` | POST | Создание пользователя | Admin |
| `/users` | GET | Список пользователей | Admin |
| `/admin/user/{id}` | DELETE | Удаление пользователя | Admin |
| `/analyze` | POST | Анализ (сырой отчёт) | User+ |
| `/analyze_structured` | POST | Анализ (структурированный) | User+ |
| `/export_pdf` | POST | Экспорт в PDF | User+ |
| `/reload_config` | POST | Горячая перезагрузка правил | Admin |
| `/admin/config/file` | GET/POST | Чтение/запись конфигов | Admin |
| `/admin/history/{id}` | GET | История пациента | Admin |
| `/health` | GET | Проверка статуса | Публичный |

Полное описание запросов/ответов — в [`api.md`](api.md).

## Безопасность

- JWT-токены с ограниченным сроком действия
- Пароли хранятся в хешированном виде (`pbkdf2_sha256`)
- Пользователи `admin`/`doctor`, создаваемые при первом запуске, получают случайный пароль (`secrets.token_urlsafe`), а не фиксированный — он печатается в лог один раз
- Роли (`admin`, `doctor`, `user`) ограничивают доступ к эндпоинтам
- `SECRET_KEY` генерируется случайно при старте, если не задан явно в `.env`

## Масштабирование

- Система преимущественно stateless (кроме SQLite). Для продакшена рекомендуется заменить SQLite на PostgreSQL
- Redis используется для кэширования результатов анализа
- API и Streamlit развёртываются как отдельные контейнеры (`Dockerfile.api`, `Dockerfile.ui`)

## Дальнейшее развитие

- Расширение числа enriched-правил (сейчас 13 из 243)
- Табличный/структурированный парсер как альтернатива токенизации свободного текста, если появится реальный сценарий со сканами бланков
- Интеграция с ЭМК через HL7/FHIR
