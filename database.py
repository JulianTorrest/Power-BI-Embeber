"""
database.py
Persistencia local en JSON para usuarios, auditoría, favoritos, historial,
perfiles, anuncios y analytics.
Nota: en Streamlit Cloud el filesystem es efímero; para producción usar una
base de datos externa (Supabase, PostgreSQL, S3, etc.).
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import bcrypt
import streamlit as st

DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _path(name: str) -> Path:
    return DATA_DIR / name


def _load(name: str, default: Any = None) -> Any:
    path = _path(name)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save(name: str, data: Any):
    _path(name).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


# --- Password hashing --------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    if not hashed or not password:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# --- Users -------------------------------------------------------------------

def get_users() -> Dict[str, Dict]:
    return _load("users.json", {})


def get_user(email: str) -> Optional[Dict]:
    return get_users().get(email.lower())


def save_user(email: str, data: Dict):
    users = get_users()
    users[email.lower()] = data
    _save("users.json", users)


def create_user(email: str, password: str, role: str = "reader", name: str = None, preferences: Dict = None):
    email = email.lower()
    if get_user(email):
        return False
    save_user(email, {
        "email": email,
        "name": name or email,
        "role": role,
        "password_hash": hash_password(password),
        "favorites": [],
        "history": [],
        "preferences": preferences or {"theme": "light", "language": "es"},
    })
    return True


def update_user(email: str, **kwargs):
    user = get_user(email) or {}
    user.update(kwargs)
    save_user(email, user)


def migrate_secrets_users(secrets_users: Dict[str, str]):
    """Migra usuarios en texto plano de secrets.toml a users.json con hash."""
    for email, entry in secrets_users.items():
        if get_user(email):
            continue
        parts = str(entry).split(",")
        plain = parts[0].strip()
        role = parts[1].strip() if len(parts) > 1 else "reader"
        create_user(email, plain, role, name=email)


# --- Audit log ---------------------------------------------------------------

def log_event(email: str, event: str, details: str = ""):
    log = _load("audit_log.json", [])
    log.append({
        "timestamp": datetime.now().isoformat(),
        "user": email.lower(),
        "event": event,
        "details": details,
    })
    _save("audit_log.json", log[-5000:])


def get_audit_log() -> List[Dict]:
    return _load("audit_log.json", [])


# --- Favorites & history -----------------------------------------------------

def add_dashboard_view(email: str, dashboard_id: str, dashboard_name: str):
    user = get_user(email) or {}
    history = user.get("history", [])
    history.insert(0, {
        "id": dashboard_id,
        "name": dashboard_name,
        "timestamp": datetime.now().isoformat(),
    })
    user["history"] = history[:20]
    save_user(email, user)
    _increment_dashboard_view(dashboard_id)


def toggle_favorite(email: str, dashboard_id: str, dashboard_name: str):
    user = get_user(email) or {}
    favorites = user.get("favorites", [])
    ids = [f["id"] for f in favorites]
    if dashboard_id in ids:
        favorites = [f for f in favorites if f["id"] != dashboard_id]
    else:
        favorites.insert(0, {"id": dashboard_id, "name": dashboard_name})
    user["favorites"] = favorites
    save_user(email, user)


def get_favorites(email: str) -> List[Dict]:
    user = get_user(email)
    return user.get("favorites", []) if user else []


def get_history(email: str) -> List[Dict]:
    user = get_user(email)
    return user.get("history", []) if user else []


# --- Analytics ---------------------------------------------------------------

def _increment_dashboard_view(dashboard_id: str):
    analytics = _load("analytics.json", {})
    analytics.setdefault("views", {}).setdefault(dashboard_id, 0)
    analytics["views"][dashboard_id] += 1
    _save("analytics.json", analytics)


def get_analytics() -> Dict:
    return _load("analytics.json", {})


# --- Announcements -----------------------------------------------------------

def get_announcements() -> List[Dict]:
    return _load("announcements.json", [])


def add_announcement(title: str, message: str, roles: List[str] = None, active: bool = True):
    anns = get_announcements()
    anns.append({
        "id": len(anns) + 1,
        "title": title,
        "message": message,
        "roles": roles or ["admin", "editor", "reader"],
        "active": active,
        "created": datetime.now().isoformat(),
    })
    _save("announcements.json", anns)
