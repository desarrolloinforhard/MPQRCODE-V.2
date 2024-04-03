import os
path_script = os.path.dirname(os.path.abspath(__file__))
path_assets = os.path.join(path_script, '..', 'assets')
import sys
sys.path.append(path_assets)
import tkinter as tk
from image_path import *
from tkinter import ttk, messagebox

class CrearCajaApp:
    def __init__(self, conexionAPI, conexionDBA):
        self.ventana_creacion_caja = tk.Tk()
        self.ventana_creacion_caja.title("Creación de Caja")
        self.conexionAPI = conexionAPI
        self.conexionDBA = conexionDBA
        
        self.icon()

        # Agregar ComboBox para elegir la sucursal
        self.label_sucursal = ttk.Label(self.ventana_creacion_caja, text="Selecciona la Sucursal:")
        self.label_sucursal.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        self.selected_external_id = tk.StringVar()

        # Obtener todos los External IDs de la tabla MPQRCODE_SUCURSAL
        external_ids = self.obtener_todos_los_external_id('MPQRCODE_SUCURSAL')

        # ComboBox con los resultados de la función
        self.combo_sucursal = ttk.Combobox(self.ventana_creacion_caja, values=external_ids, textvariable=self.selected_external_id)
        self.combo_sucursal.grid(row=0, column=1, padx=10, pady=5, sticky='ew')

        # Botón para abrir la ventana de creación del POS
        ttk.Button(self.ventana_creacion_caja, text="Siguiente", command=self.abrir_ventana_crear_pos).grid(row=1, column=0, columnspan=2, pady=10)

    def icon(self):
        #ICONO
        directorio_script = os.path.dirname(os.path.abspath(__file__))
        ruta_relativa = os.path.join(directorio_script, "..")
        rutaicono = os.path.join(ruta_relativa, Icono_MercadoPago_Blue())
        self.ventana_creacion_caja.iconbitmap(rutaicono)
        
    def obtener_todos_los_external_id(self, tabla):
        try:
            # Implementa la lógica para obtener los External IDs desde la base de datos
            # Puedes usar tu función existente
            external_ids = self.conexionDBA.obtener_todos_los_external_id(tabla)
            return external_ids
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener los External IDs: {e}")

    def abrir_ventana_crear_pos(self):
        # Obtener el External ID seleccionado
        selected_external_id = self.combo_sucursal.get()

        if not selected_external_id:
            messagebox.showwarning("Advertencia", "Selecciona una sucursal primero.")
            return

        # Crear una nueva ventana para ingresar detalles del POS
        ventana_pos = tk.Toplevel(self.ventana_creacion_caja)
        ventana_pos.title("Creación de POS")

        ttk.Label(ventana_pos, text="Nombre del POS:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        entry_nombre_pos = ttk.Entry(ventana_pos)
        entry_nombre_pos.grid(row=0, column=1, padx=10, pady=5, sticky='ew')

        ttk.Label(ventana_pos, text="Categoría MCC del POS:").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        entry_categoria_pos = ttk.Entry(ventana_pos)
        entry_categoria_pos.grid(row=1, column=1, padx=10, pady=5, sticky='ew')

        ttk.Label(ventana_pos, text="External ID del POS:").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        entry_external_id_pos = ttk.Entry(ventana_pos)
        entry_external_id_pos.grid(row=2, column=1, padx=10, pady=5, sticky='ew')
        
        ttk.Label(ventana_pos, text="URL de la IPN LOCAL:").grid(row=3, column=0, padx=10, pady=5, sticky='w')
        entry_IPN_url = ttk.Entry(ventana_pos)
        entry_IPN_url.grid(row=3, column=1, padx=10, pady=5, sticky='ew')

        # Botón para realizar la creación del POS
        ttk.Button(ventana_pos, text="Crear POS", command=lambda: self.crear_pos(entry_nombre_pos.get(), entry_categoria_pos.get(), entry_external_id_pos.get(), entry_IPN_url.get())).grid(row=4, column=0, columnspan=2, pady=10)

    def crear_pos(self, nombre_pos, categoria_pos, external_id_pos, IPN_url):
        try:
            external_store_id = self.combo_sucursal.get()
            external_id = external_store_id + external_id_pos
            datosPOS = [categoria_pos, external_id, nombre_pos]
            
            # Crea una ventana modal de carga
            loading_window = tk.Toplevel()
            loading_window.title("Cargando...")

            # Etiqueta para mostrar el mensaje
            loading_label = ttk.Label(loading_window, text="Creando sucursal...")
            loading_label.pack(padx=20, pady=10)

            # Barra de progreso giratoria (indeterminada)
            progressbar = ttk.Progressbar(loading_window, mode='indeterminate')
            progressbar.pack(padx=20, pady=10)
            progressbar.start()

            # Actualiza la interfaz para que se muestre la ventana de carga
            self.ventana_creacion_caja.update_idletasks()

            # Espera la respuesta
            respuesta = self.conexionAPI.crearCaja(external_store_id, datosPOS, IPN_url)

            if respuesta.status_code >= 200 and respuesta.status_code < 300:
                try:
                    messagebox.showinfo("Éxito", "Caja creada con éxito.")
                    self.ventana_creacion_caja.destroy()
                #DEFINIR BIEN LA LOGICA DE ERRORES CON conexiones.py
                except Exception as e:
                    if respuesta.status_code >= 300 and respuesta.status_code < 500:
                        for clave_error, valor_error in respuesta:
                            if clave_error == 'message':
                                messagebox.showerror(f"Error {respuesta.status_code}", f"Error al crear sucursal: {valor_error}, {str(e)}")
                    
        except Exception as e:
            # Captura excepciones generales
            messagebox.showerror("Error", f"Error al crear sucursal: {str(e)}")

        finally:
            # Cierra la ventana de carga independientemente del resultado
            if loading_window:
                loading_window.destroy()