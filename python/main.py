"""
MAIN - PIPELINE COMPLETO DE GENERACIÓN DE VIDEOS

1 -> Generar video completo y subir a YouTube
2 -> Regenerar todos los videos existentes usando solamente MoviePy
0 -> Salir

El pipeline utiliza el estado de cada idea para
continuar desde el último paso completado.
"""

from pathlib import Path
import json


# ==========================================================
# BASE DE DATOS
# ==========================================================

from ideas_db import (
    crear_tabla,
    guardar_idea,
    obtener_idea_incompleta,
    obtener_idea_no_usada,
    obtener_idea_por_id,
    modificar_estado,
    contar_ideas_no_usadas,
    registrar_error,
    guardar_youtube,
    marcar_miniatura_youtube
)


# ==========================================================
# GENERADORES
# ==========================================================

from ideas_generator import generar_ideas

from guion_generator import generate_guion

from manejo_guion import (
    generate_scenes,
    crear_fichas,
    optimizador_fichas,
    creador_prompts_imagenes
)

from images_generator import generar_imagenes

from voice_generator import generate_voice

from video_generator import generar_video

from metadata_generator import generar_metadata

from youtube_uploader import (
    subir_video,
    configurar_miniatura
)


# ==========================================================
# RUTAS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

DIR_IDEAS = (
    BASE_DIR /
    "data" /
    "ideas"
)


# ==========================================================
# IDEA ACTUAL
# ==========================================================

IDEA_ACTUAL = None


# ==========================================================
# CONFIGURACIÓN DE YOUTUBE
# ==========================================================

# Para esta primera prueba automática:
#
# private  -> el video se sube pero queda privado.
# unlisted -> el video queda no listado.
# public   -> el video queda público.
#
# Cuando quieras publicación automática:
#
# PRIVACIDAD_YOUTUBE = "public"

PRIVACIDAD_YOUTUBE = "private"

CATEGORIA_YOUTUBE = "22"


# ==========================================================
# INICIALIZACIÓN
# ==========================================================

print()
print("=" * 60)
print("                    VIDEOS API")
print("=" * 60)
print()

print(
    "[INFO] Inicializando base de datos..."
)

crear_tabla()

print(
    "[OK] Base de datos lista."
)


# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def ruta_idea(idea_id):
    """
    Devuelve la carpeta de una idea.
    """

    return (
        DIR_IDEAS /
        f"idea_{idea_id:05d}"
    )


def cargar_archivo_json(ruta):
    """
    Carga un archivo JSON.
    """

    if not ruta.exists():

        raise FileNotFoundError(
            f"No existe el archivo: {ruta}"
        )

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def cargar_guion(idea_id):
    """
    Carga el guion guardado en la carpeta de la idea.
    """

    ruta = (
        ruta_idea(idea_id) /
        f"guion_{idea_id}.txt"
    )

    if not ruta.exists():

        raise FileNotFoundError(
            f"No se encontró el guion: {ruta}"
        )

    return ruta.read_text(
        encoding="utf-8"
    ).strip()


def cargar_scenes(idea_id):
    """
    Carga las escenas previamente generadas.
    """

    ruta = (
        ruta_idea(idea_id) /
        f"scenes_{idea_id}.json"
    )

    return cargar_archivo_json(
        ruta
    )


def cargar_optimized_scenes(idea_id):
    """
    Carga las escenas con fichas optimizadas.
    """

    ruta = (
        ruta_idea(idea_id) /
        f"optimized_scenes_{idea_id}.json"
    )

    return cargar_archivo_json(
        ruta
    )


def cargar_metadata_final(idea_id):
    """
    Carga la descripción final de YouTube
    y los hashtags específicos ya guardados.
    """

    ruta_descripcion = (
        ruta_idea(idea_id) /
        f"descripcion_youtube_{idea_id}.txt"
    )

    if not ruta_descripcion.exists():

        raise FileNotFoundError(
            "No se encontró la descripción final de YouTube:"
            f"\n{ruta_descripcion}"
        )

    descripcion = (
        ruta_descripcion
        .read_text(
            encoding="utf-8"
        )
        .strip()
    )

    ruta_hashtags = (
        ruta_idea(idea_id) /
        f"hashtags_{idea_id}.txt"
    )

    hashtags = []

    if ruta_hashtags.exists():

        hashtags = (
            ruta_hashtags
            .read_text(
                encoding="utf-8"
            )
            .split()
        )

    return (
        descripcion,
        hashtags
    )


