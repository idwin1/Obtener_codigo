import os
import sys
import subprocess
import json
import threading
from tkinter import messagebox

# =========================================================
# 1. VERIFICACIÓN E INSTALACIÓN DE LIBRERÍAS
# =========================================================
LIBRERIAS_REQUERIDAS = {
    "psycopg2": "psycopg2-binary",
    "customtkinter": "customtkinter"
}

def verificar_e_instalar_librerias():
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

verificar_e_instalar_librerias()

import customtkinter as ctk
import psycopg2
from psycopg2.extras import DictCursor

# =========================================================
# 2. CARGA DE CONFIGURACIÓN SEGURA
# =========================================================
CONFIG_FILE = "config.json"

def cargar_configuracion():
    if not os.path.exists(CONFIG_FILE):
        messagebox.showerror("Error Crítico", f"No se encontró el archivo de configuración '{CONFIG_FILE}'.")
        sys.exit(1)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Error Crítico", f"Error al cargar la configuración:\n{e}")
        sys.exit(1)

config_datos = cargar_configuracion()

CORREO_DEFAULT_1 = config_datos["CORREOS_DEFAULT"]["correo_1"]
CORREO_DEFAULT_2 = config_datos["CORREOS_DEFAULT"]["correo_2"]
ENTORNOS = config_datos["ENTORNOS"]
QUERY_BUSQUEDA = config_datos["QUERIES"]["BUSCAR_VERIFICACION"]

# =========================================================
# 3. PALETA DE COLORES "DEEP ZINC" (Ultra Moderna)
# =========================================================
BG_APP = "#09090b"
BG_SIDEBAR = "#18181b"
BG_CARD = "#27272a"
BG_CARD_HOVER = "#3f3f46"
ACCENT = "#3b82f6"
ACCENT_HOVER = "#2563eb"
BORDER = "#3f3f46"
TEXT_MAIN = "#fafafa"
TEXT_MUTED = "#a1a1aa"
TEXT_SUCCESS = "#4ade80"
TEXT_ERROR = "#f87171"
TEXT_WARN = "#fbbf24"

