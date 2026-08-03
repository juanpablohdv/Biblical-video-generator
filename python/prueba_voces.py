"Prueba de generación de voz"

from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

client = OpenAI()

def genera_voz_prueba(voz):
    "Función de prueba para generar voz con diferentes voces disponibles"
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=voz,
        input="Andrea si yo veo vidrio en tu casa lo voy partiendo."
    ) as response:
        respuesta = response.stream_to_file(f"prueba_voz_Andrea_{voz}.mp3")
        return respuesta

if __name__ == "__main__":
    voces = ["onyx"]
    for voz_prueba in voces:
        genera_voz_prueba(voz_prueba)