def obtener_primera_imagen(idea_id):
    """
    Obtiene la primera imagen de la idea
    para utilizarla como miniatura.
    """

    carpeta = (
        ruta_idea(idea_id) /
        "images"
    )

    imagenes = sorted(
        carpeta.glob(
            "scene_*.png"
        )
    )

    if not imagenes:

        raise FileNotFoundError(
            "No se encontraron imágenes para "
            f"la miniatura en:\n{carpeta}"
        )

    return imagenes[0]


# ==========================================================
# SELECCIONAR IDEA
# ==========================================================

def seleccionar_idea():
    """
    Selecciona qué idea debe procesarse.

    PRIORIDAD:

    1. Idea incompleta.
    2. Idea nueva.
    3. Generar nuevas ideas.
    """

    print(
        "[INFO] Buscando ideas incompletas..."
    )

    idea = (
        obtener_idea_incompleta()
    )

    if idea:

        (
            idea_id,
            texto,
            guion_db,
            estado
        ) = idea

        print(
            "[OK] Se encontró una idea incompleta."
        )

        print(
            f"[INFO] Idea #{idea_id}"
        )

        print(
            f"[INFO] Estado actual: {estado}"
        )

        print(
            f"[INFO] Continuando desde: {estado}"
        )

        return (
            idea_id,
            texto,
            guion_db,
            estado
        )

    print(
        "[INFO] No hay ideas incompletas."
    )

    cantidad = (
        contar_ideas_no_usadas()
    )

    print(
        f"[INFO] Ideas nuevas disponibles: {cantidad}"
    )

    # ------------------------------------------------------
    # Generar nuevas ideas
    # ------------------------------------------------------

    if cantidad < 5:

        print(
            "[INFO] Hay menos de 5 ideas nuevas."
        )

        print(
            "[INFO] Generando nuevas ideas con IA..."
        )

        ideas_creadas = (
            generar_ideas()
        )

        print(
            f"[INFO] La IA generó "
            f"{len(ideas_creadas)} ideas."
        )

        for idea in ideas_creadas:

            guardar_idea(
                idea
            )

        print(
            "[OK] Nuevas ideas guardadas."
        )

    # ------------------------------------------------------
    # Obtener idea
    # ------------------------------------------------------

    idea = (
        obtener_idea_no_usada()
    )

    if not idea:

        raise RuntimeError(
            "No fue posible obtener una idea."
        )

    (
        idea_id,
        texto,
        guion_db,
        estado
    ) = idea

    print(
        f"[OK] Nueva idea seleccionada: #{idea_id}"
    )

    return (
        idea_id,
        texto,
        guion_db,
        estado
    )


# ==========================================================
# PIPELINE COMPLETO
# ==========================================================

