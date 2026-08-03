"""MAIN PROGRAM, Select modes"""

from ideas_db import (
                    crear_tabla,
                    guardar_idea,
                    obtener_guion_no_usado,
                    obtener_idea_no_usada,
                    modificar_estado,contar_ideas_no_usadas
                    )
from ideas_generator import generar_ideas
from guion_generator import generate_guion, generate_voice

crear_tabla()

def automatico():
    "Funcion para ejecutar el proceso completo de forma automatica"
    # Si hay menos de 5 ideas disponibles → generar más
    if contar_ideas_no_usadas() < 5:
        print("Generando nuevas ideas...")
        ideas_creadas = generar_ideas()
        for idea_creada in ideas_creadas:
            guardar_idea(idea_creada)
    # Si hay suficientes ideas → tomar una idea no usada
    idea_data1 = obtener_idea_no_usada()
    if idea_data1:
        idea_id_nueva, texto_idea = idea_data1
        print(f"La idea #{idea_id_nueva} no tiene guion aún: {texto_idea}, generando guion...")
        guion_nuevo = generate_guion(texto_idea, idea_id_nueva)
        print("\nGUION GUARDADO :\n", guion_nuevo)
        modificar_estado(idea_id_nueva, "GUION")
    else:
        print("No hay ideas disponibles.")

while True:
    comando = int(input("0: Salir  1: Automatico, \n 2: Generar Guion  3: Generar Voz \n" \
    "4: Generar Imagenes  5: Generar Video Crudo  6: Generar Video Final \n"))
    match comando:
        case 0:
            print("Saliendo del programa.")
            exit(0)


        case 1:
            print("Automatico seleccionado.")


        case 2:
            print("Generar Guion seleccionado.")
            # Si hay menos de 5 ideas disponibles → generar más
            if contar_ideas_no_usadas() < 5:
                print("Generando nuevas ideas...")
                ideas = generar_ideas()
                for idea in ideas:
                    guardar_idea(idea)
            # Si hay suficientes ideas → tomar una idea no usada
            idea_data = obtener_idea_no_usada()
            if idea_data:
                idea_id, texto = idea_data
                print(f"La idea #{idea_id} no tiene guion aún: {texto}, generando guion...")
                guion = generate_guion(texto, idea_id)
                print("\nGUION GUARDADO :\n", guion)
                modificar_estado(idea_id, "GUION")
            else:
                print("No hay ideas disponibles.")


        case 3:
            print("Generador de Voz.")
            guion_data = obtener_guion_no_usado()
            if guion_data:
                idea_id, texto, guion = guion_data
                print(f"La idea #{idea_id} no tiene voz aún: {texto}, generando voz...")
                voz = generate_voice(guion, idea_id)
                print("Voz generada y guardada en archivo:")
                modificar_estado(idea_id, "VOZ")
            else:
                print("No hay ideas disponibles.")


        case _:
            print("Comando no reconocido. Intenta de nuevo.")
