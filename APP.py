import sys
import psycopg2
from psycopg2.extras import DictCursor
"""
python -m PyInstaller --onefile app.py 
"""
# Correos configurados por defecto
CORREO_DEFAULT_1 = "default@gamil.com."
CORREO_DEFAULT_2 = "default@gmail.com"  # Puedes cambiar este por el que necesites

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
        "password": '',
        "host": "",  # Cambia por la IP de QA
        "port": "5432"
    }
}

def conectar_y_consultar(config_db, entorno_nombre, correo_final):
    connection = None
    try:
        print(f"\n[+] Conectando a la base de datos de [{entorno_nombre}]...")
        connection = psycopg2.connect(**config_db, cursor_factory=DictCursor)
        cursor = connection.cursor()
        
        print(f"[+] Buscando la última verificación para: {correo_final}")
        
        query = """
            SELECT * FROM ctl_verificacioncuenta 
            WHERE nom_correo = %s 
            ORDER BY fec_expiracion DESC 
            LIMIT 1;
        """
        
        cursor.execute(query, (correo_final,))
        resultado = cursor.fetchone()
        
        if resultado:
            print(f"\n[✔] Registro encontrado en {entorno_nombre}:")
            print("-" * 50)
            for columna, valor in resultado.items():
                print(f"  {columna}: {valor}")
            print("-" * 50)
        else:
            print(f"\n[⚠️] No se encontró ningún registro para [{correo_final}] en {entorno_nombre}.")
        
        cursor.close()
    except Exception as error:
        print(f"[❌] Error al conectar o consultar en {entorno_nombre}: {error}")
    finally:
        if connection:
            connection.close()
            print(f"[+] Conexión a {entorno_nombre} cerrada.")

def ejecutar_consulta_personalizada(config_db, entorno_nombre):
    print("\n" + "="*50)
    print("      CONFIGURACIÓN DE CONSULTA PERSONALIZADA")
    print("="*50)
    
    # 1. Solicitar nueva BD o dejar la actual por defecto
    print(f"Base de datos actual: {config_db['dbname']}")
    nueva_bd = input("Ingresa el nombre de la nueva BD (Presiona Enter para mantener la actual): ").strip()
    
    # Clonamos la configuración para no alterar permanentemente el entorno global
    config_temporal = config_db.copy()
    if nueva_bd:
        config_temporal["dbname"] = nueva_bd

    # 2. Solicitar la query personalizada
    print("\nEscribe tu consulta SQL completa (ej. SELECT * FROM tabla LIMIT 5):")
    query_personalizada = input("SQL > ").strip()
    
    if not query_personalizada:
        print("[!] La consulta no puede estar vacía. Cancelando operación.")
        return

    connection = None
    try:
        print(f"\n[+] Conectando a la BD [{config_temporal['dbname']}] en {entorno_nombre}...")
        connection = psycopg2.connect(**config_temporal, cursor_factory=DictCursor)
        cursor = connection.cursor()
        
        print(f"[+] Ejecutando query personalizada...")
        cursor.execute(query_personalizada)
        
        # Intentar traer resultados (maneja el caso de que sea un SELECT o algo que devuelva filas)
        try:
            resultados = cursor.fetchall()
            if resultados:
                print(f"\n[✔] Resultados obtenidos ({len(resultados)} filas):")
                print("-" * 50)
                for i, fila in enumerate(resultados, 1):
                    print(f" Registro #{i}:")
                    for columna, valor in fila.items():
                        print(f"    {columna}: {valor}")
                    print("-" * 30)
                print("-" * 50)
            else:
                print("\n[✔] Consulta ejecutada con éxito (0 filas retornadas).")
        except psycopg2.ProgrammingError:
            # Si la query no devuelve filas (ej. un UPDATE, INSERT, etc.) y se hizo de forma directa
            connection.commit()
            print("\n[✔] Comando ejecutado con éxito.")
            
        cursor.close()
    except Exception as error:
        print(f"[❌] Error al ejecutar la consulta personalizada: {error}")
    finally:
        if connection:
            connection.close()
            print(f"[+] Conexión cerrada.")

def seleccionar_entorno():
    while True:
        print("\n" + "="*50)
        print("        PASO 1: SELECCIONAR ENTORNO")
        print("="*50)
        print("1. Desarrollo (DEV)")
        print("2. Aseguramiento de Calidad (QA)")
        print("3. Salir")
        print("="*50)
        
        opcion = input("Selecciona un entorno (1-3): ").strip()
        
        if opcion == "1":
            return "DEV", ENTORNOS["DEV"]
        elif opcion == "2":
            return "QA", ENTORNOS["QA"]
        elif opcion == "3":
            print("\nSaliendo del programa...")
            sys.exit()
        else:
            print("[!] Opción no válida. Elige 1, 2 o 3.")

def seleccionar_opcion_consulta():
    while True:
        print("\n" + "="*50)
        print("        PASO 2: SELECCIONAR ACCIÓN")
        print("="*50)
        print(f"1. Usar correo default 1 ({CORREO_DEFAULT_1})")
        print(f"2. Usar correo default 2 ({CORREO_DEFAULT_2})")
        print("3. Ingresar un correo personalizado")
        print("4. [AVANZADO] Consulta personalizada (Cambiar BD y Query)")
        print("5. Volver al menú de entornos")
        print("="*50)
        
        opcion = input("Selecciona una opción (1-5): ").strip()
        
        if opcion in ["1", "2", "3", "4", "5"]:
            return opcion
        else:
            print("[!] Opción no válida. Elige de 1 a 5.")

def main():
    print("=== APLICACIÓN DE CONSULTAS MULTI-ENTORNO ===")
    
    while True:
        # 1. Selección de Entorno (DEV o QA)
        nombre_entorno, config_db = seleccionar_entorno()
        
        # 2. Selección de Acción
        opcion = seleccionar_opcion_consulta()
        
        if opcion == "5":  # Volver
            continue
            
        if opcion == "4":  # Consulta Personalizada
            ejecutar_consulta_personalizada(config_db, nombre_entorno)
        else:
            # Determinar el correo según la opción elegida
            if opcion == "1":
                correo_a_consultar = CORREO_DEFAULT_1
            elif opcion == "2":
                correo_a_consultar = CORREO_DEFAULT_2
            elif opcion == "3":
                correo_a_consultar = input("\nIngresa el correo electrónico a buscar: ").strip()
                if not correo_a_consultar:
                    print("[!] El correo no puede estar vacío.")
                    continue
            
            # Ejecutar consulta estándar de verificacióncuenta
            conectar_y_consultar(config_db, nombre_entorno, correo_a_consultar)
        
        # Preguntar si desea realizar otra operación
        print("\n" + "="*50)
        otra = input("¿Deseas realizar otra operación? (s/n): ").strip().lower()
        if otra != 's':
            print("\nSaliendo del programa...")
            break

if __name__ == "__main__":
    main()