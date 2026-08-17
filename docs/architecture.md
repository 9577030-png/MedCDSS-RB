```markdown
# Архитектура системы

## Общая структура
medical_ai1/
├── domain/ # Чистое ядро (сущности, value objects, логика)
│ ├── entities/ # PatientProfile, Parameter, ClinicalFinding, Recommendation, Report
│ ├── value_objects/ # Gender, RiskLevel, Severity, Unit
│ └── logic/ # score(), calculate_risk(), filter_contradictions()
├── application/ # Сценарии использования и порты
│ ├── ports/ # Интерфейсы (GuidelineProvider, ThresholdProvider, ParserInterface...)
│ └── services/ # InferenceEngine, ActionMapper, ReportBuilder, AnalysisPipeline,
│ # PostProcessor, ClinicalInterpreter
├── infrastructure/ # Адаптеры
│ ├── adapters/
│ │ ├── loaders/ # YAML-загрузчики (пороги, правила, рекомендации, логика)
│ │ ├── parsers/ # RegexParser с нормализацией
│ │ ├── renderers/ # ConsoleRenderer
│ │ └── storage/ # SqlHistoryRepository, SqlUserRepository
│ ├── bootstrap/ # DIContainer (сборка всех зависимостей)
│ └── logging_config.py # Настройка логирования
├── api/ # FastAPI + JWT-аутентификация
│ ├── main.py # Все эндпоинты
│ └── auth_config.py # Хеширование паролей, создание токенов
├── knowledge/ # Конфигурации в YAML
│ ├── configs/
│ │ ├── clinical_thresholds.yaml # Пороги
│ │ ├── clinical_logic.yaml # Группировка, исключения, комбинации
│ │ ├── clinical_interpretations.yaml # Клинические инсайты
│ │ └── doctor_recommendations.yaml # Рекомендации врачей
│ ├── guidelines/ # Правила (можно добавлять новые)
│ └── laboratory/ # aliases.yaml, units.yaml
├── tests/ # Юнит- и интеграционные тесты
├── docs/ # Документация
├── fonts/ # Шрифты для PDF
└── streamlit_app.py # Веб-интерфейс (Streamlit)

text

## Принципы архитектуры

- **Чистая архитектура** – ядро не зависит от внешних деталей
- **Инверсия зависимостей** – сценарии используют порты, адаптеры реализуют их
- **Внешняя конфигурация** – правила и пороги хранятся в YAML, не в коде
- **Тестируемость** – все компоненты покрыты тестами
- **Единый DI-контейнер** – все компоненты создаются в одном месте и переиспользуются

## Поток данных

1. **Вход** – данные пациента + сырой текст лабораторных показателей
2. **Парсинг** – `RegexParser` извлекает параметры, `ParameterNormalizer` приводит к каноническому виду (с учётом алиасов и единиц)
3. **Вывод (inference)** – `InferenceEngine` применяет правила (`guidelines/`) и вычисляет вероятности находок. При этом используются полозависимые пороги через `ThresholdProvider`
4. **Действия** – `ActionMapper` подбирает рекомендации врачей на основе `doctor_recommendations.yaml`
5. **Постобработка** – `PostProcessor`:
   - Фильтрует по порогу вероятности
   - Применяет исключения из `clinical_logic.yaml`
   - Фильтрует по белому списку (основные диагнозы)
   - Группирует по системам органов
   - Формирует комбинированные диагнозы
6. **Интерпретация** – `ClinicalInterpreter` генерирует клинические инсайты (критерии, дифференциалы, красные флаги, тактику) на основе `clinical_interpretations.yaml`
7. **Ответ** – структурированное заключение (JSON) или PDF/текст для пользователя

## Компоненты

### Domain (ядро)

| Компонент | Описание |
|-----------|----------|
| `PatientProfile` | Данные пациента (id, пол, возраст, жалобы, лекарства) |
| `Parameter` | Лабораторный параметр (название, значение, единица) |
| `ClinicalFinding` | Находка (диагноз) с вероятностью и уровнем риска |
| `Recommendation` | Рекомендация (специальность, срочность, тесты) |
| `AnalysisReport` | Отчёт (находки, действия, объяснение) |
| `User` | Пользователь (id, логин, хеш пароля, роль) |

### Application (сервисы)

| Сервис | Описание |
|--------|----------|
| `InferenceEngine` | Применяет правила к параметрам, вычисляет находки |
| `ActionMapper` | Сопоставляет находки с рекомендациями |
| `ReportBuilder` | Собирает отчёт из находок и действий |
| `AnalysisPipeline` | Оркестратор всего процесса анализа |
| `PostProcessor` | Постобработка: фильтрация, группировка, комбинации |
| `ClinicalInterpreter` | Генерация клинических инсайтов (шпаргалка) |

### Infrastructure (адаптеры)

| Адаптер | Описание |
|---------|----------|
| `YamlThresholdLoader` | Загрузка порогов из `clinical_thresholds.yaml` |
| `MergedGuidelineProvider` | Загрузка правил из `guidelines/` |
| `YamlRecommendationLoader` | Загрузка рекомендаций из `doctor_recommendations.yaml` |
| `ClinicalLogicLoader` | Загрузка логики постобработки из `clinical_logic.yaml` |
| `RegexParser` | Парсинг лабораторных данных |
| `ParameterNormalizer` | Нормализация имён и единиц |
| `SqlHistoryRepository` | Хранение истории в SQLite |
| `SqlUserRepository` | Хранение пользователей в SQLite |
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
| `/reload_config` | POST | Горячая перезагрузка | Admin |
| `/admin/config/file` | GET/POST | Чтение/запись конфигов | Admin |
| `/admin/history/{id}` | GET | История пациента | Admin |
| `/health` | GET | Проверка статуса | Публичный |

### Веб-интерфейс (Streamlit)

| Страница | Описание |
|----------|----------|
| **Анализ** | Форма пациента, ввод лабораторных данных, отображение заключения, PDF-экспорт |
| **Администрирование** | Управление пользователями, просмотр истории, редактирование конфигураций |

## Безопасность

- JWT-токены с ограниченным сроком действия
- Пароли хранятся в хешированном виде (pbkdf2_sha256)
- Роли (`admin`, `doctor`, `user`) ограничивают доступ к эндпоинтам
- Валидация входных данных через Pydantic
- Защита от записи за пределы `knowledge/` при редактировании конфигов

## Масштабирование

- Система stateless (кроме SQLite). Для продакшена рекомендуется заменить SQLite на PostgreSQL
- Можно добавить кэширование правил (Redis)
- API и Streamlit могут быть развёрнуты на отдельных серверах

## Дальнейшее развитие

- Интеграция с ЭМК через HL7/FHIR
- Поддержка многоязычности
- Машинное обучение для уточнения правил
- Добавление новых клинических областей (неврология, кардиология, онкология)
