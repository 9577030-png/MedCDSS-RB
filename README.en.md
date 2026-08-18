markdown
# 🧪 Laboratory Data Interpretation System (Rule‑Based)

[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-✓-blue.svg)](https://www.docker.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-orange.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/9577030-png/MedCDSS-RB/actions/workflows/ci.yml/badge.svg)](https://github.com/9577030-png/MedCDSS-RB/actions)

**A rule‑based system for laboratory data interpretation.** It analyzes test results and provides structured conclusions with diagnoses, recommendations, risk assessment, and detailed clinical insights (a cheat sheet for clinicians).

> **Русский:** Правила, основанная система для интерпретации лабораторных данных. Анализирует результаты анализов и выдаёт структурированное заключение с диагнозами, рекомендациями, оценкой риска и детальными клиническими инсайтами (шпаргалкой для врача).

---

## 📸 Screenshots

| UI | Results | Insights | Admin |
|-----|---------|----------|-------|
| ![Main screen](docs/screenshots/streamlit_main.png) | ![Analysis result](docs/screenshots/analysis_result.png) | ![Clinical insights](docs/screenshots/clinical_insights.png) | ![Admin panel](docs/screenshots/admin_panel.png) |

---

## ✨ Key Features

| Category | Description |
|----------|-------------|
| **🧪 Interpretation** | 50+ clinical rules (anemia, diabetes, kidney, liver, infections, metabolism) |
| **⚥ Gender** | Gender‑specific reference ranges for 10+ parameters (Hb, creatinine, ALT, AST, GGT, ferritin, iron, RBC, Hct, ESR) |
| **🔗 Combinations** | Syndromes based on multiple findings (primary hyperparathyroidism, septic syndrome, etc.) |
| **📋 Conclusion** | Grouped by organ systems, deduplicated, with descriptions |
| **🧠 Insights** | Criteria, differential diagnosis, red flags, treatment hints, guideline references |
| **👨‍⚕️ Recommendations** | Specialty, urgency, additional tests |
| **📊 History** | SQLite storage with ability to load last report by patient ID |
| **🔐 Security** | JWT authentication with roles (`admin`, `doctor`, `user`) |
| **🖥️ UI** | Streamlit with autocomplete, color‑coded risk, interactive cards |
| **📄 PDF** | Export conclusion with Cyrillic support |
| **🔄 Hot‑reload** | Update rules without restarting the container |
| **🐳 Docker** | One‑command launch (`docker-compose up -d`) |

---

## 🏗️ Architecture

The project follows **Clean Architecture** principles (Ports & Adapters):
MedCDSS-RB/
├── domain/ # Core (entities, value objects, business logic)
├── application/ # Use cases and ports (interfaces)
├── infrastructure/ # Adapters (loaders, parsers, storage, DI)
├── api/ # REST API (FastAPI, authentication)
├── knowledge/ # YAML configurations (thresholds, rules, interpretations)
├── tests/ # Tests (pytest)
├── docs/ # Documentation
├── streamlit_app.py # Web UI
└── docker-compose.yml # API + UI one‑command launch

text

**Tech stack:** Python 3.13, FastAPI, Pydantic, PyYAML, SQLite, JWT, ReportLab, Streamlit, Docker, GitHub Actions.

---

## 🚀 Quick Start

### Run with Docker (recommended)

```bash
git clone https://github.com/9577030-png/MedCDSS-RB.git
cd MedCDSS-RB
docker-compose up -d
After startup:

API docs: http://localhost:8000/docs

UI: http://localhost:8501

Default accounts:

Login	Password	Role
admin	admin	Administrator
doctor	doctor	Doctor
⚠️ In production, change default passwords and set a custom SECRET_KEY in .env.

Local development
bash
pip install -e .
python app.py
streamlit run streamlit_app.py   # in a separate terminal
📚 Documentation
Full documentation is available in the docs/ folder:

Installation

API Endpoints

Configuration

Architecture

Clinical Rules

🧪 Testing
bash
pytest -v
Integration tests cover configuration loading, combined diagnoses, gender‑specific thresholds, and range‑based rules.

🩺 Clinical Insights (Cheat Sheet for Clinicians)
For each diagnosis, the system provides:

Criteria – which parameters and thresholds triggered the rule

Differential diagnosis – possible alternatives

Red flags – situations requiring immediate attention

Treatment hints – step‑by‑step actions

References – to current clinical guidelines (KDIGO, ADA, ESC, etc.)

🔐 Security & Limitations
⚠️ Important Disclaimer
This system is not a medical device and does not replace a physician. It is intended for educational and research purposes only, and as a supportive tool for clinicians.
All diagnoses and recommendations must be verified by a qualified medical professional. The author assumes no responsibility for any harm arising from the use of this system in real clinical practice.

👨‍💻 Who Is This For?
Clinicians and labs – as a supportive tool and educational reference

Developers – as a reference implementation of a medical expert system

Researchers – as a foundation for testing new diagnostic rules

Students – as a learning project with a full stack (Python, FastAPI, Docker, Streamlit, JWT, YAML, CI/CD)

🤝 Contact
Author: Sergei Smirnov

GitHub: 9577030-png

Email: 9577030@gmail.com

Telegram: @smirnov-kos

Repository: MedCDSS-RB

📄 License
MIT License – free to use, modify, and distribute with attribution.