"""
app.py
Aplicación Streamlit para embeber tableros de Power BI con autenticación
(Entra ID / Microsoft y login personalizado) y control de permisos.
"""

import streamlit as st
import streamlit.components.v1 as components
from auth import check_auth, login_custom, login_entra_id, logout, current_user
from permissions import get_allowed_dashboards, can_manage
from database import (
    add_dashboard_view,
    toggle_favorite,
    get_favorites,
    get_history,
    update_user,
    get_user,
    get_announcements,
    add_announcement,
    get_audit_log,
    get_analytics,
)
from powerbi_api import generate_embed_url, export_report


st.set_page_config(page_title="Power BI Portal", layout="wide")


def show_login():
    """Muestra las opciones de inicio de sesión."""
    st.title("Portal de Tableros Power BI")

    tab1, tab2 = st.tabs(["Entra ID / Microsoft", "Login personalizado"])

    with tab1:
        login_entra_id()

    with tab2:
        login_custom()

    with st.expander("¿Cómo funciona el flujo?"):
        st.markdown(
            """
            1. El usuario elige iniciar sesión con Microsoft Entra ID o credenciales locales.
            2. La app valida la identidad y obtiene el correo corporativo.
            3. Se consulta una matriz de permisos (email / rol) para saber qué tableros puede ver.
            4. El menú lateral muestra únicamente los tableros autorizados.
            5. Al seleccionar uno, se renderiza dentro de un `iframe` usando la URL del tablero.
            """
        )


def embed_powerbi(url: str, height: int = 800):
    """Renderiza un reporte/dashboard de Power BI dentro de un iframe."""
    components.html(
        f"""
        <iframe
            title="Power BI Dashboard"
            width="100%"
            height="{height}"
            src="{url}"
            frameborder="0"
            allowFullScreen="true">
        </iframe>
        """,
        height=height,
        scrolling=False,
    )


def project_info_tab():
    """Muestra la información general del proyecto y el asistente con LLM."""

    st.header("Información del Proyecto")

    st.subheader("¿Qué hace?")
    st.markdown(
        """
        Esta aplicación es un **portal corporativo de tableros de Power BI** con autenticación y permisos por rol.
        Además del embebido de dashboards, incluye un **asistente virtual con LLM** para responder preguntas sobre
        el proyecto, la arquitectura y, en futuras versiones, sobre los datos de los tableros.
        """
    )

    st.subheader("¿Cómo lo vamos a hacer?")
    st.markdown(
        """
        1. **Autenticación**: Microsoft Entra ID y login personalizado con `bcrypt`.
        2. **Permisos**: matriz de permisos en `secrets.toml` por email y rol.
        3. **Renderizado**: pestañas con `iframe` de Power BI, búsqueda, favoritos e historial.
        4. **Inteligencia**: asistente conversacional con LLM integrado en la pestaña de información.
        5. **Administración**: panel de control con analytics, auditoría y anuncios.
        6. **Seguridad**: credenciales y tokens almacenados en Secrets de Streamlit Cloud.
        """
    )

    st.subheader("Estrategia")
    st.markdown(
        """
        - **Centralización**: portal único para todos los dashboards.
        - **Control de acceso granular**: por correo y rol.
        - **Experiencia conversacional**: asistente LLM para reducir curva de aprendizaje.
        - **Escalabilidad**: nuevos tableros y usuarios se configuran en `secrets.toml` sin tocar código.
        - **Extensibilidad**: el chat puede evolucionar para consultar datasets vía DAX, SQL o APIs.
        """
    )

    st.subheader("Arquitectura")
    st.markdown(
        """
        ```
                    Usuario / Navegador
                            │
                            ▼
                  ┌─────────────────────┐
                  │   Streamlit Cloud   │
                  │  - Auth / Permisos  │
                  │  - Tabs / iFrames   │
                  │  - Chat LLM         │
                  └─────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
      Microsoft           Power BI            OpenAI /
      Entra ID           (URLs/embed)         LLM API
      (OAuth2)                               (Chat)
        """
    )

    st.subheader("Componentes del repositorio")
    st.markdown(
        """
        - `app.py`: interfaz de Streamlit, pestañas, embebido de Power BI y chat.
        - `auth.py`: autenticación con `bcrypt` y Microsoft Entra ID.
        - `permissions.py`: permisos y roles jerárquicos.
        - `database.py`: persistencia JSON local.
        - `powerbi_api.py`: esqueleto Power BI REST API + Embed Token.
        - `requirements.txt`: dependencias incluyendo `openai`.
        - `.streamlit/secrets.toml`: credenciales, APIs y tableros/permisos.
        """
    )

    # Asistente virtual
    st.divider()
    st.subheader("Asistente Virtual")
    _render_llm_chat()


