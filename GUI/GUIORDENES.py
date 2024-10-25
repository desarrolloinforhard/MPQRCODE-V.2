import tkinter as tk
import ttkbootstrap as ttk
import window_position
import threading
import time
from decimal import Decimal
from CrearOrdenPago import CrearOrdenPago
from ttkbootstrap.constants import *
from tkinter import messagebox
from image_path import *
from PIL import Image, ImageTk
from log_errorsV2 import log_error


class GUIMAIN:
    def __init__(self, version, DICT_CONEXION):
        
        self.conexionAPI = DICT_CONEXION["conexionAPI"]
        self.conexionAPIPOINT = DICT_CONEXION["conexionAPIPOINT"]
        self.conexionDBA = DICT_CONEXION["conexionDBA"]
        self.conexionDBAServer = DICT_CONEXION["conexionDBAServer"]
        
        try:
            self.datos_para_orden = self.conexionDBA.specify_search_all_columns_nocondicion("MPQRCODE_CONEXIONPROGRAMAS")[0]
            #self.datos_para_orden[0] = nro_factura
            #self.datos_para_orden[1] = tipo_factura
            #self.datos_para_orden[2] = monto_pagar
            #self.datos_para_orden[3] = status
            #self.datos_para_orden[4] = response
            #self.datos_para_orden[5] = description
            #self.datos_para_orden[6] = tipo_point
            #self.datos_para_orden[7] = IDMercadoPago
            #self.datos_para_orden[8] = NOMCAJA
            #self.datos_para_orden[9] = NUMCAJERO
            #self.datos_para_orden[10] = NOMBRECAJERO
            
            self.datos_caja = self.conexionDBA.specify_search_all_columns("MPQRCODE_CAJA", "idINCREMENT", 1)
            #self.datos_caja[0] = idINCREMENT
            #self.datos_caja[1] = sucNAME
            #self.datos_caja[2] = posNAME
            #self.datos_caja[3] = external_id_pos
            #self.datos_caja[4] = IPN_url
        except Exception as e:
            log_error(f"Error al obtener datos para la orden: {e}", function_name='__init__')
            messagebox.showerror("Error", "No se pudo obtener los datos necesarios para la orden.")
        
        self.ventana_creacion_caja = ttk.Window(themename="lumen")
        self.ventana_creacion_caja.title(f"Creación de Orden, V.{version}")
        self.ventana_creacion_caja.resizable(False, False)
        
        
        self.frame = tk.Frame(self.ventana_creacion_caja, height=400, width=550)
        self.frame.pack()

        self.frame_conjunto = tk.Frame(self.frame)
        self.frame_conjunto.pack(pady=40)
        
        self.func_barra_progreso(DICT_CONEXION)
        
        self.logo_mp()
        
        
        
        window_position.center_window(self.ventana_creacion_caja, 400, 550)
        self.ventana_creacion_caja.mainloop()
        
        
        
    def logo_mp(self):
        try:
            path_img_dir = LOGO_MP()

            # Cargar y redimensionar la imagen
            self.logo_mp_img = Image.open(path_img_dir)
            self.logo_mp_img = self.logo_mp_img.resize((240, 190), Image.LANCZOS)
            self.logo_mp_img_tk = ImageTk.PhotoImage(self.logo_mp_img)

            # Crear y empacar el Label con la imagen
            self.logo_mp_img_label = ttk.Label(self.frame_conjunto, image=self.logo_mp_img_tk)
            self.logo_mp_img_label.pack()

        except Exception as e:
            log_error(str(e), "logo_mp")
            messagebox.showerror("Error", "Ha ocurrido un error al cargar el logo de MercadoPago.")
            
            
    def func_barra_progreso(self, DICT_CONEXION):
        self.frame_contenedor_barra_progreso = tk.Frame(self.frame)
        self.frame_contenedor_barra_progreso.pack()
        
        self.frame_barra_progreso = tk.Frame(self.frame_contenedor_barra_progreso)
        self.frame_barra_progreso.pack()
        
        self.my_label_estado = tk.Label(self.frame_contenedor_barra_progreso, text="", font=("Helvetica", 18))
        self.my_label_estado.pack(pady=10)
        
        self.my_label_aviso = tk.Label(self.frame_contenedor_barra_progreso, text="", font=("Helvetica", 18))
        self.my_label_aviso.pack(pady=10)
        
        DIC_WIDGET = {
            "root": self.ventana_creacion_caja,
            "label_estado": self.my_label_estado,
            "my_label_aviso": self.my_label_aviso,
        }
        
        
        
        
        if self.datos_para_orden[1] == 1:
            DICT_DATOS_ORDEN = {
                "external_id_pos": self.datos_caja[3], 
                "nro_factura": self.datos_para_orden[0], 
                "sucNAME": self.datos_caja[1], 
                "monto_pagar": float(self.datos_para_orden[2].quantize(Decimal('1.00'))), 
                #self.datos_caja[4],
                "url_API_AWS": self.conexionDBAServer.specify_search_condicion("SPDIR", "ID", "GRID", "url_api_AWS", False)
            }
            threading.Thread(target=CrearOrdenPago, args=(self.frame, DIC_WIDGET, DICT_DATOS_ORDEN, DICT_CONEXION)).start()