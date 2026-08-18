import os
import sys
import subprocess
import json
import re

# Lista de librerías externas que requiere tu proyecto
LIBRERIAS_REQUERIDAS = {
    "psycopg2": "psycopg2-binary",
    "colorama": "colorama"
}

def verificar_e_instalar_librerIAS():
    """Revisa si las librerías están instaladas; si no, las instala automáticamente"""
    for import_name, pip_name in LIBRERIAS_REQUERIDAS.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"[!] La librería '{import_name}' no está instalada.")
            print(f"[+] Instalando '{pip_name}' automáticamente en segundo plano...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
                print(f"[✔] '{pip_name}' instalada con éxito.\n")
            except Exception as e:
                print(f"[❌] Error crítico al intentar instalar {pip_name}: {e}")
                sys.exit(1)

verificar_e_instalar_librerIAS()

import psycopg2
from psycopg2.extras import DictCursor
from colorama import init, Fore, Style

init(autoreset=True)

# -------------------------------------------------------------------------
# CARGA DE CONFIGURACIÓN SEGURA
# -------------------------------------------------------------------------
CONFIG_FILE = "config.json"

def cargar_configuracion():
    if not os.path.exists(CONFIG_FILE):
        print(Fore.RED + f"[❌] Error crítico: No se encontró el archivo de configuración '{CONFIG_FILE}'.")
        sys.exit(1)
        
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(Fore.RED + f"[❌] Error al cargar la configuración: {e}")
        sys.exit(1)

config_datos = cargar_configuracion()

# Variables dinámicas y abstraídas
CORREO_DEFAULT_1 = config_datos["CORREOS_DEFAULT"]["correo_1"]
CORREO_DEFAULT_2 = config_datos["CORREOS_DEFAULT"]["correo_2"]
ENTORNOS = config_datos["ENTORNOS"]
QUERY_BUSQUEDA = config_datos["QUERIES"]["BUSCAR_VERIFICACION"]
# -------------------------------------------------------------------------

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def menu_interactivo(titulo, opciones):
    while True:
        limpiar_pantalla()
        print(Fore.GREEN + "=" * 60)
        print(f"{Fore.CYAN}   {titulo}")
        print(Fore.GREEN +"=" * 60)
        for i, opcion in enumerate(opciones, 1):
            print(f"   {Fore.CYAN}[{i}]{Style.RESET_ALL} {Fore.GREEN}{Style.BRIGHT}{opcion}")
        print(Fore.GREEN +"=" * 60)
        
        seleccion = input(Fore.CYAN + " Selecciona una opción > ").strip()
        if seleccion.isdigit() and 1 <= int(seleccion) <= len(opciones):
            return int(seleccion)
        
        print("\n[!] Opción no válida. Presiona Enter para intentar de nuevo...")
        input()

def conectar_y_consultar(config_db, entorno_nombre, correo_final):
    connection = None
    try:
        print(f"{Fore.GREEN} {Style.BRIGHT} \n[+] Conectando a la base de datos de [{entorno_nombre}]...")
        connection = psycopg2.connect(**config_db, cursor_factory=DictCursor)
        cursor = connection.cursor()
        
        print(f"{Fore.GREEN} {Style.BRIGHT}[+] Buscando información para: {correo_final}")
        
        # Ejecuta la consulta cargada desde el JSON
        cursor.execute(QUERY_BUSQUEDA, (correo_final,))
        resultado = cursor.fetchone()
        
        if resultado:
            print(f"{Fore.GREEN} {Style.BRIGHT} \n[✔] Registro encontrado en {entorno_nombre}:")
            print(Fore.GREEN+ "-" * 60)
            for columna, valor in resultado.items():
                print(f"  {columna}: {valor}")  # Imprime el valor real directamente
            print(Fore.GREEN + "-" * 60)
        else:
            print(f"{Fore.YELLOW} {Style.BRIGHT} \n[⚠️] No se encontró ningún registro para [{correo_final}] en {entorno_nombre}.")
        
        cursor.close()
    except Exception as error:
        print(f"{Fore.RED}[❌] Error al conectar o consultar en {entorno_nombre}: {error}")
    finally:
        if connection:
            connection.close()
            print(f"[+] Conexión a {entorno_nombre} cerrada.")

def ejecutar_consulta_personalizada(config_db, entorno_nombre):
    # 1. Leer del servidor y actualizar el JSON automáticamente
    bases_disponibles = actualizar_bases_de_datos_en_json(config_db, entorno_nombre)
    
    # 2. Cargar los queries guardados (si no hay, usa un diccionario vacío)
    queries_guardados = config_datos.get("QUERIES_GUARDADOS", {})
    nombres_queries = list(queries_guardados.keys())

    # --- PASO A: SELECCIÓN DE BASE DE DATOS ---
    opciones_bd = bases_disponibles + ["Escribir nombre manualmente", "Cancelar y regresar al menú principal"]
    seleccion_bd_idx = menu_interactivo(
        f"PASO 4: SELECCIONA LA BASE DE DATOS EN [{entorno_nombre}]",
        opciones_bd
    )
    
    if seleccion_bd_idx == len(opciones_bd): # Última opción: Cancelar
        return
        
    if seleccion_bd_idx == len(opciones_bd) - 1: # Penúltima opción: Manual
        print(f"\n{Fore.CYAN}Base de datos actual por defecto: {config_db['dbname']}")
        nueva_bd = input(Fore.CYAN + "Ingresa el nombre de la BD: " + Style.RESET_ALL).strip()
    else:
        nueva_bd = bases_disponibles[seleccion_bd_idx - 1]

    config_temporal = config_db.copy()
    if nueva_bd:
        config_temporal["dbname"] = nueva_bd

    # --- PASO B: BUCLE DE CONSULTAS (Para no regresar al menú 1-5) ---
    while True:
        opciones_query = ["Escribir consulta SQL manualmente"] + nombres_queries + ["Cambiar de Base de Datos", "Salir al menú principal (1-5)"]
        
        opc_q = menu_interactivo(
            f"MODO AVANZADO - BD ACTUAL: [{config_temporal['dbname']}]",
            opciones_query
        )
        
        if opc_q == len(opciones_query): 
            break # Salir al menú principal 1-5
            
        elif opc_q == len(opciones_query) - 1: 
            # Cambiar de BD (Reinicia la función)
            return ejecutar_consulta_personalizada(config_db, entorno_nombre)
        
       # --- PASO C: PROCESAR EL QUERY Y PEDIR PARÁMETROS ---
        valores_parametros = None
        
        if opc_q == 1:
            print(f"\n{Fore.CYAN}Escribe tu consulta SQL completa para {config_temporal['dbname']}:")
            query_personalizada = input("SQL > ").strip()
        else:
            nombre_seleccionado = nombres_queries[opc_q - 2]
            query_personalizada = queries_guardados[nombre_seleccionado]
            print(f"\n{Fore.GREEN}[+] Query seleccionado: {nombre_seleccionado}")
            print(f"{Fore.YELLOW}{query_personalizada}{Style.RESET_ALL}")
            
            # Detectar automáticamente si la consulta necesita variables %(variable)s
            parametros_requeridos = re.findall(r'%\((.*?)\)s', query_personalizada)
            
            if parametros_requeridos:
                valores_parametros = {}
                print(f"\n{Fore.CYAN}[+] Esta consulta requiere parámetros. Por favor, ingrésalos:")
                
                for param in parametros_requeridos:
                    # Si el parámetro se llama "correo", mostramos un menú con los defaults
                    if param.lower() == "correo":
                        print(f"\nSelecciona el correo:")
                        print(f"  1. Default 1 ({CORREO_DEFAULT_1})")
                        print(f"  2. Default 2 ({CORREO_DEFAULT_2})")
                        print(f"  3. Escribir manualmente")
                        opc_correo = input(Fore.CYAN + "  Opción > " + Style.RESET_ALL).strip()
                        
                        if opc_correo == '1':
                            valores_parametros[param] = CORREO_DEFAULT_1
                        elif opc_correo == '2':
                            valores_parametros[param] = CORREO_DEFAULT_2
                        else:
                            valores_parametros[param] = input(f"  Escribe el correo manualmente: ").strip()
                    else:
                        # Para cualquier otro parámetro (como idu_proveedor)
                        valores_parametros[param] = input(f"  Ingresa valor para '{param}': ").strip()
        
        if not query_personalizada:
            print(Fore.YELLOW + "[!] La consulta no puede estar vacía.")
            input(Fore.CYAN + "Presiona [ENTER] para intentar de nuevo...")
            continue

        # --- PASO D: EJECUCIÓN DEL QUERY ---
        connection = None
        try:
            print(f"{Fore.GREEN}\n[+] Conectando a [{config_temporal['dbname']}] en {entorno_nombre}...")
            connection = psycopg2.connect(**config_temporal, cursor_factory=DictCursor)
            cursor = connection.cursor()
            
            print(f"{Fore.CYAN}[+] Ejecutando query...")
            
            # Ejecutar de forma segura inyectando el diccionario de parámetros (si existe)
            if valores_parametros:
                cursor.execute(query_personalizada, valores_parametros)
            else:
                cursor.execute(query_personalizada)
            
            try:
                resultados = cursor.fetchall()
                if resultados:
                    print(f"\n[✔] Resultados obtenidos ({len(resultados)} filas):")
                    print(Fore.GREEN + "-" * 60)
                    for i, fila in enumerate(resultados, 1):
                        print(f" Registro #{i}:")
                        for columna, valor in fila.items():
                            print(f"    {columna}: {valor}")
                        print(Fore.GREEN + "-" * 40)
                else:
                    print("\n[✔] Consulta ejecutada con éxito (0 filas retornadas).")
            except psycopg2.ProgrammingError:
                # Atrapa comandos que no devuelven filas (INSERT, UPDATE, DELETE)
                connection.commit()
                # Mostramos cuántas filas fueron afectadas
                filas_afectadas = cursor.rowcount
                print(f"\n[✔] Comando ejecutado y guardado (commit) con éxito. Filas afectadas: {filas_afectadas}")
                
            cursor.close()
        except Exception as error:
            print(f"{Fore.RED}[❌] Error de PostgreSQL al ejecutar la consulta: {error}")
        finally:
            if connection:
                connection.close()
        
        print("\n" + Fore.GREEN + "=" * 60)
        input(Fore.CYAN + "Presiona [ENTER] para hacer otra consulta en esta misma BD...")

def actualizar_bases_de_datos_en_json(config_db, entorno_nombre):
    print(f"{Fore.CYAN}\n[+] Consultando las bases de datos disponibles en el servidor de [{entorno_nombre}]...")
    connection = None
    bases_actualizadas = []
    
    try:
        # Nos conectamos usando la configuración default del entorno
        connection = psycopg2.connect(**config_db)
        cursor = connection.cursor()
        
        # Query nativo de PostgreSQL para listar bases de datos (excluyendo plantillas)
        query = "SELECT datname FROM pg_database WHERE datistemplate = false;"
        cursor.execute(query)
        resultados = cursor.fetchall()
        
        # Extraemos el primer elemento de cada tupla
        bases_actualizadas = [fila[0] for fila in resultados]
        
        # Actualizamos nuestro diccionario global en memoria
        config_datos["BASES_DE_DATOS_OPCIONALES"] = bases_actualizadas
        
        # Guardamos/Sobreescribimos el archivo JSON
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_datos, f, indent=4, ensure_ascii=False)
            
        print(f"{Fore.GREEN}[✔] Archivo config.json actualizado con las bases de datos actuales del servidor.")
        
    except Exception as e:
        print(f"{Fore.RED}[❌] No se pudo obtener la lista de BDs del servidor: {e}")
        # Si falla, usamos las que ya estén en el JSON o la default como respaldo
        bases_actualizadas = config_datos.get("BASES_DE_DATOS_OPCIONALES", [config_db['dbname']])
    finally:
        if connection:
            connection.close()
            
    return bases_actualizadas