# =========================================================
# 4. INTERFAZ GRÁFICA Y LÓGICA PRINCIPAL
# =========================================================
class DataApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Data Inspector - Panel de Control")
        self.geometry("1000x700")
        self.minsize(900, 600)
        self.configure(fg_color=BG_APP)
        ctk.set_appearance_mode("dark")

        # Variables de estado
        self.entorno_var = ctk.StringVar(value="DEV")

        self.construir_interfaz()

    def construir_interfaz(self):
        # ---------------- SIDEBAR (MENÚ LATERAL) ----------------
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=BG_SIDEBAR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="📊", font=("Segoe UI Emoji", 45)).pack(pady=(30, 5))
        ctk.CTkLabel(self.sidebar, text="INSPECTOR", font=("Segoe UI", 20, "bold"), text_color=ACCENT).pack()
        ctk.CTkLabel(self.sidebar, text="Database Tool", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(pady=(0, 30))

        # Selector de Entorno
        ctk.CTkLabel(self.sidebar, text="ENTORNO DE TRABAJO", font=("Segoe UI", 11, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.radio_dev = ctk.CTkRadioButton(self.sidebar, text="Desarrollo (DEV)", variable=self.entorno_var, value="DEV", font=("Segoe UI", 13), text_color=TEXT_MAIN, fg_color=ACCENT, hover_color=ACCENT_HOVER)
        self.radio_dev.pack(anchor="w", padx=20, pady=8)
        
        self.radio_qa = ctk.CTkRadioButton(self.sidebar, text="Calidad (QA)", variable=self.entorno_var, value="QA", font=("Segoe UI", 13), text_color=TEXT_MAIN, fg_color=ACCENT, hover_color=ACCENT_HOVER)
        self.radio_qa.pack(anchor="w", padx=20, pady=8)

        # Botón de Salir
        btn_salir = ctk.CTkButton(self.sidebar, text="Salir del Programa", font=("Segoe UI", 12, "bold"), fg_color=BG_CARD, hover_color=TEXT_ERROR, corner_radius=8, command=self.quit)
        btn_salir.pack(side="bottom", pady=30, padx=20, fill="x")

        # ---------------- ÁREA PRINCIPAL (DERECHA) ----------------
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # HEADER
        self.header_row = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.header_row.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(self.header_row, text="Panel de Consultas", font=("Segoe UI", 24, "bold"), text_color=TEXT_MAIN).pack(side="left")

        # TABS (Búsqueda Rápida vs Consulta Avanzada)
        self.tabview = ctk.CTkTabview(self.main_area, fg_color=BG_CARD, segmented_button_selected_color=ACCENT, segmented_button_selected_hover_color=ACCENT_HOVER, segmented_button_unselected_color=BG_SIDEBAR, text_color=TEXT_MAIN)
        self.tabview.pack(fill="x", pady=(0, 20))
        
        tab_rapida = self.tabview.add("Búsqueda por Correo")
        tab_avanzada = self.tabview.add("Consulta Avanzada SQL")

        self.construir_tab_rapida(tab_rapida)
        self.construir_tab_avanzada(tab_avanzada)

        # ÁREA DE CONSOLA / RESULTADOS
        self.frame_consola = ctk.CTkFrame(self.main_area, fg_color=BG_CARD, corner_radius=10)
        self.frame_consola.pack(fill="both", expand=True)

        header_consola = ctk.CTkFrame(self.frame_consola, fg_color="transparent", height=30)
        header_consola.pack(fill="x", padx=15, pady=(10, 0))
        ctk.CTkLabel(header_consola, text="Terminal de Resultados", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkButton(header_consola, text="Limpiar", width=60, height=24, font=("Segoe UI", 11), fg_color=BG_SIDEBAR, hover_color=BG_CARD_HOVER, command=self.limpiar_consola).pack(side="right")

        self.consola = ctk.CTkTextbox(self.frame_consola, font=("Consolas", 13), fg_color="transparent", text_color=TEXT_MAIN, wrap="word")
        self.consola.pack(fill="both", expand=True, padx=10, pady=10)
        self.consola.configure(state="disabled")

    def construir_tab_rapida(self, parent):
        ctk.CTkLabel(parent, text="Correos Predefinidos:", font=("Segoe UI", 12), text_color=TEXT_MUTED).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        frame_btns = ctk.CTkFrame(parent, fg_color="transparent")
        frame_btns.grid(row=1, column=0, columnspan=2, sticky="w", padx=10)

        ctk.CTkButton(frame_btns, text=f"Buscar Default 1\n({CORREO_DEFAULT_1})", font=("Segoe UI", 12, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, command=lambda: self.iniciar_busqueda_correo(CORREO_DEFAULT_1)).pack(side="left", padx=(0, 10))
        ctk.CTkButton(frame_btns, text=f"Buscar Default 2\n({CORREO_DEFAULT_2})", font=("Segoe UI", 12, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, command=lambda: self.iniciar_busqueda_correo(CORREO_DEFAULT_2)).pack(side="left")

        ctk.CTkLabel(parent, text="O buscar correo personalizado:", font=("Segoe UI", 12), text_color=TEXT_MUTED).grid(row=2, column=0, sticky="w", padx=10, pady=(20, 5))
        
        self.entry_correo = ctk.CTkEntry(parent, placeholder_text="ejemplo@correo.com", width=300, font=("Segoe UI", 13), fg_color=BG_SIDEBAR, border_color=BORDER)
        self.entry_correo.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="w")
        
        ctk.CTkButton(parent, text="🔍 Buscar Personalizado", font=("Segoe UI", 12, "bold"), fg_color=BG_SIDEBAR, hover_color=BG_CARD_HOVER, border_width=1, border_color=BORDER, command=lambda: self.iniciar_busqueda_correo(self.entry_correo.get())).grid(row=3, column=1, padx=10, pady=(0, 10))

    def construir_tab_avanzada(self, parent):
        parent.grid_columnconfigure(0, weight=1)

        frame_top = ctk.CTkFrame(parent, fg_color="transparent")
        frame_top.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(frame_top, text="Override DB (Opcional):", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(side="left", padx=(0, 10))
        self.entry_db = ctk.CTkEntry(frame_top, placeholder_text="Dejar vacío para usar la actual", width=250, font=("Segoe UI", 13), fg_color=BG_SIDEBAR, border_color=BORDER)
        self.entry_db.pack(side="left")

        ctk.CTkLabel(parent, text="Consulta SQL:", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(10, 2))
        self.txt_query = ctk.CTkTextbox(parent, height=80, font=("Consolas", 13), fg_color=BG_SIDEBAR, border_color=BORDER, border_width=1)
        self.txt_query.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(parent, text="⚡ Ejecutar Consulta", font=("Segoe UI", 12, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self.iniciar_consulta_avanzada).pack(anchor="e", padx=10, pady=(0, 10))

    # =========================================================
    # LÓGICA DE TERMINAL VIRTUAL
    # =========================================================
    def imprimir_consola(self, mensaje, tipo="normal"):
        """Escribe texto en la consola virtual. Se usa thread-safe (after)"""
        def update_ui():
            self.consola.configure(state="normal")
            
            # Colorear según el tipo de mensaje
            tag = "default"
            if tipo == "exito": tag = "success"
            elif tipo == "error": tag = "error"
            elif tipo == "alerta": tag = "warning"
            elif tipo == "info": tag = "info"

            self.consola.insert("end", mensaje + "\n", tag)
            
            # Configurar colores de tags si no existen
            self.consola.tag_config("success", foreground=TEXT_SUCCESS)
            self.consola.tag_config("error", foreground=TEXT_ERROR)
            self.consola.tag_config("warning", foreground=TEXT_WARN)
            self.consola.tag_config("info", foreground=ACCENT)
            self.consola.tag_config("default", foreground=TEXT_MAIN)

            self.consola.see("end")
            self.consola.configure(state="disabled")

        self.after(0, update_ui)

    def limpiar_consola(self):
        self.consola.configure(state="normal")
        self.consola.delete("1.0", "end")
        self.consola.configure(state="disabled")

    # =========================================================
    # LÓGICA DE BASE DE DATOS (EJECUTADA EN HILOS)
    # =========================================================
    def iniciar_busqueda_correo(self, correo):
        correo = correo.strip()
        if not correo:
            self.imprimir_consola("[!] El campo de correo está vacío.", "alerta")
            return
        
        entorno = self.entorno_var.get()
        config_db = ENTORNOS[entorno]
        
        self.imprimir_consola(f"\n[{entorno}] Iniciando búsqueda para: {correo}...", "info")
        # Ejecutar en hilo para no congelar la UI
        threading.Thread(target=self.tarea_buscar_correo, args=(config_db, entorno, correo), daemon=True).start()

    def tarea_buscar_correo(self, config_db, entorno_nombre, correo_final):
        connection = None
        try:
            connection = psycopg2.connect(**config_db, cursor_factory=DictCursor)
            cursor = connection.cursor()
            
            cursor.execute(QUERY_BUSQUEDA, (correo_final,))
            resultado = cursor.fetchone()
            
            if resultado:
                self.imprimir_consola(f"[✔] Registro encontrado en {entorno_nombre}:", "exito")
                self.imprimir_consola("-" * 50)
                for columna, valor in resultado.items():
                    self.imprimir_consola(f"  {columna}: {valor}")
                self.imprimir_consola("-" * 50)
            else:
                self.imprimir_consola(f"[⚠️] No se encontró ningún registro para [{correo_final}] en {entorno_nombre}.", "alerta")
            
            cursor.close()
        except Exception as error:
            self.imprimir_consola(f"[❌] Error de conexión/consulta en {entorno_nombre}:\n{error}", "error")
        finally:
            if connection:
                connection.close()
                self.imprimir_consola(f"[+] Conexión cerrada.")

    def iniciar_consulta_avanzada(self):
        query = self.txt_query.get("1.0", "end").strip()
        nueva_bd = self.entry_db.get().strip()
        entorno = self.entorno_var.get()
        
        if not query:
            self.imprimir_consola("[!] La consulta SQL no puede estar vacía.", "alerta")
            return

        config_db = ENTORNOS[entorno].copy()
        if nueva_bd:
            config_db["dbname"] = nueva_bd

        self.imprimir_consola(f"\n[{entorno}] Ejecutando query en BD: {config_db['dbname']}...", "info")
        threading.Thread(target=self.tarea_consulta_avanzada, args=(config_db, entorno, query), daemon=True).start()

    def tarea_consulta_avanzada(self, config_db, entorno_nombre, query_personalizada):
        connection = None
        try:
            connection = psycopg2.connect(**config_db, cursor_factory=DictCursor)
            cursor = connection.cursor()
            
            cursor.execute(query_personalizada)
            
            try:
                resultados = cursor.fetchall()
                if resultados:
                    self.imprimir_consola(f"[✔] Resultados obtenidos ({len(resultados)} filas):", "exito")
                    self.imprimir_consola("-" * 60)
                    for i, fila in enumerate(resultados, 1):
                        self.imprimir_consola(f" Registro #{i}:", "info")
                        for columna, valor in fila.items():
                            self.imprimir_consola(f"    {columna}: {valor}")
                        self.imprimir_consola("-" * 40)
                    self.imprimir_consola("-" * 60)
                else:
                    self.imprimir_consola("[✔] Consulta ejecutada con éxito (0 filas retornadas).", "exito")
            except psycopg2.ProgrammingError:
                # Ocurre si la query no retorna datos (ej. UPDATE, INSERT, DELETE)
                connection.commit()
                self.imprimir_consola("[✔] Comando ejecutado con éxito (Cambios guardados).", "exito")
                
            cursor.close()
        except Exception as error:
            self.imprimir_consola(f"[❌] Error al ejecutar la consulta personalizada:\n{error}", "error")
        finally:
            if connection:
                connection.close()
                self.imprimir_consola(f"[+] Conexión cerrada.")


if __name__ == "__main__":
    # Solución para nitidez en pantallas de alta resolución (Windows)
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = DataApp()
    app.mainloop()