"""
MAIN - PIPELINE COMPLETO DE GENERACIÓN DE VIDEOS

1 -> Ejecutar proceso
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
    modificar_estado,
    contar_ideas_no_usadas,
    registrar_error,
    limpiar_error
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
# INICIALIZACIÓN
# ==========================================================

print()
print("=" * 60)
print("                    VIDEOS API")
print("=" * 60)
print()

print("[INFO] Inicializando base de datos...")

crear_tabla()

print("[OK] Base de datos lista.")


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

    return cargar_archivo_json(ruta)


def cargar_optimized_scenes(idea_id):
    """
    Carga las escenas con fichas optimizadas.
    """

    ruta = (
        ruta_idea(idea_id) /
        f"optimized_scenes_{idea_id}.json"
    )

    return cargar_archivo_json(ruta)


# ==========================================================
# SELECCIONAR IDEA
# ==========================================================

def seleccionar_idea():
    """
    Selecciona qué idea debe procesarse.

    PRIORIDAD:

    1. Idea que ya comenzó pero quedó incompleta.
    2. Idea nueva en estado IDEA.
    3. Generar nuevas ideas si no existen.
    """

    print(
        "[INFO] Buscando ideas incompletas..."
    )

    idea = obtener_idea_incompleta()

    if idea:

        idea_id, texto, guion_db, estado = idea

        print(
            f"[OK] Se encontró una idea incompleta."
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

        return idea_id, texto, guion_db, estado


    # ------------------------------------------------------
    # Buscar idea nueva
    # ------------------------------------------------------

    print(
        "[INFO] No hay ideas incompletas."
    )

    cantidad = contar_ideas_no_usadas()

    print(
        f"[INFO] Ideas nuevas disponibles: {cantidad}"
    )

    # ------------------------------------------------------
    # Generar más si tenemos pocas
    # ------------------------------------------------------

    if cantidad < 5:

        print(
            "[INFO] Hay menos de 5 ideas nuevas."
        )

        print(
            "[INFO] Generando nuevas ideas con IA..."
        )

        ideas_creadas = generar_ideas()

        print(
            f"[INFO] La IA generó "
            f"{len(ideas_creadas)} ideas."
        )

        for idea in ideas_creadas:

            guardar_idea(idea)

        print(
            "[OK] Nuevas ideas guardadas."
        )

    # ------------------------------------------------------
    # Obtener idea nueva
    # ------------------------------------------------------

    idea = obtener_idea_no_usada()

    if not idea:

        raise RuntimeError(
            "No fue posible obtener una idea."
        )

    idea_id, texto, guion_db, estado = idea

    print(
        f"[OK] Nueva idea seleccionada: #{idea_id}"
    )

    return idea_id, texto, guion_db, estado


# ==========================================================
# PIPELINE
# ==========================================================

def ejecutar_pipeline():

    print()
    print("=" * 60)
    print("          INICIANDO PIPELINE COMPLETO")
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

        print("[2/9] Generando guion...")

        guion = generate_guion(
            texto_idea,
            idea_id
        )

        if not guion:

            raise RuntimeError(
                "La generación del guion no devolvió contenido."
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
            "[2/9] GUION ya completado. Saltando..."
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

        print("[3/9] Generando escenas...")

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
            "[3/9] ESCENAS ya completadas. "
            "Cargando..."
        )

        scenes = cargar_scenes(
            idea_id
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
            "[4/9] Creando/cargando fichas..."
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
            "[4/9] FICHAS ya completadas. Saltando..."
        )

    print()


    # ======================================================
    # PASO 5 - OPTIMIZACIÓN
    # ======================================================

    if estado == "FICHAS":

        print(
            "[5/9] Optimizando fichas..."
        )

        optimized_scenes = optimizador_fichas(
            scenes,
            idea_id
        )

        if not optimized_scenes:

            raise RuntimeError(
                "No se pudieron optimizar las escenas."
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
            "[5/9] OPTIMIZACIÓN ya completada. "
            "Cargando..."
        )

        optimized_scenes = cargar_optimized_scenes(
            idea_id
        )

    else:

        optimized_scenes = None

    print()


    # ======================================================
    # PASO 6 - PROMPTS
    # ======================================================

    if estado == "OPTIMIZADO":

        print(
            "[6/9] Creando prompts de imagen..."
        )

        prompts = creador_prompts_imagenes(
            optimized_scenes,
            idea_id
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
            "[6/9] PROMPTS ya completados. Saltando..."
        )

    print()


    # ======================================================
    # PASO 7 - IMÁGENES
    # ======================================================

    if estado == "PROMPTS":

        print(
            "[7/9] Generando imágenes..."
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
            "[7/9] IMÁGENES ya completadas. Saltando..."
        )

    print()


    # ======================================================
    # PASO 8 - VOZ
    # ======================================================

    if estado == "IMAGENES":

        print(
            "[8/9] Generando narración..."
        )

        ruta_voz = generate_voice(
            guion,
            idea_id
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
            f"[OK] Narración generada: {ruta_voz}"
        )

    else:

        print(
            "[8/9] VOZ ya completada. Saltando..."
        )

    print()


    # ======================================================
    # PASO 9 - VIDEO
    # ======================================================

    if estado == "VOZ":

        print(
            "[9/9] Generando video final..."
        )

        ruta_video = generar_video(
            idea_id
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
            f"[OK] Video generado: {ruta_video}"
        )

    else:

        ruta_video = (
            ruta_idea(idea_id) /
            f"video_{idea_id}.mp4"
        )

        print(
            "[9/9] VIDEO ya generado. Saltando..."
        )

    print()


    # ======================================================
    # FINAL
    # ======================================================

    print("=" * 60)
    print("             PIPELINE TERMINADO")
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
    print("=" * 60)

    return ruta_video


# ==========================================================
# MENÚ
# ==========================================================

def main():

    while True:

        print()
        print("=" * 60)
        print("                  VIDEOS API")
        print("=" * 60)
        print()

        print(
            "1 - Generar video completo"
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
        # EJECUTAR PIPELINE
        # --------------------------------------------------

        elif opcion == "1":

            idea_id = None

            try:

                ruta_video = ejecutar_pipeline()

            except Exception as e:

                print()
                print("=" * 60)
                print("              ERROR EN PIPELINE")
                print("=" * 60)
                print()

                print(
                    f"{type(e).__name__}: {e}"
                )

                print()

                print(
                    "El estado de la idea NO fue "
                    "avanzado."
                )

                print(
                    "En la próxima ejecución "
                    "se intentará continuar."
                )

                print("=" * 60)


        # --------------------------------------------------
        # OPCIÓN INVÁLIDA
        # --------------------------------------------------

        else:

            print()
            print(
                "Opción no válida. "
                "Escribe 1 o 0."
            )


# ==========================================================
# EJECUTAR
# ==========================================================

if __name__ == "__main__":

    main()