"""
GENERADOR DE IMÁGENES CON GPT-IMAGE-1
"""

from pathlib import Path
import base64

from openai import OpenAI
from dotenv import load_dotenv


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DIR_IDEAS = BASE_DIR.parent / "data" / "ideas"

load_dotenv(BASE_DIR.parent / ".env")

client = OpenAI()


# ============================================================
# GENERAR IMAGEN
# ============================================================

def generar_imagen(prompt, ruta_salida):
    """
    Genera una imagen utilizando GPT-Image-1
    y la guarda en la ruta indicada.
    """

    print(f"[INFO] Generando imagen: {ruta_salida.name}")

    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1536"
    )

    image_base64 = response.data[0].b64_json

    image_bytes = base64.b64decode(image_base64)

    ruta_salida.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    ruta_salida.write_bytes(image_bytes)

    print(f"[OK] Imagen guardada: {ruta_salida}")

    return ruta_salida


# ============================================================
# GENERAR IMÁGENES DE UNA IDEA
# ============================================================

def generar_imagenes(idea_id):
    """
    Lee todos los prompts de una idea y genera
    una imagen por cada escena.
    """

    ruta_prompts = (
        DIR_IDEAS
        / f"idea_{idea_id:05d}"
        / "prompts"
    )

    ruta_imagenes = (
        DIR_IDEAS
        / f"idea_{idea_id:05d}"
        / "imagenes"
    )

    if not ruta_prompts.exists():
        raise FileNotFoundError(
            f"No existe la carpeta de prompts: {ruta_prompts}"
        )

    archivos_prompts = sorted(
        ruta_prompts.glob("scene_*.txt")
    )

    if not archivos_prompts:
        raise FileNotFoundError(
            f"No se encontraron prompts en: {ruta_prompts}"
        )

    print(
        f"[INFO] Se encontraron "
        f"{len(archivos_prompts)} prompts."
    )

    for ruta_prompt in archivos_prompts:

        prompt = ruta_prompt.read_text(
            encoding="utf-8"
        ).strip()

        nombre_imagen = (
            ruta_prompt.stem + ".png"
        )

        ruta_imagen = (
            ruta_imagenes / nombre_imagen
        )

        generar_imagen(
            prompt,
            ruta_imagen
        )

    print("[OK] Todas las imágenes fueron generadas.")
