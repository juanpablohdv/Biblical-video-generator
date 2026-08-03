"GENERAR IMAGENES CON OPENAI GPT-4O-MINI"

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from manejo_guion import cargar_prompts

BASE_DIR = Path(__file__).resolve().parent
DIR_IDEAS = BASE_DIR / "ideas"
load_dotenv(dotenv_path=BASE_DIR / ".env")

client=OpenAI()

def generar_imagenes(idea_id, texto_idea):
    "Funcion para generar imagenes a partir del texto de la idea"
    prompt = "prompt"

    img = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1792" #vertical para reels
    )

    return img
