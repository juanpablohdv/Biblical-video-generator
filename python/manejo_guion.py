"MANEJAR GUION, ESCENAS, PERSONAJES Y FICHAS"

import json
from pathlib import Path
import unicodedata

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent
DIR_IDEAS = BASE_DIR /"data" / "ideas"
DIR_PERSONAJES = BASE_DIR / "data" / "personajes"
load_dotenv(dotenv_path=BASE_DIR / ".env")

client=OpenAI()

def cargar_prompts(prompt_name, **kwargs):
    "Funcion para cargar los prompts desde un archivo de texto (guion, scenes, images)"
    ruta = BASE_DIR / "assets" / "prompts" / f"prompt_{prompt_name}.txt"
    with open(ruta, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(**kwargs)

def guardar_json(ruta, datos):
    """
    Guarda un objeto Python como archivo JSON.
    """

    ruta.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(
            datos,
            f,
            ensure_ascii=False,
            indent=4
        )

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
    """
    Revisa todos los personajes presentes en las escenas.
    Si una ficha ya existe, la conserva.
    Si no existe, la genera mediante OpenAI.
    """

    personajes_unicos = {}

    # --------------------------------------------------
    # 1. Obtener personajes únicos de todas las escenas
    # --------------------------------------------------

    for scene in scenes:

        for nombre in scene.get("characters", []):

            nombre_normalizado = normalizar_nombre(nombre)

            if nombre_normalizado not in personajes_unicos:
                personajes_unicos[nombre_normalizado] = nombre

    print(f"\n[INFO] Personajes detectados: {len(personajes_unicos)}")

    # --------------------------------------------------
    # 2. Revisar cada personaje
    # --------------------------------------------------

    for nombre_normalizado, nombre_original in personajes_unicos.items():

        ruta_ficha = DIR_PERSONAJES / f"{nombre_normalizado}.json"

        # --------------------------------------------------
        # 3. Si la ficha ya existe
        # --------------------------------------------------

        if ruta_ficha.exists():

            print(f"[OK] Ficha existente: {nombre_original}")
            continue

        # --------------------------------------------------
        # 4. Si la ficha NO existe, crearla
        # --------------------------------------------------

        print(f"[NEW] Creando ficha: {nombre_original}")

        prompt = cargar_prompts(
            "characters",
            personaje=nombre_original
        )

        # --------------------------------------------------
        # 5. Intentar generar la ficha
        # --------------------------------------------------

        max_intentos = 3

        for intento in range(1, max_intentos + 1):

            try:

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                content = response.choices[0].message.content.strip()

                ficha = json.loads(content)

                # ------------------------------------------
                # 6. Guardar ficha
                # ------------------------------------------

                with open(
                    ruta_ficha,
                    "w",
                    encoding="utf-8"
                ) as f:

                    json.dump(
                        ficha,
                        f,
                        ensure_ascii=False,
                        indent=4
                    )

                print(f"[OK] Ficha creada: {nombre_original}")

                break

            except json.JSONDecodeError:

                print(
                    f"[WARNING] JSON inválido para "
                    f"{nombre_original}. "
                    f"Intento {intento}/{max_intentos}"
                )

                if intento == max_intentos:

                    print(
                        f"[ERROR] No se pudo crear la ficha "
                        f"de {nombre_original}"
                    )

            except Exception as e:

                print(
                    f"[ERROR] Error creando ficha "
                    f"{nombre_original}: {e}"
                )

                break

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

def optimizador_fichas(scenes):
    """
    Optimiza las fichas de cada escena.

    Mantiene las fichas completas de los personajes principales
    y resume las de los personajes secundarios.
    """

    escenas_optimizadas = []

    for scene in scenes:

        fichas = cargar_fichas_de_escena(scene)

        prompt = cargar_prompts(
            "optimizer",
            scene=json.dumps(scene, ensure_ascii=False, indent=4),
            fichas=json.dumps(fichas, ensure_ascii=False, indent=4)
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content.strip()

        escena_optimizada = json.loads(content)

        escenas_optimizadas.append(escena_optimizada)

    return escenas_optimizadas



def creador_prompts_imagenes(characters, scene_description):
    "Funcion para crear prompts de imagen a partir de las escenas"
