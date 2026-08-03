"Generador de ideas con OpenAI GPT-4O-MINI"
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from guion_generator import cargar_prompts

# Cargar .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

client = OpenAI()

def generar_ideas():
    "Funcion para generar ideas a partir de un prompt"
    prompt = cargar_prompts("ideas")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    ideas_raw = response.choices[0].message.content
    ideas = [line.strip() for line in ideas_raw.split("\n") if line.strip()]
    return ideas


if __name__ == "__main__":
    ideas = generar_ideas()
    print("\nIDEAS GENERADAS:\n")
    for idea in ideas:
        print("-", idea)
