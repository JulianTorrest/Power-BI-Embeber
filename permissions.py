"""
permissions.py
Lógica de permisos: determina qué tableros Power BI puede ver cada usuario.
El mapeo se lee desde st.secrets (tableros) y soporta asignación por email o por rol.
"""

import streamlit as st
from typing import Dict, List


def get_user_role(email: str) -> str:
    """Obtiene el rol asociado a un email desde la sección [users] de secrets.toml."""
    user_entry = st.secrets.get("users", {}).get(email.lower(), "")
    if not user_entry:
        return ""
    parts = str(user_entry).split(",")
    return parts[1].strip() if len(parts) > 1 else ""


def get_allowed_dashboards(email: str, role: str) -> List[Dict]:
    """
    Retorna la lista de tableros que el usuario tiene permitido visualizar.
    Un tablero es visible si el email está en la lista de usuarios o el rol está en la lista de roles.
    """
    all_dashboards = st.secrets.get("tableros", [])
    allowed = []
    email_lower = email.lower()

    for d in all_dashboards:
        user_match = email_lower in [u.lower() for u in d.get("usuarios", [])]
        role_match = role in d.get("roles", [])
        if user_match or role_match:
            allowed.append(d)

    return allowed


def has_access(email: str, role: str, dashboard_id: str) -> bool:
    """Verifica si un usuario tiene acceso a un tablero específico."""
    return any(d["id"] == dashboard_id for d in get_allowed_dashboards(email, role))
