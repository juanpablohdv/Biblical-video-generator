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

def generate_guion(idea, idea_id):
    "Funcion de generacion de guion"

    prompt = cargar_prompts("guion", idea=idea)

    reponse = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    respuesta = reponse.choices[0].message.content.strip()
    guardar_guion_a_archivo(idea_id, respuesta)
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
