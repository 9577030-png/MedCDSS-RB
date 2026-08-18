<<<<<<< HEAD
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import yaml

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

# Импорты из проекта
from infrastructure.bootstrap.di_container import DIContainer
from domain.entities.patient import PatientProfile
from domain.value_objects.gender import Gender
from infrastructure.adapters.parsers.regex_parser import RegexParser
from application.services.interpreter import ClinicalInterpreter

# ---------- Настройка страницы ----------
st.set_page_config(
    page_title="Система интерпретации лабораторных данных",
    page_icon="🧪",
    layout="wide"
)

# ---------- Инициализация ----------
@st.cache_resource
def init_container():
    return DIContainer(probability_threshold=0.3)

@st.cache_resource
def init_interpreter():
    return ClinicalInterpreter("knowledge/configs/clinical_interpretations.yaml")

container = init_container()
interpreter = init_interpreter()

# ---------- Session State ----------
if "added_params" not in st.session_state:
    st.session_state.added_params = []
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""

# ---------- Функции ----------
def map_gender(gender_str: str) -> Gender:
    g = gender_str.lower()
    if g == "male":
        return Gender.MALE
    elif g == "female":
        return Gender.FEMALE
    return Gender.MALE

def load_parameter_list():
    """Загружает список параметров из aliases.yaml"""
    try:
        aliases_path = Path("knowledge/laboratory/aliases.yaml")
        with open(aliases_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        aliases = data.get("aliases", {})
        all_names = set()
        for canonical, synonyms in aliases.items():
            all_names.add(canonical)
            for syn in synonyms:
                all_names.add(syn)
        return sorted(all_names)
    except Exception as e:
        st.warning(f"Не удалось загрузить список параметров: {e}")
        return ["глюкоза", "креатинин", "гемоглобин", "ферритин", "калий", "натрий", "АЛТ", "АСТ", "ТТГ", "витамин D", "ЛПНП", "триглицериды", "ЛПВП", "мочевая кислота"]

parameters_list = load_parameter_list()

# ---------- Интерфейс ----------
st.title("🧪 Система интерпретации лабораторных данных")
st.markdown("Введите данные пациента и лабораторные показатели для получения клинического заключения.")

# Боковая панель
with st.sidebar:
    st.header("🧑‍⚕️ Данные пациента")
    patient_id = st.text_input("ID пациента", value="P001")
    gender = st.selectbox("Пол", ["male", "female", "other"])
    age = st.number_input("Возраст", min_value=0, max_value=150, value=45)
    complaints = st.text_area("Жалобы (через запятую)", value="fatigue, weakness")
    medications = st.text_area("Принимаемые лекарства (через запятую)", value="")

    st.markdown("---")
    st.markdown("### 📋 Добавить лабораторный параметр")

    param_name = st.selectbox("Параметр", options=parameters_list, key="param_select")
    col_val, col_unit = st.columns([3, 2])
    with col_val:
        param_value = st.number_input("Значение", value=0.0, step=0.1, format="%.2f", key="param_value")
    with col_unit:
        param_unit = st.text_input("Единица (опционально)", value="", placeholder="напр. ммоль/л", key="param_unit")

    if st.button("➕ Добавить параметр", use_container_width=True):
        if param_name and param_value is not None:
            st.session_state.added_params.append((param_name, param_value, param_unit))
            st.rerun()
        else:
            st.warning("Выберите параметр и введите значение.")

    if st.session_state.added_params:
        st.markdown("#### Уже добавлены:")
        for i, (pname, pval, punit) in enumerate(st.session_state.added_params):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{pname}**")
            with col2:
                st.write(f"{pval}")
            with col3:
                if punit:
                    st.write(f"{punit}")
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.added_params.pop(i)
                st.rerun()
        if st.button("Очистить все", use_container_width=True):
            st.session_state.added_params = []
            st.rerun()
    else:
        st.info("Пока нет добавленных параметров.")

    if st.session_state.added_params:
        raw_text_lines = []
        for pname, pval, punit in st.session_state.added_params:
            if punit:
                raw_text_lines.append(f"{pname} {pval} {punit}")
            else:
                raw_text_lines.append(f"{pname} {pval}")
        st.session_state.raw_text = "\n".join(raw_text_lines)
    else:
        st.session_state.raw_text = ""

    analyze_btn = st.button("🔍 Анализировать", type="primary", use_container_width=True)

# ---------- Основная область ----------
# Отладочный вывод
with st.expander("📝 Сформированный текст для анализа", expanded=False):
    st.code(st.session_state.raw_text or "(пусто)", language="text")

if analyze_btn and st.session_state.raw_text.strip():
    try:
        patient = PatientProfile(
            id=patient_id,
            gender=map_gender(gender),
            age=age,
            complaints=[c.strip() for c in complaints.split(",") if c.strip()],
            medications=[m.strip() for m in medications.split(",") if m.strip()]
        )

        with st.spinner("Выполняется анализ..."):
            result = container.pipeline.run_with_postprocessing(patient, st.session_state.raw_text)

        if result:
            st.session_state.analysis_result = result
            st.success("✅ Анализ завершён")

            # ----- Общий риск -----
            risk_level = result.get("overall_risk_level", "Неизвестно")
            color_map = {
                "Норма": "green",
                "Низкий": "blue",
                "Средний": "orange",
                "Высокий": "red",
                "Критический": "darkred"
            }
            color = color_map.get(risk_level, "gray")
            st.markdown(
                f"<div style='background-color:{color}; padding:10px; border-radius:10px; text-align:center;'>"
                f"<h2 style='color:white; margin:0;'>🚨 Общий уровень риска: {risk_level}</h2>"
                f"</div>",
                unsafe_allow_html=True
            )

            # ----- Диагнозы -----
            diagnoses = result.get("diagnoses", [])
            if diagnoses:
                st.markdown("### 📌 Выявленные состояния")
                for d in diagnoses:
                    label = d.get("label", d.get("id", "Неизвестно"))
                    risk = d.get("risk", "Норма")
                    combined = d.get("combined", False)
                    desc = d.get("description")
                    card_color = color_map.get(risk, "gray")
                    st.markdown(
                        f"""
                        <div style="border-left: 5px solid {card_color}; padding-left: 15px; margin-bottom: 10px;">
                            <strong>{label}</strong>
                            <span style="background-color:{card_color}; color:white; padding:2px 8px; border-radius:12px; font-size:0.8rem;">{risk}</span>
                            { '⚕️ (комбинированный)' if combined else '' }
                            <br>
                            <span style="font-size:0.9rem; color:#555;">{desc or ''}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("Значимых отклонений не обнаружено.")

            # ----- Группировка -----
            grouped = result.get("grouped_findings", {})
            if grouped:
                st.markdown("### 🧬 Распределение по системам органов")
                for system, findings in grouped.items():
                    with st.expander(f"**{system}** ({len(findings)})"):
                        for f in findings:
                            label = f.get("title", f.get("id", "Неизвестно"))
                            risk = f.get("risk", "Норма")
                            desc = f.get("description")
                            card_color = color_map.get(risk, "gray")
                            st.markdown(
                                f"""
                                <div style="border-left: 3px solid {card_color}; padding-left: 10px; margin: 5px 0;">
                                    <strong>{label}</strong> <span style="color:{card_color};">({risk})</span>
                                    <br><span style="font-size:0.85rem; color:#555;">{desc or ''}</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

            # ----- Рекомендации -----
            recommendations = result.get("recommendations_by_specialty", {})
            if recommendations:
                st.markdown("### 👨‍⚕️ Рекомендации по специальностям")
                for specialty, recs in recommendations.items():
                    with st.expander(f"**{specialty}** ({len(recs)})"):
                        for r in recs:
                            urgency = r.get("urgency", "unknown")
                            tests = r.get("tests", [])
                            st.markdown(f"- **Срочность:** {urgency}")
                            if tests:
                                st.markdown(f"  **Тесты:** {', '.join(tests)}")
                            st.markdown("---")
            else:
                st.info("Нет рекомендаций.")

            # ----- Клинические инсайты -----
            try:
                parser = RegexParser()
                parameters = parser.parse(st.session_state.raw_text)
                insights = interpreter.interpret(diagnoses, parameters, patient)

                if insights:
                    st.markdown("### 🧠 Клинические инсайты (подробная интерпретация)")
                    for diag_id, insight in insights.items():
                        label = getattr(insight, 'label', diag_id) if hasattr(insight, 'label') else diag_id
                        with st.expander(f"**{label}** (ID: {diag_id})"):
                            # Критерии
                            if hasattr(insight, 'criteria') and insight.criteria:
                                st.markdown("#### 📊 Критерии диагноза")
                                df_data = []
                                for c in insight.criteria:
                                    df_data.append({
                                        "Параметр": getattr(c, 'parameter', ''),
                                        "Значение": getattr(c, 'value', ''),
                                        "Норма": f"{getattr(c, 'threshold', '')} ({getattr(c, 'condition', '')})",
                                        "Комментарий": getattr(c, 'comment', '')
                                    })
                                if df_data:
                                    st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True)

                            # Дифференциалы
                            if hasattr(insight, 'differentials') and insight.differentials:
                                st.markdown("#### 🔍 Дифференциальная диагностика")
                                for diff in insight.differentials:
                                    condition = getattr(diff, 'condition', '')
                                    text = getattr(diff, 'text', '')
                                    st.markdown(f"- **Условие:** `{condition}` → {text}")

                            # Красные флаги
                            if hasattr(insight, 'red_flags') and insight.red_flags:
                                st.markdown("#### ⚠️ Красные флаги")
                                for rf in insight.red_flags:
                                    condition = getattr(rf, 'condition', '')
                                    text = getattr(rf, 'text', '')
                                    st.markdown(f"- **{condition}** → {text}")

                            # Лечебные подсказки
                            if hasattr(insight, 'treatment_hints') and insight.treatment_hints:
                                st.markdown("#### 💊 Шпаргалка по тактике")
                                for hint in insight.treatment_hints:
                                    step = getattr(hint, 'step', '')
                                    note = getattr(hint, 'note', '')
                                    st.markdown(f"- **{step}** — {note}")

                            # Ссылки
                            if hasattr(insight, 'references') and insight.references:
                                st.markdown("#### 📚 Ссылки")
                                for ref in insight.references:
                                    st.markdown(f"- {ref}")
                else:
                    st.info("Для выявленных диагнозов нет дополнительных клинических инсайтов.")
            except Exception as e:
                st.info(f"Инсайты временно недоступны: {e}")

            # ----- Заключение (текстовое) -----
            conclusion = result.get("conclusion", "")
            if conclusion:
                with st.expander("📄 Полное текстовое заключение"):
                    st.text(conclusion)

    except Exception as e:
        st.error(f"❌ Ошибка: {e}")

elif analyze_btn:
    st.warning("Добавьте хотя бы один лабораторный параметр.")

# ----- Футер -----
st.markdown("---")
st.caption("Система интерпретации лабораторных данных v1.0 | Демо-версия")

