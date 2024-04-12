import os
import tkinter as tk
from tkinter import ttk, messagebox
import logging


class CrearSucursalApp:
    def __init__(self, conexionAPI):
        self.ventana_creacion_sucursal = tk.Tk()
        self.ventana_creacion_sucursal.title("Creación de Sucursal")
        self.icono()
        
        self.conexionAPI = conexionAPI

        self.notebook = ttk.Notebook(self.ventana_creacion_sucursal)
        self.notebook.pack(fill='both', expand=True)
        
        self.dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        self.listbox_dias = tk.Listbox(selectmode=tk.MULTIPLE, height=len(self.dias_semana))
        self.selected_days = set()
        self.combo_apertura_var = tk.StringVar()
        self.combo_cierre_var = tk.StringVar()

        # Páginas
        self.pages = []
        self.create_page("Sucursal", self.page1_content, self.page2_next)
        self.create_page("Fecha y Hora", self.page2_content, self.page2_next, self.page2_prev)
        self.create_page("Dirección", self.page3_content, self.page3_next)
        self.create_page("Resumen", self.page4_content)

        # Variables
        self.external_id_var = tk.StringVar()
        self.nombre_sucursal_var = tk.StringVar()
        self.selected_days = {}

        # Variables de entrada
        self.entry_direccion_numero_var = tk.StringVar()
        self.entry_direccion_nombre_var = tk.StringVar()
        self.entry_nombre_ciudad_var = tk.StringVar()
        self.entry_nombre_provincia_var = tk.StringVar()
        self.entry_latitud_var = tk.DoubleVar()  # Cambiado a DoubleVar para almacenar valores tipo float
        self.entry_longitud_var = tk.DoubleVar()  # Cambiado a DoubleVar para almacenar valores tipo float
        self.entry_referencia_var = tk.StringVar()

        self.create_widgets()
        
    def icono(self):
        #ICON
        directorio_script = os.path.dirname(os.path.abspath(__file__))
        ruta_relativa = os.path.join(directorio_script, "..")
        rutaicono = os.path.join(ruta_relativa, "Icono-MercadoPago-Blue.ico")
        self.ventana_creacion_sucursal.iconbitmap(rutaicono)  

    def create_page(self, title, content_func, next_func=None, prev_func=None):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text=title)
        self.pages.append({"page": page, "content": content_func, "next": next_func, "prev": prev_func})

    def create_widgets(self):
        for page in self.pages:
            page["content"](page["page"])

    def page1_content(self, page):
        # Destruir todos los widgets existentes en la página
        for child in page.winfo_children():
            child.destroy()

        ttk.Label(page, text="Ingresa el External ID de la Sucursal:").place(x=60, y=60, anchor='w')
        self.external_id_var = ttk.Entry(page, font=('Helvetica', 9), textvariable=self.external_id_var)
        self.external_id_var.place(x=280, y=60, anchor='w')

        ttk.Label(page, text="Ingresa el Nombre de la Sucursal:").place(x=60, y=90, anchor='w')
        self.nombre_sucursal_var = ttk.Entry(page, font=('Helvetica', 9), textvariable=self.nombre_sucursal_var)
        self.nombre_sucursal_var.place(x=280, y=90, anchor='w')

        # Configurar la columna 0 para expandirse verticalmente
        page.columnconfigure(0, weight=1)

        ttk.Button(page, text="Siguiente", command=self.pages[0]["next"]).place(x=225, y=120, anchor='w')

    def page2_content(self, page):
        # Destruir todos los widgets existentes en la página
        for child in page.winfo_children():
            child.destroy()

        ttk.Label(page, text="Selecciona los días de la semana:").grid(row=0, column=0, padx=10, pady=5, sticky='w')

        dias_semana_espanol = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        self.listbox_dias = tk.Listbox(page, selectmode=tk.MULTIPLE, height=len(dias_semana_espanol))
        for dia_espanol in dias_semana_espanol:
            self.listbox_dias.insert(tk.END, dia_espanol)
        self.listbox_dias.grid(row=0, column=1, padx=10, pady=5, sticky='ew')

        self.centrar_contenido(page)

        ttk.Label(page, text="Horarios de apertura y cierre:").grid(row=1, column=0, padx=10, pady=5, sticky='w')

        horarios = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00',
                    '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00',
                    '23:00']
        self.combo_apertura_var = ttk.Combobox(page, values=horarios, state="readonly")
        self.combo_apertura_var.grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        self.combo_apertura_var.current(0)

        ttk.Label(page, text=" - ").grid(row=1, column=2, pady=5)

        self.combo_cierre_var = ttk.Combobox(page, values=horarios, state="readonly")
        self.combo_cierre_var.grid(row=1, column=3, padx=10, pady=5, sticky='ew')
        self.combo_cierre_var.current(0)

        ttk.Button(page, text="Anterior", command=self.pages[1]["prev"]).grid(row=2, column=0, pady=10)
        ttk.Button(page, text="Siguiente", command=self.pages[1]["next"]).grid(row=2, column=3, pady=10)

        return dias_semana_espanol

    
    def page2_next(self):
        selected_days_espanol = [self.listbox_dias.get(idx) for idx in self.listbox_dias.curselection()]

        # Mapeo de días en español a inglés y minúsculas
        dias_mapping = {'Lunes': 'monday', 'Martes': 'tuesday', 'Miércoles': 'wednesday', 'Jueves': 'thursday',
                        'Viernes': 'friday', 'Sábado': 'saturday', 'Domingo': 'sunday'}

        # Almacena los días en inglés y minúsculas con estructura de diccionario y listas
        self.selected_days = {dias_mapping[dia]: [{'open': self.combo_apertura_var.get(), 'close':  self.combo_cierre_var.get()}] for dia in selected_days_espanol}

        # Asegúrate de que self.selected_days sea un diccionario
        if not isinstance(self.selected_days, dict):
            self.selected_days = {}

        self.notebook.select(self.notebook.index(self.notebook.select()) + 1)
        self.restaurar_seleccion_dias()
        self.pages[1]['content'](self.pages[1]['page'])


    def page2_prev(self):
        self.notebook.select(self.notebook.index(self.notebook.select()) - 1)
        self.restaurar_seleccion_dias()

    def page3_content(self, page):
        self.create_address_widgets(page)
        ttk.Button(page, text="Siguiente", command=self.pages[2]["next"]).grid(row=7, column=0, columnspan=2, pady=10)
        self.centrar_contenido(page)

    def page3_next(self):
        self.notebook.select(self.notebook.index(self.notebook.select()) + 1)


    def page4_content(self, page):
        external_id = self.external_id_var.get()
        nombre_sucursal = self.nombre_sucursal_var.get()

        ttk.Label(page, text=f"External ID: {external_id}").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(page, text=f"Nombre de la Sucursal: {nombre_sucursal}").grid(row=1, column=0, padx=10, pady=5, sticky='w')

        self.display_address_info(page)
        for dia, horarios in self.selected_days.items():
            ttk.Label(page, text=f"{dia} - Apertura: {horarios[0]['open']}, Cierre: {horarios[0]['close']}").grid(row=9, column=0, padx=10, pady=5, sticky='w')

        ttk.Button(page, text="Crear Sucursal", command=self.crear_sucursal).grid(row=10, column=0, pady=10)
        self.centrar_contenido(page)

    def centrar_contenido(self, frame):
        for child in frame.winfo_children():
            child.grid_configure(padx=10, pady=5, sticky='w')

    def restaurar_seleccion_dias(self):
        dias_mapping = {'Lunes': 'monday', 'Martes': 'tuesday', 'Miércoles': 'wednesday', 'Jueves': 'thursday',
                        'Viernes': 'friday', 'Sábado': 'saturday', 'Domingo': 'sunday'}

        for idx, dia_espanol in enumerate(self.dias_semana):
            if dia_espanol in self.selected_days:
                self.listbox_dias.selection_set(idx)


    def create_address_widgets(self, page):
        # Número de la dirección
        ttk.Label(page, text="Número de la dirección:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        self.entry_direccion_nombre_var = ttk.Entry(page, font=('Helvetica', 12), textvariable=self.entry_direccion_numero_var)
        self.entry_direccion_nombre_var.grid(row=0, column=1, padx=10, pady=5, sticky='ew')

        # Nombre de la dirección
        ttk.Label(page, text="Nombre de la dirección:").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        self.entry_direccion_nombre_var = ttk.Entry(page, font=('Helvetica', 12), textvariable=self.entry_direccion_nombre_var)
        self.entry_direccion_nombre_var.grid(row=1, column=1, padx=10, pady=5, sticky='ew')

        # Nombre de la ciudad
        ttk.Label(page, text="Nombre de la ciudad:").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        self.entry_nombre_ciudad_var = ttk.Entry(page, font=('Helvetica', 12), textvariable=self.entry_nombre_ciudad_var)
        self.entry_nombre_ciudad_var.grid(row=2, column=1, padx=10, pady=5, sticky='ew')

        # Nombre de la provincia
        ttk.Label(page, text="Nombre de la provincia:").grid(row=3, column=0, padx=10, pady=5, sticky='w')
        self.entry_nombre_provincia_var = ttk.Entry(page, font=('Helvetica', 12), textvariable=self.entry_nombre_provincia_var)
        self.entry_nombre_provincia_var.grid(row=3, column=1, padx=10, pady=5, sticky='ew')

        # Latitud
        ttk.Label(page, text="Latitud:").grid(row=4, column=0, padx=10, pady=5, sticky='w')
        self.entry_latitud_var = ttk.Entry(page, font=('Helvetica', 12), textvariable=self.entry_latitud_var)
        self.entry_latitud_var.grid(row=4, column=1, padx=10, pady=5, sticky='ew')

        # Longitud
        ttk.Label(page, text="Longitud:").grid(row=5, column=0, padx=10, pady=5, sticky='w')
        self.entry_longitud_var = ttk.Entry(page, font=('Helvetica', 12), textvariable=self.entry_longitud_var)
        self.entry_longitud_var.grid(row=5, column=1, padx=10, pady=5, sticky='ew')

        # Referencia
        ttk.Label(page, text="Referencia:").grid(row=6, column=0, padx=10, pady=5, sticky='w')
        self.entry_referencia_var = ttk.Entry(page, font=('Helvetica', 12), textvariable=self.entry_referencia_var)
        self.entry_referencia_var.grid(row=6, column=1, padx=10, pady=5, sticky='ew')

    def display_address_info(self, page):
        ttk.Label(page, text=f"Número de la dirección: {self.entry_direccion_numero_var.get()}").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(page, text=f"Nombre de la dirección: {self.entry_direccion_nombre_var.get()}").grid(row=3, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(page, text=f"Nombre de la ciudad: {self.entry_nombre_ciudad_var.get()}").grid(row=4, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(page, text=f"Nombre de la provincia: {self.entry_nombre_provincia_var.get()}").grid(row=5, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(page, text=f"Latitud: {self.entry_latitud_var.get()}").grid(row=6, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(page, text=f"Longitud: {self.entry_longitud_var.get()}").grid(row=7, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(page, text=f"Referencia: {self.entry_referencia_var.get()}").grid(row=8, column=0, padx=10, pady=5, sticky='w')

    def display_schedule_info(self, page):
        for dia, horarios in self.selected_days.items():
            ttk.Label(page, text=f"{dia} - Apertura: {horarios[0]['open']}, Cierre: {horarios[0]['close']}").grid(row=9, column=0, padx=10, pady=5, sticky='w')



    def crear_sucursal(self):
        try:
            # Obtener los valores de las entradas en la página 1
            external_id = self.external_id_var.get()
            nombre_sucursal = self.nombre_sucursal_var.get()

            # Obtener los valores de las entradas en la página 2
            fechas = dict(self.selected_days)
            print(fechas)

            # Obtener los valores de las entradas en la página 3
            street_number = self.entry_direccion_numero_var.get()
            street_name = self.entry_direccion_nombre_var.get()
            city_name = self.entry_nombre_ciudad_var.get()
            state_name = self.entry_nombre_provincia_var.get()
            latitude = float(self.entry_latitud_var.get())  # Asegúrate de que sea un valor numérico
            longitude = float(self.entry_longitud_var.get())  # Asegúrate de que sea un valor numérico
            reference = self.entry_referencia_var.get()
            
            sucursal_info = {
                    'business_hours': fechas,
                    'external_id': f'{external_id}',
                    'location': {
                        'street_number': street_number,
                        'street_name': street_name,
                        'city_name': city_name,
                        'state_name': state_name,
                        'latitude': latitude,
                        'longitude': longitude,
                        'reference': reference
                    },
                    'name': nombre_sucursal,
                }

            print(sucursal_info)

            # Verificar que los campos necesarios no estén vacíos
            if not (external_id and nombre_sucursal):
                messagebox.showerror("Error", "Por favor, completa todos los campos obligatorios.")
                return

            # Crea una ventana modal de carga
            loading_window = tk.Toplevel()
            loading_window.title("Cargando...")
            try:
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
                self.ventana_creacion_sucursal.update_idletasks()

                # Espera la respuesta
                respuesta = self.conexionAPI.creacionSUC(sucursal_info).json()

                if respuesta.status_code >= 200 and respuesta.status_code < 300:
                    messagebox.showinfo("Éxito", "Sucursal creada con éxito.")
                    self.ventana_creacion_sucursal.destroy()  # Cierra la ventana principal al crear con éxito
                    
                elif respuesta.status_code >= 300 and respuesta.status_code < 500:
                    # Muestra detalles de error específicos
                    error_message = f"Error al crear la sucursal. Verifica la respuesta.\n\n"
                    error_message += self.get_api_error_message(respuesta)
                    messagebox.showerror("Error", error_message)
                else:
                    # Muestra detalles de error específicos
                    error_message = f"Error al crear la sucursal. Verifica la respuesta.\n\n"
                    error_message += self.get_api_error_message(respuesta)
                    messagebox.showerror("Error", error_message)

            except ValueError as ve:
                # Captura excepción específica para campos numéricos
                messagebox.showerror("Error", f"Latitud y longitud deben ser valores numéricos. Detalles: {str(ve)}")

            except respuesta.status_code as api_error:
                # Manejar excepciones específicas de la API
                messagebox.showerror("Error", f"Error de la API: {str(api_error)}")

            except Exception as e:
                # Captura excepciones generales
                messagebox.showerror("Error", f"Error al crear sucursal: {str(e)}")

            finally:
                # Cierra la ventana de carga independientemente del resultado
                if loading_window:
                    loading_window.destroy()

        except Exception as e:
            # Manejo genérico de excepciones para garantizar que la aplicación no se bloquee
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
            logging.exception("Error inesperado al crear sucursal.")