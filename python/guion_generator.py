"GENERAR GUION CON OPENAI GPT-4O-MINI"

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from utils import cargar_prompts

BASE_DIR = Path(__file__).resolve().parent
DIR_IDEAS = BASE_DIR / "data" / "ideas"

load_dotenv(dotenv_path=BASE_DIR / ".env")

client=OpenAI()

def guardar_guion_a_archivo(id_idea, text):
    "Funcion para guardar el guion en un archivo de texto"
    carpeta = DIR_IDEAS / f"idea_{id_idea:05d}"
    carpeta.mkdir(parents=True, exist_ok=True)

    carpeta_imagenes = carpeta / "images"
    carpeta_imagenes.mkdir(parents=True, exist_ok=True)

    ruta = carpeta / f"guion_{id_idea}.txt"

    ruta.write_text(text, encoding="utf-8")

def generate_guion(idea, idea_id, tematica):
    """
    Genera el guion usando un prompt distinto
    según la temática de la idea.
    """

    tematica = (tematica or "").strip().upper()

    if tematica == "GENERICA":
        nombre_prompt = "guion_generico"

    elif tematica == "ESPECIFICA":
        nombre_prompt = "guion_especifico"

    else:
        raise ValueError(
            f"La idea #{idea_id} no tiene una temática válida: "
            f"{tematica!r}. Se esperaba GENERICA o ESPECIFICA."
        )

    print(
        f"[INFO] Generando guion para idea #{idea_id} "
        f"con el prompt: {nombre_prompt}"
    )

    prompt = cargar_prompts(
        nombre_prompt,
        idea=idea
    )

    response = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    respuesta = response.choices[0].message.content.strip()

    if not respuesta:
        raise RuntimeError(
            f"La IA devolvió un guion vacío para la idea #{idea_id}."
        )

    guardar_guion_a_archivo(
        idea_id,
        respuesta
    )

    return respuesta

def generate_voice(text, idea_id):
    "Funcion para generar voz a partir del guion"
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="cedar",
        input=text
    ) as response:
        respuesta =response.stream_to_file(DIR_IDEAS / f"idea_{idea_id:05d}" / f"voz_{idea_id}.mp3")
        return respuesta
