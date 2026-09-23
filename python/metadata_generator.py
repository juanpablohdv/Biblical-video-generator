"""
GENERADOR DE METADATA PARA YOUTUBE

Genera:
    - Descripción específica del video
    - Hashtags específicos
    - Descripción final combinando:
        descripción IA
        +
        hashtags específicos
        +
        hashtags por defecto
"""

from pathlib import Path
import json
import re

from openai import OpenAI
from dotenv import load_dotenv

from utils import cargar_prompts


# ==========================================================
# RUTAS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

DIR_IDEAS = (
    BASE_DIR /
    "data" /
    "ideas"
)

DIR_ASSETS = (
    BASE_DIR /
    "assets"
)

RUTA_HASHTAGS_DEFAULT = (
    DIR_ASSETS /
    "hashtags_default.txt"
)


# ==========================================================
# OPENAI
# ==========================================================

load_dotenv(
    dotenv_path=BASE_DIR / ".env"
)

client = OpenAI()


# ==========================================================
# LIMPIAR HASHTAG
# ==========================================================

def limpiar_hashtag(hashtag):
    """
    Normaliza un hashtag.

    Ejemplo:

        Cristiano
        ↓
        #Cristiano
    """

    hashtag = str(
        hashtag
    ).strip()

    if not hashtag:
        return ""

    if not hashtag.startswith("#"):
        hashtag = "#" + hashtag

    hashtag = re.sub(
        r"[^\w#ÁÉÍÓÚáéíóúÑñÜü]",
        "",
        hashtag,
        flags=re.UNICODE
    )

    return hashtag


# ==========================================================
# CARGAR HASHTAGS DEFAULT
# ==========================================================

def cargar_hashtags_default():
    """
    Carga los hashtags generales desde:

        assets/hashtags_default.txt
    """

    if not RUTA_HASHTAGS_DEFAULT.exists():

        raise FileNotFoundError(
            "No se encontró el archivo de hashtags "
            f"por defecto:\n{RUTA_HASHTAGS_DEFAULT}"
        )

    lineas = (
        RUTA_HASHTAGS_DEFAULT
        .read_text(
            encoding="utf-8"
        )
        .splitlines()
    )

    hashtags = []

    for linea in lineas:

        # Permitir uno o varios hashtags
        # por línea.
        for hashtag in linea.split():

            hashtag = limpiar_hashtag(
                hashtag
            )

            if not hashtag:
                continue

            claves_existentes = [
                h.lower()
                for h in hashtags
            ]

            if hashtag.lower() not in claves_existentes:

                hashtags.append(
                    hashtag
                )

    return hashtags


# ==========================================================
# COMBINAR HASHTAGS
# ==========================================================

def combinar_hashtags(
    hashtags_especificos,
    hashtags_default
):
    """
    Combina hashtags específicos y generales
    eliminando duplicados.
    """

    resultado = []

    vistos = set()

    todos = (
        hashtags_especificos
        +
        hashtags_default
    )

    for hashtag in todos:

        hashtag = limpiar_hashtag(
            hashtag
        )

        if not hashtag:
            continue

        clave = hashtag.lower()

        if clave not in vistos:

            vistos.add(
                clave
            )

            resultado.append(
                hashtag
            )

    return resultado


# ==========================================================
# GENERAR METADATA
# ==========================================================

