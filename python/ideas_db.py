"""
FUNCIONES PARA MANEJAR LA BASE DE DATOS DE IDEAS
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# ==========================================================
# CONFIGURACIÓN
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

DB_NAME = BASE_DIR / "data" / "ideas.db"

DB_NAME.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# ESTADOS DEL PIPELINE
# ==========================================================

ESTADOS = (
    "IDEA",
    "GUION",
    "ESCENAS",
    "FICHAS",
    "OPTIMIZADO",
    "PROMPTS",
    "IMAGENES",
    "VOZ",
    "V_FINAL",
    "METADATA",
    "SUBIDO",

    # Estado antiguo.
    # Se conserva para compatibilidad con
    # registros de versiones anteriores.
    "COMPLETADA"
)

# ==========================================================
# OBTENER TEMÁTICA POR ID
# ==========================================================

def obtener_tematica_por_id(idea_id):
    """
    Obtiene la temática de una idea por su ID.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tematica
        FROM ideas
        WHERE id = ?
    """, (idea_id,))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None



# ==========================================================
# CONEXIÓN
# ==========================================================

def conectar():
    """
    Crea y devuelve una conexión a la base de datos.
    """

    return sqlite3.connect(DB_NAME)


# ==========================================================
# CREAR / ACTUALIZAR TABLA
# ==========================================================

def crear_tabla():
    """
    Crea la tabla de ideas si todavía no existe.

    También actualiza bases de datos creadas
    con versiones anteriores del programa.
    """

    conn = conectar()
    cursor = conn.cursor()

    # ------------------------------------------------------
    # Crear tabla si no existe
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT UNIQUE,
            guion TEXT,
            estado TEXT DEFAULT 'IDEA',
            fecha_creacion TEXT,
            fecha_actualizacion TEXT,
            error TEXT,
            youtube_video_id TEXT,
            youtube_url TEXT,
            youtube_thumbnail_ok INTEGER DEFAULT 0,
            tematica TEXT,
            fecha_publicacion TEXT
        )
    """)

    # ------------------------------------------------------
    # Obtener columnas existentes
    # ------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(ideas)"
    )

    columnas = {
        fila[1]
        for fila in cursor.fetchall()
    }

    # ------------------------------------------------------
    # Columnas antiguas
    # ------------------------------------------------------

    if "error" not in columnas:

        cursor.execute("""
            ALTER TABLE ideas
            ADD COLUMN error TEXT
        """)

    if "fecha_creacion" not in columnas:

        cursor.execute("""
            ALTER TABLE ideas
            ADD COLUMN fecha_creacion TEXT
        """)

    if "fecha_actualizacion" not in columnas:

        cursor.execute("""
            ALTER TABLE ideas
            ADD COLUMN fecha_actualizacion TEXT
        """)

    # ------------------------------------------------------
    # NUEVAS COLUMNAS DE YOUTUBE
    # ------------------------------------------------------

    if "youtube_video_id" not in columnas:

        cursor.execute("""
            ALTER TABLE ideas
            ADD COLUMN youtube_video_id TEXT
        """)

    if "youtube_url" not in columnas:

        cursor.execute("""
            ALTER TABLE ideas
            ADD COLUMN youtube_url TEXT
        """)

    if "youtube_thumbnail_ok" not in columnas:

        cursor.execute("""
            ALTER TABLE ideas
            ADD COLUMN youtube_thumbnail_ok INTEGER DEFAULT 0
        """)

    # ------------------------------------------------------
# NUEVAS COLUMNAS PARA PLANIFICAR LAS PUBLICACIONES
# ------------------------------------------------------

    if "tematica" not in columnas:

        cursor.execute("""
            ALTER TABLE ideas
            ADD COLUMN tematica TEXT
        """)

    if "fecha_publicacion" not in columnas:

        cursor.execute("""
            ALTER TABLE ideas
            ADD COLUMN fecha_publicacion TEXT
        """)

    conn.commit()
    conn.close()

    print(
        f"[INFO] Base de datos cargada: {DB_NAME}"
    )


# ==========================================================
# GUARDAR IDEA
# ==========================================================


# ==========================================================
# GUARDAR IDEA
# ==========================================================


