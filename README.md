# Biblical Video Generator

Sistema automático para generar videos bíblicos utilizando inteligencia artificial.

El proyecto convierte una idea sencilla en un video completo mediante un pipeline automatizado que genera:

- Guion
- Escenas
- Personajes consistentes
- Imágenes cinematográficas
- Narración con TTS
- Video final

---

# Flujo

Idea
↓
Guion
↓
Escenas
↓
Detección de personajes
↓
Creación de fichas técnicas
↓
Optimización de personajes por escena
↓
Prompts de imagen
↓
Generación de imágenes
↓
Narración
↓
Video final

---

# Tecnologías

- Python
- OpenAI API
- GPT-4o-mini
- GPT-Image-1
- GPT-4o-mini-TTS
- SQLite
- Pillow
- MoviePy
- FFmpeg

---

# Estructura

```
assets/
    prompts/
    music/

data/
    ideas/
    personajes/

output/
    images/
    videos/

main.py
```

---

# Instalación

```bash
git clone https://github.com/juanpablohdv/Biblical-video-generator.git

cd Biblical-video-generator

pip install -r requirements.txt
```

Crear un archivo

```
.env
```

con

```
OPENAI_API_KEY=tu_api_key
```

---

# Estado

Actualmente el proyecto implementa:

- generación automática de guiones
- separación automática en escenas
- creación de fichas técnicas de personajes
- mantenimiento de consistencia visual
- generación automática de imágenes

En desarrollo:

- renderizado del video final
- música
- subtítulos
