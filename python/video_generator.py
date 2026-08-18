"""
GENERADOR DE VIDEO A PARTIR DE IMÁGENES Y NARRACIÓN
"""

from pathlib import Path

from moviepy import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips
)


BASE_DIR = Path(__file__).resolve().parent
DIR_IDEAS = BASE_DIR / "data" / "ideas"


def generar_video(idea_id):
    """
    Genera un video vertical utilizando las imágenes
    de las escenas y la narración del guion.
    """

    ruta_idea = DIR_IDEAS / f"idea_{idea_id:05d}"

    ruta_imagenes = ruta_idea / "imagenes"
    ruta_voz = ruta_idea / f"voz_{idea_id}.mp3"

    ruta_video = ruta_idea / f"video_{idea_id}.mp4"

    # --------------------------------------------------
    # Verificar imágenes
    # --------------------------------------------------

    if not ruta_imagenes.exists():
        raise FileNotFoundError(
            f"No existe la carpeta de imágenes: {ruta_imagenes}"
        )

    archivos_imagenes = sorted(
        ruta_imagenes.glob("scene_*.png")
    )

    if not archivos_imagenes:
        raise FileNotFoundError(
            f"No se encontraron imágenes en: {ruta_imagenes}"
        )

    # --------------------------------------------------
    # Verificar voz
    # --------------------------------------------------

    if not ruta_voz.exists():
        raise FileNotFoundError(
            f"No se encontró la narración: {ruta_voz}"
        )

    print(
        f"[INFO] Imágenes encontradas: "
        f"{len(archivos_imagenes)}"
    )

    print(f"[INFO] Voz encontrada: {ruta_voz}")

    # --------------------------------------------------
    # Cargar narración
    # --------------------------------------------------

    audio = AudioFileClip(str(ruta_voz))

    duracion_audio = audio.duration

    print(
        f"[INFO] Duración de la narración: "
        f"{duracion_audio:.2f} segundos"
    )

    # --------------------------------------------------
    # Calcular duración por imagen
    # --------------------------------------------------

    duracion_por_imagen = (
        duracion_audio / len(archivos_imagenes)
    )

    print(
        f"[INFO] Duración por imagen: "
        f"{duracion_por_imagen:.2f} segundos"
    )

    # --------------------------------------------------
    # Crear clips
    # --------------------------------------------------

    clips = []

    for ruta_imagen in archivos_imagenes:

        print(
            f"[INFO] Procesando: "
            f"{ruta_imagen.name}"
        )

        clip = (
            ImageClip(str(ruta_imagen))
            .with_duration(duracion_por_imagen)
        )

        clips.append(clip)

    # --------------------------------------------------
    # Unir imágenes
    # --------------------------------------------------

    video = concatenate_videoclips(
        clips,
        method="compose"
    )

    # --------------------------------------------------
    # Añadir narración
    # --------------------------------------------------

    video = video.with_audio(audio)

    # --------------------------------------------------
    # Exportar
    # --------------------------------------------------

    print(
        f"[INFO] Generando video: "
        f"{ruta_video}"
    )

    video.write_videofile(
        str(ruta_video),
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )

    # --------------------------------------------------
    # Liberar recursos
    # --------------------------------------------------

    audio.close()
    video.close()

    for clip in clips:
        clip.close()

    print(
        f"[OK] Video generado correctamente: "
        f"{ruta_video}"
    )

    return ruta_video