def guardar_idea(
    texto,
    tematica=None,
    fecha_publicacion=None
):
    """Guarda una idea y devuelve True si se insertó."""

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO ideas (
                texto,
                fecha_creacion,
                fecha_actualizacion,
                estado,
                tematica,
                fecha_publicacion
            )
            VALUES (
                ?,
                datetime('now'),
                datetime('now'),
                'IDEA',
                ?,
                ?
            )
        """, (
            texto,
            tematica,
            fecha_publicacion
        ))

        conn.commit()
        return cursor.rowcount == 1

    except sqlite3.IntegrityError as error:
        conn.rollback()

        print(
            f"[DB] No se guardó la idea por duplicado "
            f"u otra restricción: {texto!r}. Detalle: {error}"
        )

        return False

    finally:
        conn.close()



# ==========================================================
# OBTENER IDEA INCOMPLETA
# ==========================================================

def obtener_idea_incompleta():
    """
    Busca una idea que ya comenzó a procesarse
    pero todavía no ha terminado.

    Se excluyen:

        IDEA
        SUBIDO
        COMPLETADA

    La idea más antigua se procesa primero.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            texto,
            guion,
            estado
        FROM ideas
        WHERE estado IN (
            'GUION',
            'ESCENAS',
            'FICHAS',
            'OPTIMIZADO',
            'PROMPTS',
            'IMAGENES',
            'VOZ',
            'V_FINAL',
            'METADATA'
        )
        ORDER BY id ASC
        LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()

    return row


# ==========================================================
# OBTENER IDEA NUEVA
# ==========================================================

def obtener_idea_no_usada():
    """
    Busca una idea que todavía no ha comenzado
    a procesarse.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            texto,
            guion,
            estado
        FROM ideas
        WHERE estado = 'IDEA'
        ORDER BY id ASC
        LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()

    return row


# ==========================================================
# OBTENER IDEA POR ID
# ==========================================================

def obtener_idea_por_id(idea_id):
    """
    Obtiene toda la información de una idea
    utilizando su ID.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            texto,
            guion,
            estado,
            fecha_creacion,
            fecha_actualizacion,
            error,
            youtube_video_id,
            youtube_url,
            youtube_thumbnail_ok
        FROM ideas
        WHERE id = ?
    """, (idea_id,))

    row = cursor.fetchone()

    conn.close()

    return row


# ==========================================================
# GUARDAR GUION
# ==========================================================

def guardar_guion(idea_id, guion):
    """
    Guarda el guion generado dentro de la base de datos.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE ideas
        SET
            guion = ?,
            fecha_actualizacion = datetime('now')
        WHERE id = ?
    """, (
        guion,
        idea_id
    ))

    conn.commit()
    conn.close()


# ==========================================================
# MODIFICAR ESTADO
# ==========================================================

def modificar_estado(idea_id, estado):
    """
    Cambia el estado de una idea.
    """

    if estado not in ESTADOS:

        raise ValueError(
            f"Estado no reconocido: {estado}"
        )

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE ideas
        SET
            estado = ?,
            fecha_actualizacion = datetime('now'),
            error = NULL
        WHERE id = ?
    """, (
        estado,
        idea_id
    ))

    conn.commit()
    conn.close()

    print(
        f"[DB] Idea #{idea_id} → {estado}"
    )


# ==========================================================
# GUARDAR INFORMACIÓN DE YOUTUBE
# ==========================================================

def guardar_youtube(
    idea_id,
    video_id,
    youtube_url
):
    """
    Guarda la información del video subido a YouTube.

    No cambia automáticamente el estado.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE ideas
        SET
            youtube_video_id = ?,
            youtube_url = ?,
            fecha_actualizacion = datetime('now'),
            error = NULL
        WHERE id = ?
    """, (
        video_id,
        youtube_url,
        idea_id
    ))

    conn.commit()
    conn.close()

    print(
        f"[DB] YouTube guardado para idea #{idea_id}"
    )

    print(
        f"[DB] Video ID: {video_id}"
    )

    print(
        f"[DB] URL: {youtube_url}"
    )


# ==========================================================
# MARCAR MINIATURA COMO CONFIGURADA
# ==========================================================

def marcar_miniatura_youtube(
    idea_id,
    configurada=True
):
    """
    Registra si la miniatura de YouTube
    fue configurada correctamente.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE ideas
        SET
            youtube_thumbnail_ok = ?,
            fecha_actualizacion = datetime('now')
        WHERE id = ?
    """, (
        1 if configurada else 0,
        idea_id
    ))

    conn.commit()
    conn.close()

    estado_texto = (
        "OK"
        if configurada
        else "PENDIENTE"
    )

    print(
        f"[DB] Miniatura YouTube #{idea_id}: "
        f"{estado_texto}"
    )


# ==========================================================
# REGISTRAR ERROR
# ==========================================================

