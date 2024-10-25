import tkinter as tk
import pytz
import image_path
import json
import threading
import os
import time
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font
from tkinter import filedialog, messagebox
from Conexion_APIs_MP import Conexion_Api
from ctk_components.ctk_components import *
from CTkScrollableDropdown import *
from window_position import center_window
from GUI_Envio_SERVERCENTRAL import ProgramadorComprobacion, BuscarDatosEnvios
from PIL import Image
from tkcalendar import Calendar
from tksheet import Sheet
from datetime import datetime, date
from dateutil import parser

class GUIVentas_MP:
    def __init__(self, root, frame, conexion_dba_server, conexion_dba_central=False):
        self.conexion_dba_server = conexion_dba_server
        self.conexion_dba_central = conexion_dba_central
        self.activado_envio_automatico = False
        self.root = root
        self.clase_envio_auto = None
        self.frame_sheet_main = None

        # Obtener datos de la base de datos
        """ self.ALL_NRO_FACTURA = self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGOServer', 'external_reference')
        self.ALL_id_pago_MP = self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGOServer', 'data')
        self.ALL_HS_ACTUALIZACION = self.parsear_hs_buenos_aires(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGOServer', 'date_last_updated'))
        self.ALL_PAYMENT_METHOD_ID = self.parsear_id_metodo_pago(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGOServer', 'payment_metodo_id'))
        self.ALL_STATUS_DETAIL = self.parsear_estado_pago(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGOServer', 'status_detail'))
        self.ALL_TRANSACTION_REFUND = self.parsear_monto_total(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGOServer', 'transaction_amount_refunded'))
        self.ALL_TRANSACTION_DETAIL = self.parsear_monto_total(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGOServer', 'transaction_details_total_paid_amount'))"""
        self.ALL_NomCaja = self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGOServer', 'NomCaja')
        """self.ALL_NumCajero = self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGOServer', 'NumCajero')"""
        self.ALL_NombreCajero = self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGOServer', 'NombreCajero')
        
        self.lista_nombre_caja = self.bucle_traer_no_repetir(self.ALL_NomCaja)
        self.ordenar_por = "NRO_FACTURA"  # Asegúrate de tener los datos correctos aquí
        
        #CARGA DE IMAGENES
        self.reemplazar_png = ImageTk.PhotoImage(Image.open(image_path.REEMPLAZAR()).resize((25, 25)))
        
        self.lista_de_posicion_ordenar = []
        self.frame_seleccion_caja_cajero(frame)

        
        self.root.protocol("WM_DELETE_WINDOW", self.confirmar_salida)
        self.root.bind("<Control-p>", self.save_sheet)
        
        
    def bucle_traer_no_repetir(self, lista):
        seen = set()
        unique_list = []
        unique_list.append("Todos")
        for x in lista:
            if x is not None and x not in seen:
                unique_list.append(x)
                seen.add(x)
        return unique_list
    
    def bucle_traer_cajeros(self, NomCaja):
        cajeros = []
        cajeros.append("Todos")
        if not NomCaja == "all":
            for tupla in self.lista_con_datos:    
                if tupla[7] == NomCaja and tupla[9] not in cajeros:
                    cajeros.append(tupla[9])
        else:
            for tupla in self.lista_con_datos:  
                if tupla[9] not in cajeros and tupla[9] is not None:
                        cajeros.append(tupla[9])
        return cajeros
        
        

    def confirmar_salida(self):
        print(self.activado_envio_automatico)
        if not self.activado_envio_automatico:
            if messagebox.askquestion("Confirmar salida", "¿Estás seguro que deseas salir?") == "yes":
                self.root.destroy()
        else:
            messagebox.showerror("Error", "No puedes salir mientras el envío automático está activado")

    def parsear_hs_buenos_aires(self, lista_hora):
        if type(lista_hora) == list or type(lista_hora) == tuple:
            lista_hora_parseada = []
            for HS_ISO in lista_hora:
                # Parsear la fecha y hora usando dateutil.parser
                fecha_hora_utc = parser.parse(HS_ISO)

                # Definir la zona horaria de Buenos Aires
                zona_horaria_buenos_aires = pytz.timezone('America/Argentina/Buenos_Aires')

                # Convertir la fecha y hora a la zona horaria de Buenos Aires
                fecha_hora_buenos_aires = fecha_hora_utc.astimezone(zona_horaria_buenos_aires)

                # Formatear la fecha y hora en un formato legible
                fecha_hora_formateada = fecha_hora_buenos_aires.strftime('%Y-%m-%d %H:%M:%S')
                lista_hora_parseada.append(fecha_hora_formateada)
            return lista_hora_parseada
        else:
            # Parsear la fecha y hora usando dateutil.parser
                fecha_hora_utc = parser.parse(lista_hora)

                # Definir la zona horaria de Buenos Aires
                zona_horaria_buenos_aires = pytz.timezone('America/Argentina/Buenos_Aires')

                # Convertir la fecha y hora a la zona horaria de Buenos Aires
                fecha_hora_buenos_aires = fecha_hora_utc.astimezone(zona_horaria_buenos_aires)

                # Formatear la fecha y hora en un formato legible
                fecha_hora_formateada = fecha_hora_buenos_aires.strftime('%Y-%m-%d %H:%M:%S')
                return fecha_hora_formateada
    
    def parsear_monto_total(self, lista_monto_total): #UPDATE 20-07-24
        if type(lista_monto_total) == list or type(lista_monto_total) == tuple:
            lista_monto_total_parseada = []
            for monto_total in lista_monto_total:
                if not monto_total == None:
                    lista_monto_total_parseada.append(f"$ {self.format_number(float(monto_total))}")
                else:
                    lista_monto_total_parseada.append("NO DATA")
            return lista_monto_total_parseada
        else:
            if not lista_monto_total == None:
                return f"$ {self.format_number(float(lista_monto_total))}"
            else:
                return "NO DATA"
    
    def parsear_tipo_metodo_pago(self, lista_tipo_metodo_pago):
        if type(lista_tipo_metodo_pago) == list or type(lista_tipo_metodo_pago) == tuple:
            lista_tipo_metodo_pago_parseada = []
            for tipo_metodo_pago in lista_tipo_metodo_pago:
                if tipo_metodo_pago == "account_money":
                    lista_tipo_metodo_pago_parseada.append("Cuenta Local")
                elif tipo_metodo_pago == "debit_card":
                    lista_tipo_metodo_pago_parseada.append("Tarjeta de Debito")
                elif tipo_metodo_pago == "credit_card":
                    lista_tipo_metodo_pago_parseada.append("Tarjeta de Credito")
                else:
                    lista_tipo_metodo_pago_parseada.append(tipo_metodo_pago)
            return lista_tipo_metodo_pago_parseada
        else:
            if lista_tipo_metodo_pago == "account_money":
                return "Cuenta Local"
            elif lista_tipo_metodo_pago == "debit_card":
                return "Tarjeta de Debito"
            elif lista_tipo_metodo_pago == "credit_card":
                return "Tarjeta de Credito"
            else:
                return lista_tipo_metodo_pago
                
    def parsear_id_metodo_pago(self, lista_id_metodo_pago):
        if type(lista_id_metodo_pago) == list or type(lista_id_metodo_pago) == tuple:
            lista_id_metodo_pago_parseada = []
            for tipo_metodo_pago in lista_id_metodo_pago:
                if tipo_metodo_pago == "account_money":
                    lista_id_metodo_pago_parseada.append("Mercado Pago")
                elif tipo_metodo_pago == "debmaster":
                    lista_id_metodo_pago_parseada.append("Debito Mastercard")
                elif tipo_metodo_pago == "master":
                    lista_id_metodo_pago_parseada.append("Credito Mastercard")
                elif tipo_metodo_pago == "debvisa":
                    lista_id_metodo_pago_parseada.append("Debito Visa")
                elif tipo_metodo_pago == "visa":
                    lista_id_metodo_pago_parseada.append("Credito Visa")
                elif tipo_metodo_pago == "amex":
                    lista_id_metodo_pago_parseada.append("American Express")
                else:
                    lista_id_metodo_pago_parseada.append(tipo_metodo_pago)
                    
            return lista_id_metodo_pago_parseada
        else:
            if lista_id_metodo_pago == "account_money":
                return "Mercado Pago"
            elif lista_id_metodo_pago == "debmaster":
                return "Debito Mastercard"
            elif lista_id_metodo_pago == "master":
                return "Credito Mastercard"
            elif lista_id_metodo_pago == "debvisa":
                return "Debito Visa"
            elif lista_id_metodo_pago == "visa":
                return "Credito Visa"
            elif lista_id_metodo_pago == "amex":
                return "American Express"
            else:
                return lista_id_metodo_pago
    
    def parsear_estado_pago(self, lista_estado_pago):
        if type(lista_estado_pago) == list or type(lista_estado_pago) == tuple:
            lista_estado_pago_parseada = []
            for tipo_estado_pago in lista_estado_pago:
                if tipo_estado_pago == "accredited":
                    lista_estado_pago_parseada.append("Acreditado")
                elif tipo_estado_pago == "refunded":
                    lista_estado_pago_parseada.append("Devuelto")
                else:
                    lista_estado_pago_parseada.append(tipo_estado_pago)
            return lista_estado_pago_parseada
        else:
            if lista_estado_pago == "accredited":
                return "Acreditado"
            elif lista_estado_pago == "refunded":
                return "Devuelto"
            else:
                return lista_estado_pago
    
    def format_number(self, num):
        # Redondear el número a 2 decimales
        num_rounded = round(num, 2)
        
        # Convertir el número a cadena con comas como separadores de miles
        num_str = f"{num_rounded:,.2f}"
        
        # Reemplazar las comas con puntos
        formatted_num = num_str.replace(",", "X").replace(".", ",").replace("X", ".")
        
        return formatted_num
    
    def obtener_posiciones_originales(self, lista):
        # Crear una lista de índices
        indices = list(range(len(lista)))
        
        # Ordenar la lista de índices basado en los valores de la lista original
        indices_ordenados = sorted(indices, key=lambda x: lista[x])
        
        return indices_ordenados
    
    def frame_seleccion_caja_cajero(self, frame):
        self.fecha_actual = datetime.now().strftime('%d-%m-%Y')
        self.frame_contenido_seleccion_caja_cajero = ttk.Frame(frame, borderwidth=5)
        
        self.lista_con_datos = self.obtener_lista_con_datos()
        self.lista_cajeros = self.bucle_traer_cajeros("all")
        
        
        self.frame_seleccion_caja = ttk.Frame(self.frame_contenido_seleccion_caja_cajero)
        self.label_seleccion_caja = ttk.Label(self.frame_seleccion_caja, text="Seleccione un caja:")
        self.combobox_seleccion_caja = ttk.Combobox(self.frame_seleccion_caja, state="readonly", values=self.lista_nombre_caja)
        self.combobox_seleccion_caja.bind("<<ComboboxSelected>>", self.combobox_callback_seleccion_caja)
        self.combobox_seleccion_caja.set(self.lista_nombre_caja[0])
        #self.combobox_seleccion_caja_Dropdown = CTkScrollableDropdown(self.combobox_seleccion_caja, values=self.lista_nombre_caja, command=self.combobox_callback_seleccion_caja, width=200)
        self.frame_seleccion_cajero = ttk.Frame(self.frame_contenido_seleccion_caja_cajero)
        self.label_seleccion_cajero = ttk.Label(self.frame_seleccion_cajero, text="Seleccione un cajero:")
        self.variable_combobox_seleccion_cajero = tk.StringVar(value=self.lista_cajeros[0])
        self.combobox_seleccion_cajero = ttk.Combobox(self.frame_seleccion_cajero, state="readonly", values=self.bucle_traer_cajeros("all"))
        self.combobox_seleccion_cajero.bind("<<ComboboxSelected>>", self.combobox_callback_seleccion_cajero)
        self.combobox_seleccion_cajero.set(self.lista_cajeros[0])
        #self.combobox_seleccion_cajero_Dropdown = CTkScrollableDropdown(self.combobox_seleccion_cajero, values=self.bucle_traer_cajeros("all"),command=self.combobox_callback_seleccion_cajero, width=200)
        
        self.frame_seleccion_fecha = ttk.Frame(self.frame_contenido_seleccion_caja_cajero)
        
        self.frame_fecha_inicio = ttk.Frame(self.frame_seleccion_fecha)
        self.label_fecha_inicio  = ttk.Label(self.frame_fecha_inicio, text="Fecha Inicio: ")
        self.label_fecha_inicio_variable = ttk.Label(self.frame_fecha_inicio, text="Hoy")
        self.boton_cambiar_fecha_inicio = ttk.Button(self.frame_fecha_inicio, text="", image=self.reemplazar_png, width=20, command=lambda:self.command_abrir_calendar("Fecha_Inicio"))
        
        self.frame_fecha_final = ttk.Frame(self.frame_seleccion_fecha)
        self.label_fecha_final  = ttk.Label(self.frame_fecha_final, text="Fecha Final: ")
        self.label_fecha_final_variable = ttk.Label(self.frame_fecha_final, text="Hoy")
        self.boton_cambiar_fecha_final = ttk.Button(self.frame_fecha_final, text="", image=self.reemplazar_png, width=20, command=lambda:self.command_abrir_calendar("Fecha_Final"))
        
        self.button_buscar_ = ttk.Button(self.frame_contenido_seleccion_caja_cajero, text="Buscar", command=lambda:self.bucle_comenzar_filtrado(frame))
        
        self.frame_contenido_seleccion_caja_cajero.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.frame_seleccion_caja.pack(padx=10, pady=10)
        self.label_seleccion_caja.pack(padx=3, pady=3, side="left")
        self.combobox_seleccion_caja.pack(padx=3, pady=3, side="right")
        
        self.frame_seleccion_cajero.pack(padx=10, pady=10)
        self.label_seleccion_cajero.pack(padx=3, pady=3, side="left")
        self.combobox_seleccion_cajero.pack(padx=3, pady=3, side="right")
        
        self.frame_seleccion_fecha.pack(pady=5, padx=5, fill="both", expand=True)
        
        self.frame_fecha_inicio.pack()
        self.label_fecha_inicio.grid(column=0, row=0, pady=3, padx=10, sticky="nsew")
        self.label_fecha_inicio_variable.grid(column=1, row=0, pady=3, padx=10, sticky="nsew")
        self.boton_cambiar_fecha_inicio.grid(column=2, row=0, pady=3, padx=10, sticky="nsew")
        
        self.frame_fecha_final.pack()
        self.label_fecha_final.grid(column=0, row=0, pady=3, padx=10, sticky="nsew")
        self.label_fecha_final_variable.grid(column=1, row=0, pady=3, padx=10, sticky="nsew")
        self.boton_cambiar_fecha_final.grid(column=2, row=0, pady=3, padx=10, sticky="nsew")
        
        self.button_buscar_.pack(padx=3, pady=5)
        
    def bucle_comenzar_filtrado(self, frame):
        self.estado_hilo_buscar_y_comparar  = False
        self.marked_rows = set()  # Conjunto para almacenar las filas marcada
        self.hilo_frame_cargar_loader = threading.Thread(target=self.frame_carga, args=(frame, ))
        self.hilo_frame_cargar_loader.start()
        self.hilo_buscar_y_comparar = threading.Thread(target=self.comenzar_filtrado, args=(frame, ))
        self.hilo_buscar_y_comparar.start()
        self.hilo_bucle_controlador = threading.Thread(target=self.bucle_controlador_loader)
        self.hilo_bucle_controlador.start()
        
    def bucle_controlador_loader(self):
        while not self.estado_hilo_buscar_y_comparar:
            time.sleep(1)
            pass
        else:
            self.ctk_loader.stop_loader()
            self.frame_carga_loader.destroy()
            self.frame_sheet_main.pack(fill="both", expand=True)
        
    def combobox_callback_seleccion_caja(self, choice):
        if not self.combobox_seleccion_caja.get() == "Todos":
            self.combobox_seleccion_cajero.config(values=self.bucle_traer_cajeros(self.combobox_seleccion_caja.get()))
        else:
            self.combobox_seleccion_cajero.config(values=self.bucle_traer_cajeros("all"))
            
    def combobox_callback_seleccion_cajero(self, choice):
        self.variable_combobox_seleccion_cajero.set(self.combobox_seleccion_cajero.get())
        
    def comenzar_filtrado(self, frame):
        self.frame_contenido_seleccion_caja_cajero.pack_forget()
        self.frame_tabla_con_datos(frame)
        print(self.combobox_seleccion_caja.get(), self.combobox_seleccion_cajero.get())
        self.filtrar_datos(self.combobox_seleccion_caja.get(), self.combobox_seleccion_cajero.get())
            
            
    def filtrar_datos(self, caja, cajero):
        if caja == "Todos" and cajero == "Todos":
            # Mostrar todas las filas
            self.filtered_data = [list(row) for row in self.lista_con_datos]
        elif caja == "Todos" and cajero != "Todos":
            # Mostrar filas que coincidan con el cajero
            self.filtered_data = [
                list(row) for row in self.lista_con_datos 
                if row[9] is not None and cajero in row[9]
            ]
        elif caja != "Todos" and cajero == "Todos":
            # Mostrar filas que coincidan con la caja
            self.filtered_data = [
                list(row) for row in self.lista_con_datos 
                if row[7] is not None and caja in row[7]
            ]
        elif caja != "Todos" and cajero != "Todos":
            # Mostrar filas que coincidan con la caja y el cajero
            self.filtered_data = [
                list(row) for row in self.lista_con_datos 
                if (row[7] is not None and caja in row[7]) and (row[9] is not None and cajero in row[9])
            ]
        
        self.filtrar_por_fecha(self.label_fecha_inicio_variable.cget("text"), self.label_fecha_final_variable.cget("text"))
        
        self.estado_hilo_buscar_y_comparar = True
            
    def conectar_MercadoPago_account(self):
        datos_clientes = self.conexion_dba_server.seleccionar_tabla("MPQRCODE_CLIENTE")[0]
        print(datos_clientes)
        conexion_MP = Conexion_Api(datos_clientes[1], datos_clientes[2])
        
        all_responses = []

        for index, row in enumerate(self.filtered_data):
            print(f"\nESTADO DEL PAGO ID: {row[1]}\r")
            response = conexion_MP.obtener_pago(row[1])
            if response.status_code == 200:
                try:
                    datos_dba_own = self.conexion_dba_server.specify_search_fila("MPQRCODE_OBTENERPAGOServer", "data", row[1])[0]
                    json_data = response.json()
                    self.label_estado_factura_variable.configure(text=datos_dba_own[0])
                    print(f"""
                        Factura: {json_data["external_reference"]},
                        Fecha Pago: {json_data["date_created"]}
                        Estado del pago: {json_data["status"]},
                        Detalle estado del pago: {json_data["status_detail"]},
                        Monto: ${json_data["transaction_details"]["total_paid_amount"]}
                        """)

                    lista_estados = [
                        json_data["external_reference"] == datos_dba_own[0],
                        json_data["date_created"] == datos_dba_own[6],
                        json_data["payment_method_id"] == datos_dba_own[22],
                        json_data["payment_type_id"] == datos_dba_own[24],
                        json_data["status"] == datos_dba_own[29],
                        json_data["status_detail"] == datos_dba_own[30],
                        json_data["transaction_details"]["total_paid_amount"] == float(datos_dba_own[35])
                    ]
                    print(f"ESTADO DE FACTURA {row[0]} = {lista_estados}")
                    if False in lista_estados:
                        self.remarcar_fila(index, "red")

                    all_responses.append(json_data)
                except ValueError:
                    print("La respuesta no es un JSON válido")
            else:
                print(f"Error en la solicitud: {response.status_code}")
                print(response.text)

        return all_responses

    
    def remarcar_fila(self, fila_index, color):
        if color == 'red':
            self.marked_rows.add(fila_index)
        total_columns = self.sheet.total_columns()
        for col in range(total_columns):
            self.sheet.highlight_cells(row=fila_index, column=col, bg=color)
        self.sheet.redraw()

    def highlight_cells(self, row, column, bg):
        # Sobrescribir la lógica de resaltado para proteger las filas marcadas
        if row in self.marked_rows and bg != 'red':
            return  # No permitir cambiar el color de una fila marcada
        self.sheet.highlight_cells(row=row, column=column, bg=bg)
        self.sheet.redraw()
        
    
    def apply_marked_rows(self):
        if self.marked_rows:
            for row in self.marked_rows:
                self.remarcar_fila(row, 'red')
    
    def frame_tabla_con_datos(self, frame): # UPDATE 24-07-2024
        self.frame_sheet_main = ttk.Frame(frame,)

        # Crear el frame superior
        self.lupa_png = ImageTk.PhotoImage(Image.open(image_path.LUPA()).resize((25, 25)))
        self.frame_sheet_top = ttk.Frame(self.frame_sheet_main, height=100,)
        self.frame_sheet_top.pack(fill="x", pady=10)
        self.show_content_frame()
        
        self.frame_sheet = ttk.Frame(self.frame_sheet_main)
        self.frame_sheet.pack(fill="both", expand=True)
        # Definir nombres de las columnas
        self.columnas_name = ["Nro Factura", "ID MercadoPago", 'Hs Actualización', 'Metodo de Pago', 'Estado del Pago', 'Monto Devuelto', 'Monto Total', 'Monto Neto Recibido', "Caja", "Número Cajero", "Cajero" ]  

        # Crear y configurar la hoja de datos
        self.sheet = Sheet(self.frame_sheet, header_align="center", row_index_align="center")
        self.sheet.change_theme(theme="light green", redraw=True)
        self.sheet.default_column_width(width=180)
        self.sheet.headers(newheaders=self.columnas_name, index=len(self.columnas_name), reset_col_positions=False, show_headers_if_not_sheet=True, redraw=False)
        self.sheet.font(newfont=("Arial", 9, "normal"), reset_row_positions=True)
        self.sheet.header_font(newfont=("Arial", 11, "bold"))
        self.sheet.enable_bindings("single_select", "row_select", "rc_select", "copy", "ctrl_selec", "right_click_popup_menu", "double_click_row_resize", "up", "down", "left", "right")
        self.sheet.pack(fill="both", expand=True)
        self.sheet.align(align="center", redraw=True)  # Centrar el contenido de las celdas
        
    def frame_carga(self, frame):
        self.frame_carga_loader = ttk.Frame(frame,)
        self.frame_carga_loader.pack(fill="both", expand=True)
        self.ctk_loader = CTkLoader(master=self.frame_carga_loader, opacity=0.8, width=40, height=40)
        self.frame_label_loader = ttk.Frame(self.frame_carga_loader)
        self.label_estado_factura = ttk.Label(self.frame_label_loader, text="Comparando estado de la factura: ")
        self.label_estado_factura_variable = ttk.Label(self.frame_label_loader, text="")
        self.frame_label_loader.pack(side="bottom", pady=15)
        self.label_estado_factura.pack(side="left", padx=5)
        self.label_estado_factura_variable.pack(side="right", padx=5)
    
    def show_content_frame(self):
        self.button_volver = ttk.Button(self.frame_sheet_top, text="Volver", command=self.commannd_boton_volver)
        self.button_volver.pack(pady=5)
        
        self.content_frame_sheet_top = ttk.Frame(self.frame_sheet_top,)
        self.content_frame_sheet_top.pack(fill="both", expand=True)
        
        self.busqueda_frame =  ttk.Frame(self.content_frame_sheet_top, borderwidth= 3,)
        self.busqueda_frame.grid(row=0, column=0, padx=50, sticky="NSEW")
        
        self.frame_icon_label = ttk.Frame(self.busqueda_frame,)
        self.label_icon = ttk.Label(self.frame_icon_label, text="", image=self.lupa_png)
        self.label_buscardor = ttk.Label(self.frame_icon_label, text="Buscador")
        self.entry_buscador = ttk.Entry(self.busqueda_frame, width=250,)#placeholder_text="Ingresar texto"
        self.label_icon.pack(side="left", padx=3)
        self.label_buscardor.pack(side="right", padx=3)
        self.frame_icon_label.pack(pady=25, padx=5)
        self.entry_buscador.pack(padx=5)
        self.entry_buscador.bind("<KeyRelease>", self.buscar_y_filtrar) #self.buscar_automatico

        
        self.option_menu_frame = ttk.Frame(self.content_frame_sheet_top, borderwidth= 3,)
        self.option_menu_frame.grid(row=0, column=1, padx=50, sticky="NSEW")
        
        self.frame_ordenar_por = ttk.Frame(self.option_menu_frame)
        self.frame_ordenar_por.pack(pady=10, padx=10)
        
        self.label_ordenar_por = ttk.Label(self.frame_ordenar_por, text="Ordenar por: ")
        self.ordenar_por_optionmenu_var = tk.StringVar(value=self.ordenar_por)
        self.ordenar_por_optionmenu = ttk.OptionMenu(
                        self.frame_ordenar_por, 
                        self.ordenar_por_optionmenu_var,  # Variable
                        "Seleccione una opción...",  # Valor inicial
                        "Número de Factura", "Cajero",  # Opciones
            command=self.optionmenu_callback  # Callback
        )
        self.ordenar_por_optionmenu.config(width=30)
        self.label_ordenar_por.pack(side="left",pady=5, padx=5)
        self.ordenar_por_optionmenu.pack(side="right",pady=5, padx=5)
        
        self.frame_filtrar_por = ttk.Frame(self.option_menu_frame)
        self.label_filtrar_por = ttk.Label(self.frame_filtrar_por, text= "Resaltar: ")
        self.label_filtrar_por.pack(side="left",pady=5, padx=5)
        self.frame_filtrar_por.pack(pady=10, padx=10)
        self.entry_buscador_resaltador = ttk.Entry(self.frame_filtrar_por, width=250)
        self.entry_buscador_resaltador.pack(side="right",pady=5, padx=5, fill="x", expand=True)
        self.entry_buscador_resaltador.bind("<KeyRelease>", self.buscar_automatico)
        
        """self.label_filtrar_por = ttk.Label(self.frame_filtrar_por, text= "Filtrar por: ")
        self.filtrar_por_optionmenu_var = CTk.StringVar(value="Defecto")
        self.filtrar_por_optionmenu = ttk.OptionMenu(self.frame_filtrar_por,values=["Defecto", "Acreditado", "Devuelto"],
                                                command=self.filtrar_por_option_callback,
                                                variable=self.filtrar_por_optionmenu_var,
                                                width=250)
        self.label_filtrar_por.pack(side="left",pady=5, padx=5)
        self.filtrar_por_optionmenu.pack(side="right",pady=5, padx=5)"""
        
        self.config_envio_frame = ttk.Frame(self.content_frame_sheet_top,)
        self.config_envio_frame.grid(row=0, column=2, padx=50, sticky="NSEW")
        
        if not self.conexion_dba_central == False:
            self.frame_config_envio_left = ttk.Frame(self.config_envio_frame,)
            self.frame_config_envio_left.pack(padx=3, side="left")
            
            self.frame_config_envio_right = ttk.Frame(self.config_envio_frame,)
            self.frame_config_envio_right.pack(padx=3, side="right")
            self.boton_activar = ttk.Button(self.frame_config_envio_left, text="Activar Envio", command=self.commannd_boton_activar)
            self.boton_detener = ttk.Button(self.frame_config_envio_left, text="Detener Envio", command=self.commannd_boton_detener)
            self.boton_enviar = ttk.Button(self.frame_config_envio_left, text="Enviar", command=self.commannd_boton_enviar)
            self.boton_activar.pack(padx=5, pady=5)
            self.boton_detener.pack(padx=5, pady=5)
            self.boton_enviar.pack(padx=5, pady=5)
            self.toggle_disable(self.boton_detener)  # Quita el segundo argumento de toggle_disable
            
            self.label_ultimo_envio = ttk.Label(self.frame_config_envio_right, text="Ultimo envio:")
            self.label_fecha_ultimo_Envio = ttk.Label(self.frame_config_envio_right)
            self.label_proximo_envio = ttk.Label(self.frame_config_envio_right, text="Proximo envio:")
            self.label_fecha_proximo_Envio = ttk.Label(self.frame_config_envio_right)
            if self.activado_envio_automatico:
                self.label_fecha_proximo_Envio.configure(text=f"{self.dia_actual_hs_11()} 23:00")
            else:
                self.label_fecha_proximo_Envio.configure(text="Envio Desactivado")
            self.label_proximo_envio
            self.label_ultimo_envio.pack(padx=3, pady=3)
            self.label_fecha_ultimo_Envio.pack(padx=3, pady=3)
            self.label_proximo_envio.pack(padx=3, pady=3)
            self.label_fecha_proximo_Envio.pack(padx=3, pady=3)
            self.variables_label_act()
        else:
            self.label_aviso_no_central = ttk.Label(self.config_envio_frame, text="No se detecto Servidor Central")
            self.label_aviso_no_central.pack(pady=10)
        
    def variables_label_act(self):
        self.label_fecha_ultimo_Envio.configure(text=self.buscar_ultimo_envio())
        self.root.after(1000, self.variables_label_act)
        
    def buscar_y_filtrar(self, event=None):
        termino_busqueda = self.entry_buscador.get().lower()

        if not termino_busqueda:
            self.sheet.set_sheet_data(self.filtered_data, reset_col_positions=True, reset_row_positions=True)
        else:
            filas_a_mostrar = []
            for fila in self.filtered_data:
                if any(termino_busqueda in str(celda).lower() for celda in fila):
                    filas_a_mostrar.append(fila)
            self.sheet.set_sheet_data(filas_a_mostrar, reset_col_positions=True, reset_row_positions=True)
            
        self.apply_marked_rows()

        # Mantener el foco en el Entry
        self.entry_buscador.focus_set()
        
    def optionmenu_callback(self, choice):
        print("optionmenu dropdown clicked:", choice)
        if choice ==  "Número de Factura":
            self.ordenar_por_factura()
        elif choice == "Cajero":
            self.ordenar_por_cajero_y_factura()
            
    def ordenar_por_factura(self):
        # Verificar si la lista de datos filtrados está vacía
        if not self.filtered_data:
            # Ordenar los datos filtrados por la columna "Nro Factura" (índice 0)
            self.lista_con_datos.sort(key=lambda row: row[0])

            # Actualizar los datos en la hoja
            self.sheet.set_sheet_data(self.filtered_data)
            self.sheet.redraw()

            print("Datos ordenados por Nro Factura:")
            print(self.lista_con_datos)
        else:
            # Ordenar los datos filtrados por la columna "Nro Factura" (índice 0)
            self.filtered_data.sort(key=lambda row: row[0])

            # Actualizar los datos en la hoja
            self.sheet.set_sheet_data(self.filtered_data)
            self.sheet.redraw()

            print("Datos ordenados por Nro Factura:")
            print(self.filtered_data)
            self.apply_marked_rows()
        
    def ordenar_por_cajero_y_factura(self):
    # Verificar si la lista de datos filtrados está vacía
        if not self.filtered_data:
            # Ordenar los datos filtrados primero por cajero (índice 9) y luego por número de factura (índice 0)
            # Las filas donde el cajero es None irán al final
            self.lista_con_datos.sort(key=lambda row: (row[9] is None, row[9], row[0]))

            # Actualizar los datos en la hoja
            self.sheet.set_sheet_data(self.lista_con_datos)
            self.sheet.redraw()

            print("Datos ordenados por Cajero y Nro Factura:")
            print(self.lista_con_datos)
        else:
            # Ordenar los datos filtrados primero por cajero (índice 9) y luego por número de factura (índice 0)
            # Las filas donde el cajero es None irán al final
            self.filtered_data.sort(key=lambda row: (row[9] is None, row[9], row[0]))

            # Actualizar los datos en la hoja
            self.sheet.set_sheet_data(self.filtered_data)
            self.sheet.redraw()

            print("Datos ordenados por Cajero y Nro Factura:")
            print(self.filtered_data)
            self.apply_marked_rows()

    def filtrar_por_fecha(self, fecha_inicio_str, fecha_final_str):
        # Convertir las cadenas de fecha a objetos datetime
        if fecha_inicio_str == "Hoy":
            fecha_inicio = date.today()
        elif fecha_inicio_str != "Inicio":
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%d-%m-%Y').date()
        else:
            fecha_inicio = None

        if fecha_final_str == "Hoy":
            fecha_final = date.today()
        elif fecha_final_str != "Final":
            fecha_final = datetime.strptime(fecha_final_str, '%d-%m-%Y').date()
        else:
            fecha_final = date.today()

        # Filtrar las tuplas basadas en el rango de fechas
        filtered_data = []
        for row in self.filtered_data:
            if row[2] is not None:
                row_fecha = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S').date()
                if fecha_inicio is None and fecha_final_str == "Final":
                    # Caso: Mostrar todas las filas
                    filtered_data.append(row)
                elif fecha_inicio is None:
                    # Caso: Mostrar filas hasta fecha_final
                    if row_fecha <= fecha_final:
                        filtered_data.append(row)
                elif fecha_final_str == "Final":
                    # Caso: Mostrar filas desde fecha_inicio hasta hoy
                    if row_fecha >= fecha_inicio:
                        filtered_data.append(row)
                else:
                    # Caso: Mostrar filas dentro del rango de fechas
                    if fecha_inicio <= row_fecha <= fecha_final:
                        filtered_data.append(row)
        self.filtered_data = filtered_data
        # Convertir las tuplas filtradas a listas para tksheet
        self.sheet.set_sheet_data([list(row) for row in self.filtered_data])
        self.sheet.redraw()

        print(f"Datos filtrados por fecha desde {fecha_inicio_str} hasta {fecha_final_str}:")
        print(self.filtered_data)
        self.conectar_MercadoPago_account()
        self.apply_marked_rows()


    
    def filtrar_por_option_callback(self, choice):
        print(choice)
        if not choice == "Defecto":
            self.get_tuple_filter_by(choice)
            self.sheet.set_sheet_data(data = self.lista_con_datos,
                reset_col_positions = True,
                reset_row_positions = True,
                redraw = True,
                verify = False,
                reset_highlights = False)
            self.set_ordenar_por_NRO_FACTURA()
        else:
            self.lista_con_datos = []
            self.set_ordenar_por_NRO_FACTURA()
            self.sheet.set_sheet_data(data = self.lista_con_datos,
                reset_col_positions = True,
                reset_row_positions = True,
                redraw = True,
                verify = False,
                reset_highlights = False)
        
    def toggle_disable(self, boton, evento=None):
        if boton.cget('state') == "disabled":
            boton.configure(state= "normal")
            boton.bind("<Button-1>", evento)
        else:
            boton.configure(state= "disabled")
            boton.unbind("<Button-1>")
            
    def widget_enable(self, boton, evento=None):
            boton.configure(state= "normal")
            boton.bind("<Button-1>", evento)
    
    def widget_disable(self, boton):
        boton.configure(state= "disabled")
        boton.unbind("<Button-1>")
            

    def save_sheet(self, event=None):
        filepath = filedialog.asksaveasfilename(parent=self.sheet,
                                                title="Save sheet as",
                                                filetypes=[('Excel files', '.xlsx')],
                                                defaultextension=".xlsx",
                                                confirmoverwrite=True)
        if not filepath or not filepath.lower().endswith(".xlsx"):
            return

        try:
            workbook = openpyxl.Workbook()
            worksheet = workbook.active

            # Ajustar orientación horizontal
            worksheet.page_setup.orientation = worksheet.ORIENTATION_LANDSCAPE

            # Ajustar para que toda la hoja quepa en una sola página
            worksheet.page_setup.fitToWidth = 1
            worksheet.page_setup.fitToHeight = 1

            # Ajustar márgenes estrechos
            worksheet.page_margins.left = 0.25
            worksheet.page_margins.right = 0.25
            worksheet.page_margins.top = 0.75
            worksheet.page_margins.bottom = 0.75
            worksheet.page_margins.header = 0.3
            worksheet.page_margins.footer = 0.3

            # Obtener los datos del sheet
            data = self.sheet.get_sheet_data(get_header=False, get_index=False)
            headers = self.sheet.headers()
            headers = [headers]  # Make headers a list of lists

            # Combinar headers con data para obtener la hoja completa
            full_data = headers + [['']*len(headers[0])] + data

            # Escribir los datos en el archivo de Excel
            for row_num, row_data in enumerate(full_data, 1):
                for col_num, cell_value in enumerate(row_data, 1):
                    cell = worksheet.cell(row=row_num, column=col_num, value=cell_value)

                    # Centrando alineación
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                    # Hacer las cabeceras en negrita y más grandes
                    if row_num == 1:
                        cell.font = Font(bold=True, size=12)
                    else:
                        cell.font = Font(size=10)

            # Ajustar el ancho de las columnas al contenido
            for col_num in range(1, len(headers[0]) + 1):
                max_length = 0
                column = get_column_letter(col_num)
                for cell in worksheet[column]:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column].width = adjusted_width

            # Guardar el archivo
            workbook.save(filepath)
            print(f"Archivo guardado en {filepath}")

            # Abrir el archivo después de guardar
            import os
            os.startfile(filepath)
        except Exception as e:
            print(f"Error al guardar el archivo: {e}")

        
    def get_tuple_filter_by(self, tipo_filtrado):
        # Filtrar tuplas donde el valor en la posición 4 es 'Acreditado'
        self.lista_con_datos = [tupla for tupla in self.lista_con_datos if tupla[3] == tipo_filtrado]
        
    def obtener_lista_con_datos(self): #UPDATE 24-07-24
        try:
            lista_nueva  = []
            for dato in self.conexion_dba_server.seleccionar_tabla('MPQRCODE_OBTENERPAGOServer'):
                print(dato)
                lista_nueva.append((dato[0], dato[1], self.parsear_hs_buenos_aires(dato[7]), self.parsear_id_metodo_pago(dato[22]), self.parsear_estado_pago(dato[30]), self.parsear_monto_total(dato[34]), self.parsear_monto_total(dato[35]), self.parsear_monto_total(dato[39]) ,dato[36], dato[37], dato[38]))
            return lista_nueva
        except Exception as e:
            print(e)
            return None

    def clear_highlights(self):
        # Remover el color de fondo de todas las celdas
        total_rows = self.sheet.total_rows()
        total_cols = self.sheet.total_columns()
        for row in range(total_rows):
            for col in range(total_cols):
                self.sheet.highlight_cells(row, col, bg=None)

    def highlight_rows(self, rows, color):
        # Aplicar el color de fondo a todas las celdas en las filas especificadas
        total_cols = self.sheet.total_columns()
        for row in rows:
            for col in range(total_cols):
                self.sheet.highlight_cells(row, col, bg=color)

    def buscar_automatico(self, event=None):
        termino_busqueda = self.entry_buscador_resaltador.get()

        if not termino_busqueda:
            self.clear_highlights()
            self.sheet.redraw()
            return

        coincidencias = set()
        for i, fila in enumerate(self.filtered_data):
            for j, celda in enumerate(fila):
                if termino_busqueda.lower() in str(celda).lower():
                    coincidencias.add(i)
        self.apply_marked_rows()
        self.clear_highlights()

        if coincidencias:
            self.highlight_rows(coincidencias, "green")
        else:
            self.clear_highlights()

        self.sheet.redraw()

    def commannd_boton_activar(self):
        try:
            if messagebox.askquestion("Confirmar automatización", "Estas por activar el envio Automatico a la Central. ¿Deseas activar el envio automatico?") == "yes":
                self.clase_envio_auto = ProgramadorComprobacion()
                self.clase_envio_auto.iniciar(self.root)
                self.activado_envio_automatico = True
                self.toggle_disable(self.boton_detener)
                self.toggle_disable(self.boton_activar)
                self.toggle_disable(self.boton_enviar)
                if self.activado_envio_automatico:
                    self.label_fecha_proximo_Envio.configure(text=f"{self.dia_actual_hs_11()} 23:00")
                else:
                    self.label_fecha_proximo_Envio.configure(text="Envio Desactivado")
        except Exception as e:
            messagebox.showerror("Error Activar", e)

    def commannd_boton_detener(self):
        try:
            if messagebox.askquestion("Confirmar detención", "Estas por desactivar el envio Automatico a la Central. ¿Deseas desactivar el envio automatico?") == "yes":
                self.clase_envio_auto.detener()
                self.clase_envio_auto = None
                self.activado_envio_automatico = False
                self.toggle_disable(self.boton_activar)
                self.toggle_disable(self.boton_enviar)
                self.toggle_disable(self.boton_detener)
                self.label_fecha_proximo_Envio.configure(text="Envio Desactivado")
        except Exception as e:
            messagebox.showerror("Error Detener", e)

    def commannd_boton_enviar(self):
        if hasattr(self, 'top_level_calendar') and self.top_level_calendar.winfo_exists():
            # Si la ventana ya existe, solo la mostramos
            self.top_level_calendar.deiconify()
            self.top_level_calendar.lift()
        else:
            self.top_level_calendar = tk.Toplevel(self.root)
            self.top_level_calendar.overrideredirect(True)  # Elimina la barra de título y los bordes
            self.cal = Calendar(self.top_level_calendar, font="Arial 9", selectmode='day', locale='es_ES', cursor="hand1")
            self.cal.pack(fill="both", expand=True)
            ttk.Button(self.top_level_calendar, text="Buscar y Enviar", command=self.print_sel).pack()
            self.top_level_calendar.lift()
        # Obtener el tamaño de la ventana con todos los widgets incluidos
        center_window(self.top_level_calendar, 250, 215)
        
    def commannd_boton_volver(self):
        self.frame_sheet_main.pack_forget()
        self.frame_contenido_seleccion_caja_cajero.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
    def command_abrir_calendar(self, tipo_fecha):
        self.top_level_calendar_filtrado = tk.Toplevel(self.root)
        self.top_level_calendar_filtrado.title("Calendario")
        self.top_level_calendar_filtrado.after(250, lambda: self.top_level_calendar_filtrado.iconbitmap(image_path.Icono_MercadoPago_Blue()))
        cal_filtrar_fecha = Calendar(self.top_level_calendar_filtrado, font="Arial 9", selectmode='day', locale='es_ES', cursor="hand1", maxdate=datetime.now().date())
        cal_filtrar_fecha.pack(fill="both", expand=True)
        
        ttk.Button(self.top_level_calendar_filtrado, text="Seleccionar", command=lambda:self.command_fijar_fecha(tipo_fecha, cal_filtrar_fecha.selection_get())).pack(pady=5)
        self.top_level_calendar_filtrado.grab_set()
        center_window(self.top_level_calendar_filtrado, 260, 230)

            
    def command_fijar_fecha(self, tipo_fecha, fecha):
        if tipo_fecha == "Fecha_Inicio":
            self.label_fecha_inicio_variable.configure(text=fecha.strftime('%d-%m-%Y'))
        else:
            self.label_fecha_final_variable.configure(text=fecha.strftime('%d-%m-%Y'))
        self.top_level_calendar_filtrado.destroy()
            
    def print_sel(self):
        self.top_level_calendar_filtrado.destroy()
        self.ventana_envio_progress()

    
    
    def buscar_ultimo_envio(self):
        try:
            directorio_script_json = os.path.dirname(os.path.abspath(__file__))
            ruta_relativaJSON = os.path.join(directorio_script_json, "configuracion.json")
            with open(ruta_relativaJSON, "r") as file:
                data = json.load(file)
                ultimo_envio = data.get("ultimo_envio")
                if ultimo_envio:
                    return ultimo_envio
                else:
                    return "Sin registro"
        except FileNotFoundError:
            print(f"El archivo configuracion.json no existe.")
        except json.JSONDecodeError:
            print(f"Error al decodificar el archivo JSON: configuracion.json")
        except Exception as e:
            print(f"Error inesperado: {e}")
            return None
    
    def dia_actual_hs_11(self):
        return datetime.now().strftime("%d-%m-%Y") #fecha: Año-Mes-Día
    
    def ventana_envio_progress(self):
        self.toplevel_envio_progres = tk.Toplevel()
        self.toplevel_envio_progres.grab_set()
        
        self.texto_aviso = 'Iniciar'
        self.cambio_aviso_label = True
        
        self.frame_contenido = ttk.Frame(self.toplevel_envio_progres,)
        self.frame_contenido.pack(pady=20, padx=30)
        
        self.progress_bar = ttk.Progressbar(self.frame_contenido, orientation="horizontal", mode='indeterminate', height=20, width=250)
        self.progress_bar.pack(pady=15)
        self.progress_bar.start()
        
        self.label_aviso = ttk.Label(self.frame_contenido, text='Buscando', font=('Cascadia Code', 14), wraplength=300)
        self.label_aviso.pack(pady=5, padx=10)
        if self.activado_envio_automatico:
            threading.Thread(target=BuscarDatosEnvios, args=(False, self.label_aviso, self.toplevel_envio_progres, )).start()
        else:
            threading.Thread(target=BuscarDatosEnvios, args=(self.cal.selection_get(), self.label_aviso, self.toplevel_envio_progres, )).start()
        
        center_window(self.toplevel_envio_progres, 400, 150)
        
        
