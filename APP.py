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
    for import_name, pip_name in LIBRERIAS_REQUERIDAS.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"[!] Instalando '{pip_name}'...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
            except Exception as e:
                sys.exit(1)

verificar_e_instalar_librerias()

import customtkinter as ctk
import psycopg2
from psycopg2.extras import DictCursor

# =========================================================
# 2. CARGA DE CONFIGURACIÓN
# =========================================================
CONFIG_FILE = "config.json"

def cargar_configuracion():
    if not os.path.exists(CONFIG_FILE):
        messagebox.showerror("Error", f"Falta el archivo {CONFIG_FILE}.")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

config_datos = cargar_configuracion()

CORREO_DEFAULT_1 = config_datos["CORREOS_DEFAULT"]["correo_1"]
CORREO_DEFAULT_2 = config_datos["CORREOS_DEFAULT"]["correo_2"]
ENTORNOS = config_datos["ENTORNOS"]
QUERY_BUSQUEDA = config_datos["QUERIES"]["BUSCAR_VERIFICACION"]
QUERIES_GUARDADOS = config_datos.get("QUERIES_GUARDADOS", {})
BDS_OPCIONALES = config_datos.get("BASES_DE_DATOS_OPCIONALES", [])

# =========================================================
# 3. COLORES
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