def registrar_error(idea_id, error):
    """
    Guarda información sobre un error sin cambiar
    el estado actual de la idea.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE ideas
        SET
            error = ?,
            fecha_actualizacion = datetime('now')
        WHERE id = ?
    """, (
        str(error),
        idea_id
    ))

    conn.commit()
    conn.close()


# ==========================================================
# LIMPIAR ERROR
# ==========================================================

def limpiar_error(idea_id):
    """
    Elimina el error registrado de una idea.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE ideas
        SET
            error = NULL,
            fecha_actualizacion = datetime('now')
        WHERE id = ?
    """, (idea_id,))

    conn.commit()
    conn.close()


# ==========================================================
# CONTAR IDEAS NUEVAS
# ==========================================================

def contar_ideas_no_usadas():
    """
    Cuenta las ideas que todavía están en estado IDEA.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM ideas
        WHERE estado = 'IDEA'
    """)

    count = cursor.fetchone()[0]

    conn.close()

    return count


# ==========================================================
# CONTAR IDEAS INCOMPLETAS
# ==========================================================

def contar_ideas_incompletas():
    """
    Cuenta las ideas que ya comenzaron pero todavía
    no han llegado a SUBIDO.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM ideas
        WHERE estado IN (
            'GUION',
            'ESCENAS',
            'FICHAS',
            'OPTIMIZADO',
            'PROMPTS',
            'IMAGENES',
            'VOZ',
            'V_FINAL',
            'METADATA'
        )
    """)

    count = cursor.fetchone()[0]

    conn.close()

    return count


# ==========================================================
# ACTUALIZAR FECHA
# ==========================================================

def actualizar_fecha_act(idea_id):
    """
    Actualiza únicamente la fecha de modificación.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE ideas
        SET
            fecha_actualizacion = datetime('now')
        WHERE id = ?
    """, (idea_id,))

    conn.commit()
    conn.close()

# ==========================================================
# OBTENER LAS ULTIMAS 14 IDEAS GENERICAS
# ==========================================================


# ==========================================================
# OBTENER LAS ULTIMAS 14 IDEAS PARA EVITAR REPETICIONES
# ==========================================================


def obtener_ultimas_14_genericas():
    """
    Obtiene hasta 14 ideas para prevenir repeticiones.

    Prioridad:
    1. Ideas GENERICA más recientes.
    2. Ideas sin clasificación reconocida, si faltan.
    """

    conn = conectar()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, texto, tematica, fecha_publicacion
            FROM ideas
            WHERE UPPER(TRIM(COALESCE(tematica, ''))) = 'GENERICA'
            ORDER BY id DESC
            LIMIT 14
        """)

        genericas = [
            dict(fila)
            for fila in cursor.fetchall()
        ]

        resultado = list(genericas)
        faltantes = 14 - len(resultado)

        if faltantes > 0:
            cursor.execute("""
                SELECT id, texto, tematica, fecha_publicacion
                FROM ideas
                WHERE UPPER(TRIM(COALESCE(tematica, '')))
                    NOT IN ('GENERICA', 'ESPECIFICA')
                ORDER BY id DESC
                LIMIT ?
            """, (faltantes,))

            resultado.extend(
                dict(fila)
                for fila in cursor.fetchall()
            )

        resultado.sort(
            key=lambda idea: idea["id"],
            reverse=True
        )

        print(
            f"[DB] Historial: {len(genericas)} genéricas y "
            f"{len(resultado) - len(genericas)} sin clasificar."
        )

        return resultado

    finally:
        conn.close()


# ==========================================================
# OBTENER LA ULTIMA PROGRAMACION
# ==========================================================

def obtener_ultima_programacion():
    """
    Devuelve la fecha y hora programadas para la idea
    con el ID más reciente.

    Si no existen ideas, o la última no tiene una
    fecha válida, devuelve la fecha y hora actuales
    del dispositivo.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT fecha_publicacion
        FROM ideas
        ORDER BY id DESC
        LIMIT 1
    """)

    fila = cursor.fetchone()

    conn.close()

    # Si no existen ideas, usar la fecha actual.
    if fila is None:
        return datetime.now()

    fecha_guardada = fila[0]

    # Si la última idea no tiene fecha, usar la actual.
    if not fecha_guardada:
        return datetime.now()

    try:
        return datetime.fromisoformat(fecha_guardada)

    except (ValueError, TypeError):
        # Si la fecha tiene un formato incorrecto,
        # evitar que se detenga el generador.
        return datetime.now()
