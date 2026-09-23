from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DIR_CREDENTIALS = BASE_DIR / "credentials"

CLIENT_SECRETS_FILE = DIR_CREDENTIALS / "client_secret.json"
TOKEN_FILE = DIR_CREDENTIALS / "token_youtube.json"


# ============================================================
# CONFIGURACIÓN DE YOUTUBE
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]


# ============================================================
# AUTENTICACIÓN
# ============================================================

def obtener_credenciales():
    """
    Obtiene las credenciales OAuth de YouTube.

    Primera ejecución:
        - Abre el navegador.
        - El usuario autoriza el acceso.
        - Se guarda token_youtube.json.

    Ejecuciones posteriores:
        - Reutiliza el token guardado.
        - Si está vencido, intenta renovarlo automáticamente.
    """

    credenciales = None

    # --------------------------------------------------------
    # 1. Intentar cargar un token existente
    # --------------------------------------------------------

    if TOKEN_FILE.exists():

        credenciales = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    # --------------------------------------------------------
    # 2. Si no existe o ya no es válido
    # --------------------------------------------------------

    if not credenciales or not credenciales.valid:

        # ----------------------------------------------------
        # Token vencido pero con refresh token
        # ----------------------------------------------------

        if (
            credenciales
            and credenciales.expired
            and credenciales.refresh_token
        ):

            print("[INFO] Renovando credenciales de YouTube...")

            credenciales.refresh(Request())

        # ----------------------------------------------------
        # Primera autorización
        # ----------------------------------------------------

        else:

            if not CLIENT_SECRETS_FILE.exists():

                raise FileNotFoundError(
                    "\nNo se encontró el archivo de credenciales de Google.\n"
                    f"Debe existir aquí:\n{CLIENT_SECRETS_FILE}\n"
                )

            print("[INFO] No existe una autorización previa.")
            print("[INFO] Se abrirá el navegador para autorizar YouTube.")

            flujo = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                SCOPES
            )

            credenciales = flujo.run_local_server(
                port=0
            )

        # ----------------------------------------------------
        # Guardar credenciales para próximas ejecuciones
        # ----------------------------------------------------

        DIR_CREDENTIALS.mkdir(
            parents=True,
            exist_ok=True
        )

        TOKEN_FILE.write_text(
            credenciales.to_json(),
            encoding="utf-8"
        )

        print(
            f"[OK] Credenciales guardadas en:\n{TOKEN_FILE}"
        )

    return credenciales


# ============================================================
# CREAR SERVICIO DE YOUTUBE
# ============================================================

def obtener_servicio_youtube():
    """
    Crea el cliente de la API de YouTube.
    """

    credenciales = obtener_credenciales()

    youtube = build(
        "youtube",
        "v3",
        credentials=credenciales
    )

    return youtube


# ============================================================
# SUBIR VIDEO
# ============================================================

def subir_video(
    ruta_video,
    titulo,
    descripcion="",
    tags=None,
    categoria_id="22",
    privacidad="private"
):
    """
    Sube un video a YouTube.

    Parámetros:
        ruta_video:
            Ruta del archivo MP4.

        titulo:
            Título del video.

        descripcion:
            Descripción del video.

        tags:
            Lista de etiquetas.

        categoria_id:
            Categoría de YouTube.
            22 = People & Blogs.

        privacidad:
            "private"
            "unlisted"
            "public"

    Retorna:
        video_id
    """

    ruta_video = Path(ruta_video)

    # --------------------------------------------------------
    # Validar archivo
    # --------------------------------------------------------

    if not ruta_video.exists():

        raise FileNotFoundError(
            f"No se encontró el video:\n{ruta_video}"
        )

    if ruta_video.suffix.lower() != ".mp4":

        raise ValueError(
            "El archivo debe ser un video MP4."
        )

    # --------------------------------------------------------
    # Añadir #Shorts si no existe
    # --------------------------------------------------------

    if (
        "#shorts" not in titulo.lower()
        and "#shorts" not in descripcion.lower()
    ):

        descripcion = (
            descripcion.rstrip()
            + "\n\n#Shorts"
        ).strip()

    # --------------------------------------------------------
    # Obtener servicio
    # --------------------------------------------------------

    youtube = obtener_servicio_youtube()

    # --------------------------------------------------------
    # Información del video
    # --------------------------------------------------------

    cuerpo = {
        "snippet": {
            "title": titulo,
            "description": descripcion,
            "tags": tags or [],
            "categoryId": categoria_id
        },

        "status": {
            "privacyStatus": privacidad,
            "selfDeclaredMadeForKids": False
        }
    }

    # --------------------------------------------------------
    # Preparar archivo
    # --------------------------------------------------------

    media = MediaFileUpload(
        str(ruta_video),
        mimetype="video/mp4",
        resumable=True,
        chunksize=8 * 1024 * 1024
    )

    # --------------------------------------------------------
    # Crear solicitud
    # --------------------------------------------------------

    solicitud = youtube.videos().insert(
        part="snippet,status",
        body=cuerpo,
        media_body=media
    )

    # --------------------------------------------------------
    # Subir
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("SUBIENDO VIDEO A YOUTUBE")
    print("=" * 60)
    print(f"Archivo: {ruta_video.name}")
    print(f"Título: {titulo}")
    print(f"Privacidad: {privacidad}")
    print()

    respuesta = None

    try:

        while respuesta is None:

            estado, respuesta = solicitud.next_chunk()

            if estado:

                porcentaje = int(
                    estado.progress() * 100
                )

                print(
                    f"[UPLOAD] {porcentaje}%"
                )

    except HttpError as error:

        print()
        print("[ERROR] YouTube rechazó la subida.")
        print(error)

        raise

    # --------------------------------------------------------
    # Obtener ID
    # --------------------------------------------------------

    video_id = respuesta.get("id")

    if not video_id:

        raise RuntimeError(
            "YouTube respondió correctamente, "
            "pero no devolvió un video_id."
        )

    url = (
        f"https://www.youtube.com/shorts/{video_id}"
    )

    print()
    print("[OK] Video subido correctamente.")
    print(f"[OK] Video ID: {video_id}")
    print(f"[OK] URL: {url}")
    print()

    return video_id


# ============================================================
# PRUEBA MANUAL
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("PRUEBA DE YOUTUBE UPLOADER")
    print("=" * 60)

    ruta = input(
        "Introduce la ruta del video MP4: "
    ).strip()

    titulo = input(
        "Introduce el título: "
    ).strip()

    descripcion = input(
        "Introduce la descripción: "
    ).strip()

    subir_video(
        ruta_video=ruta,
        titulo=titulo,
        descripcion=descripcion,
        privacidad="private"
    )