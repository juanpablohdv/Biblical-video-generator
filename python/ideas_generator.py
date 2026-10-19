
"""
GENERADOR DE IDEAS PARA VIDEOS CATOLICOS
"""

import json
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

from openai import OpenAI
from dotenv import load_dotenv

from utils import cargar_prompts
from ideas_db import (
    obtener_ultimas_14_genericas,
    obtener_ultima_programacion,
)


# ==========================================================
# CONFIGURACION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(dotenv_path=BASE_DIR / ".env")

client = OpenAI()

# Agrega aqui las paginas web que quieras consultar.
FUENTES_WEB = [
    # "https://ejemplo.com/santoral",
    # "https://ejemplo.com/calendario-liturgico",
    "https://es.wikipedia.org/wiki/Anexo:Santoral_cat%C3%B3lico#"
]

HORARIOS_PUBLICACION = (10, 14, 19)

CANTIDAD_IDEAS = 21


# ==========================================================
# EXTRAER TEXTO DE UNA PAGINA WEB
# ==========================================================

class ExtractorHTML(HTMLParser):
    """Extrae texto visible de una pagina HTML."""

    def __init__(self):
        super().__init__()
        self.textos = []
        self.omitir = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ("script", "style", "noscript"):
            self.omitir += 1

    def handle_endtag(self, tag):
        if tag.lower() in ("script", "style", "noscript"):
            self.omitir = max(0, self.omitir - 1)

    def handle_data(self, data):
        if not self.omitir and data.strip():
            self.textos.append(data.strip())


def leer_fuentes_web():
    """
    Lee las paginas configuradas en FUENTES_WEB.
    Si una pagina falla, continua con las demas.
    """

    contenidos = []

    for url in FUENTES_WEB:

        try:
            solicitud = Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            with urlopen(solicitud, timeout=15) as respuesta:
                html = respuesta.read().decode(
                    "utf-8",
                    errors="replace"
                )

            extractor = ExtractorHTML()
            extractor.feed(html)

            texto = " ".join(extractor.textos)

            # Limitar el texto para no enviar paginas enormes.
            texto = texto[:12000]

            contenidos.append(
                f"FUENTE: {url}\n{texto}"
            )

            print(f"[WEB] Fuente consultada: {url}")

        except Exception as error:
            print(
                f"[WEB] No se pudo leer {url}: {error}"
            )

    return "\n\n".join(contenidos)


# ==========================================================
# CALCULAR LAS PROXIMAS PUBLICACIONES
# ==========================================================


def calcular_programacion(fecha_base, cantidad=21):
    """
    Genera las proximas publicaciones y asigna la
    categoria correspondiente a cada horario.
    """

    programacion = []
    dia = fecha_base.date()

    while len(programacion) < cantidad:

        for hora in HORARIOS_PUBLICACION:

            fecha = datetime.combine(
                dia,
                datetime.min.time()
            ).replace(
                hour=hora,
                minute=0,
                second=0,
                microsecond=0
            )

            if fecha <= fecha_base:
                continue

            tematica = (
                "GENERICA"
                if hora == 19
                else "ESPECIFICA"
            )

            programacion.append({
                "fecha_publicacion": fecha.isoformat(),
                "tematica": tematica
            })

            if len(programacion) == cantidad:
                break

        dia += timedelta(days=1)

    return programacion


# ==========================================================
# GENERAR LAS 21 IDEAS
# ==========================================================

def generar_ideas():

    print("[IDEAS] Leyendo historial de ideas genericas...")

    historial = obtener_ultimas_14_genericas()

    historial_json = json.dumps(
        historial,
        ensure_ascii=False,
        indent=2
    )

    print(
        f"[IDEAS] Ideas genericas encontradas: {len(historial)}"
    )

    print("[IDEAS] Consultando ultima programacion...")

    fecha_base = obtener_ultima_programacion()

    print(
        f"[IDEAS] Fecha base: {fecha_base.isoformat()}"
    )

    programacion = calcular_programacion(
        fecha_base,
        CANTIDAD_IDEAS
    )

    programacion_json = json.dumps(
        [
            fecha.isoformat()
            for fecha in programacion
        ],
        ensure_ascii=False,
        indent=2
    )

    print("[IDEAS] Consultando fuentes web...")

    fuentes_web = leer_fuentes_web()

    if not fuentes_web:
        fuentes_web = (
            "No se pudo obtener contenido de las fuentes web. "
            "No inventes celebraciones ni afirmes haberlas verificado."
        )

    print("[IDEAS] Cargando prompt...")

    prompt = cargar_prompts(
        "ideas",
        historial_genericas=historial_json,
        programacion=programacion_json,
        fuentes_web=fuentes_web
    )

    print("[IDEAS] Solicitando ideas a OpenAI...")

    response = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    contenido = response.choices[0].message.content

    if not contenido:
        raise ValueError(
            "OpenAI devolvio una respuesta vacia."
        )

    datos = json.loads(contenido)

    ideas = datos["ideas"]

    if len(ideas) != CANTIDAD_IDEAS:
        raise ValueError(
            f"Se esperaban {CANTIDAD_IDEAS} ideas, "
            f"pero se recibieron {len(ideas)}."
        )

    # Asignar la categoria segun la posicion.
    # Dos especificas y una generica.
    resultado = []

    for indice, idea in enumerate(ideas):

        tematica_esperada = (
            "GENERICA"
            if indice % 3 == 2
            else "ESPECIFICA"
        )

        texto = idea.get("texto", "").strip()

        if not texto:
            raise ValueError(
                f"La idea {indice + 1} no tiene texto."
            )

        resultado.append({
            "texto": texto,
            "tematica": tematica_esperada,
            "fecha_publicacion": (
                programacion[indice].isoformat()
            ),
            "celebracion": idea.get(
                "celebracion",
                ""
            )
        })

    print(
        f"[IDEAS] Ideas preparadas: {len(resultado)}"
    )

    return resultado


if __name__ == "__main__":

    ideas = generar_ideas()

    print("\nIDEAS GENERADAS:\n")

    for idea in ideas:
        print(
            f"{idea['fecha_publicacion']} | "
            f"{idea['tematica']} | "
            f"{idea['texto']}"
        )
