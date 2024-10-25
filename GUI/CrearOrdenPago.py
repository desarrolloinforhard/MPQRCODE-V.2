import time
from tkinter import messagebox
from BarraProgreso import BarraProgreso
from qrcode_mpV2 import crear_qr_data
from log_errorsV2 import log_error

class CrearOrdenPago(BarraProgreso):
    def __init__(self, frame, DICT_WIDGETS, DICT_DATOS_ORDEN, DICT_CONEXION):
        try:
        
            # Inicializar correctamente la clase base ttk.Progressbar
            super().__init__(frame)
            
            self.crearorden = True
            self.orden_creada = False
            self.DICT_CONEXION = DICT_CONEXION
            self.DICT_DATOS_ORDEN = DICT_DATOS_ORDEN
            
            self.DICT_PROGRESO = {
                "widgets": DICT_WIDGETS,
                "text_label_aviso": "Creando Orden",
                "carga": 25,
                "command": self.crear_orden
            }
            while self.crearorden:
                #print(f"self.crearorden: {self.crearorden}")
                if not self.orden_creada:
                    #threading.Thread(target=self.crear_orden).start()
                    self.progreso(**self.DICT_PROGRESO)
                    self.orden_creada = True
                time.sleep(1)
        except Exception as e:
            log_error(e, "CrearOrdenPago")
        
        
        
    def crear_orden(self):
        try:
            print("HOLA")
            self.qr_data = self.DICT_CONEXION["conexionAPI"].crearOrdenDinamicoV2(
                self.DICT_DATOS_ORDEN["external_id_pos"], 
                self.DICT_DATOS_ORDEN["nro_factura"], 
                self.DICT_DATOS_ORDEN["sucNAME"], 
                self.DICT_DATOS_ORDEN["monto_pagar"], 
                #self.datos_caja[4],
                self.DICT_DATOS_ORDEN["url_API_AWS"] ## PRUEBA
            )
            print(self.qr_data)
            if not self.qr_data == None and self.qr_data.status_code == 200:
                data_qr = self.qr_data.json()['qr_data']
                print(data_qr)
                crear_qr_data(data_qr)
                #LUEGO AGREGAR FUNCION CREA IMG QR
                self.DICT_PROGRESO["text_label_aviso"] = "Orden Creada"
                self.DICT_PROGRESO["carga"] = 40
                self.DICT_PROGRESO["command"] = self.func_orden_creada
                self.progreso(**self.DICT_PROGRESO)
            else:
                if self.qr_data == None:
                    log_error("ERROR 500", "No conexión")
                    messagebox.showerror(f"ERROR 500", "No conexión")
                else:
                    log_error(self.qr_data.json()['message'], "Error: Respuesta de MP al Crear Pago")
                    messagebox.showerror(f"ERROR {self.qr_data.status_code}", self.qr_data.json()['message'])
                self.cierre_ERROR()
        except Exception as e:
            log_error(str(e), 'crear_orden')
            messagebox.showerror('Error', 'Ocurrió un error al crear la orden.')
            self.cierre_ERROR()
        
    def func_orden_creada(self):
        self.DICT_PROGRESO["text_label_aviso"] = "Orden Creada"
        self.DICT_PROGRESO["carga"] = 50
        self.DICT_PROGRESO["command"] = self.print_hola
        
        self.progreso(**self.DICT_PROGRESO)
        
        
    def print_hola(self):
        print("Hola Mundo")
        """ while barra_progreso.estado():
            print(barra_progreso.estado())
            time.sleep(1)
        DICT_PROGRESO["carga"] = 60"""
        #barra_progreso.progreso(**DICT_PROGRESO)
        
        
    def cierre_ERROR(self):
        self.DICT_PROGRESO["text_label_aviso"] = "ERROR"
        self.DICT_PROGRESO["carga"] = 99
        self.progreso(**self.DICT_PROGRESO)
        print("CIERRE")
        self.crearorden = False