def _render_llm_chat():
    """Renderiza un chat con OpenAI dentro de la pestaña de información."""
    openai_config = st.secrets.get("openai", {})
    api_key = openai_config.get("api_key", "")
    model = openai_config.get("model", "gpt-3.5-turbo")

    if not api_key or api_key == "TU_OPENAI_API_KEY":
        st.warning("Falta configurar `openai.api_key` en secrets.toml.")
        return

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": "Hola, soy el asistente del portal. ¿Qué te gustaría saber sobre el proyecto o los tableros de Power BI?",
            }
        ]

    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Escribe tu pregunta...")
    if prompt:
        st.session_state["chat_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            import openai

            client = openai.OpenAI(api_key=api_key)
            messages = [
                {
                    "role": "system",
                    "content": "Eres un asistente útil del portal corporativo de Power BI. Responde de forma clara y concisa sobre el proyecto, la arquitectura y los tableros.",
                }
            ] + st.session_state["chat_messages"]
            response = client.chat.completions.create(model=model, messages=messages)
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"Error al contactar el LLM: {e}"

        st.session_state["chat_messages"].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)


def show_announcements(role: str):
    """Muestra anuncios activos visibles para el rol del usuario."""
    for a in get_announcements():
        if a.get("active") and role in a.get("roles", []):
            st.info(f"**{a['title']}**: {a['message']}")


def render_dashboards_tab(user: dict, allowed: list):
    """Buscador, selector, favoritos, embebido y exportación de tableros."""
    search = st.text_input(
        "Buscar tablero", placeholder="Escribe el nombre...", key="search_dashboard"
    )
    term = search.lower()
    filtered = [
        d
        for d in allowed
        if term in d["nombre"].lower() or term in d.get("categoria", "").lower()
    ]
    if not filtered:
        st.warning("No se encontraron tableros con ese criterio.")
        return

    selected = st.selectbox(
        "Selecciona un tablero:",
        options=filtered,
        format_func=lambda x: x["nombre"],
        key="selected_dashboard",
    )

    # Favoritos
    favs = get_favorites(user["email"])
    is_fav = any(f["id"] == selected["id"] for f in favs)
    fav_label = "⭐ Quitar de favoritos" if is_fav else "⭐ Agregar a favoritos"
    if st.button(fav_label, key="fav_btn"):
        toggle_favorite(user["email"], selected["id"], selected["nombre"])
        st.rerun()

    # Modo de embebido
    embed_mode = st.radio(
        "Modo de embebido",
        ["URL / iFrame", "Power BI REST API + Embed Token"],
        key="embed_mode",
    )

    embed_url = selected["url"]
    if embed_mode == "Power BI REST API + Embed Token":
        entra = st.secrets.get("entra", {})
        powerbi = st.secrets.get("powerbi", {})
        workspace_id = powerbi.get("workspace_id", "")
        if st.button("Generar embed token"):
            result = generate_embed_url(
                selected["id"],
                workspace_id,
                entra.get("tenant_id", ""),
                entra.get("client_id", ""),
                entra.get("client_secret", ""),
            )
            if "error" in result:
                st.error(result["error"])
            else:
                embed_url = result["embed_url"]
                st.session_state["embed_token"] = result["embed_token"]
                st.success("Embed token generado correctamente.")

    # Registro de vista
    add_dashboard_view(user["email"], selected["id"], selected["nombre"])

    # Exportar
    col_export, _ = st.columns([1, 5])
    with col_export:
        if st.button("Exportar reporte"):
            entra = st.secrets.get("entra", {})
            powerbi = st.secrets.get("powerbi", {})
            st.json(
                export_report(
                    selected["id"],
                    powerbi.get("workspace_id", ""),
                    entra.get("tenant_id", ""),
                    entra.get("client_id", ""),
                    entra.get("client_secret", ""),
                )
            )

    st.title(selected["nombre"])
    if "embed_token" in st.session_state:
        st.caption(f"Embed token: {st.session_state['embed_token'][:20]}...")
    st.caption(f"URL embebida: {embed_url}")
    embed_powerbi(embed_url)


