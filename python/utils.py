from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def leer_txt(ruta):
    """
    Lee un archivo .txt y devuelve su contenido.
    """

    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def cargar_prompts(prompt_name, **kwargs):
    """
    Carga un prompt desde la carpeta prompts
    y reemplaza sus variables.
    """

    ruta = BASE_DIR / "prompts" / f"prompt_{prompt_name}.txt"

    with open(ruta, "r", encoding="utf-8") as f:
        template = f.read()

    return template.format(**kwargs)