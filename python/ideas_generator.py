"""Generador de ideas para videos catolicos."""

import json
import re
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from openai import OpenAI

from ideas_db import (
    obtener_ultimas_14_genericas,
    obtener_ultima_programacion,
)
from utils import cargar_prompts


# ==========================================================
# CONFIGURACION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")
client = OpenAI()

# Agrega aqui las paginas web que quieras consultar.
FUENTES_WEB = [
    "https://es.wikipedia.org/wiki/Anexo:Santoral_cat%C3%B3lico",
    # "https://URL-DE-OTRA-FUENTE",
]

HORARIOS_PUBLICACION = (10, 14, 19)
CANTIDAD_IDEAS = 21


# ==========================================================
# EXTRAER TEXTO DE UNA PAGINA WEB
# ==========================================================

class ExtractorHTML(HTMLParser):
    """Extrae texto visible de una pagina HTML."""

    ETIQUETAS_OMITIR = {"script", "style", "noscript", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.textos = []
        self.omitir = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.ETIQUETAS_OMITIR:
            self.omitir += 1

    def handle_endtag(self, tag):
        if tag.lower() in self.ETIQUETAS_OMITIR:
            self.omitir = max(0, self.omitir - 1)

    def handle_data(self, data):
        texto = data.strip()
        if not self.omitir and texto:
            self.textos.append(texto)



MESES_ES = (
    "enero", "febrero", "marzo", "abril",
    "mayo", "junio", "julio", "agosto",
    "septiembre", "octubre", "noviembre", "diciembre"
)


def leer_fuentes_web(programacion):
    """Extrae contenido relevante para las fechas programadas."""

    contenidos = []

    for url in FUENTES_WEB:
        try:
            solicitud = Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            with urlopen(solicitud, timeout=20) as respuesta:
                html = respuesta.read().decode(
                    "utf-8",
                    errors="replace"
                )

            extractor = ExtractorHTML()
            extractor.feed(html)
            texto = " ".join(extractor.textos)

            if not texto:
                print(f"[WEB] Sin texto legible: {url}")
                continue

            fragmentos = []
            fragmentos_vistos = set()

            for slot in programacion:
                fecha = datetime.fromisoformat(
                    slot["fecha_publicacion"]
                )

                dia = fecha.day
                mes = MESES_ES[fecha.month - 1]

                patron = (
                    rf"\b{dia}\s+de\s+{mes}"
                    rf"(?:\s+de\s+\d{{4}})?\b"
                )

                for coincidencia in re.finditer(
                    patron, texto, re.IGNORECASE
                ):
                    inicio = max(0, coincidencia.start() - 700)
                    fin = min(len(texto), coincidencia.end() + 1800)
                    fragmento = texto[inicio:fin].strip()

                    if fragmento not in fragmentos_vistos:
                        fragmentos.append(
                            f"Fecha buscada: {dia} de {mes}\n"
                            f"{fragmento}"
                        )
                        fragmentos_vistos.add(fragmento)

            if fragmentos:
                contenidos.append(
                    f"FUENTE: {url}\n"
                    + "\n\n".join(fragmentos)
                )
                print(
                    f"[WEB] Se encontraron fragmentos "
                    f"para fechas programadas: {url}"
                )

            elif len(texto) <= 18000:
                # Una fuente corta puede aportar contexto general.
                contenidos.append(
                    f"FUENTE: {url}\nCONTENIDO:\n{texto}"
                )
                print(
                    f"[WEB] Fuente general consultada: {url}. "
                    "No se identificaron fechas concretas."
                )

            else:
                print(
                    f"[WEB] No se encontraron fechas programadas "
                    f"en la fuente extensa: {url}"
                )

        except Exception as error:
            print(f"[WEB] No se pudo leer {url}: {error}")

    return "\n\n".join(contenidos)


# ==========================================================
# CALCULAR LAS PROXIMAS PUBLICACIONES
# ==========================================================

def calcular_programacion(fecha_base, cantidad=CANTIDAD_IDEAS):
    """Genera los siguientes espacios de publicacion y su categoria."""
    if not isinstance(fecha_base, datetime):
        raise TypeError("fecha_base debe ser un objeto datetime.")

    # Para evitar errores al comparar fechas, trabajamos con fechas locales sin zona horaria.
    if fecha_base.tzinfo is not None:
        fecha_base = fecha_base.astimezone().replace(tzinfo=None)

    programacion = []
    dia = fecha_base.date()

    while len(programacion) < cantidad:
        for hora in HORARIOS_PUBLICACION:
            fecha = datetime.combine(dia, datetime.min.time()).replace(
                hour=hora,
                minute=0,
                second=0,
                microsecond=0,
            )

            # Solo se consideran horarios posteriores a la fecha base.
            if fecha <= fecha_base:
                continue

            tematica = "GENERICA" if hora == 19 else "ESPECIFICA"
            programacion.append({
                "fecha_publicacion": fecha.isoformat(timespec="seconds"),
                "tematica": tematica,
            })

            if len(programacion) >= cantidad:
                break

        dia += timedelta(days=1)

    return programacion


# ==========================================================
# INTERPRETAR LA RESPUESTA JSON DE OPENAI
# ==========================================================

def interpretar_respuesta_json(contenido):
    """Convierte la respuesta del modelo en un diccionario JSON."""
    contenido = contenido.strip()

    # Tolerar bloques Markdown por si el modelo los devuelve.
    if contenido.startswith("```"):
        lineas = contenido.splitlines()
        if lineas and lineas[0].startswith("```"):
            lineas = lineas[1:]
        if lineas and lineas[-1].strip() == "```":
            lineas = lineas[:-1]
        contenido = "\n".join(lineas).strip()

    try:
        return json.loads(contenido)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"OpenAI no devolvio un JSON valido: {error}"
        ) from error


