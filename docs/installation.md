# Установка и настройка

## Требования

- Python 3.13+
- Docker (опционально, но рекомендуется)
- Git

## Установка через Docker (рекомендуется)

1. Клонируйте репозиторий:

```bash
git clone https://github.com/9577030-png/MedCDSS-RB.git
cd MedCDSS-RB
```

Убедитесь, что в корне есть `Dockerfile.api`, `Dockerfile.ui`, `docker-compose.yml`.

2. Запустите контейнеры:

```bash
docker-compose up -d
```

3. Проверьте, что API работает:

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:
```json
{"status":"ok","message":"Medical AI service is running"}
```

4. Откройте веб-интерфейс: http://localhost:8501

---

## Локальная установка (для разработки)

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

pip install -e .
python app.py
```

В отдельном терминале:
```bash
streamlit run streamlit_app.py
```

---

## Переменные окружения

Скопируйте `.env.example` в `.env` и при необходимости отредактируйте:

```env
APP_NAME=Medical Clinical Decision Support System — Rule-Based Expert Engine
DEBUG=false

KNOWLEDGE_DIR=knowledge
GUIDELINES_DIR=knowledge/guidelines
FONTS_DIR=fonts

DB_PATH=cdss.db
LOG_LEVEL=INFO

# Если не задать - сгенерируется случайно при каждом запуске (значит после
# перезапуска старые токены станут невалидными). Для продакшена задайте свой.
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

API_HOST=0.0.0.0
API_PORT=8000
API_BASE=http://api:8000  # Для Streamlit в Docker
```

---

## Пользователи по умолчанию

При первом запуске создаются две учётные записи — `admin` и `doctor`. **Пароль для каждой генерируется случайно** (`secrets.token_urlsafe`), а не является фиксированным `admin/admin`. Пароль печатается в лог **один раз**, при первом создании пользователя, и больше нигде не хранится в открытом виде:

```bash
docker-compose logs api | grep "паролем"
# или, при локальном запуске:
python app.py 2>&1 | grep "паролем"
```

Если контейнер уже был запущен раньше и лог с паролем потерян — самый быстрый способ восстановить доступ: удалить файл БД (`cdss.db` по умолчанию) и перезапустить, пароли сгенерируются заново. Учтите, что это удалит и историю отчётов.

Смените пароль сразу после первого входа через админ-интерфейс.

---

## Проверка работоспособности

```bash
pytest -v
```

Ожидается 44 прошедших теста, 0 упавших.

```bash
flake8 . --select=E9,F63,F7,F82
```

Должно завершиться без вывода (0 замечаний).

---

## Примеры использования

В папке `examples/` — скрипты для ручного тестирования API:

```bash
python examples/test_api.py
python examples/test_new_params.py
python examples/test_structured_combined.py
python examples/test_gender_thresholds.py
python examples/test_gender_full.py
```

---

## Устранение неполадок

**`ModuleNotFoundError: No module named 'api'`**
Убедитесь, что вы находитесь в корневой папке проекта и установили зависимости: `pip install -e .`

**`port is already allocated`**
Измените порты в `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"   # вместо 8000
  - "8502:8501"   # вместо 8501
```

**Шрифты не отображаются в PDF**
Убедитесь, что в `fonts/` есть `DejaVuSans.ttf`. Если нет — скачайте с https://dejavu-fonts.github.io/

**Забыли пароль admin, а лог с исходным паролем утерян**
См. раздел «Пользователи по умолчанию» выше — удалите `cdss.db` и перезапустите (потеряете историю отчётов), либо создайте нового admin-пользователя напрямую через SQL, если БД важна.