def ejecutar_pipeline():

    global IDEA_ACTUAL

    print()
    print("=" * 60)
    print(
        "          INICIANDO PIPELINE COMPLETO"
    )
    print("=" * 60)
    print()

    # ======================================================
    # SELECCIONAR IDEA
    # ======================================================

    (
        idea_id,
        texto_idea,
        guion_db,
        estado
    ) = seleccionar_idea()

    IDEA_ACTUAL = idea_id

    print()
    print(
        f"[INFO] IDEA #{idea_id}:"
    )

    print(
        f"       {texto_idea}"
    )

    print(
        f"[INFO] Estado inicial: {estado}"
    )

    print()


    # ======================================================
    # PASO 2 - GUION
    # ======================================================

    if estado == "IDEA":

        print(
            "[2/11] Generando guion..."
        )

        guion = generate_guion(
            texto_idea,
            idea_id
        )

        if not guion:

            raise RuntimeError(
                "La generación del guion "
                "no devolvió contenido."
            )

        modificar_estado(
            idea_id,
            "GUION"
        )

        estado = "GUION"

        print(
            "[OK] Guion generado."
        )

    else:

        print(
            "[2/11] GUION ya completado. Saltando..."
        )

        guion = guion_db

        if not guion:

            guion = cargar_guion(
                idea_id
            )

        print(
            "[OK] Guion cargado."
        )

    print()


    # ======================================================
    # PASO 3 - ESCENAS
    # ======================================================

    if estado == "GUION":

        print(
            "[3/11] Generando escenas..."
        )

        scenes = generate_scenes(
            guion,
            idea_id
        )

        if not scenes:

            raise RuntimeError(
                "No se generaron escenas."
            )

        modificar_estado(
            idea_id,
            "ESCENAS"
        )

        estado = "ESCENAS"

        print(
            f"[OK] Se generaron "
            f"{len(scenes)} escenas."
        )

    elif estado in (
        "ESCENAS",
        "FICHAS",
        "OPTIMIZADO",
        "PROMPTS",
        "IMAGENES",
        "VOZ"
    ):

        print(
            "[3/11] ESCENAS ya completadas. "
            "Cargando..."
        )

        scenes = (
            cargar_scenes(
                idea_id
            )
        )

        print(
            f"[OK] {len(scenes)} escenas cargadas."
        )

    else:

        scenes = None

    print()


    # ======================================================
    # PASO 4 - FICHAS
    # ======================================================

    if estado == "ESCENAS":

        print(
            "[4/11] Creando/cargando fichas..."
        )

        crear_fichas(
            scenes
        )

        modificar_estado(
            idea_id,
            "FICHAS"
        )

        estado = "FICHAS"

        print(
            "[OK] Fichas listas."
        )

    else:

        print(
            "[4/11] FICHAS ya completadas. "
            "Saltando..."
        )

    print()


    # ======================================================
    # PASO 5 - OPTIMIZACIÓN
    # ======================================================

    if estado == "FICHAS":

        print(
            "[5/11] Optimizando fichas..."
        )

        optimized_scenes = (
            optimizador_fichas(
                scenes,
                idea_id
            )
        )

        if not optimized_scenes:

            raise RuntimeError(
                "No se pudieron optimizar "
                "las escenas."
            )

        modificar_estado(
            idea_id,
            "OPTIMIZADO"
        )

        estado = "OPTIMIZADO"

        print(
            "[OK] Fichas optimizadas."
        )

    elif estado in (
        "OPTIMIZADO",
        "PROMPTS",
        "IMAGENES",
        "VOZ"
    ):

        print(
            "[5/11] OPTIMIZACIÓN ya completada. "
            "Cargando..."
        )

        optimized_scenes = (
            cargar_optimized_scenes(
                idea_id
            )
        )

    else:

        optimized_scenes = None

    print()


    # ======================================================
    # PASO 6 - PROMPTS
    # ======================================================

    if estado == "OPTIMIZADO":

        print(
            "[6/11] Creando prompts de imagen..."
        )

        prompts = (
            creador_prompts_imagenes(
                optimized_scenes,
                idea_id
            )
        )

        if not prompts:

            raise RuntimeError(
                "No se generaron prompts."
            )

        modificar_estado(
            idea_id,
            "PROMPTS"
        )

        estado = "PROMPTS"

        print(
            f"[OK] Se generaron "
            f"{len(prompts)} prompts."
        )

    else:

        print(
            "[6/11] PROMPTS ya completados. "
            "Saltando..."
        )

    print()


    # ======================================================
    # PASO 7 - IMÁGENES
    # ======================================================

    if estado == "PROMPTS":

        print(
            "[7/11] Generando imágenes..."
        )

        generar_imagenes(
            idea_id
        )

        modificar_estado(
            idea_id,
            "IMAGENES"
        )

        estado = "IMAGENES"

        print(
            "[OK] Imágenes generadas."
        )

    else:

        print(
            "[7/11] IMÁGENES ya completadas. "
            "Saltando..."
        )

    print()


    # ======================================================
    # PASO 8 - VOZ
    # ======================================================

    if estado == "IMAGENES":

        print(
            "[8/11] Generando narración..."
        )

        ruta_voz = (
            generate_voice(
                guion,
                idea_id
            )
        )

        if not ruta_voz:

            raise RuntimeError(
                "No se pudo generar la narración."
            )

        modificar_estado(
            idea_id,
            "VOZ"
        )

        estado = "VOZ"

        print(
            f"[OK] Narración generada: "
            f"{ruta_voz}"
        )

    else:

        print(
            "[8/11] VOZ ya completada. "
            "Saltando..."
        )

    print()


    # ======================================================
    # PASO 9 - VIDEO
    # ======================================================

    if estado == "VOZ":

        print(
            "[9/11] Generando video final..."
        )

        ruta_video = (
            generar_video(
                idea_id
            )
        )

        if not ruta_video:

            raise RuntimeError(
                "No se pudo generar el video."
            )

        modificar_estado(
            idea_id,
            "V_FINAL"
        )

        estado = "V_FINAL"

        print(
            f"[OK] Video generado: "
            f"{ruta_video}"
        )

    else:

        ruta_video = (
            ruta_idea(idea_id)
            /
            f"video_{idea_id}.mp4"
        )

        if not ruta_video.exists():

            raise FileNotFoundError(
                "El estado indica que el video "
                "ya existe, pero no se encontró:\n"
                f"{ruta_video}"
            )

        print(
            "[9/11] VIDEO ya generado. "
            "Saltando..."
        )

    print()


    # ======================================================
    # PASO 10 - METADATA
    # ======================================================

    if estado in (
        "V_FINAL",
        "METADATA"
    ):

        print(
            "[10/11] Generando metadata de YouTube..."
        )

        metadata = (
            generar_metadata(
                idea_id,
                texto_idea,
                guion
            )
        )

        if not metadata:

            raise RuntimeError(
                "No se pudo generar la metadata."
            )

        if estado == "V_FINAL":

            modificar_estado(
                idea_id,
                "METADATA"
            )

            estado = "METADATA"

        print(
            "[OK] Metadata lista."
        )

        print(
            f"[OK] Hashtags finales: "
            f"{len(metadata['hashtags_final'])}"
        )

    else:

        raise RuntimeError(
            f"Estado inesperado antes de YouTube: "
            f"{estado}"
        )

    print()


    # ======================================================
    # PASO 11 - YOUTUBE
    # ======================================================

    print(
        "[11/11] Subiendo video a YouTube..."
    )

    # ------------------------------------------------------
    # Recuperar información actual de la BD
    # ------------------------------------------------------

    registro = (
        obtener_idea_por_id(
            idea_id
        )
    )

    if not registro:

        raise RuntimeError(
            f"No se encontró la idea #{idea_id} "
            "en la base de datos."
        )

    # Nuestra versión actualizada de ideas_db.py
    # devuelve:
    #
    # 0 id
    # 1 texto
    # 2 guion
    # 3 estado
    # 4 fecha_creacion
    # 5 fecha_actualizacion
    # 6 error
    # 7 youtube_video_id
    # 8 youtube_url
    # 9 youtube_thumbnail_ok

    youtube_video_id = (
        registro[7]
    )

    youtube_url = (
        registro[8]
    )

    youtube_thumbnail_ok = bool(
        registro[9]
    )

    # ------------------------------------------------------
    # ¿Ya se subió?
    # ------------------------------------------------------

    if youtube_video_id:

        print(
            "[INFO] La idea ya tiene "
            "un video_id de YouTube."
        )

        print(
            f"[INFO] Video ID: "
            f"{youtube_video_id}"
        )

        if not youtube_url:

            youtube_url = (
                "https://www.youtube.com/shorts/"
                f"{youtube_video_id}"
            )

    # ------------------------------------------------------
    # SUBIR VIDEO
    # ------------------------------------------------------

    else:

        try:

            (
                descripcion_final,
                hashtags_guardados
            ) = cargar_metadata_final(
                idea_id
            )

        except FileNotFoundError:

            descripcion_final = (
                metadata["description"]
            )

            hashtags_guardados = (
                metadata["hashtags_final"]
            )

        # --------------------------------------------------
        # Tags internos de YouTube
        # --------------------------------------------------

        tags = [

            hashtag.lstrip("#")

            for hashtag
            in hashtags_guardados
        ]

        print(
            "[INFO] Preparando subida..."
        )

        youtube_video_id = (
            subir_video(
                ruta_video=ruta_video,

                titulo=texto_idea,

                descripcion=descripcion_final,

                tags=tags,

                categoria_id=CATEGORIA_YOUTUBE,

                privacidad=PRIVACIDAD_YOUTUBE
            )
        )

        youtube_url = (
            "https://www.youtube.com/shorts/"
            f"{youtube_video_id}"
        )

        # --------------------------------------------------
        # Guardar inmediatamente el ID
        # --------------------------------------------------

        guardar_youtube(
            idea_id,
            youtube_video_id,
            youtube_url
        )

    print()


    # ======================================================
    # MINIATURA
    # ======================================================

    if youtube_thumbnail_ok:

        print(
            "[OK] La miniatura ya estaba "
            "configurada. Saltando..."
        )

    else:

        ruta_miniatura = (
            obtener_primera_imagen(
                idea_id
            )
        )

        configurar_miniatura(
            youtube_video_id,
            ruta_miniatura
        )

        marcar_miniatura_youtube(
            idea_id,
            True
        )

    # ======================================================
    # MARCAR COMO SUBIDO
    # ======================================================

    modificar_estado(
        idea_id,
        "SUBIDO"
    )

    estado = "SUBIDO"

    print()
    print(
        "[OK] Video y miniatura "
        "procesados correctamente."
    )

    print(
        f"[OK] YouTube: {youtube_url}"
    )

    print()
    print("=" * 60)
    print(
        "             PIPELINE TERMINADO"
    )
    print("=" * 60)
    print()

    print(
        f"IDEA #{idea_id}"
    )

    print(
        f"ESTADO: {estado}"
    )

    print()

    print(
        "VIDEO FINAL:"
    )

    print(
        ruta_video
    )

    print()

    print(
        "YOUTUBE:"
    )

    print(
        youtube_url
    )

    print()

    print("=" * 60)

    return ruta_video


