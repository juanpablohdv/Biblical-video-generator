"Funciones para manejar la base de datos"

import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_NAME = BASE_DIR / "data" / "ideas.db"

DB_NAME.parent.mkdir(
    parents=True,
    exist_ok=True
)

print(f"son las {datetime.now()} y se ha cargado el módulo de ideas_db")

def conectar():
    "Funcion para conectar a la base de datos"
    return sqlite3.connect(DB_NAME)

def crear_tabla():
    "Crea la tabla de ideas si no existe"
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT UNIQUE,
            guion TEXT,
            estado TEXT DEFAULT 'IDEA',
            fecha_creacion TEXT,
            fecha_actualizacion TEXT
        )
    """)
    conn.commit()
    conn.close()

def guardar_idea(texto):
    "Funcion para guardar una nueva idea en la base de datos con estado 'IDEA'"
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO ideas (texto, fecha_creacion, fecha_actualizacion, estado)
            VALUES (?, datetime('now'), datetime('now'), 'IDEA')
        """, (texto,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

#def guardar_guion(idea_id, guion):
#obtener una idea no usada busca en la base de datos una idea con estado 'IDEA' y la retorna

def obtener_idea_no_usada():
    "Busca ideas en estado de idea y retorna el id y el texto"
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, texto FROM ideas WHERE estado = 'IDEA' LIMIT 1"
    )
    row = cursor.fetchone()
    conn.close()
    return row

def obtener_guion_no_usado():
    "Busca ideas en estado de guion y retorna el id y el guion"
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, texto, guion FROM ideas WHERE estado = 'GUION' LIMIT 1"
    )
    row = cursor.fetchone()
    conn.close()
    return row

def modificar_estado(idea_id,estado):
    "Actualiza el estado de una idea-> IDEA-GUION-VOZ-VIDEO_CRUDO-FINAL-COMPLETADA"

    conn = conectar()
    cursor = conn.cursor()
    if estado=='IDEA' or estado=='GUION' or estado=='VOZ' or estado=='V_CRUDO' or estado=='V_FINAL':
        cursor.execute(
            f"UPDATE ideas SET estado = '{estado}' WHERE id = ?",
            (idea_id,)
        )
    else:
        print("Estado no reconocido.")
    conn.commit()
    conn.close()

def contar_ideas_no_usadas():
    "Cuenta la cantidad de ideas con estado 'IDEA' en la base de datos"
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM ideas WHERE estado = 'IDEA'"
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count

def actualizar_fecha_act(idea_id):
    "Modifica la fecha de actualización de una idea"
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE ideas SET fecha_actualizacion = datetime('now') WHERE id = ?",
        ( idea_id,)
    )
    conn.commit()
    conn.close()
