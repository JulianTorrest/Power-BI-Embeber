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


def show_dashboards():
    """Página principal con menú lateral y renderizado condicional de tableros."""
    user = current_user()
    email = user["email"]
    role = user["role"]

    allowed = get_allowed_dashboards(email, role)

    with st.sidebar:
        st.header("Menú")
        st.write(f"**Usuario:** {user['name']}")
        st.write(f"**Email:** {email}")
        st.write(f"**Rol:** {role or 'sin rol'} ({user['source']})")

        st.divider()

        if not allowed:
            st.warning("No tienes tableros asignados.")
            selected_id = None
        else:
            selected = st.radio(
                "Selecciona un tablero:",
                options=allowed,
                format_func=lambda x: x["nombre"],
                key="selected_dashboard",
            )
            selected_id = selected["id"]
            selected_url = selected["url"]

        st.divider()
        if st.button("Cerrar sesión"):
            logout()

    if selected_id:
        st.title(selected["nombre"])
        st.caption(f"URL embebida: {selected_url}")
        embed_powerbi(selected_url)
    else:
        st.info("Selecciona un tablero desde el menú lateral para comenzar.")


def main():
    if not check_auth():
        show_login()
    else:
        show_dashboards()


if __name__ == "__main__":
    main()
