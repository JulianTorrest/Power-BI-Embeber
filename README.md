# Portal Power BI con Streamlit + Microsoft Entra ID

Aplicación **Streamlit** desplegable en **Streamlit Cloud** que permite embeber tableros de **Power BI** y controlar el acceso por correo/rol mediante autenticación personalizada y/o Microsoft Entra ID (Azure AD).

## Flujo conceptual

```
┌──────────────────────────────┐
│   Usuario entra a Streamlit  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────────┐
│   Autenticación con Entra ID     │
│ (Retorna el Email / Rol del User)│
└────────────────┬─────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│   Lógica de Permisos (Mapeo/Tabla) │
│  ¿Qué tableros tiene asignados?    │
└─────────────────┬──────────────────┘
               │
   ┌─────────────┴─────────────┐
   ▼                           ▼
┌─────────────────┐   ┌─────────────────┐
│ Tablero A       │   │ Tablero B       │
│  (iFrame)       │   │  (iFrame)       │
└─────────────────┘   └─────────────────┘
```

1. **Autenticación**: El usuario inicia sesión con Microsoft Entra ID (SSO / OAuth2) o credenciales locales.
2. **Identificación**: Se obtiene su correo corporativo.
3. **Permisos**: Se consulta `secrets.toml` para saber qué tableros le corresponden por email o rol.
4. **Renderizado**: El menú lateral muestra solo los tableros autorizados y se embeben usando un `iframe` con la URL de Power BI.

## Estructura del proyecto

```
.
├── .streamlit/
│   └── secrets.toml       # Variables sensibles: Entra ID, usuarios, tableros
├── app.py                 # Aplicación principal de Streamlit
├── auth.py                # Lógica de autenticación
├── permissions.py         # Lógica de permisos y mapeo
├── requirements.txt       # Dependencias
└── README.md              # Este archivo
```

## Cómo embeber un tablero solo con su URL

Power BI ofrece varias maneras de obtener una URL embebible:

- **Publicar en la web**: `Archivo → Compartir → Publicar en la web`. Genera una URL pública tipo `https://app.powerbi.com/view?r=...`. Ideal para iframe sin autenticación adicional.
- **Compartir de la organización**: URL de `app.powerbi.com` que requiere que el usuario tenga una sesión activa de Microsoft y permisos sobre el reporte.
- **API de Power BI + Embed Token**: para embebido seguro con capacidad de edición. Requiere backend adicional para generar tokens. Más información: https://docs.microsoft.com/power-bi/developer/embedded/

Coloca la URL que tengas en `secrets.toml` bajo `tableros.url` y la app la usará directamente.

## Configuración de Microsoft Entra ID

1. Registra una aplicación en **Azure Active Directory** → **App registrations**.
2. Obtén el **Application (client) ID** y genera un **Client secret**.
3. Configura el **Redirect URI** del tipo Web:
   - Producción Streamlit Cloud:
     `https://TU-APP.streamlit.app/component/streamlit_oauth/OAuth2Component/index.html`
   - Desarrollo local:
     `http://localhost:8501/component/streamlit_oauth/OAuth2Component/index.html`
4. Completa esos valores en `.streamlit/secrets.toml`.

## Configuración de Streamlit Cloud

1. Sube este repositorio a GitHub.
2. Crea una app en https://streamlit.io/cloud.
3. En **Settings → Secrets**, copia el contenido de `.streamlit/secrets.toml`.
4. Despliega.

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notas de seguridad

- No subas `.streamlit/secrets.toml` a repositorios públicos.
- El login personalizado del ejemplo usa passwords en texto plano solo para demostración. En producción usa hashing (por ejemplo, `bcrypt`) o preferiblemente Entra ID.
- El decode del JWT en `auth.py` no verifica firma por simplicidad en Streamlit Cloud. En producción valida la firma usando las llaves públicas de Microsoft.