# =========================================================
# 4. APLICACIÓN
# =========================================================
class DataApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("APP - Portal Proveedores")
        self.geometry("1050x750")
        self.configure(fg_color=BG_APP)
        ctk.set_appearance_mode("dark")

        self.entorno_var = ctk.StringVar(value="DEV")
        self.construir_interfaz()

    def construir_interfaz(self):
        # -- SIDEBAR --
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=BG_SIDEBAR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="📊", font=("Segoe UI Emoji", 45)).pack(pady=(30, 5))
        ctk.CTkLabel(self.sidebar, text="APP", font=("Segoe UI", 20, "bold"), text_color=ACCENT).pack()

        ctk.CTkLabel(self.sidebar, text="ENTORNO", font=("Segoe UI", 11, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(30, 5))
        ctk.CTkRadioButton(self.sidebar, text="Desarrollo (DEV)", variable=self.entorno_var, value="DEV", fg_color=ACCENT).pack(anchor="w", padx=20, pady=8)
        ctk.CTkRadioButton(self.sidebar, text="Calidad (QA)", variable=self.entorno_var, value="QA", fg_color=ACCENT).pack(anchor="w", padx=20, pady=8)

        ctk.CTkButton(self.sidebar, text="Salir", fg_color=BG_CARD, hover_color=TEXT_ERROR, command=self.quit).pack(side="bottom", pady=30, padx=20, fill="x")

        # -- MAIN AREA --
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.tabview = ctk.CTkTabview(self.main_area, fg_color=BG_CARD, segmented_button_selected_color=ACCENT)
        self.tabview.pack(fill="x", pady=(0, 20))
        
        self.construir_tab_rapida(self.tabview.add("Búsqueda por Correo"))
        self.construir_tab_avanzada(self.tabview.add("Consulta Avanzada SQL"))

        # -- CONSOLA --
        self.frame_consola = ctk.CTkFrame(self.main_area, fg_color=BG_CARD)
        self.frame_consola.pack(fill="both", expand=True)
        
        header_consola = ctk.CTkFrame(self.frame_consola, fg_color="transparent", height=30)
        header_consola.pack(fill="x", padx=15, pady=(10, 0))
        ctk.CTkLabel(header_consola, text="Terminal de Resultados", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkButton(header_consola, text="Limpiar", width=60, height=24, fg_color=BG_SIDEBAR, command=self.limpiar_consola).pack(side="right")

        self.consola = ctk.CTkTextbox(self.frame_consola, font=("Consolas", 13), fg_color="transparent", text_color=TEXT_MAIN)
        self.consola.pack(fill="both", expand=True, padx=10, pady=10)
        self.consola.configure(state="disabled")

    def construir_tab_rapida(self, parent):
        frame_btns = ctk.CTkFrame(parent, fg_color="transparent")
        frame_btns.pack(anchor="w", padx=10, pady=10)

        ctk.CTkButton(frame_btns, text=f"\n({CORREO_DEFAULT_1})", fg_color=ACCENT, command=lambda: self.iniciar_busqueda(CORREO_DEFAULT_1)).pack(side="left", padx=(0, 10))
        ctk.CTkButton(frame_btns, text=f"\n({CORREO_DEFAULT_2})", fg_color=ACCENT, command=lambda: self.iniciar_busqueda(CORREO_DEFAULT_2)).pack(side="left")

        self.entry_correo = ctk.CTkEntry(parent, placeholder_text="ejemplo@correo.com", width=300)
        self.entry_correo.pack(anchor="w", padx=10, pady=(10, 5))
        ctk.CTkButton(parent, text="🔍 Buscar Personalizado", command=lambda: self.iniciar_busqueda(self.entry_correo.get())).pack(anchor="w", padx=10)

    def construir_tab_avanzada(self, parent):
        # Fila 1: Selectores
        frame_selectores = ctk.CTkFrame(parent, fg_color="transparent")
        frame_selectores.pack(fill="x", padx=10, pady=10)

        # 1. Recuperamos tus BD opcionales del JSON
        ctk.CTkLabel(frame_selectores, text="BD Opcional:", text_color=TEXT_MUTED).pack(side="left", padx=(0, 5))
        opciones_bd = ["-- Usar BD por defecto --"] + BDS_OPCIONALES
        self.combo_db = ctk.CTkComboBox(frame_selectores, values=opciones_bd, width=200)
        self.combo_db.pack(side="left", padx=(0, 20))

        # 2. Recuperamos tus Queries guardados del JSON
        ctk.CTkLabel(frame_selectores, text="Cargar Query:", text_color=TEXT_MUTED).pack(side="left", padx=(0, 5))
        opciones_queries = ["-- Seleccionar --"] + list(QUERIES_GUARDADOS.keys())
        self.combo_queries = ctk.CTkComboBox(frame_selectores, values=opciones_queries, width=250, command=self.cargar_query)
        self.combo_queries.pack(side="left")

        # Fila 2: Textbox de SQL
        self.txt_query = ctk.CTkTextbox(parent, height=80, font=("Consolas", 13), fg_color=BG_SIDEBAR)
        self.txt_query.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(parent, text="⚡ Ejecutar Consulta", fg_color=ACCENT, command=self.iniciar_consulta_avanzada).pack(anchor="e", padx=10, pady=5)

    def cargar_query(self, seleccion):
        """Inyecta el query guardado en el JSON dentro del cuadro de texto"""
        if seleccion in QUERIES_GUARDADOS:
            self.txt_query.delete("1.0", "end")
            self.txt_query.insert("1.0", QUERIES_GUARDADOS[seleccion])

    def imprimir_consola(self, mensaje, tag="default"):
        def update_ui():
            self.consola.configure(state="normal")
            self.consola.insert("end", mensaje + "\n", tag)
            self.consola.tag_config("success", foreground=TEXT_SUCCESS)
            self.consola.tag_config("error", foreground=TEXT_ERROR)
            self.consola.tag_config("info", foreground=ACCENT)
            self.consola.tag_config("default", foreground=TEXT_MAIN)
            self.consola.see("end")
            self.consola.configure(state="disabled")
        self.after(0, update_ui)

    def limpiar_consola(self):
        self.consola.configure(state="normal")
        self.consola.delete("1.0", "end")
        self.consola.configure(state="disabled")

    # -- LÓGICA DE BD --
    def iniciar_busqueda(self, correo):
        if not correo.strip(): return
        entorno = self.entorno_var.get()
        threading.Thread(target=self.tarea_buscar, args=(ENTORNOS[entorno], entorno, correo.strip()), daemon=True).start()

    def tarea_buscar(self, config_db, entorno, correo):
        self.imprimir_consola(f"\n[{entorno}] Buscando verificación para: {correo}", "info")
        try:
            with psycopg2.connect(**config_db, cursor_factory=DictCursor) as conn:
                with conn.cursor() as cur:
                    cur.execute(QUERY_BUSQUEDA, (correo,))
                    resultado = cur.fetchone()
                    if resultado:
                        self.imprimir_consola("[✔] Registro encontrado:", "success")
                        for col, val in resultado.items(): self.imprimir_consola(f"  {col}: {val}")
                    else:
                        self.imprimir_consola("[⚠️] Sin resultados.", "error")
        except Exception as e:
            self.imprimir_consola(f"[❌] Error: {e}", "error")

    def iniciar_consulta_avanzada(self):
        query = self.txt_query.get("1.0", "end").strip()
        if not query: return
        
        entorno = self.entorno_var.get()
        config_db = ENTORNOS[entorno].copy()
        
        # Override de BD si se seleccionó una de la lista
        bd_seleccionada = self.combo_db.get()
        if bd_seleccionada != "-- Usar BD por defecto --":
            config_db["dbname"] = bd_seleccionada

        threading.Thread(target=self.tarea_avanzada, args=(config_db, entorno, query), daemon=True).start()

    def tarea_avanzada(self, config_db, entorno, query):
        self.imprimir_consola(f"\n[{entorno} | BD: {config_db['dbname']}] Ejecutando SQL...", "info")
        try:
            with psycopg2.connect(**config_db, cursor_factory=DictCursor) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    try:
                        res = cur.fetchall()
                        self.imprimir_consola(f"[✔] {len(res)} filas obtenidas:", "success")
                        for i, fila in enumerate(res, 1):
                            self.imprimir_consola(f" Registro #{i}:", "info")
                            for col, val in fila.items(): self.imprimir_consola(f"    {col}: {val}")
                    except psycopg2.ProgrammingError:
                        conn.commit()
                        self.imprimir_consola("[✔] Comando ejecutado con éxito.", "success")
        except Exception as e:
            self.imprimir_consola(f"[❌] Error SQL: {e}", "error")

if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    DataApp().mainloop()