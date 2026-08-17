```markdown
# Установка и настройка

## Требования

- Python 3.13+
- Docker (опционально)
- Git

## Установка через Docker (рекомендуется)

1. Клонируйте репозиторий:

```bash
git clone https://github.com/9577030-png/MedCDSS-RB.git
cd MedCDSS-RB
Убедитесь, что в корне есть файлы:

Dockerfile.api – для сборки API

Dockerfile.ui – для сборки Streamlit

docker-compose.yml – оркестрация

Запустите контейнеры:

bash
docker-compose up -d
Проверьте, что API работает:

bash
curl http://localhost:8000/health
Ожидаемый ответ:

json
{"status":"ok","message":"Medical AI service is running"}
Откройте веб-интерфейс:

bash
start http://localhost:8501   # Windows
open http://localhost:8501    # MacOS
xdg-open http://localhost:8501 # Linux
Локальная установка (для разработки)
Создайте виртуальное окружение:

bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
Установите зависимости:

bash
pip install -e .
Запустите API:

bash
python app.py
Запустите Streamlit (в отдельном терминале):

bash
streamlit run streamlit_app.py
Настройка переменных окружения
Создайте файл .env в корне проекта (можно скопировать из .env.example):

env
APP_NAME=Medical Clinical Decision Support System — Rule-Based Expert Engine
APP_VERSION=1.0.0
DEBUG=false

KNOWLEDGE_DIR=knowledge
CONFIGS_DIR=knowledge/configs
GUIDELINES_DIR=knowledge/guidelines
LABORATORY_DIR=knowledge/laboratory
FONTS_DIR=fonts
DATA_DIR=data

DB_PATH=data/history.db
LOG_LEVEL=INFO

SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

API_HOST=0.0.0.0
API_PORT=8000

API_BASE=http://api:8000  # Для Streamlit в Docker
Пользователи по умолчанию
При первом запуске в базе данных создаются две учётные записи:

Логин	Пароль	Роль
admin	admin	Администратор (полный доступ)
doctor	doctor	Врач (только анализ)
Пароли можно изменить через интерфейс администратора или напрямую в БД.

Проверка работоспособности
Запустите тесты:

bash
pytest -v
Все тесты должны проходить (37+).

Примеры использования
В папке examples/ находятся скрипты для тестирования API:

bash
python examples/test_new_params.py
python examples/test_structured_combined.py
python examples/test_gender_thresholds.py
Устранение неполадок
Ошибка: ModuleNotFoundError: No module named 'api'

Убедитесь, что вы находитесь в корневой папке проекта и установили зависимости:

bash
pip install -e .
Ошибка: port is already allocated

Измените порты в docker-compose.yml:

yaml
ports:
  - "8001:8000"   # вместо 8000
  - "8502:8501"   # вместо 8501
Ошибка: шрифты не отображаются в PDF

Убедитесь, что в папке fonts/ есть файл DejaVuSans.ttf. Если нет – скачайте с https://dejavu-fonts.github.io/