"""
app.py
Aplicación Streamlit para embeber tableros de Power BI con autenticación
(Entra ID / Microsoft y login personalizado) y control de permisos.
"""

import streamlit as st
import streamlit.components.v1 as components
from auth import check_auth, login_custom, login_entra_id, logout, current_user
from permissions import get_allowed_dashboards


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
    """Muestra la información general del proyecto en una sola pestaña."""

    st.header("Información del Proyecto")

    st.subheader("¿Qué hace?")
    st.markdown(
        """
        Esta aplicación es un **portal corporativo de tableros de Power BI** ejecutado en Streamlit Cloud.
        Permite a los usuarios autenticarse con Microsoft Entra ID o credenciales locales, y acceder únicamente
        a los reportes/dashboards de Power BI que les hayan sido asignados por correo o rol.
        """
    )

    st.subheader("¿Cómo lo vamos a hacer?")
    st.markdown(
        """
        1. **Autenticación**: se integra Microsoft Entra ID (OAuth2) y un login personalizado como respaldo.
        2. **Identificación**: se obtiene el email corporativo del usuario que inicia sesión.
        3. **Permisos**: se consulta una matriz de permisos en `secrets.toml` para saber qué tableros puede ver cada usuario/rol.
        4. **Renderizado**: se muestran pestañas con los tableros disponibles y se embebe cada uno mediante un `iframe` usando la URL de Power BI.
        5. **Seguridad**: todo el manejo de credenciales, tokens y URLs queda fuera del código, almacenado en los Secrets de Streamlit Cloud.
        """
    )

    st.subheader("Estrategia")
    st.markdown(
        """
        - **Centralización**: un único punto de acceso web para todos los dashboards de la organización.
        - **Control de acceso granular**: asignación de reportes por correo electrónico o rol (admin, analista, etc.).
        - **Experiencia unificada**: pestañas limpias que separan los tableros de la documentación del proyecto.
        - **Escalabilidad**: agregar nuevos tableros o usuarios es solo editar `secrets.toml` sin modificar código.
        """
    )

    st.subheader("Arquitectura")
    st.markdown(
        """
        ```
        ┌─────────────────────────────────┐
        │        Usuario / Navegador       │
        └──────────────┬──────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────┐
        │      Streamlit Cloud (app.py)    │
        │  - Auth (Entra ID / custom)     │
        │  - Permisos (email/rol)         │
        │  - Tabs + iframe Power BI       │
        └──────────────┬──────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
        Microsoft                Power BI
        Entra ID                 (URLs/embed)
        (OAuth2)                 (tableros)
        """
    )

    st.subheader("Componentes del repositorio")
    st.markdown(
        """
        - `app.py`: interfaz de Streamlit, pestañas y embebido de Power BI.
        - `auth.py`: lógica de login con Microsoft Entra ID y credenciales locales.
        - `permissions.py`: evaluación de qué tableros corresponden a cada usuario/rol.
        - `.streamlit/secrets.toml`: credenciales, configuración de Entra ID y lista de tableros/permisos.
        - `requirements.txt`: librerías necesarias para Streamlit Cloud.
        """
    )


def show_dashboards():
    """Página principal con pestañas y renderizado condicional de tableros."""
    user = current_user()
    email = user["email"]
    role = user["role"]

    allowed = get_allowed_dashboards(email, role)

    with st.sidebar:
        st.header("Usuario")
        st.write(f"**Nombre:** {user['name']}")
        st.write(f"**Email:** {email}")
        st.write(f"**Rol:** {role or 'sin rol'} ({user['source']})")
        st.divider()
        if st.button("Cerrar sesión"):
            logout()

    tableros_tab, info_tab = st.tabs(["Tableros", "Información del Proyecto"])

    with tableros_tab:
        if not allowed:
            st.warning("No tienes tableros asignados.")
        else:
            selected = st.selectbox(
                "Selecciona un tablero:",
                options=allowed,
                format_func=lambda x: x["nombre"],
                key="selected_dashboard",
            )
            st.title(selected["nombre"])
            st.caption(f"URL embebida: {selected['url']}")
            embed_powerbi(selected["url"])

    with info_tab:
        project_info_tab()


def main():
    if not check_auth():
        show_login()
    else:
        show_dashboards()


if __name__ == "__main__":
    main()