# ==========================================================
# REGENERAR VIDEOS EXISTENTES
# ==========================================================

def regenerar_videos_existentes():
    """
    Regenera todos los videos que ya tienen
    imágenes, voz y guion.

    IMPORTANTE:

    Esta opción solamente ejecuta MoviePy.

    NO:
        - genera ideas
        - genera guiones
        - genera imágenes
        - genera voces
        - genera metadata
        - sube videos a YouTube
    """

    print()
    print("=" * 60)
    print(
        "       REGENERACIÓN DE VIDEOS EXISTENTES"
    )
    print("=" * 60)
    print()

    if not DIR_IDEAS.exists():

        print(
            f"[INFO] No existe la carpeta: "
            f"{DIR_IDEAS}"
        )

        return

    carpetas = sorted(
        DIR_IDEAS.glob(
            "idea_*"
        )
    )

    if not carpetas:

        print(
            "[INFO] No se encontraron ideas."
        )

        return

    procesadas = 0
    errores = 0
    omitidas = 0

    for carpeta in carpetas:

        # --------------------------------------------------
        # Obtener ID
        # --------------------------------------------------

        try:

            idea_id = int(
                carpeta.name.split(
                    "_"
                )[1]
            )

        except (
            ValueError,
            IndexError
        ):

            continue

        ruta_images = (
            carpeta /
            "images"
        )

        ruta_voz = (
            carpeta /
            f"voz_{idea_id}.mp3"
        )

        ruta_guion = (
            carpeta /
            f"guion_{idea_id}.txt"
        )

        # --------------------------------------------------
        # Verificar archivos
        # --------------------------------------------------

        imagenes = list(
            ruta_images.glob(
                "scene_*.png"
            )
        ) if ruta_images.exists() else []

        if not imagenes:

            print(
                f"[SKIP] Idea #{idea_id}: "
                "no tiene imágenes."
            )

            omitidas += 1

            continue

        if not ruta_voz.exists():

            print(
                f"[SKIP] Idea #{idea_id}: "
                "no tiene narración."
            )

            omitidas += 1

            continue

        if not ruta_guion.exists():

            print(
                f"[SKIP] Idea #{idea_id}: "
                "no tiene guion."
            )

            omitidas += 1

            continue

        print()
        print("-" * 60)
        print(
            f"[REGEN] Regenerando idea #{idea_id}"
        )
        print("-" * 60)

        try:

            ruta_video = (
                generar_video(
                    idea_id
                )
            )

            procesadas += 1

            print(
                f"[OK] Idea #{idea_id} regenerada:"
            )

            print(
                ruta_video
            )

        except Exception as error:

            errores += 1

            print()
            print(
                f"[ERROR] Falló la "
                f"regeneración de la idea #{idea_id}"
            )

            print(
                f"{type(error).__name__}: "
                f"{error}"
            )

    print()
    print("=" * 60)
    print(
        "         REGENERACIÓN TERMINADA"
    )
    print("=" * 60)
    print()

    print(
        f"[OK] Videos regenerados: "
        f"{procesadas}"
    )

    print(
        f"[SKIP] Videos omitidos: "
        f"{omitidas}"
    )

    print(
        f"[ERROR] Errores: "
        f"{errores}"
    )

    print()


