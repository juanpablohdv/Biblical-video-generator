from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

client = OpenAI()

def generate_voice(text,salida="voz.mp3"):
    "Funcion para generar voz a partir del guion"
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    ) as response:
        response.stream_to_file(BASE_DIR /salida)