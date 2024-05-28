import customtkinter as CTk
import pytz
import image_path
from tkinter import filedialog
import csv
from os.path import normpath
from tkinter import ttk
from PIL import Image
from tksheet import Sheet
from dateutil import parser




class GUIVentas_MP:
    def __init__(self, root, conexion_dba_server):
        self.conexion_dba_server = conexion_dba_server
        self.ALL_NRO_FACTURA = self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'external_reference')
        self.ALL_HS_ACTUALIZACION = self.parsear_hs_buenos_aires(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'date_last_updated'))
        self.ALL_PAYMENT_METHOD_ID = self.parsear_id_metodo_pago(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'payment_metodo_id'))
        self.ALL_STATUS_DETAIL = self.parsear_estado_pago(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'status_detail'))
        self.ALL_TRANSACTION_REFUND = self.parsear_monto_total(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'transaction_amount_refunded'))
        self.ALL_TRANSACTION_DETAIL = self.parsear_monto_total(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'transaction_details_total_paid_amount'))
        self.ALL_NomCaja = self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'NomCaja')
        self.ALL_NumCajero = self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'NumCajero')
        self.ALL_NombreCajero  = self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'NombreCajero')
        self.ordenar_por = "NRO_FACTURA"
        self.lista_con_datos = []
        self.lista_de_posicion_ordenar = []
        
        self.lupa_png = CTk.CTkImage(Image.open(image_path.LUPA()), size=(25, 25))
        self.frame_sheet_top = CTk.CTkFrame(root, height=100, fg_color='transparent')
        self.frame_sheet_top.pack(fill="x", pady=10)
        self.show__content_frame()
        
        self.columnas_name = ["Nro Factura", 'Hs Actualización', 'Metodo de Pago', 'Estado del Pago', 'Monto Devuelto', 'Monto Total', "Caja", "Cajero", "Número Cajero"]
        self.frame_sheet = CTk.CTkFrame(root)
        self.frame_sheet.pack(fill="both", expand=True)
        self.sheet = Sheet(self.frame_sheet, align='center')
        self.sheet.change_theme(theme = "light green", redraw = True)
        self.sheet.default_column_width(width = 180)
        self.sheet.headers(newheaders = self.columnas_name, index = len(self.columnas_name), reset_col_positions = False, show_headers_if_not_sheet = True, redraw = False)
        self.set_ordenar_por_NRO_FACTURA()
        self.sheet.font(newfont = ("Arial", 9 , "normal"), reset_row_positions = True)
        self.sheet.header_font(newfont = ("Arial", 11, "bold"))
        self.sheet.enable_bindings("single_select", "row_select", "rc_select", "copy", "ctrl_selec", "right_click_popup_menu", "double_click_row_resize", "up", "down", "left", "right")
        self.sheet.pack(fill="both", expand=True)
        """self.ventas_mp_table = TableCanvas(root, data=data) #UTILIZACION DEL MODULO TKINTERTABLE
        self.ventas_mp_table.show()"""
        
    def crear_dict_datos(self, column_names, datos):
        #print(datos)
        data = {}
        nro_columna = 1 
        for dato in datos:
            dict_vacio = {}
            for column_name in range(0, len(column_names)):
                dict_vacio[column_names[column_name]] = dato[column_name]
            data[nro_columna] = dict_vacio
            nro_columna += 1
        #print(data)
        return data
    
    def mostrar_datos(self):
        for contador in range(0, len(self.ALL_NRO_FACTURA)):
            self.lista_con_datos.append(self.get_tuple_orber_by(contador, self.lista_de_posicion_ordenar[contador]))
            
    
    
    def crear_lista_datos(self):
        lista_fila = []
        for contador in range(0, len(self.ALL_NRO_FACTURA)):
            lista_fila.append(self.crear_tupla_datos(contador))
        return lista_fila
        #Crear seleccion de tablas y traduccion de palabras.
            #data[nro_columna] = 

    def crear_tupla_datos(self, rango):
        return (self.ALL_NRO_FACTURA[rango],
                self.ALL_HS_ACTUALIZACION[rango],
                self.ALL_PAYMENT_METHOD_ID[rango],
                self.ALL_STATUS_DETAIL[rango],
                self.ALL_TRANSACTION_REFUND[rango],
                self.ALL_TRANSACTION_DETAIL[rango],
                self.ALL_NomCaja[rango] if not None else "" ,
                self.ALL_NombreCajero[rango] if not None else "",
                self.ALL_NumCajero[rango] if not None else "")

    def parsear_hs_buenos_aires(self, lista_hora):
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
    
    def parsear_monto_total(self, lista_monto_total):
        lista_monto_total_parseada = []
        for monto_total in lista_monto_total:
            lista_monto_total_parseada.append(f"$ {self.format_number(float(monto_total))}")
        return lista_monto_total_parseada
    
    def parsear_tipo_metodo_pago(self, lista_tipo_metodo_pago):
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
                
    def parsear_id_metodo_pago(self, lista_id_metodo_pago):
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
    
    def parsear_estado_pago(self, lista_estado_pago):
        lista_estado_pago_parseada = []
        for tipo_estado_pago in lista_estado_pago:
            if tipo_estado_pago == "accredited":
                lista_estado_pago_parseada.append("Acreditado")
            elif tipo_estado_pago == "refunded":
                lista_estado_pago_parseada.append("Devuelto")
            else:
                lista_estado_pago_parseada.append(tipo_estado_pago)
        return lista_estado_pago_parseada
    
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
    
    def get_full_main_order(self):
        if self.ordenar_por == "NRO_FACTURA":
            self.lista_de_posicion_ordenar = self.obtener_posiciones_originales(self.ALL_NRO_FACTURA)
            self.ALL_NRO_FACTURA = sorted(self.ALL_NRO_FACTURA)
        else:
            self.ALL_NRO_FACTURA = self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'external_reference')
            
            
        if self.ordenar_por == "PAYMENT_METHOD_ID":
            self.lista_de_posicion_ordenar = self.obtener_posiciones_originales(self.ALL_PAYMENT_METHOD_ID)
            self.ALL_PAYMENT_METHOD_ID = sorted(self.ALL_PAYMENT_METHOD_ID)
        else:
            self.ALL_PAYMENT_METHOD_ID = self.parsear_id_metodo_pago(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'payment_metodo_id'))
            
        if self.ordenar_por == "STATUS_DETAIL":
            self.lista_de_posicion_ordenar = self.obtener_posiciones_originales(self.ALL_STATUS_DETAIL)
            self.ALL_STATUS_DETAIL = sorted(self.ALL_STATUS_DETAIL)
        else:
            self.ALL_STATUS_DETAIL = self.parsear_estado_pago(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'status_detail'))
            
        if self.ordenar_por == "TRANSACTION_REFUND":
            self.ALL_TRANSACTION_REFUND = self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'transaction_amount_refunded')
            self.ALL_TRANSACTION_REFUND = [float(num) for num in self.ALL_TRANSACTION_REFUND]
            self.lista_de_posicion_ordenar = self.obtener_posiciones_originales(self.ALL_TRANSACTION_REFUND)
            self.ALL_TRANSACTION_REFUND = sorted(self.ALL_TRANSACTION_REFUND)
            self.ALL_TRANSACTION_REFUND = self.parsear_monto_total(self.ALL_TRANSACTION_REFUND)
        else:
            self.ALL_TRANSACTION_REFUND = self.parsear_monto_total(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'transaction_amount_refunded'))
        
        if self.ordenar_por == "TRANSACTION_DETAIL":
            self.ALL_TRANSACTION_DETAIL = self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'transaction_details_total_paid_amount')
            self.ALL_TRANSACTION_DETAIL = [float(num) for num in self.ALL_TRANSACTION_DETAIL]
            self.lista_de_posicion_ordenar = self.obtener_posiciones_originales(self.ALL_TRANSACTION_DETAIL)
            self.ALL_TRANSACTION_DETAIL = sorted(self.ALL_TRANSACTION_DETAIL)
            self.ALL_TRANSACTION_DETAIL = self.parsear_monto_total(self.ALL_TRANSACTION_DETAIL)
        else:
            self.ALL_TRANSACTION_DETAIL = self.parsear_monto_total(self.conexion_dba_server.specify_search_columna('MPQRCODE_OBTENERPAGO', 'transaction_details_total_paid_amount'))
    
    def get_tuple_orber_by(self, rango, posicion):
        if self.ordenar_por == "NRO_FACTURA":
            return (self.ALL_NRO_FACTURA[rango],
                    self.ALL_HS_ACTUALIZACION[posicion],
                    self.ALL_PAYMENT_METHOD_ID[posicion],
                    self.ALL_STATUS_DETAIL[posicion],
                    self.ALL_TRANSACTION_REFUND[posicion],
                    self.ALL_TRANSACTION_DETAIL[posicion],
                    self.ALL_NomCaja[posicion] if not None else "" ,
                    self.ALL_NombreCajero[posicion] if not None else "",
                    self.ALL_NumCajero[posicion] if not None else "")
        elif self.ordenar_por == "PAYMENT_METHOD_ID":
            return (self.ALL_NRO_FACTURA[posicion],
                    self.ALL_HS_ACTUALIZACION[posicion],
                    self.ALL_PAYMENT_METHOD_ID[rango],
                    self.ALL_STATUS_DETAIL[posicion],
                    self.ALL_TRANSACTION_REFUND[posicion],
                    self.ALL_TRANSACTION_DETAIL[posicion],
                    self.ALL_NomCaja[posicion] if not None else "" ,
                    self.ALL_NombreCajero[posicion] if not None else "",
                    self.ALL_NumCajero[posicion] if not None else "")
        elif self.ordenar_por == "STATUS_DETAIL":
            return (self.ALL_NRO_FACTURA[posicion],
                    self.ALL_HS_ACTUALIZACION[posicion],
                    self.ALL_PAYMENT_METHOD_ID[posicion],
                    self.ALL_STATUS_DETAIL[rango],
                    self.ALL_TRANSACTION_REFUND[posicion],
                    self.ALL_TRANSACTION_DETAIL[posicion],
                    self.ALL_NomCaja[posicion] if not None else "" ,
                    self.ALL_NombreCajero[posicion] if not None else "",
                    self.ALL_NumCajero[posicion] if not None else "")
        elif self.ordenar_por == "TRANSACTION_REFUND":
            return (self.ALL_NRO_FACTURA[posicion],
                    self.ALL_HS_ACTUALIZACION[posicion],
                    self.ALL_PAYMENT_METHOD_ID[posicion],
                    self.ALL_STATUS_DETAIL[posicion],
                    self.ALL_TRANSACTION_REFUND[rango],
                    self.ALL_TRANSACTION_DETAIL[posicion],
                    self.ALL_NomCaja[posicion] if not None else "" ,
                    self.ALL_NombreCajero[posicion] if not None else "",
                    self.ALL_NumCajero[posicion] if not None else "")
        elif self.ordenar_por == "TRANSACTION_DETAIL":
            return (self.ALL_NRO_FACTURA[posicion],
                    self.ALL_HS_ACTUALIZACION[posicion],
                    self.ALL_PAYMENT_METHOD_ID[posicion],
                    self.ALL_STATUS_DETAIL[posicion],
                    self.ALL_TRANSACTION_REFUND[posicion],
                    self.ALL_TRANSACTION_DETAIL[rango],
                    self.ALL_NomCaja[posicion] if not None else "" ,
                    self.ALL_NombreCajero[posicion] if not None else "",
                    self.ALL_NumCajero[posicion] if not None else "")
            
            
    def show__content_frame(self):
        self.content_frame_sheet_top = CTk.CTkFrame(self.frame_sheet_top, fg_color='red')
        self.content_frame_sheet_top.pack(fill="both", expand=True)
        
        self.busqueda_frame =  CTk.CTkFrame(self.content_frame_sheet_top, border_width= 3, fg_color='transparent')
        self.busqueda_frame.grid(row=0, column=0, padx=100)
        
        self.frame_icon_label = CTk.CTkFrame(self.busqueda_frame, fg_color='transparent')
        self.label_icon = CTk.CTkLabel(self.frame_icon_label, text="", image=self.lupa_png)
        self.label_buscardor = CTk.CTkLabel(self.frame_icon_label, text="Buscador")
        self.label_icon.pack(side="left", padx=3)
        self.label_buscardor.pack(side="right", padx=3)
        self.entry_buscador = CTk.CTkEntry(self.busqueda_frame, width=250, placeholder_text="Ingresar texto")
        self.frame_icon_label.pack(pady=5, padx=5)
        self.entry_buscador.pack(pady=5, padx=5)
        
        self.option_menu_frame = CTk.CTkFrame(self.content_frame_sheet_top, border_width= 3, fg_color='transparent')
        self.option_menu_frame.grid(row=0, column=1, padx=100)
        
        self.frame_ordenar_por = CTk.CTkFrame(self.option_menu_frame)
        self.frame_ordenar_por.pack(pady=10, padx=10)
        
        self.label_ordenar_por = CTk.CTkLabel(self.frame_ordenar_por, text= "Ordenar por: ")
        self.ordenar_por_optionmenu_var = CTk.StringVar(value=self.ordenar_por)
        self.ordenar_por_optionmenu = CTk.CTkOptionMenu(self.frame_ordenar_por,values=["Número de Factura","Metodo de Pago","Estado del Pago","Transacciones Devueltas","Total de Transacciones"],
                                                command=self.optionmenu_callback,
                                                variable=self.ordenar_por_optionmenu_var,
                                                width=250)
        self.label_ordenar_por.pack(side="left",pady=5, padx=5)
        self.ordenar_por_optionmenu.pack(side="right",pady=5, padx=5)
        
        self.frame_filtrar_por = CTk.CTkFrame(self.option_menu_frame)
        self.frame_filtrar_por.pack(pady=10, padx=10)
        
        self.label_filtrar_por = CTk.CTkLabel(self.frame_filtrar_por, text= "Filtrar por: ")
        self.filtrar_por_optionmenu_var = CTk.StringVar(value="Defecto")
        self.filtrar_por_optionmenu = CTk.CTkOptionMenu(self.frame_filtrar_por,values=["Defecto", "Acreditado", "Devuelto"],
                                                command=self.filtrar_por_option_callback,
                                                variable=self.filtrar_por_optionmenu_var,
                                                width=250)
        self.label_filtrar_por.pack(side="left",pady=5, padx=5)
        self.filtrar_por_optionmenu.pack(side="right",pady=5, padx=5)
        
    def optionmenu_callback(self, choice):
        print("optionmenu dropdown clicked:", choice)
        self.lista_con_datos = []
        if choice ==  "Número de Factura":
            self.set_ordenar_por_NRO_FACTURA()
        elif choice == "Metodo de Pago":
            self.set_ordenar_por_PAYMENT_METHOD_ID()
        elif choice == "Estado del Pago":
            self.set_ordenar_por_STATUS_DETAIL()
        elif choice == "Transacciones Devueltas":
            self.set_ordenar_por_TRANSACTION_REFUND()
        elif choice == "Total de Transacciones":
            self.set_ordenar_por_TRANSACTION_DETAIL()
        self.sheet.set_sheet_data(data = self.lista_con_datos,
               reset_col_positions = True,
               reset_row_positions = True,
               redraw = True,
               verify = False,
               reset_highlights = False)
        #self.save_sheet()
        
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
    def set_ordenar_por_NRO_FACTURA(self):
        self.ordenar_por = "NRO_FACTURA"
        self.get_full_main_order()
        self.mostrar_datos()
    
    def set_ordenar_por_PAYMENT_METHOD_ID(self):
        self.ordenar_por = "PAYMENT_METHOD_ID"
        self.get_full_main_order()
        self.mostrar_datos()
    
    def set_ordenar_por_STATUS_DETAIL(self):
        self.ordenar_por = "STATUS_DETAIL"
        self.get_full_main_order()
        self.mostrar_datos()
    
    def set_ordenar_por_TRANSACTION_REFUND(self):
        self.ordenar_por = "TRANSACTION_REFUND"
        self.get_full_main_order()
        self.mostrar_datos()
    
    def set_ordenar_por_TRANSACTION_DETAIL(self):
        self.ordenar_por = "TRANSACTION_DETAIL"
        self.get_full_main_order()
        self.mostrar_datos()

    def save_sheet(self):
        filepath = filedialog.asksaveasfilename(parent = self.sheet,
                                                title = "Save sheet as",
                                                filetypes = [('CSV File','.csv'),
                                                             ('TSV File','.tsv')],
                                                defaultextension = ".csv",
                                                confirmoverwrite = True)
        if not filepath or not filepath.lower().endswith((".csv", ".tsv")):
            return
        try:
            with open(normpath(filepath), "w", newline = "", encoding = "utf-8") as fh:
                writer = csv.writer(fh,
                                    dialect = csv.excel if filepath.lower().endswith(".csv") else csv.excel_tab,
                                    lineterminator = "\n")
                writer.writerows(self.sheet.get_sheet_data(get_header = False, get_index = False))
        except:
            return
        
    def get_tuple_filter_by(self, tipo_filtrado):
        # Filtrar tuplas donde el valor en la posición 4 es 'Acreditado'
        self.lista_con_datos = [tupla for tupla in self.lista_con_datos if tupla[3] == tipo_filtrado]
        