def generar_metadata(
    idea_id,
    idea,
    guion
):
    """
    Genera la metadata de YouTube.

    Archivos creados:

        descripcion_ID.txt
        hashtags_ID.txt
        descripcion_youtube_ID.txt

    Si ya existen los dos primeros,
    se reutilizan y no se vuelve a llamar
    a OpenAI.
    """

    ruta_idea = (
        DIR_IDEAS /
        f"idea_{idea_id:05d}"
    )

    ruta_idea.mkdir(
        parents=True,
        exist_ok=True
    )

    ruta_descripcion = (
        ruta_idea /
        f"descripcion_{idea_id}.txt"
    )

    ruta_hashtags = (
        ruta_idea /
        f"hashtags_{idea_id}.txt"
    )

    ruta_descripcion_final = (
        ruta_idea /
        f"descripcion_youtube_{idea_id}.txt"
    )

    # ======================================================
    # REUTILIZAR METADATA EXISTENTE
    # ======================================================

    if (
        ruta_descripcion.exists()
        and
        ruta_hashtags.exists()
    ):

        print(
            "[INFO] Metadata ya existente."
        )

        print(
            "[INFO] Cargando archivos guardados..."
        )

        descripcion = (
            ruta_descripcion
            .read_text(
                encoding="utf-8"
            )
            .strip()
        )

        hashtags_especificos = [
            limpiar_hashtag(
                hashtag
            )
            for hashtag in (
                ruta_hashtags
                .read_text(
                    encoding="utf-8"
                )
                .split()
            )
        ]

        hashtags_especificos = [
            hashtag
            for hashtag in hashtags_especificos
            if hashtag
        ]

    # ======================================================
    # GENERAR CON IA
    # ======================================================

    else:

        print(
            "[INFO] Generando descripción "
            "y hashtags con IA..."
        )

        prompt = cargar_prompts(
            "metadata",
            idea=idea,
            guion=guion
        )

        respuesta = (
            client
            .chat
            .completions
            .create(
                model="gpt-4o-mini",
                response_format={
                    "type": "json_object"
                },
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        )

        contenido = (
            respuesta
            .choices[0]
            .message
            .content
            .strip()
        )

        try:

            datos = json.loads(
                contenido
            )

        except json.JSONDecodeError as error:

            raise RuntimeError(
                "La IA no devolvió un JSON "
                f"válido para la metadata: {error}"
            ) from error

        descripcion = str(
            datos.get(
                "description",
                ""
            )
        ).strip()

        hashtags_especificos = (
            datos.get(
                "hashtags",
                []
            )
        )

        if not descripcion:

            raise RuntimeError(
                "La IA no devolvió una descripción."
            )

        if not isinstance(
            hashtags_especificos,
            list
        ):

            raise RuntimeError(
                "Los hashtags devueltos por "
                "la IA no tienen formato de lista."
            )

        hashtags_especificos = [
            limpiar_hashtag(
                hashtag
            )
            for hashtag in hashtags_especificos
        ]

        hashtags_especificos = [
            hashtag
            for hashtag in hashtags_especificos
            if hashtag
        ]

        # --------------------------------------------------
        # Guardar descripción
        # --------------------------------------------------

        ruta_descripcion.write_text(
            descripcion,
            encoding="utf-8"
        )

        # --------------------------------------------------
        # Guardar hashtags específicos
        # --------------------------------------------------

        ruta_hashtags.write_text(
            " ".join(
                hashtags_especificos
            ),
            encoding="utf-8"
        )

        print(
            "[OK] Descripción guardada:"
        )

        print(
            ruta_descripcion
        )

        print(
            "[OK] Hashtags específicos guardados:"
        )

        print(
            ruta_hashtags
        )

    # ======================================================
    # HASHTAGS DEFAULT
    # ======================================================

    hashtags_default = (
        cargar_hashtags_default()
    )

    # ======================================================
    # COMBINAR
    # ======================================================

    hashtags_finales = combinar_hashtags(
        hashtags_especificos,
        hashtags_default
    )

    # ======================================================
    # DESCRIPCIÓN FINAL
    # ======================================================

    descripcion_final = (
        descripcion.rstrip()
        +
        "\n\n"
        +
        " ".join(
            hashtags_finales
        )
    ).strip()

    ruta_descripcion_final.write_text(
        descripcion_final,
        encoding="utf-8"
    )

    print(
        "[OK] Descripción final de YouTube:"
    )

    print(
        ruta_descripcion_final
    )

    return {
        "description": descripcion_final,

        "hashtags_specific":
            hashtags_especificos,

        "hashtags_default":
            hashtags_default,

        "hashtags_final":
            hashtags_finales,

        "description_path":
            ruta_descripcion,

        "hashtags_path":
            ruta_hashtags,

        "youtube_description_path":
            ruta_descripcion_final
    }