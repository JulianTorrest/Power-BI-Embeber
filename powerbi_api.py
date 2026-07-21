"""
powerbi_api.py
Esqueleto para obtener Embed Tokens y URLs seguras desde la API REST de Power BI.
Requiere un Service Principal configurado en Azure/Entra ID con permisos sobre el
workspace de Power BI y capacidad Premium para exportaciones.
"""

import requests


def _powerbi_token_url(tenant_id: str) -> str:
    return f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"


def get_powerbi_access_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    """Obtiene access token de Microsoft para el servicio de Power BI."""
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://analysis.windows.net/powerbi/api/.default",
    }
    r = requests.post(_powerbi_token_url(tenant_id), data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def generate_embed_url(workspace_id: str, report_id: str, tenant_id: str, client_id: str, client_secret: str):
    """
    Retorna embedUrl y embedToken para un reporte vía REST API.
    """
    token = get_powerbi_access_token(tenant_id, client_id, client_secret)

    # Embed token
    embed_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/GenerateToken"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"accessLevel": "View"}
    r = requests.post(embed_url, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    embed_token = r.json().get("token")

    # Report metadata
    meta_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
    r2 = requests.get(meta_url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    r2.raise_for_status()
    embed_url_value = r2.json().get("embedUrl")

    return {"embed_url": embed_url_value, "embed_token": embed_token, "report_id": report_id}


def export_report(report_id: str, workspace_id: str, tenant_id: str, client_id: str, client_secret: str, fmt: str = "PDF"):
    """
    Placeholder para exportar un reporte. Power BI requiere capacidad Premium y
    manejo asíncrono del trabajo de exportación.
    """
    return {
        "status": "not_implemented",
        "message": (
            f"Exportar a {fmt} requiere capacidad Premium y un flujo asíncrono "
            "(POST /v1.0/myorg/groups/{workspaceId}/reports/{reportId}/Export/To)."
        ),
    }
