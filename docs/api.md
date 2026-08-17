markdown
# API-эндпоинты

Базовый URL: `http://localhost:8000`

## Аутентификация

Большинство эндпоинтов защищены JWT-токеном. Для получения токена выполните запрос к `/token`.

**Пример запроса:**

```bash
curl -X POST http://localhost:8000/token \
  -d "username=admin&password=admin" \
  -H "Content-Type: application/x-www-form-urlencoded"
Ответ:

json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
Далее при вызове защищённых эндпоинтов передавайте токен в заголовке Authorization: Bearer <токен>.

1. /token — получение токена
Метод: POST
Защита: Нет

Параметры (form-data):

username – логин

password – пароль

Ответ: {"access_token": "...", "token_type": "bearer"}

2. /analyze — сырой отчёт
Метод: POST
Защита: JWT (любая роль)

Тело запроса (JSON):

json
{
  "patient": {
    "id": "P123",
    "gender": "male",
    "age": 45,
    "complaints": ["fatigue"],
    "medications": []
  },
  "raw_text": "Hb 130 g/L\nMCV 85 fL\nFerritin 12 ug/L"
}
Ответ (JSON):

json
{
  "findings": [
    {
      "id": "iron_deficiency",
      "title": "Guideline iron_deficiency",
      "probability": 1.0,
      "risk": "Высокий",
      "doctor_specialty": null,
      "tests": [],
      "evidence": []
    }
  ],
  "actions": [
    {
      "doctor_specialty": "Hematologist",
      "urgency": "moderate",
      "additional_tests": ["Iron", "TIBC"]
    }
  ],
  "explanation": "Findings:\n- Guideline iron_deficiency (probability 100%, risk Высокий)"
}
3. /analyze_structured — структурированное заключение
Метод: POST
Защита: JWT (любая роль)

Тело запроса: аналогично /analyze

Ответ (JSON):

json
{
  "diagnoses": [
    {
      "id": "diabetes_mellitus_type_2",
      "label": "Сахарный диабет 2 типа",
      "risk": "Высокий",
      "combined": false,
      "description": "Уровень глюкозы ≥ 7.0 ммоль/л – диабет."
    }
  ],
  "grouped_findings": {
    "Эндокринная система": [
      {
        "id": "diabetes_mellitus_type_2",
        "title": "Сахарный диабет 2 типа",
        "risk": "Высокий",
        "description": "Уровень глюкозы ≥ 7.0 ммоль/л – диабет."
      }
    ]
  },
  "recommendations_by_specialty": {
    "Endocrinologist": [
      {
        "urgency": "high",
        "tests": ["Oral glucose tolerance test", "Fasting insulin", "C-peptide"]
      }
    ]
  },
  "overall_risk_level": "Высокий",
  "conclusion": "============================================================\nКЛИНИЧЕСКОЕ ЗАКЛЮЧЕНИЕ\n============================================================\n\n▶ Выявленные состояния:\n  - Сахарный диабет 2 типа: Уровень глюкозы ≥ 7.0 ммоль/л – диабет.\n\n▶ По системам органов:\n  Эндокринная система:\n    - Уровень глюкозы ≥ 7.0 ммоль/л – диабет. (риск Высокий)\n\n▶ Рекомендации по дополнительному обследованию:\n  Нет дополнительных рекомендаций.\n\n▶ Общий уровень риска: Высокий\n\n============================================================",
  "clinical_insights": {
    "diabetes_mellitus_type_2": {
      "diagnosis_id": "diabetes_mellitus_type_2",
      "label": "Сахарный диабет 2 типа",
      "category": "Эндокринология",
      "description": "Хроническое метаболическое заболевание...",
      "criteria": [...],
      "differentials": [...],
      "red_flags": [...],
      "treatment_hints": [...],
      "references": [...]
    }
  }
}
4. /export_pdf — экспорт заключения в PDF
Метод: POST
Защита: JWT (любая роль)

Тело запроса: аналогично /analyze

Ответ: бинарный PDF-файл с заголовком Content-Disposition: attachment; filename=report_<patient_id>.pdf

5. /reload_config — горячая перезагрузка конфигурации
Метод: POST
Защита: JWT (только роль admin)

Ответ:

json
{
  "status": "ok",
  "message": "Configuration reloaded successfully"
}
6. /register — создание нового пользователя
Метод: POST
Защита: JWT (только роль admin)

Тело запроса:

json
{
  "username": "new_doctor",
  "password": "secure_pass",
  "role": "doctor"
}
Ответ:

json
{
  "id": 3,
  "username": "new_doctor",
  "role": "doctor",
  "created_at": "2025-07-30T12:00:00"
}
7. /users — список всех пользователей
Метод: GET
Защита: JWT (только роль admin)

Ответ: массив объектов UserResponse

8. /admin/user/{user_id} — удаление пользователя
Метод: DELETE
Защита: JWT (только роль admin)

Ответ:

json
{
  "status": "ok",
  "message": "User 3 deleted"
}
9. /admin/config/file — загрузка/сохранение конфигурационных файлов
Метод: GET / POST
Защита: JWT (только роль admin)

GET – параметр path (относительно knowledge/)

POST – тело запроса:

json
{
  "path": "configs/clinical_thresholds.yaml",
  "content": "..."
}
Ответ: содержимое файла (GET) или статус сохранения (POST)

10. /admin/history/{patient_id} — получение истории пациента
Метод: GET
Защита: JWT (только роль admin)

Ответ:

json
{
  "patient_id": "P001",
  "report": {
    "findings": [...],
    "actions": [...],
    "explanation": "..."
  }
}
11. /health — проверка статуса
Метод: GET
Защита: Нет

Ответ:

json
{
  "status": "ok",
  "message": "Medical AI service is running"
}
Коды ошибок
Код	Описание
400	Ошибка валидации входных данных
401	Неавторизованный запрос (отсутствует или невалидный токен)
403	Недостаточно прав (требуется роль admin)
404	Ресурс не найден
500	Внутренняя ошибка сервера