def render_favorites_history(user: dict):
    """Muestra favoritos e historial reciente del usuario."""
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Favoritos")
        favs = get_favorites(user["email"])
        if not favs:
            st.info("No tienes tableros favoritos.")
        else:
            for f in favs:
                st.write(f"- {f['name']}")
    with c2:
        st.subheader("Historial reciente")
        history = get_history(user["email"])
        if not history:
            st.info("Aún no has visto tableros.")
        else:
            for h in history[:10]:
                st.write(f"- {h['name']} — _{h['timestamp']}_")


def render_profile(user: dict):
    """Permite al usuario editar su nombre y preferencias."""
    user_db = get_user(user["email"])
    if not user_db:
        st.warning("Perfil no encontrado.")
        return

    st.subheader("Editar perfil")
    new_name = st.text_input(
        "Nombre", value=user_db.get("name", user["email"]), key="profile_name"
    )
    prefs = user_db.get("preferences", {})
    theme = st.selectbox(
        "Tema",
        ["light", "dark"],
        index=["light", "dark"].index(prefs.get("theme", "light")),
        key="profile_theme",
    )
    language = st.selectbox(
        "Idioma",
        ["es", "en"],
        index=["es", "en"].index(prefs.get("language", "es")),
        key="profile_lang",
    )

    if st.button("Guardar perfil", key="save_profile"):
        prefs.update({"theme": theme, "language": language})
        update_user(user["email"], name=new_name, preferences=prefs)
        st.session_state["name"] = new_name
        st.success("Perfil actualizado.")
        st.rerun()


def render_admin(user: dict):
    """Panel de administración: analytics, auditoría y anuncios."""
    if not can_manage(user["role"]):
        st.warning("No tienes permisos de administrador.")
        return

    st.subheader("Panel de administración")

    st.write("### Vistas por tablero")
    analytics = get_analytics()
    if analytics.get("views"):
        for dashboard_id, count in analytics["views"].items():
            st.write(f"- **{dashboard_id}**: {count} vistas")
    else:
        st.info("Sin datos de analytics aún.")

    st.write("### Últimos eventos de auditoría")
    log = get_audit_log()[-20:]
    if log:
        st.table(log)
    else:
        st.info("Sin eventos registrados.")

    st.write("### Crear anuncio")
    title = st.text_input("Título", key="ann_title")
    message = st.text_area("Mensaje", key="ann_message")
    roles = st.multiselect(
        "Visible para roles",
        ["admin", "editor", "reader"],
        default=["reader"],
        key="ann_roles",
    )
    if st.button("Publicar anuncio", key="publish_ann"):
        add_announcement(title, message, roles)
        st.success("Anuncio publicado.")


def show_dashboards():
    """Página principal con pestañas y renderizado condicional de tableros."""
    user = current_user()
    email = user["email"]
    role = user["role"]

    allowed = get_allowed_dashboards(email, role)

    with st.sidebar:
        show_announcements(role)
        st.header("Usuario")
        st.write(f"**Nombre:** {user['name']}")
        st.write(f"**Email:** {email}")
        st.write(f"**Rol:** {role}")
        st.divider()
        if st.button("Cerrar sesión"):
            logout()

    (
        tableros_tab,
        fav_hist_tab,
        perfil_tab,
        admin_tab,
        info_tab,
    ) = st.tabs(
        [
            "Tableros",
            "Favoritos / Historial",
            "Perfil",
            "Administración",
            "Información del Proyecto",
        ]
    )

    with tableros_tab:
        if not allowed:
            st.warning("No tienes tableros asignados.")
        else:
            render_dashboards_tab(user, allowed)

    with fav_hist_tab:
        render_favorites_history(user)

    with perfil_tab:
        render_profile(user)

    with admin_tab:
        render_admin(user)

    with info_tab:
        project_info_tab()


def main():
    if not check_auth():
        show_login()
    else:
        show_dashboards()


if __name__ == "__main__":
    main()
