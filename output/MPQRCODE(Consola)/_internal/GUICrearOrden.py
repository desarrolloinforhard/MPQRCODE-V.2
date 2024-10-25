
from image_path import *

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import threading
import time
import keyboard
from decimal import Decimal
from PIL import Image, ImageTk
from qrcode_mp import crear_qr_data

class CrearOrdenApp:
    def __init__(self, conexionAPI, conexionAPIPOINT, conexionDBA, conexionDBAServer, version):
        self.conexionAPI = conexionAPI
        self.conexionAPIPOINT = conexionAPIPOINT
        self.conexionDBA = conexionDBA
        self.conexionDBAServer = conexionDBAServer
        self.datos_para_orden = self.conexionDBA.specify_search_all_columns_nocondicion("MPQRCODE_CONEXIONPROGRAMAS")[0]
        self.datos_caja = self.conexionDBA.specify_search_all_columns("MPQRCODE_CAJA", "idINCREMENT", 1)
        
        
        self.ventana_creacion_caja = ttk.Window(themename="lumen")
        self.ventana_creacion_caja.title(f"Creación de Orden, V.{version}")
        self.ventana_creacion_caja.geometry("400x550")
        # Configurar el evento de cambio de tamaño
        self.ventana_creacion_caja.resizable(False, False)
        self.icon()       
            
        self.id_order_var = tk.StringVar()
        self.obtenerPago = None
        self.progresoNRO = 0
        self.status_cancel = 0
        self.stop_thread = False
        self.eleccion_message = None
        
        self.idPOINT = None
        self.idPAYMENT = None
        self.frame = tk.Frame(self.ventana_creacion_caja,)

        self.frame.pack(side='left', padx=10)
        #CONJUNTO DE BARRA DE PROGRESO, TEMP Y QR EN PANTALLA
        self.frame_conjunto = tk.Frame(self.frame, bg=self.ventana_creacion_caja['bg'])
        self.frame_conjunto.pack(padx=10)

        #LOGO DE MERCADO PAGO
        self.logo_mp()  
        
        self.frame_left = tk.Frame(self.frame_conjunto,)
        self.frame_left.pack(padx=20)
        
        self.frame_right = tk.Frame(self.ventana_creacion_caja,)
        self.frame_right.pack(side='right', padx=20)  
            
        self.my_progressbar = ttk.Progressbar(self.frame_left, orient="horizontal", length=350, mode='determinate', style='color.Horizontal.TProgressbar')
        self.my_progressbar.pack(pady=15)

        """# Creamos el estilo para la barra de progreso
        style = ttk.Style()
        style.theme_use('default')

        # Configuramos el estilo para que la barra de progreso sea de color celeste
        style.configure('color.Horizontal.TProgressbar', foreground='lightblue', background='lightblue')

        # También puedes configurar otras propiedades como el grosor de la barra (thickness)
        style.configure('color.Horizontal.TProgressbar', thickness=10)"""
        
        self.my_progressbar['value'] = 0
            
        self.framebottons = tk.Frame(self.frame_conjunto, height=100,)
        self.framebottons.pack(pady=10)
            
        self.my_buttonDLT = tk.Button(self.framebottons, text="Cancelar Orden", command=self.cancelar_ordenELECC, state=tk.DISABLED, width=15, height=2)

        self.my_buttonDLT.bind("<a>", self.simular_clic)
        self.my_buttonDLT.bind("<6>", self.simular_clic)
        self.my_buttonDLT.pack(side="right", padx=5)
            
            
        self.my_label_aviso = tk.Label(self.frame_left, text="", font=("Helvetica", 18))
        self.my_label_aviso.pack(pady=10)

            
        self.my_label = tk.Label(self.frame_left, text="", font=("Helvetica", 18))
        self.my_label.pack(pady=10)
            
        self.my_label_time = tk.Label(self.frame_left, text="", font=("Helvetica", 16))
        self.my_label_time.pack(pady=10)
        self.timer_id = None          
        self.functionMAIN()
        self.ventana_creacion_caja.protocol("WM_DELETE_WINDOW", self.mostrar_error)
        # Configurar el evento de mapeo de la ventana
        self.ventana_creacion_caja.bind("<Map>", self.on_map)
        #self.center_window(self.ventana_creacion_caja)
        self.ventana_creacion_caja.mainloop()
        
    def mostrar_error(self):
        # Mostrar un mensaje de error
        messagebox.showerror("Error", "No se puede cerrar la ventana porque una orden está en proceso.")
        
    
    def icon(self):
        rutaicono = Icono_MercadoPago_Blue()
        self.ventana_creacion_caja.iconbitmap(rutaicono)         
    def update_window(self):
        self.ventana_creacion_caja.update_idletasks()

    def clicker(self):
        self.my_progressbar.step()
        self.my_label.config(text=str((int(self.my_progressbar['value']*1))) + "%")
        """self.progresoNRO = int(self.my_progressbar['value']*1)"""
        
        self.update_window()
        
        
    def functionMAIN(self):
        if self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 1:
            self.crear_orden()
            threading.Thread(target=self.clickerFull).start()
        elif self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 2:
            threading.Thread(target=self.clickerFullReembolso).start()
        elif self.datos_para_orden[6] == 1 and self.datos_para_orden[1] == 1:
            threading.Thread(target=self.clickerFullPoint).start()
            
    def clickerFull(self):
        clickerProgress = int(self.my_progressbar['value'])
        while not clickerProgress == 99 and not self.stop_thread: # Resto del código del hilo
            if clickerProgress <= 25:
                self.my_label_aviso.config(text="Creando Orden...")
                if not clickerProgress == 25:
                    while not clickerProgress == 25:
                        self.clicker()
                        clickerProgress = int(self.my_progressbar['value'])
                        time.sleep(0.05)
                    else:
                        self.clicker()
                        clickerProgress = int(self.my_progressbar['value'])
                        time.sleep(0.5)
                        crear_qr_data(self.qr_data)
                        self.my_label_aviso.config(text="Orden Creada. Escanee el QR")
                        self.label_img()
            elif clickerProgress < 50:
                if not clickerProgress == 50:
                    while not clickerProgress == 50 and type(self.id_order_var.get()) == str:
                        
                        self.clicker()
                        clickerProgress = int(self.my_progressbar['value'])
                        time.sleep(0.05)
                    else:
                        clickerProgress = int(self.my_progressbar['value'])
                        time.sleep(0.25)
                        self.my_label_aviso.config(text="Esperando Pago...")
                        self.my_buttonDLT.config(state=tk.NORMAL)
                        # Asociar la función on_a_and_7 al evento KeyPress
                        keyboard.hook(self.on_a_and_7)
                        # Asociar la combinación de teclas con la función cancelar_orden
                        self.obteneridOrder(self.datos_para_orden[0], None)
                        self.ventana_creacion_caja.geometry("400x550")

                        self.clicker()
                        self.my_buttonDLT.config(state=tk.DISABLED)
            elif clickerProgress < 80:
                
                if self.status_cancel == 0: 
                    
                    self.obtenerPago = self.obtnerPago(self.id_order_var.get(), True, self.datos_para_orden[6])
                if not clickerProgress == 80:
                    while not clickerProgress == 80:
                        if self.id_order_var.get() == "":
                            
                            self.clicker()
                            clickerProgress = int(self.my_progressbar['value'])
                        else:
                            self.clicker()
                            clickerProgress = int(self.my_progressbar['value'])
                    else:
                        self.clicker()
                        clickerProgress = int(self.my_progressbar['value'])
                        time.sleep(0.05)
                        self.my_label_aviso.config(text="Comparando Registros...")
                        if self.conexionDBA.specify_search_condicion("MPQRCODE_OBTENERPAGO", "status", "external_reference", self.datos_para_orden[0], False) == 'approved' or self.status_cancel > 200:
                            pass
                        else:
                            self.message_status = self.conexionDBA.specify_search_condicion("MPQRCODE_OBTENERPAGO", "status", "external_reference", self.datos_para_orden[0], False)
                            self.message_status_detail= self.buscar_errorESP(self.conexionDBA.specify_search_condicion("MPQRCODE_OBTENERPAGO", "status_detail", "external_reference", self.datos_para_orden[0], False))
                            while self.id_order_var.get() == None or not self.message_status == "approved":
                                keyboard.hook(self.on_a_and_8)
                                if self.eleccion_message == None:
                                    self.eleccion_message = messagebox.askretrycancel(message=f"No sea recibido el pago.\n ERROR: {self.message_status}\n DETALLE: {self.message_status_detail[1]}\n ¿Desea reintentar el pago?", title="Error de Pago")
                                else:
                                    if self.eleccion_message:
                                        self.status_cancel = 0
                                        self.my_label_aviso.config(text="Esperando Pago...")
                                        self.my_buttonDLT.config(state=tk.NORMAL)
                                        self.my_progressbar['value'] = 50
                                        self.my_label.config(text=str((int(self.my_progressbar['value']*1))) + "%")
                                        self.update_window()
                                        self.obteneridOrder(self.datos_para_orden[0], self.conexionDBA.specify_search_condicion("MPQRCODE_OBTENERPAGO", "id", "external_reference", self.datos_para_orden[0], False))
                                        self.my_buttonDLT.config(state=tk.DISABLED)
                                        self.clicker()
                                        clickerProgress = int(self.my_progressbar['value'])        
                                        if clickerProgress < 80:
                                            
                                            self.obtenerPago = self.obtnerPago(self.id_order_var.get(), False, self.datos_para_orden[6])
                                            if not clickerProgress == 80:
                                                while not clickerProgress == 80:
                                                    if self.id_order_var.get() == "":
                                                        self.clicker()
                                                        clickerProgress = int(self.my_progressbar['value'])                        
                                                    else:
                                                        self.clicker()
                                                        clickerProgress = int(self.my_progressbar['value'])                        
                                                else:
                                                    self.clicker()
                                                    clickerProgress = int(self.my_progressbar['value'])                    
                                                    time.sleep(0.05)
                                                    self.my_label_aviso.config(text="Comparando Registros...")
                                        self.message_status = self.conexionDBA.specify_search_condicion("MPQRCODE_OBTENERPAGO", "status", "external_reference", self.datos_para_orden[0], False)                              
                                        self.message_status_detail= self.buscar_errorESP(self.conexionDBA.specify_search_condicion("MPQRCODE_OBTENERPAGO", "status_detail", "external_reference", self.datos_para_orden[0], False))
                                    else:
                                        self.terminar_orden()
                                    break
            elif clickerProgress < 100:
                if not clickerProgress == 98:
                    while not clickerProgress == 98:
                        clickerProgress = int(self.my_progressbar['value'])
                        self.clicker()
                        time.sleep(0.05)
                elif clickerProgress == 99:
                    self.my_label.config(text=str(100) + "%")
                    break
                break
            time.sleep(0.05)
        self.finalizarPago(self.obtenerPago)
        
    def clickerFullReembolso(self):
        clickerProgress = int(self.my_progressbar['value']*1)
        while not clickerProgress == 99 and not self.stop_thread:
            if clickerProgress <= 25:
                self.my_label_aviso.config(text="Buscando ID de la Factura...")
                if not clickerProgress == 25:
                    while not clickerProgress == 25:
                        self.clicker()
                        clickerProgress = int(self.my_progressbar['value']*1)
                        time.sleep(0.05)
                    else:
                        self.clicker()
                        clickerProgress = int(self.my_progressbar['value']*1)
                        self.obteneridOrder(self.datos_para_orden[0], None)
                        time.sleep(0.5)
                        if not self.id_order_var.get() == None:
                            self.my_label_aviso.config(text="ID encontrado")
                        else:
                            self.my_label_aviso.config(text="ID no encontrado. Factura no existente")
                            break
            elif clickerProgress < 50:
                if not clickerProgress == 50:
                    while not clickerProgress == 50 and type(self.id_order_var.get()) == str:
                        self.clicker()
                        clickerProgress = int(self.my_progressbar['value']*1)
                        time.sleep(0.05)
                    else:
                        clickerProgress = int(self.my_progressbar['value']*1)
                        time.sleep(0.25)
                        self.my_label_aviso.config(text="Creando Orden...")
                        self.crear_orden_reemboslso(float(self.datos_para_orden[2].quantize(Decimal('1.00'))))
                        self.clicker()
            elif clickerProgress < 80:
                self.obtenerPago = self.obtnerPago(self.id_order_var.get(), False, self.datos_para_orden[6])
                if not clickerProgress == 80:
                    while not clickerProgress == 80:
                        if self.id_order_var.get() == "":
                            self.clicker()
                            clickerProgress = int(self.my_progressbar['value']*1)
                        else:
                            self.clicker()
                            clickerProgress = int(self.my_progressbar['value']*1)
                    else:
                        self.clicker()
                        clickerProgress = int(self.my_progressbar['value']*1)
                        time.sleep(0.05)
                        self.my_label_aviso.config(text="Esperando ID del Reembolso...")
            elif clickerProgress < 100:
                if not clickerProgress == 99:
                    while not clickerProgress == 99:
                        self.clicker()
                        clickerProgress = int(self.my_progressbar['value']*1)
                        time.sleep(0.05)
                    else:
                        self.my_progressbar.config(value=100)
            time.sleep(0.05)
        self.finalizarPago(self.obtenerPago)
        
    def clickerFullPoint(self):
        pos_id = self.conexionDBAServer.specify_search_condicion("MPQRCODE_CAJAS", 'id', 'external_id', self.datos_caja[3], False)
        store_id = self.conexionDBAServer.specify_search_condicion("MPQRCODE_CAJAS", 'store_id', 'external_id', self.datos_caja[3], False)
        self.idPOINT = self.conexionAPIPOINT.obtenerPointPOS(store_id, pos_id) # 'INGENICO_MOVE2500__ING-ARG-6401494660'
        if not self.idPOINT == "No se encontro el dispositivo":
            clickerProgress = int(self.my_progressbar['value']*1)
            # Modificar los valores que pasen de estar con coma a sin coma
            valor_decimal = self.datos_para_orden[2].quantize(Decimal('1.00'))
            valor_con_comas = str(valor_decimal)
            valor_sin_comas = int(valor_con_comas.replace('.', '').replace(',', ''))
            self.idPAYMENT = self.conexionAPIPOINT.crearIntencionPAGOPoint(self.idPOINT, self.datos_para_orden[0], valor_sin_comas, "000000").json()
            if not 'message' in self.idPAYMENT:
                self.idPAYMENT = self.idPAYMENT['id']
                
                self.my_label_aviso.config(text="Creando Orden...")
                while not clickerProgress == 99 and not self.stop_thread:
                    if clickerProgress <= 25:
                        if not clickerProgress == 25:
                            while not clickerProgress == 25:
                                self.clicker()
                                clickerProgress = int(self.my_progressbar['value']*1)
                                self.my_label_aviso.config(text="Creando Orden...")
                                time.sleep(0.05)
                            else:
                                self.clicker()
                                clickerProgress = int(self.my_progressbar['value']*1)
                                self.my_label_aviso.config(text="Enviando Orden al POINT...")
                                time.sleep(0.5)
                    elif clickerProgress < 50:
                        if not clickerProgress == 50:
                            while not clickerProgress == 50 and type(self.id_order_var.get()) == str:
                                self.clicker()
                                clickerProgress = int(self.my_progressbar['value']*1)
                                time.sleep(0.05)
                            else:
                                clickerProgress = int(self.my_progressbar['value']*1)
                                time.sleep(0.25)
                                self.my_label_aviso.config(text="Valla al POINT.\nEsperando Pago...")
                                self.my_buttonDLT.config(state=tk.NORMAL)
                                # Asociar la función on_a_and_7 al evento KeyPress
                                keyboard.hook(self.on_a_and_7)
                                # Asociar la combinación de teclas con la función cancelar_orden
                                self.obteneridOrder(self.datos_para_orden[0], None)
                                self.clicker()
                                self.my_buttonDLT.config(state=tk.DISABLED)
                    elif clickerProgress < 80:
                        if self.status_cancel == 0 and not self.id_order_var.get() == "None":
                            
                            self.obtenerPago = self.obtnerPago(self.id_order_var.get(), True, self.datos_para_orden[6])
                        if not clickerProgress == 80:
                            while not clickerProgress == 80:
                                if self.id_order_var.get() == "":
                                    self.clicker()
                                    clickerProgress = int(self.my_progressbar['value']*1)
                                else:
                                    self.clicker()
                                    clickerProgress = int(self.my_progressbar['value']*1)
                            else:
                                self.clicker()
                                clickerProgress = int(self.my_progressbar['value']*1)
                                time.sleep(0.05)
                                self.my_label_aviso.config(text="Comparando Registros...")
                    elif clickerProgress < 100:
                        if not clickerProgress == 99:
                            while not clickerProgress == 99:
                                self.clicker()
                                clickerProgress = int(self.my_progressbar['value']*1)
                                time.sleep(0.05)
                            else:
                                self.my_progressbar.config(value=100)
                    time.sleep(0.05)
                if not self.id_order_var.get() == "None":
                    self.finalizarPago(self.obtenerPago)
                else:
                    self.finalizarPago(False)
            else:
                messagebox.showerror('Error', self.idPAYMENT['message'])
        else:
            messagebox.showerror('Error', self.idPOINT)
        
        
    def crear_orden(self):
        self.qr_data = self.conexionAPI.crearOrdenDinamico(self.datos_caja[3], self.datos_para_orden[0], self.datos_caja[1], float(self.datos_para_orden[2].quantize(Decimal('1.00'))), self.datos_caja[4])
    
    def crear_orden_reemboslso(self, monto_devolver):
        respuesta = self.conexionAPI.crear_orden_reembolso(self.id_order_var.get(), monto_devolver)
        
        
    
    def obteneridOrder(self, external_reference, obtenido_ID):
        pos_id = self.conexionDBAServer.specify_search_condicion("MPQRCODE_CAJAS", 'id', 'external_id', self.datos_caja[3], False)
        
        if self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 1:
            self.orden_cronometro(280, self.cancelar_orden)
            
            if obtenido_ID == None:
                obtener_ID = None
                while obtener_ID is None and self.status_cancel == 0:
                    obtener_ID = self.conexionDBAServer.specify_search_condicionID("MPQRCODE_OBTENERPAGOServer", "data", "external_reference", external_reference, 'pos_id', pos_id, False)
                    if obtener_ID is None:
                        
                        time.sleep(1) # Puedes ajustar el tiempo de espera según sea necesario
                    else:
                        
                        self.id_order_var.set(obtener_ID)
            else:
                
                obtener_ID = self.conexionDBAServer.specify_search_condicionID("MPQRCODE_OBTENERPAGOServer", "data", "external_reference", external_reference, 'pos_id', pos_id, False)
                while obtener_ID == str(obtenido_ID) and self.status_cancel == 0:
                    
                    time.sleep(1)
                    obtener_ID = self.conexionDBAServer.specify_search_condicionID("MPQRCODE_OBTENERPAGOServer", "data", "external_reference", external_reference, 'pos_id', pos_id, False)
                    
                    if not obtener_ID == obtenido_ID:
                        
                        self.id_order_var.set(obtener_ID)
                    else:
                        pass
            self.detener_temporizador()
            self.my_label_time.config(text=f"")
        elif self.datos_para_orden[6] == 1 and self.datos_para_orden[1] == 1:
            self.orden_cronometro(280, self.cancelar_orden)
            if obtenido_ID == None:
                statePOINT  = self.conexionAPIPOINT.buscarIntencionPAGOPoint(self.idPAYMENT).json()
                
                while statePOINT['state'] == 'OPEN' or statePOINT['state'] == 'ON_TERMINAL' or statePOINT['state'] == 'PROCESSING':
                    time.sleep(5)#Cada 5 segundos pregunta a la API el estado del Point
                    if 'state' in statePOINT:
                        statePOINT = self.conexionAPIPOINT.buscarIntencionPAGOPoint(self.idPAYMENT).json()
                        
                        if statePOINT['state'] == 'FINISHED':
                            obtener_ID = None
                            while obtener_ID is None and self.status_cancel == 0:
                                obtener_ID = self.conexionDBAServer.specify_search_condicionID("MPQRCODE_OBTENERPAGOPOINTServer", "data", "external_reference", external_reference, 'pos_id', pos_id, False)
                                if obtener_ID is None:
                                    
                                    time.sleep(1) # Puedes ajustar el tiempo de espera según sea necesario
                                else:
                                    
                                    self.id_order_var.set(obtener_ID)
                        elif statePOINT['state'] == 'CANCELED':
                            messagebox.showerror('ERROR', statePOINT['state'])
                            self.id_order_var.set(None)
                        elif statePOINT['state'] == 'ERROR':
                            messagebox.showerror('ERROR', statePOINT['state'])
                            self.id_order_var.set(None)
                        else:
                            pass
            else:
                obtener_ID = self.conexionDBAServer.specify_search_condicionID("MPQRCODE_OBTENERPAGOPOINTServer", "data", "external_reference", external_reference, 'pos_id', pos_id, False)
                while obtener_ID == str(obtenido_ID) and self.status_cancel == 0:
                    
                    time.sleep(1)
                    obtener_ID = self.conexionDBAServer.specify_search_condicionID("MPQRCODE_OBTENERPAGOPOINTServer", "data", "external_reference", external_reference, 'pos_id', pos_id, False)
                    
                    if not obtener_ID == obtenido_ID:
                        
                        self.id_order_var.set(obtener_ID)
                    else:
                        pass
            self.detener_temporizador()
            self.my_label_time.config(text=f"")            
        elif self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 2:
            if obtenido_ID == None:
                
                obtener_ID = self.conexionDBAServer.specify_search_condicion("MPQRCODE_OBTENERPAGOServer", "data", "external_reference", external_reference, False)
                
                self.id_order_var.set(obtener_ID)
    
    def obtnerPago(self, step_two, insertar, tipo_pago):
        if self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 1:
            response = self.conexionAPI.obtenerPago(step_two, self.datos_para_orden[0], self.datos_caja[3], insertar, tipo_pago)
            return response
        elif self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 2:           
            status = self.conexionDBAServer.specify_search_condicion("MPQRCODE_OBTENERPAGOServer", "status", "external_reference", self.datos_para_orden[0], False)
            while not status == "refunded":
                status = self.conexionDBAServer.specify_search_condicion("MPQRCODE_OBTENERPAGOServer", "status", "external_reference", self.datos_para_orden[0], False)
                
                time.sleep(1)
            else:
                response = self.conexionAPI.obtenerPago(step_two, self.datos_para_orden[0], self.datos_caja[3], insertar, tipo_pago)
                return response
        elif self.datos_para_orden[6] == 1 and self.datos_para_orden[1] == 1:
            response = self.conexionAPIPOINT.obtenerPago(step_two, self.datos_para_orden[0], self.datos_caja[3], insertar, tipo_pago)
            return response      
        
    def finalizarPago(self, respuesta):
        self.ventana_creacion_caja.after(0, self.mostrar_resultado_pago, respuesta)

    def mostrar_resultado_pago(self, respuesta):
        response = respuesta
        if response == True:
            if self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 1:
                self.my_label_aviso.configure(text="Pago Recibido")
                messagebox.showinfo("Exito", "Pago Recibido")
                datos = {
                    'status': 1,
                    'response': 0,
                    'description': 'accredited',
                    'IDMercadoPago': self.id_order_var.get(),
                }
                
                datos_obtener_pago = {
                    'NomCaja': self.datos_para_orden[8],
                    'NumCajero': self.datos_para_orden[9],
                    'NombreCajero': self.datos_para_orden[10]
                }
                self.conexionDBA.actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMAS", datos, "nro_factura", f"'{self.datos_para_orden[0]}'")
                if self.datos_para_orden[6] == 0:
                    self.conexionDBA.actualizar_datos_condicion("MPQRCODE_OBTENERPAGOServer", datos_obtener_pago, "external_reference", f"'{self.datos_para_orden[0]}'")
                    self.conexionDBAServer.actualizar_datos_condicion("MPQRCODE_OBTENERPAGOServer", datos_obtener_pago, "external_reference", f"'{self.datos_para_orden[0]}'")
                elif self.datos_para_orden[7] == 1:
                    self.conexionDBA.actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMASPOINTServer", datos_obtener_pago, "external_reference", f"'{self.datos_para_orden[0]}'")
                    self.conexionDBAServer.actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMASPOINTServer", datos_obtener_pago, "external_reference", f"'{self.datos_para_orden[0]}'")
        elif self.status_cancel == 400:
            self.ventana_creacion_caja.after(0, self.mostrar_cancelacion_orden)
        else:
            if self.datos_para_orden[1] == 1:
                self.ventana_creacion_caja.after(0, self.mostrar_error_pago)
            elif self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 2:
                self.my_label_aviso.configure(text="Reembolso Hecho")
                self.ventana_creacion_caja.after(0, self.mostrar_exito_reembolso)
                datos = {
                    'status': 1,
                    'response': 0,
                    'description': 'refund'
                }
                self.conexionDBA.actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMAS", datos, "nro_factura", f"'{self.datos_para_orden[0]}'")
        # Cerrar la ventana después de 3000 milisegundos (3 segundos)
        self.ventana_creacion_caja.after(1000, self.cerrar_ventana)

    def cerrar_ventana(self):
        self.ventana_creacion_caja.destroy()

    def mostrar_cancelacion_orden(self):
        messagebox.showinfo("Cancelar Orden", "La Orden ha sido Cancelada")

    def mostrar_error_pago(self):
        messagebox.showerror("Error", "No se recibió el pago")
        datos = {
            'status': 0,
            'response': self.message_status_detail[0],
            'description': self.message_status_detail[1]
        }
        self.conexionDBA.actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMAS", datos, "nro_factura", f"'{self.datos_para_orden[0]}'")

    def mostrar_exito_reembolso(self):
        messagebox.showinfo("Exito", "Se se devuelto el Dinero")

            
    def cancelar_orden(self, event=None):
        respusta = self.conexionAPI.cancelarOrden(self.datos_caja[3])
        datos = {
                'response': 10,
                'description': 'orden-cancelada'
            }
        self.conexionDBA.actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMAS", datos, "nro_factura", f"'{self.datos_para_orden[0]}'")
        self.status_cancel = respusta
        
    def cancelar_ordenPOINT(self, event=None):
        respusta = self.conexionAPI.cancelarIntencionPAGOPoint(self.idPOINT, self.idPAYMENT)
        
        datos = {
                'response': 10,
                'description': 'orden-cancelada'
            }
        self.conexionDBA.actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMAS", datos, "nro_factura", f"'{self.datos_para_orden[0]}'")
        self.status_cancel = respusta
        
    def simular_clic(self, event):
        self.my_buttonDLT.event_generate("<Button-1>")
        
    def terminar_orden(self):
        respusta = self.conexionAPI.cancelarOrden(self.datos_caja[3])
        self.status_cancel = respusta
        
    def buscar_errorESP(self, error):
        errores = {
            'cc_rejected_insufficient_amount': {
                'nro_error': 20.1,
                'description': 'Saldo Insuficiente',
            },
            
            'cc_rejected_call_for_authorize': {
                'nro_error': 20.2,
                'description': 'Pago no autorizado',
            },
            'cc_rejected_bad_filled_security_code': {
                'nro_error': 20.3,
                'description': 'Código de seguridad inválido',
            },
            'cc_rejected_bad_filled_date': {
                'nro_error': 20.4,
                'description': 'Fecha de Vencimiento de la Tarjeta Invalida',
            },
            'cc_rejected_bad_filled_other': {
                'nro_error': 20.5,
                'description': 'Error en algún dato de la Tarjeta',
            },
            'cc_rejected_other_reason': {
                'nro_error': 20.6,
                'description': 'Pago Rechazado por la Tarjeta',
            }
        }
        
        error_lista = []

        for errorENG, errorEsp in errores.items():
            if errorENG == error:
                for error_clave, error_valor in errorEsp.items():
                    if error_clave == 'nro_error' or error_clave == 'description':
                        error_lista.append(error_valor)
        return error_lista

    def orden_cronometro(self, tiempo, funcion):
        tiempo_espera = 0
        self.actualizar_label(tiempo_espera, tiempo)
        self.temporizador(self.ventana_creacion_caja, tiempo, tiempo_espera, funcion)

    def actualizar_label(self, tiempo_espera, tiempo):
        self.my_label_time.config(text=f"Tiempo de respuesta: {tiempo_espera} de {tiempo}")
        self.update_window()

    def temporizador(self, app, tiempo, tiempo_espera, funcion):
        if tiempo_espera < tiempo:
            tiempo_espera += 1
            self.timer_id = app.after(1000, self.temporizador, app, tiempo, tiempo_espera, funcion)
            self.actualizar_label(tiempo_espera, tiempo)
        else:
            app.after(0, funcion)
            
    def detener_temporizador(self):
        if self.timer_id is not None:
            self.ventana_creacion_caja.after_cancel(self.timer_id)
            self.timer_id = None
            
    def logo_mp(self):
        path_img_dir = LOGO_MP()
        
        # Cargar y redimensionar la imagen
        self.logo_mp_img = Image.open(path_img_dir)
        self.logo_mp_img = self.logo_mp_img.resize((240, 190), Image.LANCZOS)
        self.logo_mp_img_tk = ImageTk.PhotoImage(self.logo_mp_img)

        # Crear y empacar el Label con la imagen
        self.logo_mp_img_label = tk.Label(self.frame_conjunto, image=self.logo_mp_img_tk)
        self.logo_mp_img_label.pack()

        
    def label_img(self):
        self.ventana_creacion_caja.geometry("800x550")
        path_script = os.path.dirname(os.path.abspath(__file__))
        path_img_dir = os.path.join(path_script, 'QRIMGDATA', 'Scan.png')
        self.frame_aviso_qr = ttk.Frame(self.frame_right,)
        self.frame_aviso_qr.pack(pady=20)

        self.label_aviso_QR_left = ttk.Label(self.frame_aviso_qr, text="Escanee el ", font=("Helvetica", 18))
        self.label_aviso_QR_left.pack(side="left")
        
        self.label_aviso_QR_right = ttk.Label(self.frame_aviso_qr, text="CÓDIGO QR", font=("Arial Black", 18), foreground="#13a5d5")
        self.label_aviso_QR_right.pack(side="right")
        
        self.qr_img = Image.open(path_img_dir)
        self.qr_img = self.qr_img.resize((300, 300), Image.LANCZOS)
        self.qr_img_tk = ImageTk.PhotoImage(self.qr_img)

        self.qr_img_label = tk.Label(self.frame_right, image=self.qr_img_tk)
        self.qr_img_label.pack()

        
    def on_a_and_7(self, event):  # Quitar 'self' como argumento
        if keyboard.is_pressed('a') and keyboard.is_pressed('7'):
            self.cancelar_orden()
            
            
    def on_a_and_8(self, event):  # Quitar 'self' como argumento
        if keyboard.is_pressed('a') and keyboard.is_pressed('8'):
            self.eleccion_message == False
            
            
    def cancelar_ordenELECC(self):
        if self.datos_para_orden[6] == 0:
            if self.datos_para_orden[1] == 1 or self.datos_para_orden[1] == 2:
                self.cancelar_orden()
        elif self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 1:
            self.cancelar_ordenPOINT()
            
    def center_window(self):
        self.ventana_creacion_caja.update_idletasks()
        width = self.ventana_creacion_caja.winfo_width()
        height = self.ventana_creacion_caja.winfo_height()
        screen_width = self.ventana_creacion_caja.winfo_screenwidth()
        screen_height = self.ventana_creacion_caja.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.ventana_creacion_caja.geometry(f"{width}x{height}+{x}+{y}")
        
    def on_map(self, event):
        # Centrar la ventana cuando se mapea por completo
        self.center_window()
        
    def eliminar(self):
        # Implementar la funcionalidad de eliminación si es necesario
        pass

    def detener(self):
        self.stop_thread = True

    def iniciar(self):
        self.stop_thread = False
        threading.Thread(target=self.actualizar_progreso).start()

    def actualizar_progreso(self):
        while self.my_progressbar['value'] < 100 and not self.stop_thread:
            self.my_progressbar['value'] += 1
            time.sleep(0.1)  # Ajusta el tiempo para controlar la velocidad de progreso

        if self.my_progressbar['value'] >= 100:
            messagebox.showinfo("Completado", "Proceso completado")


