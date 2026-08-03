"MANEJAR GUION, ESCENAS, PERSONAJES Y FICHAS"

import json
from pathlib import Path
import unicodedata

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent
DIR_IDEAS = BASE_DIR / "ideas"
DIR_PERSONAJES = BASE_DIR / "personajes"
load_dotenv(dotenv_path=BASE_DIR / ".env")

client=OpenAI()

def cargar_prompts(prompt_name, **kwargs):
    "Funcion para cargar los prompts desde un archivo de texto (guion, scenes, images)"
    ruta = BASE_DIR / "prompts" / f"prompt_{prompt_name}.txt"
    with open(ruta, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(**kwargs)

def normalizar_nombre(nombre):
    "Funcion para normalizar el nombre de un personaje (eliminar acentos, mayusculas, etc.)"
    nombre = nombre.lower().strip()
    nombre = unicodedata.normalize("NFD", nombre)
    nombre = "".join(c for c in nombre if unicodedata.category(c) != "Mn")
    return nombre

def generate_scenes(guion):
    "Funcion para generar escenas a partir del guion"
    prompt = cargar_prompts("scenes", guion=guion)
    reponse = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    content = reponse.choices[0].message.content.strip()
    scenes = json.loads(content)
    return scenes

def crear_fichas(scenes):
    "Funcion para detectar personajes y crear fichas no existentes"
    personajes_unicos = {}

    for scene in scenes:
        for nombre in scene.get("characters", []):
            nombre_normalizado = normalizar_nombre(nombre)

            if nombre_normalizado not in personajes_unicos:
                personajes_unicos[nombre_normalizado] = nombre

    personajes = [
        {"name" :nombre_original}
        for nombre_original in personajes_unicos.values()
    ]

    for personaje in personajes:
        nombre_normalizado = normalizar_nombre(personaje["name"])
        ruta_ficha = DIR_PERSONAJES / f"{nombre_normalizado}.json"

        if not ruta_ficha.exists():
            prompt = cargar_prompts("characters", personaje=personaje["name"])
            reponse = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            content = reponse.choices[0].message.content.strip()

            try:
                ficha = json.loads(content)
                with open(ruta_ficha, "w", encoding="utf-8") as f:
                    json.dump(ficha, f, ensure_ascii=False, indent=4)

            except json.JSONDecodeError:
                print(f"Error al decodificar JSON para el personaje {personaje['name']}: {content}")

def cargar_ficha_personaje(nombre):
    """
    Carga la ficha técnica de un personaje desde assets/personajes/
    """

    nombre_normalizado = normalizar_nombre(nombre)
    ruta_ficha = DIR_PERSONAJES / f"{nombre_normalizado}.json"

    if not ruta_ficha.exists():
        raise FileNotFoundError(f"No se encontró la ficha del personaje: {nombre}")

    with open(ruta_ficha, "r", encoding="utf-8") as f:
        ficha = json.load(f)

    return ficha

def cargar_fichas_de_escena(scene):
    fichas = []

    for nombre in scene.get("characters", []):
        ficha = cargar_ficha_personaje(nombre)
        fichas.append(ficha)

    return fichas

def optimizador_fichas():
    "Funcion para optimizar las fichas de los personajes a partir de las escenas"
    



def creador_prompts_imagenes(characters, scene_description):
    "Funcion para crear prompts de imagen a partir de las escenas"