def main():
    while True:
        # 1. Selección de Entorno
        opc_entorno = menu_interactivo(
            "PASO 1: SELECCIONAR ENTORNO", 
            ["Desarrollo (DEV)", "Aseguramiento de Calidad (QA)", "Salir del Programa"]
        )
        
        if opc_entorno == 3:
            limpiar_pantalla()
            print("\nSaliendo del programa de forma segura...")
            sys.exit()
            
        entorno_nombre = "DEV" if opc_entorno == 1 else "QA"
        config_db = ENTORNOS[entorno_nombre]
        
        # 2. Bucle de acciones dentro del entorno seleccionado
        while True:
            opciones_accion = [
                f"Usar correo default 1 ({CORREO_DEFAULT_1})",
                f"Usar correo default 2 ({CORREO_DEFAULT_2})",
                "Ingresar un correo personalizado",
                "[AVANZADO] Consulta personalizada (Cambiar BD y Query)",
                "Volver al menú de entornos (Atrás)"
            ]
            
            opc_accion = menu_interactivo(
                f"ENTORNO ACTUAL: [{entorno_nombre}] - SELECCIONAR ACCIÓN", 
                opciones_accion
            )
            
            if opc_accion == 5:
                break
                
            limpiar_pantalla()
            print(Fore.GREEN + "=" * 60)
            print(f"{Fore.CYAN}  PROCESANDO OPERACIÓN EN EL ENTORNO: [{entorno_nombre}]")
            print(Fore.GREEN + "=" * 60)
            
            if opc_accion == 4:
                ejecutar_consulta_personalizada(config_db, entorno_nombre)
            else:
                if opc_accion == 1:
                    correo_a_consultar = CORREO_DEFAULT_1
                elif opc_accion == 2:
                    correo_a_consultar = CORREO_DEFAULT_2
                elif opc_accion == 3:
                    correo_a_consultar = input("\nIngresa el correo electrónico a buscar: ").strip()
                    if not correo_a_consultar:
                        print(Fore.RED + "[!] El correo no puede estar vacío. Operación cancelada.")
                        print("\n" + "=" * 60)
                        input( Fore.CYAN + "Presiona [ENTER] para continuar...")
                        continue
                
                conectar_y_consultar(config_db, entorno_nombre, correo_a_consultar)
            
            print("\n" + Fore.GREEN + "=" * 60)
            input(Fore.CYAN + "Presiona [ENTER] para regresar al menú de acciones...")

if __name__ == "__main__":
    main()