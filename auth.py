"""
auth.py
Módulo de autenticación: soporta login personalizado (bcrypt) y Microsoft Entra ID (OAuth2).
"""

import streamlit as st
import jwt
from streamlit_oauth import OAuth2Component

from database import (
    get_user,
    create_user,
    migrate_secrets_users,
    log_event,
    verify_password,
)
from permissions import get_user_role


def _init_session(user_email: str, user_name: str, source: str):
    user_email = user_email.lower()
    migrate_secrets_users(st.secrets.get("users", {}))

    user = get_user(user_email)
    if not user:
        role = get_user_role(user_email) or "reader"
        create_user(user_email, "entra-id-no-local", role, name=user_name)
        user = get_user(user_email)

    st.session_state["user"] = user_email
    st.session_state["name"] = user.get("name", user_name)
    st.session_state["role"] = user.get("role", "reader")
    st.session_state["source"] = source
    log_event(user_email, "login", f"source={source}")
    st.rerun()


def login_custom():
    """Login con credenciales locales usando hashes bcrypt en users.json."""
    st.subheader("Login personalizado")
    email = st.text_input("Correo corporativo", key="custom_email")
    password = st.text_input("Contraseña", type="password", key="custom_password")

    if st.button("Iniciar sesión", key="custom_login"):
        migrate_secrets_users(st.secrets.get("users", {}))
        user = get_user(email.lower())
        if not user:
            st.error("Usuario no encontrado.")
            log_event(email.lower(), "login_failed", "user_not_found")
            return

        if not verify_password(password, user.get("password_hash", "")):
            st.error("Contraseña incorrecta.")
            log_event(email.lower(), "login_failed", "bad_password")
            return

        _init_session(email, user.get("name", email), "custom")


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
    email = st.session_state.get("user", "")
    if email:
        log_event(email, "logout", "")
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
