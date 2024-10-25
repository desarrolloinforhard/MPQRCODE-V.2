import tkinter as tk
import ttkbootstrap as ttk
import window_position
import threading
import time
import keyboard
from ttkbootstrap.constants import *
from tkinter import messagebox
from image_path import *
from decimal import Decimal
from PIL import Image, ImageTk
from qrcode_mp import crear_qr_data
from log_errors import log_error

class CrearOrdenApp:
    def __init__(self, conexionAPI, conexionAPIPOINT, conexionDBA, conexionDBAServer, version):
        log_error(f"INICIO SISTEMA: ----------------------------------------------------------------------------------------", function_name='__init__')
        self.conexionAPI = conexionAPI
        self.conexionAPIPOINT = conexionAPIPOINT
        self.conexionDBA = conexionDBA
        self.conexionDBAServer = conexionDBAServer
        
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
        self.ventana_creacion_caja.geometry("400x550")
        self.ventana_creacion_caja.bind("<Map>", self.on_map)
        self.ventana_creacion_caja.resizable(False, False)
        self.icon()

        self.id_order_var = tk.StringVar()
        self.obtenerPago = None
        self.progresoNRO = 0
        self.status_cancel = 0
        self.stop_thread = False
        self.error = 0
        """self.message_status = None
        self.message_status_detail = None"""
        self.eleccion_message = None
        
        self.idPOINT = None
        self.idPAYMENT = None
        self.frame = tk.Frame(self.ventana_creacion_caja)
        self.frame.pack(side='left', padx=10)

        self.frame_conjunto = tk.Frame(self.frame, bg=self.ventana_creacion_caja['bg'])
        self.frame_conjunto.pack(padx=10)

        self.logo_mp()

        self.frame_left = tk.Frame(self.frame_conjunto)
        self.frame_left.pack(padx=20)

        self.frame_right = tk.Frame(self.ventana_creacion_caja)
        self.frame_right.pack(side='right', padx=20)
        
        self.my_progressbar = ttk.Progressbar(self.frame_left, orient="horizontal", length=350, mode='determinate', style='color.Horizontal.TProgressbar')
        self.my_progressbar.pack(pady=15)
        self.my_progressbar['value'] = 0
            
        self.framebottons = tk.Frame(self.frame_conjunto, height=100)
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
        try:
            self.functionMAIN()
        except Exception as e:
            log_error(f"Error al iniciar la función principal: {e}", function_name='functionMAIN')
            messagebox.showerror("Error", "Error al iniciar la aplicación.")
        
        self.ventana_creacion_caja.protocol("WM_DELETE_WINDOW", self.mostrar_error)
        self.ventana_creacion_caja.mainloop()
        log_error(f"FIN SISTEMA: ----------------------------------------------------------------------------------------", function_name='__init__')
        
    def mostrar_error(self):
        # Mostrar un mensaje de error
        messagebox.showerror("Error", "No se puede cerrar la ventana porque una orden está en proceso.")

    def icon(self):
        try:
            rutaicono = Icono_MercadoPago_Blue()
            self.ventana_creacion_caja.iconbitmap(rutaicono)
        except Exception as e:
            log_error(f"Error al establecer el icono: {e}", function_name='icon')
            messagebox.showerror("Error", "No se pudo establecer el icono de la ventana.")

    def update_window(self):
        try:
            self.ventana_creacion_caja.update_idletasks()
        except Exception as e:
            log_error(f"Error al actualizar la ventana: {e}", function_name='update_window')
            messagebox.showerror("Error", "No se pudo actualizar la ventana.")

    def clicker(self):
        try:
            self.my_progressbar.step()
            self.my_label.config(text=str((int(self.my_progressbar['value'] * 1))) + "%")
            self.update_window()
        except Exception as e:
            log_error(f"Error en el método clicker: {e}", function_name='clicker')
            messagebox.showerror("Error", "Ocurrió un error al actualizar el progreso.")

    def functionMAIN(self):
        try:
            if self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 1:
                self.crear_orden()
                threading.Thread(target=self.clickerFull).start()
            elif self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 2:
                threading.Thread(target=self.clickerFullReembolso).start()
            elif self.datos_para_orden[6] == 1 and self.datos_para_orden[1] == 1:
                threading.Thread(target=self.clickerFullPoint).start()
        except Exception as e:
            log_error(f"Error en functionMAIN: {e}", function_name='functionMAIN')
            messagebox.showerror("Error", "Ocurrió un error al procesar la función principal.")

            
    def clickerFull(self):
        try:
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
                            if self.conexionDBA.specify_search_condicion("SPDIR", "ID", "GRID", "teclado_km84", False) == "true":
                                keyboard.hook(self.on_a_and_7)
                                keyboard.hook(self.on_a_and_6)
                            else:
                                # Asociar la combinación de teclas con la función cancelar_orden
                                keyboard.add_hotkey('ctrl+alt+s', self.fun_ventana_buscar_pago_manual)
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
                                if self.realizar_comparacion():
                                    pass
                                else:
                                    self.my_label_aviso.config(text="Error al comparar registros")
                                    self.message_status_detail = [self.error, self.buscar_errores(self.error)]
                                    messagebox.showerror("Error al cerrar pago", self.buscar_errores(self.error))
                                    break
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
        except Exception as e:
            log_error(f"Error en clickerFull: {e}", function_name='clickerFull')
            messagebox.showerror("Error", "Ocurrió un error en el proceso de pago.")
            
        self.finalizarPago(self.obtenerPago)

        
    def clickerFullReembolso(self):
        try:
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
        except Exception as e:
            log_error(str(e), 'clickerFullReembolso')
            messagebox.showerror('Error', 'Ocurrió un error en el proceso de reembolso.')

    def clickerFullPoint(self):
        try:
            pos_id = self.conexionDBAServer.specify_search_condicion("MPQRCODE_CAJAS", 'id', 'external_id', self.datos_caja[3], False)
            store_id = self.conexionDBAServer.specify_search_condicion("MPQRCODE_CAJAS", 'store_id', 'external_id', self.datos_caja[3], False)
            self.idPOINT = self.conexionAPIPOINT.obtenerPointPOS(store_id, pos_id)  # 'INGENICO_MOVE2500__ING-ARG-6401494660'
            if not self.idPOINT == "No se encontro el dispositivo":
                clickerProgress = int(self.my_progressbar['value']*1)
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
                                    keyboard.hook(self.on_a_and_7)
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
        except Exception as e:
            log_error(str(e), 'clickerFullPoint')
            messagebox.showerror('Error', 'Ocurrió un error en el proceso de creación de punto de venta.')
            
    def crear_orden(self):
        try:
            self.qr_data = self.conexionAPI.crearOrdenDinamico(
                self.datos_caja[3], 
                self.datos_para_orden[0], 
                self.datos_caja[1], 
                float(self.datos_para_orden[2].quantize(Decimal('1.00'))), 
                self.datos_caja[4],
                #self.conexionDBAServer.specify_search_condicion("SPDIR", "ID", "GRID", "url_api_AWS", False) #ESTE CODIGO ES PARA LA NUEVA FUNCION CON AWS
            )
        except Exception as e:
            log_error(str(e), 'crear_orden')
            messagebox.showerror('Error', 'Ocurrió un error al crear la orden.')

    def crear_orden_reemboslso(self, monto_devolver):
        try:
            respuesta = self.conexionAPI.crear_orden_reembolso(self.id_order_var.get(), monto_devolver)
        except Exception as e:
            log_error(str(e), 'crear_orden_reemboslso')
            messagebox.showerror('Error', 'Ocurrió un error al crear el reembolso.')

    def obteneridOrder(self, external_reference, obtenido_ID):
        try:
            pos_id = self.conexionDBAServer.specify_search_condicion(
                "MPQRCODE_CAJAS", 'id', 'external_id', self.datos_caja[3], False
            )

            if self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 1:
                self.orden_cronometro(280, self.cancelar_orden)

                if obtenido_ID is None:
                    self.obtener_ID = None
                    while self.obtener_ID is None and self.status_cancel == 0:
                        self.obtener_ID = self.conexionDBAServer.specify_search_condicionID(
                            "MPQRCODE_OBTENERPAGOServer", "data", "external_reference", 
                            external_reference, 'pos_id', pos_id, False
                        )
                        if self.obtener_ID is None:
                            print(self.obtener_ID)
                            time.sleep(1)  # Puedes ajustar el tiempo de espera según sea necesario
                        else:
                            self.id_order_var.set(self.obtener_ID)
                else:
                    self.obtener_ID = self.conexionDBAServer.specify_search_condicionID(
                        "MPQRCODE_OBTENERPAGOServer", "data", "external_reference", 
                        external_reference, 'pos_id', pos_id, False
                    )
                    while self.obtener_ID == str(obtenido_ID) and self.status_cancel == 0:
                        time.sleep(1)
                        self.obtener_ID = self.conexionDBAServer.specify_search_condicionID(
                            "MPQRCODE_OBTENERPAGOServer", "data", "external_reference", 
                            external_reference, 'pos_id', pos_id, False
                        )

                        if not self.obtener_ID == obtenido_ID:
                            self.id_order_var.set(self.obtener_ID)

                self.detener_temporizador()
                self.my_label_time.config(text=f"")

            elif self.datos_para_orden[6] == 1 and self.datos_para_orden[1] == 1:
                self.orden_cronometro(280, self.cancelar_orden)
                if obtenido_ID is None:
                    statePOINT = self.conexionAPIPOINT.buscarIntencionPAGOPoint(self.idPAYMENT).json()

                    while statePOINT['state'] in ['OPEN', 'ON_TERMINAL', 'PROCESSING']:
                        time.sleep(5)  # Cada 5 segundos pregunta a la API el estado del Point
                        if 'state' in statePOINT:
                            statePOINT = self.conexionAPIPOINT.buscarIntencionPAGOPoint(self.idPAYMENT).json()

                            if statePOINT['state'] == 'FINISHED':
                                self.obtener_ID = None
                                while self.obtener_ID is None and self.status_cancel == 0:
                                    self.obtener_ID = self.conexionDBAServer.specify_search_condicionID(
                                        "MPQRCODE_OBTENERPAGOPOINTServer", "data", "external_reference", 
                                        external_reference, 'pos_id', pos_id, False
                                    )
                                    if self.obtener_ID is None:
                                        time.sleep(1)  # Puedes ajustar el tiempo de espera según sea necesario
                                    else:
                                        self.id_order_var.set(self.obtener_ID)
                            elif statePOINT['state'] in ['CANCELED', 'ERROR']:
                                messagebox.showerror('ERROR', statePOINT['state'])
                                self.id_order_var.set(None)

            elif self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 2:
                if obtenido_ID is None:
                    self.obtener_ID = self.conexionDBAServer.specify_search_condicion(
                        "MPQRCODE_OBTENERPAGOServer", "data", "external_reference", 
                        external_reference, False
                    )
                    self.id_order_var.set(self.obtener_ID)
        except Exception as e:
            log_error(str(e), 'obteneridOrder')
            messagebox.showerror('Error', 'Ocurrió un error al obtener el ID de la orden.')
            
    def obtnerPago(self, step_two, insertar, tipo_pago):
        try:
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
        except Exception as e:
            log_error(e)
            messagebox.showerror("Error", "Ocurrió un error al obtener el pago.")
            return None  # Devuelve None o algún otro valor que indique que hubo un error

    def finalizarPago(self, respuesta):
        try:
            self.ventana_creacion_caja.after(0, self.mostrar_resultado_pago, respuesta)
        except Exception as e:
            log_error(e)
            messagebox.showerror("Error", "Ocurrió un error al finalizar el pago.")
            
            
    def realizar_comparacion(self):
        try:
            if float(self.datos_para_orden[2].quantize(Decimal('1.00'))) == float(self.conexionDBA.specify_search_condicion("MPQRCODE_OBTENERPAGO", "transaction_details_total_paid_amount", "external_reference", f"{self.datos_para_orden[0]}", False)):
                print(float(self.datos_para_orden[2].quantize(Decimal('1.00'))) == float(self.conexionDBA.specify_search_condicion("MPQRCODE_OBTENERPAGO", "transaction_details_total_paid_amount", "external_reference", f"{self.datos_para_orden[0]}", False)))
                return True
            else:
                self.error = 10
                return False
        except Exception as e:
            log_error(e, "realizar_comparacion")
            messagebox.showerror("Error", e)
        

    def mostrar_resultado_pago(self, respuesta):
        try:
            response = respuesta
            if response == True and self.error == 0:
                if self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 1:
                    self.my_label_aviso.configure(text="Pago Recibido")
                    messagebox.showinfo("Éxito", "Pago Recibido")
                    
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

            # Cerrar la ventana después de 1000 milisegundos (1 segundo)
            self.ventana_creacion_caja.after(1000, self.cerrar_ventana)

        except Exception as e:
            log_error(e)  # Registrar el error en el archivo de logs
            messagebox.showerror("Error", "Ocurrió un error al mostrar el resultado del pago.")

            
    def fun_ventana_buscar_pago_manual(self): 
        try:
            self.ventana_buscar_pago_manual = ttk.Toplevel(self.ventana_creacion_caja)
            self.ventana_buscar_pago_manual.title("Buscar pago manual")
            self.ventana_buscar_pago_manual.iconbitmap(Icono_MercadoPago_Blue())
            self.ventana_buscar_pago_manual.grab_set()

            self.frame_buscar_pago_manual = ttk.Frame(self.ventana_buscar_pago_manual)
            self.frame_buscar_pago_manual.pack(pady=50, padx=100)

            self.label_info_buscar_pago = ttk.Label(self.frame_buscar_pago_manual, text="Ingrese el ID de Operación a verificar:")
            self.placeholder_text = "ID de Operación"
            self.entry_info_buscar_pago = ttk.Entry(self.frame_buscar_pago_manual, width=30, validate="key")
            self.button_info_buscar_pago = ttk.Button(self.frame_buscar_pago_manual, text="Buscar", command=self.buscar_id_pago_manual)

            self.label_info_buscar_pago.pack(pady=5)
            self.entry_info_buscar_pago.pack(pady=5)
            self.button_info_buscar_pago.pack(pady=5)

            # Registrar el método de validación
            vcmd = self.entry_info_buscar_pago.register(self.validate_number)
            self.entry_info_buscar_pago.config(validatecommand=(vcmd, '%P'))

            self.entry_info_buscar_pago.insert(0, self.placeholder_text)
            self.entry_info_buscar_pago.config(foreground='gray')

            self.entry_info_buscar_pago.bind("<FocusIn>", self.entry_info_buscar_pago_on_focus_in)
            self.entry_info_buscar_pago.bind("<FocusOut>", self.entry_info_buscar_pago_on_focus_out)
            self.entry_info_buscar_pago.focus_set()
            # Inicializa una lista para guardar la secuencia de teclas
            self.tecla_secuencia = []

            # Asocia el evento de presionar tecla
            self.entry_info_buscar_pago.bind("<KeyPress>", self.detectar_secuencia)

            self.ventana_buscar_pago_manual.bind("<Button-1>", self.handle_click_outside)
            keyboard.hook(self.on_4_and_a)

            window_position.center_window(self.ventana_buscar_pago_manual, 400, 225)

        except Exception as e:
            log_error(str(e), "fun_ventana_buscar_pago_manual")
            messagebox.showerror("Error", "Ha ocurrido un error en la ventana de búsqueda de pago manual.")
        
        
    def entry_info_buscar_pago_on_focus_in(self, event):
        try:
            if self.entry_info_buscar_pago.get() == self.placeholder_text:
                self.entry_info_buscar_pago.delete(0, "end")
                self.entry_info_buscar_pago.config(foreground='black')
        except Exception as e:
            log_error(str(e), "entry_info_buscar_pago_on_focus_in")
            messagebox.showerror("Error", "Error al enfocar la entrada de ID de operación.")


    def entry_info_buscar_pago_on_focus_out(self, event):
        try:
            if self.entry_info_buscar_pago.get() == "":
                self.entry_info_buscar_pago.insert(0, self.placeholder_text)
                self.entry_info_buscar_pago.config(foreground='gray')
        except Exception as e:
            log_error(str(e), "entry_info_buscar_pago_on_focus_out")
            messagebox.showerror("Error", "Error al desenfocar la entrada de ID de operación.")

            
    def validate_number(self, entry_value):
        try:
            # Validar si la entrada es un número
            if entry_value == "" or entry_value.isdigit() or entry_value == self.placeholder_text:
                return True
            else:
                # Mostrar el mensaje de error
                messagebox.showerror("Error", "Solo puedes ingresar valores numéricos.")
                return False
        except Exception as e:
            log_error(str(e), "validate_number")
            messagebox.showerror("Error", "Error al validar el número.")
            return False

            
    def handle_click_outside(self, event):
        try:
            # Verificar si el clic fue fuera del Entry
            widget_under_cursor = self.ventana_buscar_pago_manual.winfo_containing(event.x_root, event.y_root)
            if widget_under_cursor != self.entry_info_buscar_pago:
                # Llamar al método de pérdida de foco manualmente
                self.entry_info_buscar_pago.focus_set()
                self.ventana_buscar_pago_manual.focus_set()  # O enfocar el contenedor principal para garantizar la pérdida de foco
        except Exception as e:
            log_error(str(e), "handle_click_outside")
            messagebox.showerror("Error", "Error al procesar el clic fuera del campo de entrada.")

            
    def detectar_secuencia(self, event):
        try:
            # Agregar la tecla presionada a la secuencia
            if event.keysym.isdigit() or event.keysym == "Return" or event.keysym == "a":
                self.tecla_secuencia.append(event.keysym)

            # Diccionario con las combinaciones de teclas
            combinaciones = {
                ('4', '6', 'Return'): '0',
                ('4', '7', 'Return'): '00',
                ('4', '8', 'Return'): '.',
                ('5', '6', 'Return'): '1',
                ('5', '7', 'Return'): '2',
                ('5', '8', 'Return'): '3',
                ('6', '6', 'Return'): '4',
                ('6', '7', 'Return'): '5',
                ('6', '8', 'Return'): '6',
                ('7', '6', 'Return'): '7',
                ('7', '7', 'Return'): '8',
                ('7', '8', 'Return'): '9'
            }

            # Verificar la longitud de la secuencia y procesar si es necesario
            if len(self.tecla_secuencia) >= 3:
                # Solo consideramos las últimas 3 teclas
                secuencia_tupla = tuple(self.tecla_secuencia[-3:])
                if secuencia_tupla == ('8', '6', 'Return'):
                    # Limpiar el Entry si la secuencia es '8', '6', 'Return'
                    self.entry_info_buscar_pago.delete(0, tk.END)
                    # Limpiar la secuencia después de la inserción
                    self.tecla_secuencia = []
                elif secuencia_tupla in combinaciones:
                    valor_reemplazo = combinaciones[secuencia_tupla]
                    
                    # Obtener el contenido actual del Entry
                    current_text = self.entry_info_buscar_pago.get()
                    
                    # Para reemplazos específicos, definimos patrones
                    patrones_reemplazo = {
                        ('4', '6', 'Return'): '46',
                        ('4', '7', 'Return'): '47',
                        ('4', '8', 'Return'): '48',
                        ('5', '6', 'Return'): '56',
                        ('5', '7', 'Return'): '57',
                        ('5', '8', 'Return'): '58',
                        ('6', '6', 'Return'): '66',
                        ('6', '7', 'Return'): '67',
                        ('6', '8', 'Return'): '68',
                        ('7', '6', 'Return'): '76',
                        ('7', '7', 'Return'): '77',
                        ('7', '8', 'Return'): '78'
                    }
                    
                    # Reemplazar la secuencia detectada con el valor correspondiente
                    patron = patrones_reemplazo.get(secuencia_tupla, '')
                    if patron:
                        # Eliminar el patrón en el texto y añadir el nuevo valor
                        if patron in current_text:
                            start_idx = current_text.rfind(patron)
                            new_text = current_text[:start_idx] + valor_reemplazo + current_text[start_idx + len(patron):]
                        else:
                            # Si el patrón no está, añadir al final
                            new_text = current_text + valor_reemplazo
                    else:
                        # Para otras secuencias, simplemente añadir al final
                        new_text = current_text + valor_reemplazo
                    
                    # Establecer el nuevo texto en el Entry
                    self.entry_info_buscar_pago.delete(0, tk.END)
                    self.entry_info_buscar_pago.insert(tk.END, new_text)
                    
                    # Limpiar la secuencia después de la inserción
                    self.tecla_secuencia = []
                else:
                    # Mantener solo las últimas 3 teclas si la secuencia no coincide
                    self.tecla_secuencia = self.tecla_secuencia[-3:]
        except Exception as e:
            log_error(str(e), "detectar_secuencia")
            messagebox.showerror("Error", "Error al procesar la secuencia de teclas.")
            
    def buscar_id_pago_manual(self):
        try:
            respuesta = self.conexionAPI.obtenerPago_manual(self.entry_info_buscar_pago.get(), self.datos_para_orden[0], self.datos_caja[3])

            if respuesta == True:
                messagebox.showinfo("Nro Operacion exitosa", "Se ha encontrado el número de operación")
                self.detener_temporizador()
                self.my_label_time.config(text=f"")
                self.obtener_ID = self.entry_info_buscar_pago.get()
                self.id_order_var.set(self.entry_info_buscar_pago.get())

            elif respuesta == False:
                messagebox.showerror("Error", "No se ha encontrado el número de operación")
            else:
                messagebox.showerror("Error", respuesta)

            self.ventana_buscar_pago_manual.destroy()

        except Exception as e:
            log_error(str(e), "buscar_id_pago_manual")
            messagebox.showerror("Error", "Ha ocurrido un error al buscar el ID de pago manual.")

            
    def cerrar_ventana(self):
        try:
            self.ventana_creacion_caja.destroy()
        except Exception as e:
            log_error(str(e), "cerrar_ventana")
            messagebox.showerror("Error", "Ha ocurrido un error al cerrar la ventana.")

    def mostrar_cancelacion_orden(self):
        try:
            messagebox.showinfo("Cancelar Orden", "La Orden ha sido Cancelada")
        except Exception as e:
            log_error(str(e), "mostrar_cancelacion_orden")
            messagebox.showerror("Error", "Ha ocurrido un error al mostrar la cancelación de la orden.")


    def mostrar_error_pago(self):
        try:
            messagebox.showerror("Error", "No se recibió el pago")
            datos = {
                'status': 0,
                'response': self.message_status_detail[0],
                'description': self.message_status_detail[1]
            }
            self.conexionDBA.actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMAS", datos, "nro_factura", f"'{self.datos_para_orden[0]}'")
        except Exception as e:
            log_error(str(e), "mostrar_error_pago")
            messagebox.showerror("Error", "Ha ocurrido un error al procesar el error de pago.")


    def mostrar_exito_reembolso(self):
        try:
            messagebox.showinfo("Exito", "Se ha devuelto el Dinero")
        except Exception as e:
            log_error(str(e), "mostrar_exito_reembolso")
            messagebox.showerror("Error", "Ha ocurrido un error al mostrar el éxito del reembolso.")


            
    def cancelar_orden(self, event=None):
        try:
            respuesta = self.conexionAPI.cancelarOrden(self.datos_caja[3])
            datos = {
                'response': 10,
                'description': 'orden-cancelada'
            }
            self.conexionDBA.actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMAS", datos, "nro_factura", f"'{self.datos_para_orden[0]}'")
            self.status_cancel = respuesta
        except Exception as e:
            log_error(str(e), "cancelar_orden")
            messagebox.showerror("Error", "Ha ocurrido un error al cancelar la orden.")

        
    def cancelar_ordenPOINT(self, event=None):
        try:
            respuesta = self.conexionAPI.cancelarIntencionPAGOPoint(self.idPOINT, self.idPAYMENT)
            datos = {
                'response': 10,
                'description': 'orden-cancelada'
            }
            self.conexionDBA.actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMAS", datos, "nro_factura", f"'{self.datos_para_orden[0]}'")
            self.status_cancel = respuesta
        except Exception as e:
            log_error(str(e), "cancelar_ordenPOINT")
            messagebox.showerror("Error", "Ha ocurrido un error al cancelar la orden en POINT.")

        
    def simular_clic(self, event):
        try:
            self.my_buttonDLT.event_generate("<Button-1>")
        except Exception as e:
            log_error(str(e), "simular_clic")
            messagebox.showerror("Error", "Ha ocurrido un error al simular el clic.")

        
    def terminar_orden(self):
        try:
            respuesta = self.conexionAPI.cancelarOrden(self.datos_caja[3])
            self.status_cancel = respuesta
        except Exception as e:
            log_error(str(e), "terminar_orden")
            messagebox.showerror("Error", "Ha ocurrido un error al terminar la orden.")

        
    def buscar_errorESP(self, error):
        try:
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

        except Exception as e:
            log_error(str(e), "buscar_errorESP")
            messagebox.showerror("Error", "Ha ocurrido un error al buscar la descripción del error.")
            return []
        
        
    def buscar_errores(self, nro_error):
        try:
            errores = {
                10: "El monto ingresado no es el mismo recibido en MercadoPago"
            }
            
            return errores[nro_error]
        except Exception as e:
            log_error(str(e), "buscar_errores")


    def orden_cronometro(self, tiempo, funcion):
        try:
            tiempo_espera = 0
            self.actualizar_label(tiempo_espera, tiempo)
            self.temporizador(self.ventana_creacion_caja, tiempo, tiempo_espera, funcion)
        except Exception as e:
            log_error(str(e), "orden_cronometro")
            messagebox.showerror("Error", "Ha ocurrido un error en el cronómetro de la orden.")


    def actualizar_label(self, tiempo_espera, tiempo):
        try:
            self.my_label_time.config(text=f"Tiempo de respuesta: {tiempo_espera} de {tiempo}")
            self.update_window()
        except Exception as e:
            log_error(str(e), "actualizar_label")
            messagebox.showerror("Error", "Ha ocurrido un error al actualizar el label de tiempo.")


    def temporizador(self, app, tiempo, tiempo_espera, funcion):
        try:
            if tiempo_espera < tiempo:
                tiempo_espera += 1
                self.timer_id = app.after(1000, self.temporizador, app, tiempo, tiempo_espera, funcion)
                self.actualizar_label(tiempo_espera, tiempo)
            else:
                app.after(0, funcion)
        except Exception as e:
            log_error(str(e), "temporizador")
            messagebox.showerror("Error", "Ha ocurrido un error en el temporizador.")

            
    def detener_temporizador(self):
        try:
            if self.timer_id is not None:
                self.ventana_creacion_caja.after_cancel(self.timer_id)
                self.timer_id = None
        except Exception as e:
            log_error(str(e), "detener_temporizador")
            messagebox.showerror("Error", "Ha ocurrido un error al detener el temporizador.")

            
    def logo_mp(self):
        try:
            path_img_dir = LOGO_MP()

            # Cargar y redimensionar la imagen
            self.logo_mp_img = Image.open(path_img_dir)
            self.logo_mp_img = self.logo_mp_img.resize((240, 190), Image.LANCZOS)
            self.logo_mp_img_tk = ImageTk.PhotoImage(self.logo_mp_img)

            # Crear y empacar el Label con la imagen
            self.logo_mp_img_label = tk.Label(self.frame_conjunto, image=self.logo_mp_img_tk)
            self.logo_mp_img_label.pack()

        except Exception as e:
            log_error(str(e), "logo_mp")
            messagebox.showerror("Error", "Ha ocurrido un error al cargar el logo de MercadoPago.")

        
    def label_img(self):
        try:
            self.ventana_creacion_caja.geometry("800x550")
            path_script = os.path.dirname(os.path.abspath(__file__))
            path_img_dir = os.path.join(path_script, 'QRIMGDATA', 'Scan.png')
            self.frame_aviso_qr = ttk.Frame(self.frame_right)
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

        except Exception as e:
            log_error(str(e), "label_img")
            messagebox.showerror("Error", "Ha ocurrido un error al cargar la imagen QR.")


        
    def on_a_and_6(self, event):
        try:
            if keyboard.is_pressed('a') and keyboard.is_pressed('6'):
                self.fun_ventana_buscar_pago_manual()
        except Exception as e:
            log_error(str(e), "on_a_and_6")
            messagebox.showerror("Error", "Ha ocurrido un error al detectar las teclas 'a' y '6'.")

    
    def on_a_and_7(self, event):
        try:
            if keyboard.is_pressed('a') and keyboard.is_pressed('7'):
                self.cancelar_orden()
        except Exception as e:
            log_error(str(e), "on_a_and_7")
            messagebox.showerror("Error", "Ha ocurrido un error al detectar las teclas 'a' y '7'.")

    def on_a_and_8(self, event):
        try:
            if keyboard.is_pressed('a') and keyboard.is_pressed('8'):
                self.eleccion_message = False
        except Exception as e:
            log_error(str(e), "on_a_and_8")
            messagebox.showerror("Error", "Ha ocurrido un error al detectar las teclas 'a' y '8'.")

            
    def on_4_and_a(self, event):
        try:
            if keyboard.is_pressed('4') and keyboard.is_pressed('a'):
                self.buscar_id_pago_manual()
        except Exception as e:
            log_error(str(e), "on_4_and_a")
            messagebox.showerror("Error", "Ha ocurrido un error al detectar las teclas '4' y 'a'.")

            
                
    def cancelar_ordenELECC(self):
        try:
            if self.datos_para_orden[6] == 0:
                if self.datos_para_orden[1] == 1 or self.datos_para_orden[1] == 2:
                    self.cancelar_orden()
            elif self.datos_para_orden[6] == 0 and self.datos_para_orden[1] == 1:
                self.cancelar_ordenPOINT()
        except Exception as e:
            log_error(str(e), "cancelar_ordenELECC")
            messagebox.showerror("Error", "Ha ocurrido un error al intentar cancelar la orden.")

                
    def center_window(self):
        try:
            self.ventana_creacion_caja.update_idletasks()
            width = self.ventana_creacion_caja.winfo_width()
            height = self.ventana_creacion_caja.winfo_height()
            screen_width = self.ventana_creacion_caja.winfo_screenwidth()
            screen_height = self.ventana_creacion_caja.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.ventana_creacion_caja.geometry(f"{width}x{height}+{x}+{y}")
        except Exception as e:
            log_error(str(e), "center_window")
            messagebox.showerror("Error", "Ha ocurrido un error al centrar la ventana.")

        
    def on_map(self, event):
        try:
            # Centrar la ventana cuando se mapea por completo
            self.center_window()
        except Exception as e:
            log_error(str(e), "on_map")
            messagebox.showerror("Error", "Ha ocurrido un error al mapear la ventana.")

        
    def eliminar(self):
        try:
            # Implementar la funcionalidad de eliminación si es necesario
            pass
        except Exception as e:
            log_error(str(e), "eliminar")
            messagebox.showerror("Error", "Ha ocurrido un error en la función de eliminación.")


    def detener(self):
        try:
            self.stop_thread = True
        except Exception as e:
            log_error(str(e), "detener")
            messagebox.showerror("Error", "Ha ocurrido un error al detener el proceso.")


    def iniciar(self):
        try:
            self.stop_thread = False
            threading.Thread(target=self.actualizar_progreso).start()
        except Exception as e:
            log_error(str(e), "iniciar")
            messagebox.showerror("Error", "Ha ocurrido un error al iniciar el proceso.")


    def actualizar_progreso(self):
        try:
            while self.my_progressbar['value'] < 100 and not self.stop_thread:
                self.my_progressbar['value'] += 1
                time.sleep(0.1)  # Ajusta el tiempo para controlar la velocidad de progreso

            if self.my_progressbar['value'] >= 100:
                messagebox.showinfo("Completado", "Proceso completado")
        except Exception as e:
            log_error(str(e), "actualizar_progreso")
            messagebox.showerror("Error", "Ha ocurrido un error al actualizar el progreso.")