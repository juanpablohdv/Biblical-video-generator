"""
GENERADOR DE VIDEO A PARTIR DE IMÁGENES,
NARRACIÓN, MÚSICA Y SUBTÍTULOS
"""

from pathlib import Path
import re

from moviepy import (
    ImageClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips
)

from moviepy.audio.fx import AudioLoop


# ==========================================================
# RUTAS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

DIR_IDEAS = BASE_DIR / "data" / "ideas"

DIR_MUSIC = BASE_DIR / "assets" / "music"

FONT_SUBTITULOS = BASE_DIR / "assets" / "fonts" / "Montserrat-SemiBold.ttf"

# ==========================================================
# SELECCIONAR MÚSICA
# ==========================================================

def seleccionar_musica(idea_id):
    """
    Selecciona automáticamente una pista de música
    basándose en el ID de la idea.

    Si existen 6 músicas:

    idea 1 -> música 1
    idea 2 -> música 2
    ...
    idea 6 -> música 6
    idea 7 -> música 1
    """

    musicas = sorted(DIR_MUSIC.glob("*.mp3"))

    if not musicas:
        raise FileNotFoundError(
            f"No se encontraron músicas en: {DIR_MUSIC}"
        )

    indice = (idea_id - 1) % len(musicas)

    musica = musicas[indice]

    print(f"[INFO] Música seleccionada: {musica.name}")

    return musica


# ==========================================================
# CREAR SUBTÍTULOS
# ==========================================================

def crear_subtitulos(guion, duracion_audio):
    """
    Divide el guion en frases y bloques de subtítulos.

    - Máximo aproximadamente 32 caracteres por línea.
    - Nunca corta una palabra.
    - Mantiene las palabras completas.
    - La duración se reparte proporcionalmente
      según la cantidad de palabras.
    """

    # ------------------------------------------------------
    # Limpiar texto
    # ------------------------------------------------------

    guion = guion.replace("\ufeff", "").strip()

    # ------------------------------------------------------
    # Dividir el guion por frases
    # ------------------------------------------------------

    frases = re.split(
        r'(?<=[.!?])\s+',
        guion
    )

    frases = [
        frase.strip()
        for frase in frases
        if frase.strip()
    ]

    if not frases:
        return []

    # ------------------------------------------------------
    # Crear bloques sin cortar palabras
    # ------------------------------------------------------

    bloques = []

    for frase in frases:

        palabras = frase.split()

        bloque_actual = ""

        for palabra in palabras:

            # Primera palabra del bloque
            if not bloque_actual:

                bloque_actual = palabra

            # Si la palabra cabe, agregarla
            elif len(bloque_actual) + 1 + len(palabra) <= 32:

                bloque_actual += " " + palabra

            # Si no cabe, empezar nuevo bloque
            else:

                bloques.append(bloque_actual)

                bloque_actual = palabra

        # Guardar último bloque
        if bloque_actual:

            bloques.append(bloque_actual)

    # ------------------------------------------------------
    # Contar palabras
    # ------------------------------------------------------

    total_palabras = sum(
        len(bloque.split())
        for bloque in bloques
    )

    subtitulos = []

    tiempo_actual = 0

    # ------------------------------------------------------
    # Distribuir duración
    # ------------------------------------------------------

    for bloque in bloques:

        palabras = len(bloque.split())

        duracion = (
            palabras / total_palabras
        ) * duracion_audio

        subtitulos.append({
            "inicio": tiempo_actual,
            "fin": tiempo_actual + duracion,
            "texto": bloque
        })

        tiempo_actual += duracion

    return subtitulos

# ==========================================================
# CREAR CLIPS DE TEXTO
# ==========================================================

def crear_clips_subtitulos(
    subtitulos,
    video_width,
    video_height
):
    """
    Convierte los subtítulos en TextClips de MoviePy.
    """

    clips_subtitulos = []

    for subtitulo in subtitulos:

        texto = subtitulo["texto"]

        duracion = (
            subtitulo["fin"]
            - subtitulo["inicio"]
        )

        # --------------------------------------------------
        # Crear texto
        # --------------------------------------------------

        clip = TextClip(
            text=texto,
            font=str(FONT_SUBTITULOS),
            font_size=58,
            color="white",
            stroke_color="black",
            stroke_width=3,
            method="caption",
            size=(video_width - 160, None),
            text_align="center"
        )   

        # --------------------------------------------------
        # Posición y duración
        # --------------------------------------------------

        clip = (
            clip
            .with_start(subtitulo["inicio"])
            .with_duration(duracion)
            .with_position(
                ("center", video_height - 500)
            )
        )

        clips_subtitulos.append(clip)

    return clips_subtitulos


# ==========================================================
# GENERAR VIDEO
# ==========================================================

