"""
auth.py
Módulo de autenticación: soporta login personalizado y Microsoft Entra ID (OAuth2).
"""

import streamlit as st
import jwt
import requests
from streamlit_oauth import OAuth2Component
from permissions import get_user_role


def _init_session(user_email: str, user_name: str, source: str):
    st.session_state["user"] = user_email.lower()
    st.session_state["name"] = user_name
    st.session_state["source"] = source
    st.session_state["role"] = get_user_role(user_email)
    st.rerun()


def login_custom():
    """Login con credenciales locales definidas en secrets.toml bajo [users]."""
    st.subheader("Login personalizado")
    email = st.text_input("Correo corporativo", key="custom_email")
    password = st.text_input("Contraseña", type="password", key="custom_password")

    if st.button("Iniciar sesión", key="custom_login"):
        user_entry = st.secrets.get("users", {}).get(email.lower(), "")
        if not user_entry:
            st.error("Usuario no encontrado.")
            return

        parts = str(user_entry).split(",")
        stored_password = parts[0].strip()
        if password == stored_password:
            _init_session(email, email, "custom")
        else:
            st.error("Contraseña incorrecta.")


def login_entra_id():
    """Login con Microsoft Entra ID usando streamlit-oauth."""
    st.subheader("Iniciar sesión con Microsoft")

    entra = st.secrets.get("entra", {})
    tenant_id = entra.get("tenant_id", "")
    client_id = entra.get("client_id", "")
    client_secret = entra.get("client_secret", "")
    redirect_uri = entra.get("redirect_uri", "")

    if not all([tenant_id, client_id, client_secret, redirect_uri]):
        st.warning("Falta configurar Microsoft Entra ID en secrets.toml.")
        return

    authorize_endpoint = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
    token_endpoint = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    oauth2 = OAuth2Component(
        client_id=client_id,
        client_secret=client_secret,
        authorize_endpoint=authorize_endpoint,
        token_endpoint=token_endpoint,
    )

    result = oauth2.authorize_button(
        name="Continuar con Microsoft",
        redirect_uri=redirect_uri,
        scope="openid email profile User.Read",
        extras_params={"response_type": "code"},
    )

    if result:
        # El token JWT de Microsoft puede venir como id_token o access_token
        token = result.get("id_token") or result.get("access_token", "")
        if token:
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                email = payload.get("preferred_username") or payload.get("email") or payload.get("upn")
                name = payload.get("name") or email
                if email:
                    _init_session(email, name, "entra")
                else:
                    st.error("No se pudo obtener el correo del token de Microsoft.")
            except Exception as e:
                st.error(f"Error al decodificar el token: {e}")
        else:
            st.error("No se recibió token de Microsoft.")


def logout():
    """Cierra la sesión del usuario."""
    for key in ["user", "name", "source", "role"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def check_auth() -> bool:
    """Retorna True si el usuario ya inició sesión."""
    return "user" in st.session_state


def current_user() -> dict:
    """Retorna un diccionario con la información del usuario autenticado."""
    return {
        "email": st.session_state.get("user", ""),
        "name": st.session_state.get("name", ""),
        "role": st.session_state.get("role", ""),
        "source": st.session_state.get("source", ""),
    }