# ==========================================================
# MENÚ
# ==========================================================

def main():

    while True:

        print()
        print("=" * 60)
        print(
            "                  VIDEOS API"
        )
        print("=" * 60)
        print()

        print(
            "1 - Generar video completo "
            "y subir a YouTube"
        )

        print(
            "2 - Regenerar videos existentes "
            "(solo MoviePy)"
        )

        print(
            "0 - Salir"
        )

        print()

        opcion = input(
            "Selecciona una opción: "
        ).strip()

        # --------------------------------------------------
        # SALIR
        # --------------------------------------------------

        if opcion == "0":

            print()
            print(
                "Saliendo del programa..."
            )

            break

        # --------------------------------------------------
        # PIPELINE COMPLETO
        # --------------------------------------------------

        elif opcion == "1":

            try:

                ejecutar_pipeline()

            except Exception as error:

                print()
                print("=" * 60)
                print(
                    "              ERROR EN PIPELINE"
                )
                print("=" * 60)
                print()

                print(
                    f"{type(error).__name__}: "
                    f"{error}"
                )

                print()

                # ------------------------------------------
                # Registrar error en BD
                # ------------------------------------------

                if IDEA_ACTUAL is not None:

                    registrar_error(
                        IDEA_ACTUAL,
                        error
                    )

                print(
                    "El estado de la idea NO fue "
                    "avanzado después del punto "
                    "que produjo el error."
                )

                print(
                    "En la próxima ejecución "
                    "se intentará continuar."
                )

                print("=" * 60)

        # --------------------------------------------------
        # REGENERAR VIDEOS
        # --------------------------------------------------

        elif opcion == "2":

            try:

                regenerar_videos_existentes()

            except Exception as error:

                print()
                print("=" * 60)
                print(
                    "          ERROR EN REGENERACIÓN"
                )
                print("=" * 60)
                print()

                print(
                    f"{type(error).__name__}: "
                    f"{error}"
                )

                print("=" * 60)

        # --------------------------------------------------
        # OPCIÓN INVÁLIDA
        # --------------------------------------------------

        else:

            print()
            print(
                "Opción no válida. "
                "Escribe 1, 2 o 0."
            )


# ==========================================================
# EJECUTAR
# ==========================================================

if __name__ == "__main__":

    main()