def generar_video(idea_id):
    """
    Genera un video vertical utilizando:

    - Imágenes de las escenas
    - Narración
    - Música de fondo
    - Subtítulos
    """

    # ======================================================
    # RUTAS DE LA IDEA
    # ======================================================

    ruta_idea = (
        DIR_IDEAS /
        f"idea_{idea_id:05d}"
    )

    ruta_images = (
        ruta_idea /
        "images"
    )

    ruta_voz = (
        ruta_idea /
        f"voz_{idea_id}.mp3"
    )

    ruta_guion = (
        ruta_idea /
        f"guion_{idea_id}.txt"
    )

    ruta_video = (
        ruta_idea /
        f"video_{idea_id}.mp4"
    )

    # ======================================================
    # VERIFICAR IMÁGENES
    # ======================================================

    if not ruta_images.exists():

        raise FileNotFoundError(
            f"No existe la carpeta de imágenes: "
            f"{ruta_images}"
        )

    archivos_images = sorted(
        ruta_images.glob("scene_*.png")
    )

    if not archivos_images:

        raise FileNotFoundError(
            f"No se encontraron imágenes en: "
            f"{ruta_images}"
        )

    print(
        f"[INFO] Imágenes encontradas: "
        f"{len(archivos_images)}"
    )

    # ======================================================
    # VERIFICAR VOZ
    # ======================================================

    if not ruta_voz.exists():

        raise FileNotFoundError(
            f"No se encontró la narración: "
            f"{ruta_voz}"
        )

    print(
        f"[INFO] Voz encontrada: "
        f"{ruta_voz}"
    )

    # ======================================================
    # VERIFICAR GUION
    # ======================================================

    if not ruta_guion.exists():

        raise FileNotFoundError(
            f"No se encontró el guion: "
            f"{ruta_guion}"
        )

    print(
        f"[INFO] Guion encontrado: "
        f"{ruta_guion}"
    )

    # ======================================================
    # CARGAR GUION
    # ======================================================

    with open(
        ruta_guion,
        "r",
        encoding="utf-8"
    ) as f:

        guion = f.read().strip()

    print("[DEBUG] GUION:")
    print(repr(guion))

    # ======================================================
    # CARGAR NARRACIÓN
    # ======================================================

    audio = AudioFileClip(
        str(ruta_voz)
    )

    duracion_audio = audio.duration

    print(
        f"[INFO] Duración de la narración: "
        f"{duracion_audio:.2f} segundos"
    )

    # ======================================================
    # CALCULAR DURACIÓN POR IMAGEN
    # ======================================================

    duracion_por_imagen = (
        duracion_audio /
        len(archivos_images)
    )

    print(
        f"[INFO] Duración por imagen: "
        f"{duracion_por_imagen:.2f} segundos"
    )

    # ======================================================
    # CREAR CLIPS DE IMÁGENES
    # ======================================================

    clips = []

    for ruta_imagen in archivos_images:

        print(
            f"[INFO] Procesando imagen: "
            f"{ruta_imagen.name}"
        )

        clip = (
            ImageClip(
                str(ruta_imagen)
            )
            .with_duration(
                duracion_por_imagen
            )
        )

        clips.append(clip)

    # ======================================================
    # UNIR IMÁGENES
    # ======================================================

    print("[INFO] Uniendo imágenes...")

    video_base = concatenate_videoclips(
        clips,
        method="compose"
    )

    print(
        f"[INFO] Resolución del video: "
        f"{video_base.w}x{video_base.h}"
    )

    # ======================================================
    # CREAR SUBTÍTULOS
    # ======================================================

    print("[INFO] Generando subtítulos...")

    subtitulos = crear_subtitulos(
        guion,
        duracion_audio
    )

    print(
        f"[INFO] Subtítulos generados: "
        f"{len(subtitulos)}"
    )

    clips_subtitulos = crear_clips_subtitulos(
        subtitulos,
        video_base.w,
        video_base.h
    )

    # ======================================================
    # AÑADIR SUBTÍTULOS AL VIDEO
    # ======================================================

    print("[INFO] Añadiendo subtítulos...")

    video = CompositeVideoClip(
        [
            video_base,
            *clips_subtitulos
        ]
    )

    # ======================================================
    # SELECCIONAR MÚSICA
    # ======================================================

    ruta_musica = seleccionar_musica(
        idea_id
    )

    # ======================================================
    # CARGAR MÚSICA
    # ======================================================

    musica = AudioFileClip(
        str(ruta_musica)
    )

    # ======================================================
    # HACER LOOP DE LA MÚSICA
    # ======================================================

    musica = musica.with_effects([
        AudioLoop(
            duration=duracion_audio
        )
    ])

    # ------------------------------------------------------
    # Bajar volumen de la música
    # ------------------------------------------------------

    musica = musica.with_volume_scaled(
        0.12
    )

    # ======================================================
    # COMBINAR AUDIOS
    # ======================================================

    print(
        "[INFO] Combinando narración y música..."
    )

    audio_final = CompositeAudioClip([
        audio,
        musica
    ])

    # ======================================================
    # AÑADIR AUDIO AL VIDEO
    # ======================================================

    video = video.with_audio(
        audio_final
    )

    # ======================================================
    # EXPORTAR
    # ======================================================

    print(
        f"[INFO] Generando video final: "
        f"{ruta_video}"
    )

    video.write_videofile(
        str(ruta_video),
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )

    # ======================================================
    # LIBERAR RECURSOS
    # ======================================================

    print("[INFO] Liberando recursos...")

    audio.close()
    musica.close()
    video_base.close()
    video.close()

    for clip in clips:
        clip.close()

    for clip in clips_subtitulos:
        clip.close()

    print(
        f"[OK] Video generado correctamente: "
        f"{ruta_video}"
    )

    return ruta_video