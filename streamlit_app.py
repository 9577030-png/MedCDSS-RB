import os
import streamlit as st
import requests
import json
import pandas as pd
from config import settings
import jwt
from typing import List, Dict, Any

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# ---------- Вспомогательные функции ----------
def get_token(username, password):
    resp = requests.post(f"{API_BASE}/token", data={"username": username, "password": password})
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None

def analyze_data(payload, token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{API_BASE}/analyze_structured", json=payload, headers=headers, timeout=30)
    return resp

def generate_pdf(payload, token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{API_BASE}/export_pdf", json=payload, headers=headers, timeout=30)
    return resp

def reload_config(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{API_BASE}/reload_config", headers=headers)
    return resp

def get_users(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/users", headers=headers)
    return resp

def register_user(token, username, password, role="user"):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"username": username, "password": password, "role": role}
    resp = requests.post(f"{API_BASE}/register", json=payload, headers=headers)
    return resp

def delete_user(token, user_id):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.delete(f"{API_BASE}/admin/user/{user_id}", headers=headers)
    return resp

def get_history(token, patient_id):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/admin/history/{patient_id}", headers=headers)
    return resp

def get_config_file(token, path):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/admin/config/file", params={"path": path}, headers=headers)
    return resp

def save_config_file(token, path, content):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"path": path, "content": content}
    resp = requests.post(f"{API_BASE}/admin/config/file", json=payload, headers=headers)
    return resp

# ---------- Загрузка списка параметров для автоподстановки ----------
@st.cache_data(ttl=3600)
def load_parameter_list():
    """Загружает все известные параметры из aliases.yaml (канонические и синонимы)"""
    try:
        import yaml
        aliases_path = os.path.join("knowledge", "laboratory", "aliases.yaml")
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
        return []

# ---------- Инициализация сессии ----------
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Анализ"
if "last_payload" not in st.session_state:
    st.session_state.last_payload = None
if "parameters_list" not in st.session_state:
    st.session_state.parameters_list = load_parameter_list()
if "added_params" not in st.session_state:
    st.session_state.added_params = []  # список кортежей (name, value, unit)
# --- Добавлена инициализация patient_id ---
if "patient_id" not in st.session_state:
    st.session_state.patient_id = "P001"

# ---------- Аутентификация ----------
if not st.session_state.token:
    st.sidebar.markdown("### 🔐 Вход")
    username = st.sidebar.text_input("Логин")
    password = st.sidebar.text_input("Пароль", type="password")
    if st.sidebar.button("Войти"):
        token = get_token(username, password)
        if token:
            try:
               payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
               role = payload.get("role", "user")
            except jwt.InvalidTokenError:
               role = "user"
            st.session_state.token = token
            st.session_state.username = username
            st.session_state.role = role
            st.rerun()
        else:
            st.sidebar.error("Неверные логин/пароль")
    st.stop()
else:
    st.sidebar.markdown(f"✅ Вы вошли как **{st.session_state.username}** (роль: {st.session_state.role})")
    if st.sidebar.button("Выйти"):
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.analysis_result = None
        st.session_state.last_payload = None
        st.rerun()

# ---------- Навигация ----------
page = st.sidebar.radio("Выберите раздел", ["Анализ", "Администрирование"])
st.session_state.current_page = page

# =====================================================
# СТРАНИЦА АНАЛИЗА
# =====================================================
if page == "Анализ":
    st.title("🧪 Система интерпретации лабораторных данных")
    st.markdown("Введите данные пациента и лабораторные показатели для получения клинического заключения.")

    with st.sidebar:
        st.header("🧑‍⚕️ Данные пациента")
        patient_id = st.text_input("ID пациента", value=st.session_state.patient_id)
        gender = st.selectbox("Пол", ["male", "female", "other"])
        age = st.number_input("Возраст", min_value=0, max_value=150, value=45)
        complaints = st.text_area("Жалобы (через запятую)", value="fatigue, weakness")
        medications = st.text_area("Принимаемые лекарства (через запятую)", value="")

        st.markdown("---")
        st.markdown("### 📋 Добавить лабораторный параметр")

        param_options = st.session_state.parameters_list
        param_name = st.selectbox(
            "Параметр",
            options=param_options,
            format_func=lambda x: x,
            placeholder="Начните вводить название...",
            key="param_select"
        )

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

    # ---- Основная область ----
    with st.expander("📝 Сформированный текст для анализа", expanded=False):
        st.code(st.session_state.raw_text or "(пусто)", language="text")

    # ---- Логика анализа ----
    if analyze_btn:
        if not st.session_state.raw_text.strip():
            st.error("Пожалуйста, добавьте хотя бы один лабораторный параметр.")
            st.stop()

        payload = {
            "patient": {
                "id": patient_id,
                "gender": gender,
                "age": age,
                "complaints": [c.strip() for c in complaints.split(",") if c.strip()],
                "medications": [m.strip() for m in medications.split(",") if m.strip()]
            },
            "raw_text": st.session_state.raw_text
        }

        try:
            with st.spinner("Выполняется анализ..."):
                response = analyze_data(payload, st.session_state.token)
            if response.status_code == 200:
                data = response.json()
                st.session_state.analysis_result = data
                st.session_state.last_payload = payload
                # --- Сохраняем patient_id в session_state ---
                st.session_state.patient_id = patient_id
                st.success("✅ Анализ завершён")

                with st.expander("📦 Отладочная информация (запрос и ответ)", expanded=False):
                    st.markdown("**Отправленный текст (raw_text):**")
                    st.code(repr(st.session_state.raw_text), language="text")
                    st.markdown("**Payload (JSON):**")
                    st.json(payload)
                    st.markdown("**Ответ API:**")
                    st.json(data)

                risk_level = data.get("overall_risk_level", "Неизвестно")
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

                diagnoses = data.get("diagnoses", [])
                if diagnoses:
                    st.markdown("### 📌 Выявленные состояния")
                    for d in diagnoses:
                        label = d.get("label", d.get("id", "Неизвестно"))
                        risk = d.get("risk", "Норма")
                        combined = d.get("combined", False)
                        desc = d.get("description")
                        card_color = color_map.get(risk, "gray")
                        with st.container():
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

                grouped = data.get("grouped_findings", {})
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

                recommendations = data.get("recommendations_by_specialty", {})
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

                insights = data.get("clinical_insights", {})
                if insights:
                    st.markdown("### 🧠 Клинические инсайты (подробная интерпретация)")
                    for diag_id, insight in insights.items():
                        label = insight.get("label", diag_id)
                        with st.expander(f"**{label}** (ID: {diag_id})"):
                            criteria = insight.get("criteria", [])
                            if criteria:
                                st.markdown("#### 📊 Критерии диагноза")
                                df_criteria = pd.DataFrame([
                                    {
                                        "Параметр": c.get("parameter", ""),
                                        "Значение": c.get("value", ""),
                                        "Норма": f"{c.get('threshold', '')} ({c.get('condition', '')})",
                                        "Комментарий": c.get("comment", "")
                                    }
                                    for c in criteria
                                ])
                                st.dataframe(df_criteria, use_container_width=True, hide_index=True)
                            differentials = insight.get("differentials", [])
                            if differentials:
                                st.markdown("#### 🔍 Дифференциальная диагностика")
                                for diff in differentials:
                                    st.markdown(f"- **Условие:** `{diff.get('condition', '')}` → {diff.get('text', '')}")
                            red_flags = insight.get("red_flags", [])
                            if red_flags:
                                st.markdown("#### ⚠️ Красные флаги")
                                for rf in red_flags:
                                    st.markdown(f"- **{rf.get('condition', '')}** → {rf.get('text', '')}")
                            treatment_hints = insight.get("treatment_hints", [])
                            if treatment_hints:
                                st.markdown("#### 💊 Советы по тактике")
                                for hint in treatment_hints:
                                    st.markdown(f"- **{hint.get('step', '')}** — {hint.get('note', '')}")
                            references = insight.get("references", [])
                            if references:
                                st.markdown("#### 📚 Ссылки")
                                for ref in references:
                                    st.markdown(f"- {ref}")
                else:
                    st.info("Для выявленных диагнозов нет дополнительных клинических инсайтов.")

                conclusion = data.get("conclusion", "")
                if conclusion:
                    with st.expander("📄 Полное текстовое заключение "):
                        lines = conclusion.split("\n")
                        filtered = []
                        skip = False
                        for line in lines:
                            if "▶ Рекомендации по дополнительному обследованию:" in line:
                                skip = True
                                continue
                            if not skip:
                                filtered.append(line)
                        st.text("\n".join(filtered).strip())

            elif response.status_code == 401:
                st.error("❌ Сессия истекла. Войдите заново.")
                st.session_state.token = None
                st.rerun()
            else:
                st.error(f"Ошибка API: {response.status_code}")
                st.json(response.text)
        except Exception as e:
            st.error(f"❌ Ошибка: {e}")

    # ----- PDF -----
    if st.session_state.last_payload is not None and st.session_state.token is not None:
        st.markdown("---")
        if st.button("📄 Скачать PDF", use_container_width=True):
            with st.spinner("Генерация PDF..."):
                pdf_resp = generate_pdf(st.session_state.last_payload, st.session_state.token)
                if pdf_resp.status_code == 200:
                    st.download_button(
                        label="💾 Сохранить PDF",
                        data=pdf_resp.content,
                        file_name=f"report_{st.session_state.patient_id}.pdf",
                        mime="application/pdf"
                    )
                    st.success("PDF готов! Кнопка сохранения ниже.")
                elif pdf_resp.status_code == 401:
                    st.error("❌ Сессия истекла. Войдите заново.")
                    st.session_state.token = None
                    st.rerun()
                else:
                    st.error(f"Ошибка генерации PDF: {pdf_resp.status_code}")
                    st.json(pdf_resp.text)

# =====================================================
# СТРАНИЦА АДМИНИСТРИРОВАНИЯ (без изменений)
# =====================================================
elif page == "Администрирование":
    st.title("🛠️ Администрирование системы")
    if st.session_state.role != "admin":
        st.error("У вас нет прав администратора.")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["👤 Пользователи", "📜 История", "⚙️ Правила"])

    with tab1:
        st.subheader("Управление пользователями")
        if st.button("Обновить список"):
            st.rerun()

        resp = get_users(st.session_state.token)
        if resp.status_code == 200:
            users = resp.json()
            for u in users:
                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                with col1:
                    st.write(u["id"])
                with col2:
                    st.write(u["username"])
                with col3:
                    st.write(u["role"])
                with col4:
                    if u["username"] not in ("admin", "doctor"):
                        if st.button(f"Удалить {u['id']}", key=f"del_{u['id']}"):
                            del_resp = delete_user(st.session_state.token, u["id"])
                            if del_resp.status_code == 200:
                                st.success(f"Пользователь {u['username']} удалён")
                                st.rerun()
                            else:
                                st.error(f"Ошибка: {del_resp.text}")
        else:
            st.error(f"Ошибка загрузки пользователей: {resp.text}")

        st.markdown("---")
        st.subheader("Добавить нового пользователя")
        with st.form("register_form"):
            new_username = st.text_input("Логин")
            new_password = st.text_input("Пароль", type="password")
            new_role = st.selectbox("Роль", ["user", "admin", "doctor"])
            submitted = st.form_submit_button("Создать")
            if submitted:
                if new_username and new_password:
                    reg_resp = register_user(st.session_state.token, new_username, new_password, new_role)
                    if reg_resp.status_code == 200:
                        st.success(f"Пользователь {new_username} создан")
                        st.rerun()
                    else:
                        st.error(f"Ошибка: {reg_resp.text}")
                else:
                    st.warning("Заполните все поля")

        if st.button("Перезагрузить конфигурацию (правила)"):
            with st.spinner("Перезагрузка..."):
                reload_resp = reload_config(st.session_state.token)
                if reload_resp.status_code == 200:
                    st.success("Конфигурация перезагружена")
                else:
                    st.error(f"Ошибка: {reload_resp.text}")

    with tab2:
        st.subheader("Просмотр истории пациента")
        history_patient_id = st.text_input("ID пациента", value="P001")
        if st.button("Показать историю"):
            if history_patient_id:
                with st.spinner("Загрузка..."):
                    hist_resp = get_history(st.session_state.token, history_patient_id)
                    if hist_resp.status_code == 200:
                        data = hist_resp.json()
                        st.json(data)
                    else:
                        st.error(f"Ошибка: {hist_resp.text}")

    with tab3:
        st.subheader("Редактирование конфигурационных файлов")
        config_path = st.text_input("Путь к файлу (относительно knowledge/)", value="configs/clinical_thresholds.yaml")
        if st.button("Загрузить файл"):
            with st.spinner("Загрузка..."):
                file_resp = get_config_file(st.session_state.token, config_path)
                if file_resp.status_code == 200:
                    file_data = file_resp.json()
                    st.session_state.current_config_content = file_data["content"]
                    st.session_state.current_config_path = file_data["path"]
                    st.success(f"Файл {file_data['path']} загружен")
                else:
                    st.error(f"Ошибка: {file_resp.text}")

        if "current_config_content" in st.session_state:
            new_content = st.text_area("Содержимое файла", value=st.session_state.current_config_content, height=400)
            if st.button("Сохранить файл"):
                save_resp = save_config_file(
                    st.session_state.token,
                    st.session_state.current_config_path,
                    new_content
                )
                if save_resp.status_code == 200:
                    st.success("Файл сохранён")
                    st.session_state.current_config_content = new_content
                    if st.button("Перезагрузить правила после сохранения"):
                        reload_resp = reload_config(st.session_state.token)
                        if reload_resp.status_code == 200:
                            st.success("Конфигурация перезагружена")
                        else:
                            st.error(f"Ошибка перезагрузки: {reload_resp.text}")
                else:
                    st.error(f"Ошибка сохранения: {save_resp.text}")

st.markdown("---")
st.caption("Система интерпретации лабораторных данных v1.0 | API: localhost:8000")