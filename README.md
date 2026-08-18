markdown
# 🧪 Система интерпретации лабораторных данных (Rule‑Based)

[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-✓-blue.svg)](https://www.docker.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-orange.svg)](https://streamlit.io/)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Streamlit-red.svg)](https://medcdss-rb-cpymu7xlthwiptat8mirag.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/9577030-png/MedCDSS-RB/actions/workflows/ci.yml/badge.svg)](https://github.com/9577030-png/MedCDSS-RB/actions)

**Rule‑based система для интерпретации лабораторных данных.** Анализирует результаты анализов и выдаёт структурированное заключение с диагнозами, рекомендациями, оценкой риска и детальными клиническими инсайтами (шпаргалкой для врача).

> **English:** A rule‑based laboratory data interpretation system that provides structured conclusions with diagnoses, recommendations, risk assessment, and detailed clinical insights (cheat sheet for clinicians).

---

## 📸 Скриншоты

| Интерфейс | Результат | Инсайты | Админка |
|-----------|-----------|---------|---------|
| ![Главный экран](docs/screenshots/streamlit_main.png) | ![Результат анализа](docs/screenshots/analysis_result.png) | ![Клинические инсайты](docs/screenshots/clinical_insights.png) | ![Панель администратора](docs/screenshots/admin_panel.png) |

---

## ✨ Ключевые возможности

| Категория | Описание |
|-----------|----------|
| **🧪 Интерпретация** | 50+ клинических правил (анемии, диабет, почки, печень, инфекции, метаболизм) |
| **⚥ Пол** | Половозависимые референсные интервалы для 10+ параметров |
| **🔗 Комбинации** | Синдромы на основе нескольких находок (гиперпаратиреоз, септический синдром и др.) |
| **📋 Заключение** | Группировка по системам органов, дедупликация, описания |
| **🧠 Инсайты** | Критерии, дифференциальная диагностика, красные флаги, тактика, ссылки на гайдлайны |
| **👨‍⚕️ Рекомендации** | Специальность, срочность, перечень дополнительных тестов |
| **📊 История** | SQLite с загрузкой последнего отчёта по ID пациента |
| **🔐 Безопасность** | JWT-аутентификация с ролями (`admin`, `doctor`, `user`) |
| **🖥️ UI** | Streamlit с автодополнением, цветовой индикацией риска, интерактивными карточками |
| **📄 PDF** | Экспорт заключения с поддержкой кириллицы |
| **🔄 Горячая загрузка** | Обновление правил без перезапуска контейнера |
| **🐳 Docker** | Запуск одной командой (`docker-compose up -d`) |

---

## 🏗️ Архитектура

Проект следует принципам **чистой архитектуры** (Clean Architecture / Ports & Adapters):
MedCDSS-RB/
├── domain/ # Ядро (сущности, value objects, бизнес-логика)
├── application/ # Сценарии и порты (интерфейсы)
├── infrastructure/ # Адаптеры (загрузчики, парсеры, хранилище, DI)
├── api/ # REST API (FastAPI, аутентификация)
├── knowledge/ # Конфигурации в YAML (пороги, правила, интерпретации)
├── tests/ # Тесты (pytest)
├── docs/ # Документация
├── streamlit_app.py # Веб-интерфейс
└── docker-compose.yml # Запуск API + UI одной командой

text

**Технологический стек:** Python 3.13, FastAPI, Pydantic, PyYAML, SQLite, JWT, ReportLab, Streamlit, Docker, GitHub Actions.

---

## 🚀 Быстрый старт

### Запуск с Docker (рекомендуется)
**Живое демо:** [https://medcdss-rb-cpymu7xlthwiptat8mirag.streamlit.app/](https://medcdss-rb-cpymu7xlthwiptat8mirag.streamlit.app/)

```bash
git clone https://github.com/9577030-png/MedCDSS-RB.git
cd MedCDSS-RB
docker-compose up -d
После запуска:

API: http://localhost:8000/docs

UI: http://localhost:8501

Учётные записи по умолчанию:

Логин	Пароль	Роль
admin	admin	Администратор
doctor	doctor	Врач
⚠️ В продакшене обязательно смените пароли и установите собственный SECRET_KEY в .env.

Локальный запуск
bash
pip install -e .
python app.py
streamlit run streamlit_app.py   # в другом терминале
📚 Документация
Подробнее в папке docs/:

Установка

API

Конфигурация

Архитектура

Клинические правила

🧪 Тестирование
bash
pytest -v
🩺 Клинические инсайты (советы для врача)
Для каждого диагноза система предоставляет:

Критерии – какие параметры и пороги сработали

Дифференциальную диагностику – возможные альтернативы

Красные флаги – ситуации, требующие немедленного внимания

Советы по тактике – пошаговые действия

Ссылки на актуальные клинические рекомендации (KDIGO, ADA, ESC и др.)

🔐 Безопасность и ограничения
⚠️ Важное предупреждение
Данная система не является медицинским устройством и не заменяет врача. Она предназначена исключительно для образовательных и исследовательских целей, а также как вспомогательный инструмент для врачей.
Все диагнозы и рекомендации должны быть проверены квалифицированным специалистом. Автор не несёт ответственности за использование системы в реальной клинической практике.

👨‍💻 Для кого эта система?
Врачам и лабораториям – как вспомогательный инструмент и учебный справочник.

Разработчикам – как референсная реализация медицинской экспертной системы.

Исследователям – как основа для тестирования новых диагностических правил.

Студентам – как учебный проект с полным стеком (Python, FastAPI, Docker, Streamlit, JWT, YAML, CI/CD).

🤝 Контакты
Автор: Сергей Смирнов

GitHub: 9577030-png

Email: 9577030@gmail.com

Telegram: @smirnov-kos

Репозиторий: MedCDSS-RB

📄 Лицензия
MIT License – свободное использование, модификация и распространение с указанием авторства.