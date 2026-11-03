from pathlib import Path
from datetime import datetime, timedelta, timezone

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

DIR_CREDENTIALS = (
    BASE_DIR /
    "credentials"
)

CLIENT_SECRETS_FILE = (
    DIR_CREDENTIALS /
    "client_secret.json"
)

TOKEN_FILE = (
    DIR_CREDENTIALS /
    "token_youtube.json"
)


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
        - El usuario autoriza.
        - Se guarda token_youtube.json.

    Ejecuciones posteriores:
        - Reutiliza el token.
        - Si está vencido, intenta renovarlo.
    """

    credenciales = None

    # --------------------------------------------------------
    # Cargar token existente
    # --------------------------------------------------------

    if TOKEN_FILE.exists():

        credenciales = (
            Credentials
            .from_authorized_user_file(
                TOKEN_FILE,
                SCOPES
            )
        )

    # --------------------------------------------------------
    # Comprobar credenciales
    # --------------------------------------------------------

    if (
        not credenciales
        or not credenciales.valid
    ):

        # ----------------------------------------------------
        # Renovar token
        # ----------------------------------------------------

        if (
            credenciales
            and credenciales.expired
            and credenciales.refresh_token
        ):

            print(
                "[INFO] Renovando credenciales de YouTube..."
            )

            credenciales.refresh(
                Request()
            )

        # ----------------------------------------------------
        # Primera autorización
        # ----------------------------------------------------

        else:

            if not CLIENT_SECRETS_FILE.exists():

                raise FileNotFoundError(
                    "\nNo se encontró el archivo "
                    "de credenciales de Google.\n"
                    f"Debe existir aquí:\n"
                    f"{CLIENT_SECRETS_FILE}\n"
                )

            print(
                "[INFO] No existe una autorización previa."
            )

            print(
                "[INFO] Se abrirá el navegador "
                "para autorizar YouTube."
            )

            flujo = (
                InstalledAppFlow
                .from_client_secrets_file(
                    CLIENT_SECRETS_FILE,
                    SCOPES
                )
            )

            credenciales = (
                flujo.run_local_server(
                    port=0
                )
            )

        # ----------------------------------------------------
        # Guardar token
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
            "[OK] Credenciales guardadas en:"
        )

        print(
            TOKEN_FILE
        )

    return credenciales


# ============================================================
# CREAR SERVICIO
# ============================================================

def obtener_servicio_youtube():
    """
    Crea el cliente de la API de YouTube.
    """

    credenciales = (
        obtener_credenciales()
    )

    return build(
        "youtube",
        "v3",
        credentials=credenciales
    )


# ============================================================
# NORMALIZAR RUTA
# ============================================================

def normalizar_ruta(ruta):
    """
    Convierte una entrada en Path.

    También elimina comillas que pueden quedar
    pegadas cuando se copia una ruta desde PowerShell.
    """

    return Path(
        str(ruta)
        .strip()
        .strip('"')
        .strip("'")
    )


# ============================================================
# SUBIR VIDEO
# ============================================================


def subir_video(
    ruta_video,
    titulo,
    descripcion="",
    tags=None,
    categoria_id="22",
    privacidad="private",
    fecha_publicacion=None
):
    """
    Sube un video a YouTube y programa su publicación.

    fecha_publicacion debe venir de la base de datos
    en formato ISO, por ejemplo:
    2026-11-05T19:00:00
    """

    ruta_video = normalizar_ruta(ruta_video)

    if not ruta_video.exists():
        raise FileNotFoundError(
            f"No se encontró el video:\n{ruta_video}"
        )

    if ruta_video.suffix.lower() != ".mp4":
        raise ValueError("El archivo debe ser un video MP4.")

    # --------------------------------------------------------
    # VALIDAR FECHA DE PUBLICACIÓN
    # --------------------------------------------------------

    if not fecha_publicacion:
        raise ValueError(
            "La idea no tiene fecha_publicacion en la base de datos. "
            "No se subirá el video sin programación."
        )

    try:
        fecha_programada = datetime.fromisoformat(
            str(fecha_publicacion).replace("Z", "+00:00")
        )
    except (ValueError, TypeError):
        raise ValueError(
            f"Fecha de publicación inválida: {fecha_publicacion!r}"
        )

    # Las fechas sin zona horaria se interpretan como hora de Colombia.
    zona_colombia = timezone(timedelta(hours=-5))

    if fecha_programada.tzinfo is None:
        fecha_programada = fecha_programada.replace(
            tzinfo=zona_colombia
        )
    else:
        fecha_programada = fecha_programada.astimezone(
            zona_colombia
        )

    ahora = datetime.now(zona_colombia)

    # Exigimos al menos 10 minutos para evitar que la subida
    # termine después de la hora programada.
    margen_seguridad = timedelta(minutes=10)

    if fecha_programada <= ahora + margen_seguridad:
        raise ValueError(
            "La fecha programada debe estar al menos 10 minutos "
            "en el futuro.\n"
            f"Ahora: {ahora.isoformat()}\n"
            f"Programada: {fecha_programada.isoformat()}"
        )

    fecha_youtube = fecha_programada.isoformat(
        timespec="seconds"
    )

    # --------------------------------------------------------
    # AÑADIR #SHORTS
    # --------------------------------------------------------

    if (
        "#shorts" not in titulo.lower()
        and "#shorts" not in descripcion.lower()
    ):
        descripcion = (
            descripcion.rstrip() + "\n\n#Shorts"
        ).strip()

    # --------------------------------------------------------
    # SERVICIO
    # --------------------------------------------------------

    youtube = obtener_servicio_youtube()

    # --------------------------------------------------------
    # DATOS DEL VIDEO
    # --------------------------------------------------------

    cuerpo = {
        "snippet": {
            "title": titulo,
            "description": descripcion,
            "tags": tags or [],
            "categoryId": categoria_id
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": fecha_youtube,
            "containsSyntheticMedia": True,
            "selfDeclaredMadeForKids": False
        }
    }

    # --------------------------------------------------------
    # ARCHIVO
    # --------------------------------------------------------

    media = MediaFileUpload(
        str(ruta_video),
        mimetype="video/mp4",
        resumable=True,
        chunksize=8 * 1024 * 1024
    )

    # --------------------------------------------------------
    # SOLICITUD
    # --------------------------------------------------------

    solicitud = (
        youtube
        .videos()
        .insert(
            part="snippet,status",
            body=cuerpo,
            media_body=media
        )
    )

    # --------------------------------------------------------
    # SUBIR
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("SUBIENDO Y PROGRAMANDO VIDEO EN YOUTUBE")
    print("=" * 60)
    print(f"Archivo: {ruta_video.name}")
    print(f"Título: {titulo}")
    print("Privacidad inicial: private")
    print(f"Publicación programada: {fecha_youtube}")
    print()

    respuesta = None

    try:
        while respuesta is None:
            estado, respuesta = solicitud.next_chunk()

            if estado:
                porcentaje = int(estado.progress() * 100)
                print(f"[UPLOAD] {porcentaje}%")

    except HttpError as error:
        print()
        print("[ERROR] YouTube rechazó la subida.")
        print(error)
        raise

    video_id = respuesta.get("id")

    if not video_id:
        raise RuntimeError(
            "YouTube respondió correctamente, "
            "pero no devolvió un video_id."
        )

    url = (
        "https://www.youtube.com/shorts/"
        f"{video_id}"
    )

    print()
    print("[OK] Video subido y programación enviada a YouTube.")
    print(f"[OK] Video ID: {video_id}")
    print(f"[OK] URL: {url}")
    print(f"[OK] Se publicará: {fecha_youtube}")
    print()

    return video_id


# ============================================================
# CONFIGURAR MINIATURA
# ============================================================

def configurar_miniatura(
    video_id,
    ruta_imagen
):
    """
    Establece una imagen como miniatura personalizada
    del video ya subido.

    Retorna True si la operación termina correctamente.
    """

    ruta_imagen = normalizar_ruta(
        ruta_imagen
    )

    # --------------------------------------------------------
    # Validar imagen
    # --------------------------------------------------------

    if not ruta_imagen.exists():

        raise FileNotFoundError(
            "No se encontró la imagen para "
            f"la miniatura:\n{ruta_imagen}"
        )

    if ruta_imagen.suffix.lower() not in (
        ".jpg",
        ".jpeg",
        ".png"
    ):

        raise ValueError(
            "La miniatura debe ser JPG, JPEG o PNG."
        )

    # --------------------------------------------------------
    # Servicio
    # --------------------------------------------------------

    youtube = (
        obtener_servicio_youtube()
    )

    print()
    print("=" * 60)
    print("CONFIGURANDO MINIATURA DE YOUTUBE")
    print("=" * 60)

    print(
        f"Video ID: {video_id}"
    )

    print(
        f"Imagen: {ruta_imagen.name}"
    )

    print()

    # --------------------------------------------------------
    # MIME
    # --------------------------------------------------------

    mime_types = {

        ".jpg":
            "image/jpeg",

        ".jpeg":
            "image/jpeg",

        ".png":
            "image/png"
    }

    mime_type = (
        mime_types[
            ruta_imagen.suffix.lower()
        ]
    )

    media = MediaFileUpload(
        str(ruta_imagen),
        mimetype=mime_type
    )

    # --------------------------------------------------------
    # Subir miniatura
    # --------------------------------------------------------

    try:

        respuesta = (
            youtube
            .thumbnails()
            .set(
                videoId=video_id,
                media_body=media
            )
            .execute()
        )

    except HttpError as error:

        print()
        print(
            "[ERROR] YouTube no pudo "
            "configurar la miniatura."
        )

        print(error)

        raise

    if not respuesta:

        raise RuntimeError(
            "YouTube no devolvió respuesta "
            "al configurar la miniatura."
        )

    print(
        "[OK] Miniatura configurada correctamente."
    )

    return True


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