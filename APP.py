import os
import sys
import subprocess
# Lista de librerías externas que requiere tu proyecto (las nativas como os, sys o argparse no se ponen)
LIBRERIAS_REQUERIDAS = {
    "psycopg2": "psycopg2-binary",  # Nombre en import : Nombre en pip
    "colorama": "colorama"
}

def verificar_e_instalar_librerIAS():
    """Revisa si las librerías están instaladas; si no, las instala automáticamente"""
    for import_name, pip_name in LIBRERIAS_REQUERIDAS.items():
        try:
            # Intenta importar la librería dinámicamente
            __import__(import_name)
        except ImportError:
            print(f"[!] La librería '{import_name}' no está instalada.")
            print(f"[+] Instalando '{pip_name}' automáticamente en segundo plano...")
            try:
                # Ejecuta 'pip install' usando el mismo ejecutable de Python actual
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
                print(f"[✔] '{pip_name}' instalada con éxito.\n")
            except Exception as e:
                print(f"[❌] Error crítico al intentar instalar {pip_name}: {e}")
                print("Por favor, instala la librería manualmente usando: pip install " + pip_name)
                sys.exit(1)

# SE EJECUTA LA VALIDACIÓN ANTES DE CUALQUIER OTRA COSA
verificar_e_instalar_librerIAS()




import psycopg2
from psycopg2.extras import DictCursor
import argparse
from colorama import init, Fore, Style
 
 # python -m PyInstaller --onefile --noconsole app.py

init(autoreset=True)

# Correos configurados por defecto
CORREO_DEFAULT_1 = "default@gamil.com."
CORREO_DEFAULT_2 = "default@gmail.com"

# Diccionario con las credenciales de ambos entornos
ENTORNOS = {
    "DEV": {
        "dbname": "",
        "user": "",
        "password": "",
        "host": "",
        "port": "5432"
    },
    "QA": {
        "dbname": "",
        "user": "",
        "password": "",
        "host": "",  # Cambia por la IP de QA
        "port": "5432"
    }
}

def limpiar_pantalla():
    """Limpia la terminal según el sistema operativo (Windows o Linux/Mac)"""
    os.system('cls' if os.name == 'nt' else 'clear')

def menu_interactivo(titulo, opciones):
    """Genera un menú visualmente limpio en la terminal y valida la entrada"""
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
        
        print(f"{Fore.GREEN} {Style.BRIGHT}[+] Buscando la última verificación para: {correo_final}")
        
        query = """
            SELECT * FROM ctl_verificacioncuenta 
            WHERE nom_correo = %s 
            ORDER BY fec_expiracion DESC 
            LIMIT 1;
        """
        
        cursor.execute(query, (correo_final,))
        resultado = cursor.fetchone()
        
        if resultado:
            print(f"{Fore.GREEN} {Style.BRIGHT} \n[✔] Registro encontrado en {entorno_nombre}:")
            print(Fore.GREEN+ "-" * 60)
            for columna, valor in resultado.items():
                print(f"  {columna}: {valor}")
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
    print(Fore.GREEN + "\n" + "=" * 60)
    print(Fore.CYAN + "      CONFIGURACIÓN DE CONSULTA PERSONALIZADA")
    print(Fore.GREEN + "=" * 60)
    
    print(f"{Fore.CYAN}Base de datos actual: {config_db['dbname']}")
    nueva_bd = input(Fore.CYAN + "Ingresa el nombre de la nueva BD (Presiona Enter para mantener la actual): "+ Style.RESET_ALL).strip()
    
    config_temporal = config_db.copy()
    if nueva_bd:
        config_temporal["dbname"] = nueva_bd

    print("\nEscribe tu consulta SQL completa (ej. SELECT * FROM tabla LIMIT 5):")
    query_personalizada = input("SQL > ").strip()
    
    if not query_personalizada:
        print(Fore.YELLOW + "[!] La consulta no puede estar vacía. Cancelando operación.")
        return

    connection = None
    try:
        print(f"{Fore.GREEN}\n[+] Conectando a la BD [{config_temporal['dbname']}] en {entorno_nombre}...")
        connection = psycopg2.connect(**config_temporal, cursor_factory=DictCursor)
        cursor = connection.cursor()
        
        print(f"{Fore.CYAN}[+] Ejecutando query personalizada...")
        cursor.execute(query_personalizada)
        
        try:
            resultados = cursor.fetchall()
            if resultados:
                print(f"\n[✔] Resultados obtenidos ({len(resultados)} filas):")
                print("-" * 60)
                for i, fila in enumerate(resultados, 1):
                    print(f" Registro #{i}:")
                    for columna, valor in fila.items():
                        print(f"    {columna}: {valor}")
                    print("-" * 40)
                print("-" * 60)
            else:
                print("\n[✔] Consulta ejecutada con éxito (0 filas retornadas).")
        except psycopg2.ProgrammingError:
            connection.commit()
            print("\n[✔] Comando ejecutado con éxito.")
            
        cursor.close()
    except Exception as error:
        print(f"{Fore.RED}[❌] Error al ejecutar la consulta personalizada: {error}")
    finally:
        if connection:
            connection.close()
            print(f"[+] Conexión cerrada.")

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
            
            # Si elige la opción 5, rompe este bucle interno y regresa al menú de entornos
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