# ==========================================================
# GENERAR LAS 21 IDEAS
# ==========================================================

def generar_ideas():
    print("[IDEAS] Leyendo las ultimas 14 ideas genericas...")
    historial = obtener_ultimas_14_genericas()
    historial_json = json.dumps(historial, ensure_ascii=False, indent=2)
    print(f"[IDEAS] Ideas genericas encontradas: {len(historial)}")

    print("[IDEAS] Consultando la programacion mas reciente...")
    fecha_base = obtener_ultima_programacion()
    print(f"[IDEAS] Fecha base: {fecha_base.isoformat(timespec='seconds')}")

    programacion = calcular_programacion(fecha_base, CANTIDAD_IDEAS)
    programacion_json = json.dumps(
        programacion,
        ensure_ascii=False,
        indent=2,
    )

    print("[IDEAS] Consultando fuentes web...")
    fuentes_web = leer_fuentes_web(programacion)
    if not fuentes_web:
        fuentes_web = (
            "No se pudo obtener contenido de las fuentes configuradas. "
            "No afirmes haber verificado celebraciones ni inventes datos."
        )

    print("[IDEAS] Cargando prompt...")
    prompt = cargar_prompts(
        "ideas",
        historial_genericas=historial_json,
        programacion=programacion_json,
        fuentes_web=fuentes_web,
    )

    print("[IDEAS] Solicitando ideas a OpenAI...")
    response = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[{"role": "user", "content": prompt}],
    )

    contenido = response.choices[0].message.content
    if not contenido:
        raise ValueError("OpenAI devolvio una respuesta vacia.")

    datos = interpretar_respuesta_json(contenido)
    ideas_modelo = datos.get("ideas")

    if not isinstance(ideas_modelo, list):
        raise ValueError("El JSON de OpenAI debe contener una lista llamada 'ideas'.")

    if len(ideas_modelo) != CANTIDAD_IDEAS:
        raise ValueError(
            f"Se esperaban {CANTIDAD_IDEAS} ideas, pero se recibieron {len(ideas_modelo)}."
        )

    resultado = []
    titulos_vistos = set()

    for indice, idea in enumerate(ideas_modelo):
        if not isinstance(idea, dict):
            raise ValueError(f"La idea {indice + 1} no es un objeto JSON.")

        texto = idea.get("texto", "")
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError(f"La idea {indice + 1} no tiene un texto valido.")

        slot = programacion[indice]
        tematica = slot["tematica"]
        celebracion = idea.get("celebracion", "")

        # Las ideas genericas no dependen de una celebracion concreta.
        if tematica == "GENERICA":
            celebracion = ""
        elif not isinstance(celebracion, str):
            celebracion = ""

        resultado.append({
            "texto": texto.strip(),
            "tematica": tematica,
            "fecha_publicacion": slot["fecha_publicacion"],
            "celebracion": celebracion.strip(),
        })

    print(f"[IDEAS] Ideas preparadas: {len(resultado)}")
    return resultado


if __name__ == "__main__":
    ideas = generar_ideas()
    print("\nIDEAS GENERADAS:\n")

    for idea in ideas:
        print(
            f"{idea['fecha_publicacion']} | "
            f"{idea['tematica']} | {idea['texto']}"
        )
