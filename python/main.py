"""
MAIN - PIPELINE COMPLETO DE GENERACIÓN DE VIDEOS

1 -> Ejecutar todo el proceso
0 -> Salir
"""

from ideas_db import (
    crear_tabla,
    guardar_idea,
    obtener_idea_no_usada,
    modificar_estado,
    contar_ideas_no_usadas
)

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
# INICIALIZACIÓN
# ==========================================================

print()
print("=" * 60)
print("             VIDEOS API")
print("=" * 60)
print()

print("[INFO] Inicializando base de datos...")

crear_tabla()

print("[OK] Base de datos lista.")


# ==========================================================
# PIPELINE COMPLETO
# ==========================================================

def ejecutar_pipeline():

    print()
    print("=" * 60)
    print("          INICIANDO PIPELINE COMPLETO")
    print("=" * 60)
    print()

    # ======================================================
    # 1. OBTENER / GENERAR IDEA
    # ======================================================

    print("[1/9] Buscando una idea disponible...")

    cantidad_ideas = contar_ideas_no_usadas()

    print(
        f"[INFO] Ideas disponibles: {cantidad_ideas}"
    )

    # ------------------------------------------------------
    # Si tenemos menos de 5 ideas, generamos más
    # ------------------------------------------------------

    if cantidad_ideas < 5:

        print(
            "[INFO] Hay menos de 5 ideas disponibles."
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
            "[OK] Nuevas ideas guardadas en la base de datos."
        )

    # ------------------------------------------------------
    # Obtener una idea
    # ------------------------------------------------------

    idea_data = obtener_idea_no_usada()

    if not idea_data:

        raise RuntimeError(
            "No hay ninguna idea disponible para procesar."
        )

    idea_id, texto_idea = idea_data

    print(
        f"[OK] Idea seleccionada: #{idea_id}"
    )

    print(
        f"      {texto_idea}"
    )

    print()


    # ======================================================
    # 2. GENERAR GUION
    # ======================================================

    print("[2/9] Generando guion...")

    guion = generate_guion(
        texto_idea,
        idea_id
    )

    if not guion:

        raise RuntimeError(
            "La generación del guion no devolvió contenido."
        )

    print("[OK] Guion generado y guardado.")

    modificar_estado(
        idea_id,
        "GUION"
    )

    print(
        f"[INFO] Estado de idea #{idea_id}: GUION"
    )

    print()


    # ======================================================
    # 3. GENERAR ESCENAS
    # ======================================================

    print("[3/9] Generando escenas...")

    scenes = generate_scenes(
        guion,
        idea_id
    )

    if not scenes:

        raise RuntimeError(
            "No se generaron escenas."
        )

    print(
        f"[OK] Se generaron "
        f"{len(scenes)} escenas."
    )

    print()


    # ======================================================
    # 4. CREAR / CARGAR FICHAS
    # ======================================================

    print(
        "[4/9] Creando/cargando fichas "
        "de personajes..."
    )

    crear_fichas(
        scenes
    )

    print(
        "[OK] Fichas de personajes listas."
    )

    print()


    # ======================================================
    # 5. OPTIMIZAR FICHAS
    # ======================================================

    print(
        "[5/9] Optimizando fichas "
        "por escena..."
    )

    optimized_scenes = optimizador_fichas(
        scenes,
        idea_id
    )

    if not optimized_scenes:

        raise RuntimeError(
            "No se pudieron optimizar "
            "las escenas."
        )

    print(
        "[OK] Fichas optimizadas."
    )

    print()


    # ======================================================
    # 6. CREAR PROMPTS DE IMAGEN
    # ======================================================

    print(
        "[6/9] Creando prompts "
        "para las imágenes..."
    )

    prompts = creador_prompts_imagenes(
        optimized_scenes,
        idea_id
    )

    if not prompts:

        raise RuntimeError(
            "No se generaron prompts "
            "para las imágenes."
        )

    print(
        f"[OK] Se generaron "
        f"{len(prompts)} prompts."
    )

    print()


    # ======================================================
    # 7. GENERAR IMÁGENES
    # ======================================================

    print(
        "[7/9] Generando imágenes "
        "con GPT-Image-1..."
    )

    generar_imagenes(
        idea_id
    )

    print(
        "[OK] Imágenes generadas."
    )

    print()


    # ======================================================
    # 8. GENERAR VOZ
    # ======================================================

    print(
        "[8/9] Generando narración..."
    )

    ruta_voz = generate_voice(
        guion,
        idea_id
    )

    if not ruta_voz:

        raise RuntimeError(
            "No se pudo generar "
            "la narración."
        )

    print(
        f"[OK] Narración generada: "
        f"{ruta_voz}"
    )

    modificar_estado(
        idea_id,
        "VOZ"
    )

    print(
        f"[INFO] Estado de idea #{idea_id}: VOZ"
    )

    print()


    # ======================================================
    # 9. GENERAR VIDEO FINAL
    # ======================================================

    print(
        "[9/9] Generando video final..."
    )

    ruta_video = generar_video(
        idea_id
    )

    if not ruta_video:

        raise RuntimeError(
            "No se pudo generar "
            "el video final."
        )

    print(
        "[OK] Video generado correctamente."
    )

    modificar_estado(
        idea_id,
        "V_FINAL"
    )

    print(
        f"[INFO] Estado de idea #{idea_id}: V_FINAL"
    )

    print()


    # ======================================================
    # FINAL
    # ======================================================

    print("=" * 60)
    print("             PIPELINE TERMINADO")
    print("=" * 60)
    print()

    print("VIDEO FINAL:")
    print()

    print(
        ruta_video
    )

    print()
    print("=" * 60)

    return ruta_video


# ==========================================================
# MENÚ PRINCIPAL
# ==========================================================

def main():

    while True:

        print()
        print("=" * 60)
        print("                  VIDEOS API")
        print("=" * 60)
        print()
        print("1 - Generar video completo")
        print("0 - Salir")
        print()

        opcion = input(
            "Selecciona una opción: "
        ).strip()

        # --------------------------------------------------
        # SALIR
        # --------------------------------------------------

        if opcion == "0":

            print()
            print("Saliendo del programa...")
            break

        # --------------------------------------------------
        # PIPELINE COMPLETO
        # --------------------------------------------------

        elif opcion == "1":

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
                    "El pipeline se detuvo."
                )

                print("=" * 60)

        # --------------------------------------------------
        # OPCIÓN INCORRECTA
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