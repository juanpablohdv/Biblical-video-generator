"""
GENERADOR DE VOZ CON GPT-4O-MINI-TTS
"""

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent
DIR_IDEAS = BASE_DIR / "data" / "ideas"

load_dotenv(dotenv_path=BASE_DIR / ".env")

client = OpenAI()


def generate_voice(text, idea_id):
    """
    Genera la narración del guion y la guarda
    dentro de la carpeta correspondiente a la idea.
    """

    ruta_idea = DIR_IDEAS / f"idea_{idea_id:05d}"

    ruta_idea.mkdir(
        parents=True,
        exist_ok=True
    )

    ruta_salida = ruta_idea / f"voz_{idea_id}.mp3"

    print(f"[INFO] Generando voz para idea #{idea_id}...")

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    ) as response:

        response.stream_to_file(ruta_salida)

    print(f"[OK] Voz guardada en: {ruta_salida}")

    return ruta_salida