from pprint import pprint
import tkinter as tk
import time
import threading
import traceback
import keyboard
import pytz
import ttkbootstrap as ttk
from datetime import datetime
from tkinter import messagebox
from GUI.BuscarOrdenPago import Ventana_BuscarPagoManual
from GUI.Cronometro import Cronometro
from GUI.BarraProgreso import BarraProgreso
from GUI.MessageBox import mostrar_error_y_cerrar
from Func.qrcode_mpV2 import crear_qr_data
from Func.log_errorsV2 import log_error
from Func.window_position import center_window

class CrearOrdenPago(BarraProgreso):
    def __init__(self, frame, DICT_WIDGETS, DICT_DATOS_ORDEN, DICT_CONEXION):
        try:
        
            # Inicializar correctamente la clase base ttk.Progressbar
            super().__init__(frame)
            
            #---------------------------------------- VARIABLES INICIADORAS ----------------------------------------
            self.crearorden = True
            self.orden_creada = False
            self.id_pago = None
            self.datos_error = None
            self.detalle_error = None
            self.ultima_actualizacion = None
            self.datos_pagos = None
            self.NRO_ERROR = None
            self.PAGO_MANUAL = False
            self.reintentarpago = None
            self.ventana_buscarpagomanual_abierta = False
            
            
            self.card_first_six_digits = None
            self.card_last_four_digits = None
            self.payment_method_id = None
            self.payment_method_name = None
            self.payment_type_id = None

            
            self.cierre_supervisor = 0
            self.cierre_supervisor_autorizante = None
            self.cierre_supervisor_detalle = None
            
            #------------------------------------------- DICCIONARIOS CON DATOS -------------------------------------------
            self.DICT_WIDGETS = DICT_WIDGETS
            self.DICT_CONEXION = DICT_CONEXION
            self.DICT_DATOS_ORDEN = DICT_DATOS_ORDEN
            
            self.obtener_diccionario_pbs() #AGREGADO 23/04/2025
            
            self.condicion_teclado = str(self.DICT_CONEXION["conexionDBA"].specify_search_condicion("SPDIR", "ID", "GRID", "teclado_km84", False)).strip().lower() == "true"
            if self.condicion_teclado:
                self.teclado_hasar = DICT_CONEXION.get("teclado")
                self.teclado_hasar.registrar_combinacion_personalizada("98")
                self.teclado_hasar.asignar_funcion_personalizada("98", self.llamado_taskkill)
                self.teclado_hasar.registrar_combinacion_personalizada("49")
                self.teclado_hasar.asignar_funcion_personalizada("49", self.activar_modo_supervisor)
            
            self.datos_obtener_pago = {
                'NomCaja': self.DICT_DATOS_ORDEN["NomCaja"],
                'NumCajero': self.DICT_DATOS_ORDEN["NumCajero"],
                'NombreCajero': self.DICT_DATOS_ORDEN["NombreCajero"],
                'cierre_supervisor': self.cierre_supervisor,
                'cierre_supervisor_autorizante': self.cierre_supervisor_autorizante,
                'cierre_supervisor_detalle': self.cierre_supervisor_detalle
            }
            
            pprint(self.DICT_DATOS_ORDEN)
            pprint(self.datos_obtener_pago)
            
            self.DICT_PROGRESO = {
                "widgets": DICT_WIDGETS,
                "text_label_aviso": "Creando Orden",
                "carga": 25,
                "command": self.crear_orden
            }
            
            self.cronometro = Cronometro(self.DICT_WIDGETS, int(self.DICT_CONEXION["conexionDBA"].specify_search_condicion("SPDIR", "ID", "GRID", "mp_tiempo", False)), self.cancelar_orden_pasado_segundos)
            #threading.Thread(target=self.iniciar_orden).start()
            self.progreso(**self.DICT_PROGRESO)
        except Exception as e:
            log_error(e, "CrearOrdenPago")
        
    def crear_orden(self):
        try:
            reintentos = 3
            intento = 0
            error_envio = None

            while intento < reintentos:
                try:
                    if self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion("SPDIR", "ID", "GRID", "MP_NUEVA_VERSION", False).lower() == "true":
                        self.qr_data = self.DICT_CONEXION["conexionAPI"].crearOrdenDinamicoV2(
                            self.DICT_DATOS_ORDEN["external_id_pos"],
                            self.DICT_DATOS_ORDEN["nro_factura"],
                            self.DICT_DATOS_ORDEN["sucNAME"],
                            self.DICT_DATOS_ORDEN["monto_pagar"],
                            self.DICT_DATOS_ORDEN["url_API"]
                        )
                    else:
                        self.qr_data = self.DICT_CONEXION["conexionAPI"].crearOrdenDinamico(
                            self.DICT_DATOS_ORDEN["external_id_pos"],
                            self.DICT_DATOS_ORDEN["nro_factura"],
                            self.DICT_DATOS_ORDEN["sucNAME"],
                            self.DICT_DATOS_ORDEN["monto_pagar"],
                            self.DICT_DATOS_ORDEN["url_API"]
                        )
                        
                    print(self.qr_data.json())

                    if self.qr_data is not None and self.qr_data.status_code == 200:
                        log_error("Orden enviada exitosamente en el intento #" + str(intento + 1), "crear_orden")
                        break  # Salir del bucle si se envió correctamente
                    else:
                        error_envio = self.qr_data.json()['message'] if self.qr_data else "No conexión"
                        intento += 1
                        log_error(f"Error al enviar orden. Intento #{intento}: {error_envio}", "crear_orden")
                        time.sleep(1.5)

                except Exception as inner_e:
                    error_envio = str(inner_e)
                    intento += 1
                    log_error(f"Excepción al enviar orden. Intento #{intento}: {error_envio}", "crear_orden")
                    time.sleep(1.5)

            if self.qr_data is not None and self.qr_data.status_code == 200:
                data_qr = self.qr_data.json()['qr_data']
                crear_qr_data(data_qr)
                self.DICT_PROGRESO["text_label_aviso"] = "Orden Creada. Escanee el QR"
                self.DICT_PROGRESO["carga"] = 40
                self.DICT_PROGRESO["command"] = self.func_orden_creada
                self.progreso(**self.DICT_PROGRESO)
            else:
                mostrar_error_y_cerrar(self.DICT_WIDGETS, f"Fallo al crear orden después de {reintentos} intentos.\n{error_envio}", teclado_hasar=self.teclado_hasar)
                self.aviso_cancelar_orden()
        except Exception as e:
            log_error(str(e), 'crear_orden')
            mostrar_error_y_cerrar(self.DICT_WIDGETS, 'Ocurrió un error al crear la orden.', teclado_hasar=self.teclado_hasar)
            self.aviso_cancelar_orden()

        
    def func_orden_creada(self):
        try:
            if self.reintentarpago is None:
                self.DICT_PROGRESO["carga"] = 50
                self.DICT_PROGRESO["command"] = self.DICT_WIDGETS["mostrar_qr"]
                log_error("QR mostrado correctamente al usuario.", "func_orden_creada")
                self.progreso(**self.DICT_PROGRESO)
            else:
                self.DICT_WIDGETS["ventana_tamano_800_550"]()
            threading.Thread(target=self.buscar_pago_en_dba, daemon=True).start()
            self.nro_punto = 1
            self.cronometro.start_cronometro()
            #self.DICT_WIDGETS["label_cronometro"].pack(pady=10)
            self.DICT_WIDGETS["boton_cancelar"].config(command=self.aviso_cancelar_orden, state=tk.NORMAL)
            self.id_pago = None
            if self.condicion_teclado:
                self.teclado_hasar.registrar_combinacion_personalizada("a6")
                self.teclado_hasar.asignar_funcion_personalizada("a6", self.buscar_pago_manual)
                self.teclado_hasar.registrar_combinacion_personalizada("a7")
                self.teclado_hasar.asignar_funcion_personalizada("a7", self.cancelar_orden)
                self.teclado_hasar.registrar_combinacion_personalizada("ab")
                self.teclado_hasar.asignar_funcion_personalizada("ab", self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["cerrar_ventana_buscar_pago_manual"])
            else:
                keyboard.add_hotkey('ctrl+alt+s', self.buscar_pago_manual)
            while self.id_pago is None and not self.DICT_PROGRESO["text_label_aviso"] == "Cancelando Orden":
                if self.nro_punto == 1:
                    self.nro_punto += 1
                    self.DICT_WIDGETS["my_label_aviso"].config(text="Esperando Pago.")
                    print(f"Esperando Pago. {self.DICT_DATOS_ORDEN["nro_factura"]}")
                elif self.nro_punto == 2:
                    self.nro_punto += 1
                    self.DICT_WIDGETS["my_label_aviso"].config(text="Esperando Pago..")
                    print(f"Esperando Pago.. {self.DICT_DATOS_ORDEN["nro_factura"]}")
                elif self.nro_punto == 3:
                    self.nro_punto = 1
                    self.DICT_WIDGETS["my_label_aviso"].config(text="Esperando Pago...")
                    print(f"Esperando Pago... {self.DICT_DATOS_ORDEN["nro_factura"]}")
                time.sleep(1)
            if not self.DICT_PROGRESO["text_label_aviso"] == "Cancelando Orden":
                self.cerrar_cronometro()
                self.DICT_WIDGETS["ventana_tamano_400_550"]()
                
                self.DICT_PROGRESO["text_label_aviso"] = "Notificación Recibida"
                self.DICT_PROGRESO["carga"] = 51
                self.DICT_PROGRESO["command"] = None
                self.progreso(**self.DICT_PROGRESO)
                time.sleep(1)
                self.DICT_WIDGETS["label_cronometro"].pack_forget()
                if not self.id_pago is None:
                    self.DICT_WIDGETS["id_pago"].config(text=f"Nro. OP: {self.id_pago}")
                    self.DICT_WIDGETS["id_pago"].pack(pady=10)
                self.DICT_PROGRESO["text_label_aviso"] = f"Nro. OP: {self.id_pago}"
                self.DICT_PROGRESO["carga"] = 65
                self.DICT_PROGRESO["command"] = None
                self.progreso(**self.DICT_PROGRESO)
                self.DICT_PROGRESO["carga"] = 75
                self.DICT_PROGRESO["text_label_aviso"] = "Realizando Comparación"
                self.DICT_PROGRESO["command"] = None
                self.esperando_comparacion = False
                print("antes realizar_comparacion")
                if not self.PAGO_MANUAL:
                    self.buscar_pago_en_MP()
                    pprint(self.datos_pagos)
                threading.Thread(target=self.realizar_comparacion, daemon=True).start()
                print("despues realizar_comparacion")
                self.progreso(**self.DICT_PROGRESO)
                
                
                while not self.esperando_comparacion:
                    time.sleep(1)
                    print("Esperando Comparación")
                    pass
                print(self.DICT_PROGRESO["text_label_aviso"])
                if self.reintentarpago is None:
                    self.DICT_PROGRESO["text_label_aviso"] = "Guardando datos..."
                    self.DICT_PROGRESO["carga"] = 80
                    self.DICT_PROGRESO["command"] = self.agrega_datos_dba_caja
                    self.progreso(**self.DICT_PROGRESO)
                elif self.reintentarpago is True:
                    self.DICT_PROGRESO["carga"] = 50
                    self.DICT_PROGRESO["command"] = self.func_orden_creada
                    self.DICT_WIDGETS["id_pago"].pack_forget()
                    self.DICT_WIDGETS["label_cronometro"].pack()
                    self.des_progreso(**self.DICT_PROGRESO)
                elif self.reintentarpago is False:
                    self.DICT_PROGRESO["command"] = self.cancelar_orden
                    self.progreso(**self.DICT_PROGRESO)
        except Exception as e:
            log_error(e, "func_orden_creada")
            self.cierre_ERROR()
            
    def buscar_pago_en_MP(self):
        self.respuesta_pago = self.DICT_CONEXION["conexionAPI"].obtenerPAGO(self.id_pago)
        self.datos_pagos = self.respuesta_pago.json()
            
    def buscar_pago_en_dba(self): #Activado por un thread que lo hace es esperar el pago en el DBA
        try:
            pos_id = self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion("MPQRCODE_CAJAS", "id", "external_id", self.DICT_DATOS_ORDEN["external_id_pos"], False)
            #print(self.reintentarpago)
            if self.reintentarpago is None:
                while self.DICT_CONEXION["conexionDBAServer"].specify_search_condicionID("MPQRCODE_OBTENERPAGOServer", "data", "external_reference", self.DICT_DATOS_ORDEN["nro_factura"], "pos_id", pos_id, False) is None and not self.DICT_PROGRESO["text_label_aviso"] == "Cancelando Orden" and not self.PAGO_MANUAL is True:
                    time.sleep(1)
            elif self.reintentarpago is True:
                self.reintentarpago = False
                self.esperando_comparacion = True
                while self.DICT_CONEXION["conexionDBAServer"].specify_search_condicionID("MPQRCODE_OBTENERPAGOServer", "date_last_updated", "external_reference", self.DICT_DATOS_ORDEN["nro_factura"], "pos_id", pos_id, False) == self.ultima_actualizacion and not self.DICT_PROGRESO["text_label_aviso"] == "Cancelando Orden" and not self.PAGO_MANUAL is True:
                    #print(self.DICT_CONEXION["conexionDBAServer"].specify_search_condicionID("MPQRCODE_OBTENERPAGOServer", "status", "external_reference", self.DICT_DATOS_ORDEN["nro_factura"], "pos_id", pos_id, False))
                    time.sleep(1)
                    pass
            if not self.DICT_CONEXION["conexionDBAServer"].specify_search_condicionID("MPQRCODE_OBTENERPAGOServer", "data", "external_reference", self.DICT_DATOS_ORDEN["nro_factura"], "pos_id", pos_id, False) is None and not self.DICT_PROGRESO["text_label_aviso"] == "Cancelando Orden" and not self.PAGO_MANUAL is True:
                self.id_pago = self.DICT_CONEXION["conexionDBAServer"].specify_search_condicionID("MPQRCODE_OBTENERPAGOServer", "data", "external_reference", self.DICT_DATOS_ORDEN["nro_factura"], "pos_id", pos_id, False)
        except Exception as e:
            log_error(e, "buscar_pago_en_dba")
            #self.cierre_ERROR()
            
            
    def buscar_pago_manual(self):
        log_error("Ventana buscar pago manual abierta.", "buscar_pago_manual")
        
        if self.ventana_buscarpagomanual_abierta  is False:
            self.ventana_buscarpagomanual_abierta  = True
            ventana_buscarpagomanual = Ventana_BuscarPagoManual(self.DICT_WIDGETS, self.DICT_DATOS_ORDEN, self.DICT_CONEXION)
            threading.Thread(target=self.esperar_respuesta_mp, args=(ventana_buscarpagomanual, ), daemon=True).start()
        else:
            print("BLOQUEO PAGO MANUAL")
            
    def esperar_respuesta_mp(self, ventana_buscarpagomanual):
        while ventana_buscarpagomanual.return_respuesta_mp() is None:
            print(ventana_buscarpagomanual.return_respuesta_mp())
            time.sleep(1)
        print(ventana_buscarpagomanual.return_respuesta_mp())
        if not ventana_buscarpagomanual.return_respuesta_mp() is False:
            if ventana_buscarpagomanual.return_respuesta_mp() == "CERRANDO":
                self.ventana_buscarpagomanual_abierta = False
                return
            else:
                self.datos_pagos = ventana_buscarpagomanual.return_respuesta_mp()
                self.respuesta_pago = self.datos_pagos
                self.datos_pagos = self.respuesta_pago.json()
                self.id_pago = self.datos_pagos["id"]
        else:
            self.NRO_ERROR = 101
        self.esperando_pago = False
        self.PAGO_MANUAL = True
        
    def entry_info_buscar_pago_on_focus_in(self, event):
        try:
            if self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["entry_info_buscar_pago"].get() == self.placeholder_text:
                self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["entry_info_buscar_pago"].delete(0, "end")
                self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["entry_info_buscar_pago"].config(foreground='black')
        except Exception as e:
            log_error(str(e), "entry_info_buscar_pago_on_focus_in")
            #messagebox.showerror("Error", "Error al enfocar la entrada de ID de operación.")


    def entry_info_buscar_pago_on_focus_out(self, event):
        try:
            if self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["entry_info_buscar_pago"].get() == "":
                self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["entry_info_buscar_pago"].insert(0, self.placeholder_text)
                self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["entry_info_buscar_pago"].config(foreground='gray')
        except Exception as e:
            log_error(str(e), "entry_info_buscar_pago_on_focus_out")
            #messagebox.showerror("Error", "Error al desenfocar la entrada de ID de operación.")
            
    def validate_number(self, entry_value):
        try:
            # Validar si la entrada es un número
            if entry_value == "" or entry_value.isdigit() or entry_value == self.placeholder_text:
                return True
            else:
                # Mostrar el mensaje de error
                mostrar_error_y_cerrar(self.DICT_WIDGETS, "Solo puedes ingresar valores numéricos." , teclado_hasar=self.teclado_hasar)
                self.ventana_buscarpagomanual_abierta = False
                #messagebox.showerror("Error", "Solo puedes ingresar valores numéricos.")
                return False
        except Exception as e:
            log_error(str(e), "validate_number")
            #messagebox.showerror("Error", "Error al validar el número.")
            return False
        
    def handle_click_outside(self, event):
        try:
            # Verificar si el clic fue fuera del Entry
            widget_under_cursor = self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["ventana_buscar_pago_manual"].winfo_containing(event.x_root, event.y_root)
            if widget_under_cursor != self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["entry_info_buscar_pago"]:
                # Llamar al método de pérdida de foco manualmente
                self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["entry_info_buscar_pago"].focus_set()
                self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["ventana_buscar_pago_manual"].focus_set()  # O enfocar el contenedor principal para garantizar la pérdida de foco
        except Exception as e:
            log_error(str(e), "handle_click_outside")
            #messagebox.showerror("Error", "Error al procesar el clic fuera del campo de entrada.")
            
        
        
    def ERROR_API(self, label_error):
        try:
            ERRORES_API = {
                'cc_rejected_insufficient_amount': {
                    'nro_error': 20.1,
                    'description': 'Saldo insuficiente',
                },
                'cc_rejected_call_for_authorize': {
                    'nro_error': 20.2,
                    'description': 'Pago no autorizado. Debe autorizarlo con el emisor de la tarjeta.',
                },
                'cc_rejected_bad_filled_security_code': {
                    'nro_error': 20.3,
                    'description': 'Código de seguridad inválido',
                },
                'cc_rejected_bad_filled_date': {
                    'nro_error': 20.4,
                    'description': 'Fecha de vencimiento inválida',
                },
                'cc_rejected_bad_filled_other': {
                    'nro_error': 20.5,
                    'description': 'Error en los datos de la tarjeta',
                },
                'cc_rejected_other_reason': {
                    'nro_error': 20.6,
                    'description': 'Pago rechazado por la tarjeta',
                },
                'cc_rejected_card_disabled': {
                    'nro_error': 20.7,
                    'description': 'Tarjeta deshabilitada. Contacte al emisor.',
                },
                'cc_rejected_bad_filled_card_number': {
                    'nro_error': 20.8,
                    'description': 'Número de tarjeta incorrecto',
                },
                'cc_rejected_invalid_installments': {
                    'nro_error': 20.9,
                    'description': 'La tarjeta no acepta el número de cuotas elegido',
                },
                'cc_rejected_duplicated_payment': {
                    'nro_error': 21.0,
                    'description': 'Pago duplicado para el mismo importe',
                },
                'cc_rejected_card_type_not_allowed': {
                    'nro_error': 21.1,
                    'description': 'Tipo de tarjeta no permitido',
                },
                'cc_rejected_max_attempts': {
                    'nro_error': 21.2,
                    'description': 'Límite de intentos excedido. Use otro método de pago.',
                },
                'cc_rejected_blacklist': {
                    'nro_error': 21.3,
                    'description': 'Tarjeta bloqueada por el emisor',
                },
                'cc_rejected_3ds_mandatory': {
                    'nro_error': 21.4,
                    'description': 'Se requiere desafío 3DS y no fue completado.',
                },
                'cc_rejected_3ds_challenge': {
                    'nro_error': 21.5,
                    'description': 'Desafío 3DS fallido o no completado.',
                },
                'cc_rejected_card_error': {
                    'nro_error': 21.6,
                    'description': 'Error del emisor al procesar la tarjeta.',
                },
                'cc_rejected_high_risk': {
                    'nro_error': 21.7,
                    'description': 'Pago rechazado por riesgo alto. Intente otro medio (recomendado: efectivo).',
                },
                'cc_amount_rate_limit_exceeded': {
                    'nro_error': 21.8,
                    'description': 'Excede el límite permitido (CAP) del método de pago.',
                },
                'rejected_insufficient_data': {
                    'nro_error': 21.9,
                    'description': 'Faltan datos obligatorios del pago.',
                },
                'rejected_by_bank': {
                    'nro_error': 22.0,
                    'description': 'Operación rechazada por el banco.',
                },
                'rejected_by_regulations': {
                    'nro_error': 22.1,
                    'description': 'Pago rechazado por normativa/regulaciones.',
                },
                'bank_error': {
                    'nro_error': 22.2,
                    'description': 'Error del banco en transferencia bancaria.',
                },
                'insufficient_amount': {
                    'nro_error': 22.3,
                    'description': 'Importe insuficiente para completar la operación.',
                },
            }

            error_lista = []
            # Obtener la descripción del error específico en ERRORES_API
            if label_error in ERRORES_API:
                errorEsp = ERRORES_API[label_error]
                error_lista = [errorEsp[key] for key in ('nro_error', 'description') if key in errorEsp]
                self.detalle_error = label_error
                return error_lista
            else:
                # En caso de que el error no esté en el diccionario
                return ["Error no registrado"]
        except Exception as e:
            # Captura el traceback completo y lo registra
            error_detallado = traceback.format_exc()
            print(label_error, error_detallado)
            log_error(error_detallado, "ERROR_API")  # Registro del error completo


    def LISTADO_ERRORES(self):
        try:
            Monto_recibido = self.DICT_CONEXION['conexionDBAServer'].specify_search_condicion('MPQRCODE_OBTENERPAGOServer', 'transaction_amount', 'external_reference', self.DICT_DATOS_ORDEN['nro_factura'], False)
            if not Monto_recibido is None:
                Monto_recibido = float(Monto_recibido)
            DICT_ERRORES = {
                1: "Orden Cancelada",
                10: (
                    "El monto esperado no es el mismo recibido en MercadoPago\n"
                    f"Monto esperado: *(${self.DICT_DATOS_ORDEN['monto_pagar']}{{green}})*\n"
                    f"Monto recibido: *(${Monto_recibido}{{red}})*"
                )
                ,
                11: f"El ID *({self.id_pago}{{red}})* no coincide",
                12:  f"El ID *({self.id_pago}{{red}})* ya tiene una devolución hecha",
                13: "El Número de factura no coincide con el ID Obtenido",
                15: (
                    "Este medio de pago no está disponible para realizar el descuento del PBS.\n"
                    f"Medios Disponibles: {list(self.dict_pbs_disponibles.keys())}"
                ), #AGREGADO 23/04/2025
                16: f"No se pudo realizar el reembolso del ID {self.id_pago}\n Por favor, verificar con el supervisor si se necesita más información sobre el reembolso.",  #AGREGADO 23/04/2025
                21: "El pago no está aprobado",
                23: "No hemos recibido respuesta de MercadoPago",
                1001: "Error no registrado"
            }
        
            self.datos_error = {
                'status': 0,
                'response': self.NRO_ERROR,
                'description': DICT_ERRORES[self.NRO_ERROR]
            }
            print(DICT_ERRORES[self.NRO_ERROR])
            return DICT_ERRORES[self.NRO_ERROR]
        except Exception as e:
            # Captura el traceback completo y lo registra
            error_detallado = traceback.format_exc()
            print(self.NRO_ERROR, error_detallado)
            log_error(error_detallado, "LISTADO_ERRORES")  # Registro del error completo
            
    def llamado_taskkill(self):
        self.DICT_WIDGETS["cerrar_con_taskill"](self.DICT_DATOS_ORDEN['nro_factura'])            

            
#------------------------------------------------------------Comparar datos--------------------------------------------------------

    def realizar_comparacion(self):
            try:
                print("realizar_comparacion")
                if self.PAGO_MANUAL:
                        #BUSCA SI COINCIDEN LOS NÚMMEROS DE FACTURAS
                        print("BUSCA SI COINCIDEN LOS NÚMEROS DE FACTURAS")
                        if (
                                self.DICT_DATOS_ORDEN["nro_factura"] != self.datos_pagos["external_reference"]
                                and not self.DICT_WIDGETS.get("forzar_comparacion_factura", False)
                            ):

                            nro_esperado = self.DICT_DATOS_ORDEN["nro_factura"]
                            nro_recibido = self.datos_pagos["external_reference"]

                            mensaje = (
                                "El número de factura no coincide con el registrado en el pago.\n"
                                f"*(Factura esperada: {nro_esperado}{{green}})*\n"
                                f"*(Factura recibida: {nro_recibido}{{red}})*\n\n"
                                "Si desea anular este pago y generar uno nuevo, ingrese la clave de supervisor."
                            )

                            mostrar_error_y_cerrar(
                                self.DICT_WIDGETS,
                                mensaje,
                                teclado_hasar=self.teclado_hasar,
                                type_msg="warning",
                                remarcar=True
                            )
                            return
                if self.datos_pagos["status"] == 'approved':
                    #BUSCA SI COINCIDEN LOS MONTOS DE FACTURAS
                    print("BUSCA SI COINCIDEN LOS MONTOS DE FACTURAS")
                    if self.DICT_DATOS_ORDEN["monto_pagar"] == self.datos_pagos["transaction_amount"]:
                        print(self.DICT_DATOS_ORDEN["monto_pagar"], self.datos_pagos["transaction_amount"])
                    else:
                        self.NRO_ERROR = 10
                        mostrar_error_y_cerrar(self.DICT_WIDGETS, f"Error {self.NRO_ERROR}\n{self.LISTADO_ERRORES()}", teclado_hasar=self.teclado_hasar, remarcar=True)
                        #CustomMessageBox(self.DICT_WIDGETS["root"], f"Error {self.NRO_ERROR}", self.LISTADO_ERRORES(), "error")
                        #messagebox.showerror(f"Error {self.NRO_ERROR}", self.LISTADO_ERRORES())
                        self.DICT_PROGRESO["text_label_aviso"] = "ERROR"
                        
                        self.esperando_comparacion = True
                        self.reintentarpago = False
                        return 
                    if int(self.DICT_DATOS_ORDEN["response"]) == 98:
                        print("PAGO PBS")
                        if self.comprobación_PBS():  # <-- Si coincide, OMITIR devolución
                            print("Método PBS válido, continuar sin reembolso.")
                            self.esperando_comparacion = True
                            self.reintentarpago = None
                        else:
                            if not self.NRO_ERROR == 1001:
                                self.NRO_ERROR = 15
                                print(8)
                                mostrar_error_y_cerrar(self.DICT_WIDGETS, f"Error {self.NRO_ERROR}\n{self.LISTADO_ERRORES()}", teclado_hasar=self.teclado_hasar, remarcar=True)
                                """self.DICT_WIDGETS["root"].after(100, lambda: CustomMessageBox(
                                    self.DICT_WIDGETS["root"],
                                    f"Error {self.NRO_ERROR}",
                                    self.LISTADO_ERRORES(),
                                    "error",
                                    teclado_hasar=self.teclado_hasar
                                ))"""
                                self.DICT_PROGRESO["text_label_aviso"] = "Realizando reembolso"
                                self.progreso(**self.DICT_PROGRESO)

                                respuesta = self.DICT_CONEXION['conexionAPI'].crear_orden_reembolso(
                                self.id_pago, self.datos_pagos["transaction_amount"]
                            )

                            respuesta_reembolso = respuesta.status_code >= 200 and respuesta.status_code <= 299
                            print(respuesta_reembolso)

                            if respuesta_reembolso:
                                self.DICT_PROGRESO["text_label_aviso"] = "Reembolso realizado"
                                self.progreso(**self.DICT_PROGRESO)
                            else:
                                self.NRO_ERROR = 16
                                print(9)
                                mostrar_error_y_cerrar(self.DICT_WIDGETS, f"Error {self.NRO_ERROR}\n{self.LISTADO_ERRORES()}", teclado_hasar=self.teclado_hasar, remarcar=True)
                                log_error(respuesta.json(), "realizar_comparacion_comprobación_PBS")
                            self.reintentarpago = True
                            self.esperando_comparacion = True
                            self.ultima_actualizacion = self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion("MPQRCODE_OBTENERPAGOServer", "date_last_updated", "external_reference", self.DICT_DATOS_ORDEN["nro_factura"], False)
                            return    
                elif self.datos_pagos["status"] == 'refunded':
                    self.NRO_ERROR = 12
                    mostrar_error_y_cerrar(self.DICT_WIDGETS, f"Error {self.NRO_ERROR}\n{self.LISTADO_ERRORES()}", teclado_hasar=self.teclado_hasar, remarcar=True)
                    #CustomMessageBox(self.DICT_WIDGETS["root"], f"Error {self.NRO_ERROR}", self.LISTADO_ERRORES(), "error")
                    #messagebox.showerror(f"Error {self.NRO_ERROR}", self.LISTADO_ERRORES())
                    self.reintentarpago = False                    
                    self.esperando_comparacion = True
                    return
                elif self.datos_pagos["status"] == "rejected" or self.datos_pagos["status"] == 'cancelled':
                    if messagebox.askretrycancel(message=f"No sea recibido el pago.\n ERROR: \n DETALLE: {self.datos_pagos["status"]} {self.ERROR_API(self.datos_pagos["status_detail"])}\n ¿Desea reintentar el pago?", title="Error de Pago"):
                        print("Respuesta Reintentar")
                        self.reintentarpago = True
                        self.esperando_comparacion = True
                        self.ultima_actualizacion = self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion("MPQRCODE_OBTENERPAGOServer", "date_last_updated", "external_reference", self.DICT_DATOS_ORDEN["nro_factura"], False)
                        return
                    else:
                        print("Respuesta cacelada")
                        self.DICT_CONEXION["conexionDBAServer"].actualizar_datos_condicion("MPQRCODE_OBTENERPAGOServer", self.datos_obtener_pago, "external_reference", f"'{self.DICT_DATOS_ORDEN["nro_factura"]}'")
                        self.reintentarpago = False
                        self.esperando_comparacion = True
                        return
                elif self.datos_pagos["status"] == 'in_process':
                    self.DICT_PROGRESO["text_label_aviso"] = "Aguardando confirmación de Pago"
                    self.progreso(**self.DICT_PROGRESO)
                    while self.datos_pagos["status"] == 'in_process':
                        self.buscar_pago_en_MP()
                        print(self.datos_pagos["status"], self.datos_pagos["status_detail"])
                        time.sleep(3)
                    self.DICT_PROGRESO["text_label_aviso"] = "Pago Confirmado"
                    self.progreso(**self.DICT_PROGRESO)
                    self.DICT_PROGRESO["text_label_aviso"] = "Realizando comparación"
                    self.progreso(**self.DICT_PROGRESO)
                    self.realizar_comparacion()
                else:
                    mostrar_error_y_cerrar(self.DICT_WIDGETS, "ERROR DE COMPARACIÓN", teclado_hasar=self.teclado_hasar)
                    #CustomMessageBox(self.DICT_WIDGETS["root"], f"Error", "ERROR DE COMPARACIÓN", "error")
                    self.DICT_PROGRESO["text_label_aviso"] = "ERROR"
                    self.esperando_comparacion = True
                    self.reintentarpago = False
                    return
                print("TERMINO ACA")
                self.esperando_comparacion = True 
                self.reintentarpago = None   
            except Exception:
                # imprime el stack completo en consola
                traceback.print_exc()

                # y además lo guardás en tu logger personalizado
                tb = traceback.format_exc()  # <- string con todo el stack
                log_error(tb, "realizar_comparacion")

                
                
                
    def agrega_datos_dba_caja(self):
        try:
            """datos_dba = {
                "external_reference": self.datos_pago["external_reference"],
                "external_idPOS": self.DICT_DATOS_ORDEN["external_id_pos"],
                "collector_id": self.datos_pago["collector_id"],
                "coupon_amount": self.datos_pago["coupon_amount"],
                "currency_id": self.datos_pago["currency_id"],
                "date_approved": self.datos_pago["date_approved"],
                "date_created": self.datos_pago["date_created"],
                "date_last_updated": self.datos_pago["date_last_updated"],
                "date_of_expiration": self.datos_pago["date_of_expiration"],
                "deduction_schema": self.datos_pago["deduction_schema"],
                "description": self.datos_pago["description"],
                "id": self.datos_pago["id"],
                "installments": self.datos_pago["installments"],
                "integrator_id": self.datos_pago["integrator_id"],
                "issuer_id": self.datos_pago["issuer_id"],
                "live_mode": self.datos_pago["live_mode"],
                "marketplace_owner": self.datos_pago["marketplace_owner"],
                "merchant_account_id": self.datos_pago["merchant_account_id"],
                "merchant_number": self.datos_pago["merchant_number"],
                "order_id": self.datos_pago["order_id"],
                "order_type": self.datos_pago["order_type"],
                "payer_id": self.datos_pago["payer_id"],
                "payment_metodo_id": self.datos_pago["payment_method"]["payment_method_id"],
                "payment_metodo_issuer_id": self.datos_pago["payment_method"]["payment_method_issuer_id"],
                "payment_metodo_type": self.datos_pago["payment_method"]["payment_method_type"],
                "pos_id": self.datos_pago["pos_id"],
                "processing_mode": self.datos_pago["processing_mode"],
                "shipping_amount": self.datos_pago["shipping_amount"],
                "sponsor_id": self.datos_pago["sponsor_id"],
                "status": self.datos_pago["status"],
                "status_detail": self.datos_pago["status_detail"],
                "store_id": self.datos_pago["store_id"],
                "taxes_amount": self.datos_pago["32"],
                "transaction_amount": self.datos_pago["transaction_amount"],
                "transaction_amount_refunded": self.datos_pago["transaction_amount_refunded"],
                "net_received_amount": self.datos_pago["transaction_details"]["net_received_amount"],
                "transaction_details_total_paid_amount": self.datos_pago["transaction_details"]["total_paid_amount"],
                "NomCaja": self.datos_obtener_pago["NomCaja"],
                "NumCajero": self.datos_obtener_pago["NumCajero"],
                "NombreCajero":self.datos_obtener_pago["NombreCajero"]
                }"""
            
            #COMPARAR Y SEPARAR EL TIPO DE PAGO
            if self.datos_pagos["payment_method_id"] == "account_money" or self.datos_pagos["payment_method_id"] == "consumer_credits":
                pass
            elif self.datos_pagos["payment_method_id"] == "interop_transfer":
                self.payment_method_id = self.datos_pagos["payment_method_id"]
                self.payment_method_name = "MP Billetera Virtual" #03/07/25
                self.payment_type_id = self.datos_pagos["payment_type_id"]
            else:
                pagos_disponibles = self.DICT_CONEXION["conexionAPI"].obtenerTodosMediosPagos()
                name_tarjeta_encontrada = None
                for pagos in pagos_disponibles.json():
                    if pagos["id"] == self.datos_pagos["payment_method_id"]:
                        name_tarjeta_encontrada = pagos['name']
                self.card_first_six_digits = self.datos_pagos["card"]["first_six_digits"]
                self.card_last_four_digits = self.datos_pagos["card"]["last_four_digits"]
                self.payment_method_id = self.datos_pagos["payment_method_id"]
                self.payment_method_name = f"MP {name_tarjeta_encontrada}"#03/07/25
                self.payment_type_id = self.datos_pagos["payment_type_id"]
                
                
                
            self.DICT_CONEXION["conexionAPI"].obtenerPago_manual(self.DICT_DATOS_ORDEN["external_id_pos"], self.respuesta_pago)
            self.DICT_PROGRESO["carga"] = 99
            self.DICT_PROGRESO["command"] = self.finalizar_pago
            self.progreso(**self.DICT_PROGRESO)
        except Exception as e:
            log_error(e, "agrega_datos_dba_caja")       
            

        
        
#------------------------------------------------------------ CIERRES --------------------------------------------------------------
    def cierre_ERROR(self, paso_M, label_error=None ):
        print("cierre_ERROR")
        self.DICT_WIDGETS["ventana_tamano_400_550"]()
        if label_error is None:
            self.DICT_PROGRESO["text_label_aviso"] = "ERROR"
        else:
            self.DICT_PROGRESO["text_label_aviso"] = label_error
        self.DICT_PROGRESO["carga"] = 99
        self.DICT_PROGRESO["command"] = self.mostrar_error
        self.progreso(**self.DICT_PROGRESO)
        time.sleep(1)
        if paso_M:
            self.DICT_WIDGETS["cerrar_ventana"]()
                
    def mostrar_error(self):
        mostrar_error_y_cerrar(self.DICT_WIDGETS, f"Error {self.NRO_ERROR}\n{self.LISTADO_ERRORES()}", teclado_hasar=self.teclado_hasar, remarcar=True)
        #CustomMessageBox(self.DICT_WIDGETS["root"], f"Error {self.NRO_ERROR}", self.LISTADO_ERRORES(), "error")
        #messagebox.showerror(f"Error {self.NRO_ERROR}", self.LISTADO_ERRORES())
        self.DICT_CONEXION["conexionDBA"].actualizar_datos_condicion(
            "MPQRCODE_CONEXIONPROGRAMAS",
            self.datos_error,
            "nro_factura",
            f"'{self.DICT_DATOS_ORDEN['nro_factura']}'"  # Cambiado a comillas simples internas
        )
        
    def aviso_cancelar_orden(self):
        self.DICT_PROGRESO["text_label_aviso"] = "Cancelando Orden"
        self.DICT_PROGRESO["carga"] = 51
        self.DICT_PROGRESO["command"] = self.cancelar_orden
        print("aviso_cancelar_orden")
        self.progreso(**self.DICT_PROGRESO)
        log_error("Usuario solicitó cancelar la orden manualmente.", "aviso_cancelar_orden") 
        
    def cancelar_orden(self):
        try:      
            self.NRO_ERROR = 1        
            self.DICT_CONEXION["conexionAPI"].cancelarOrden(self.DICT_DATOS_ORDEN["external_id_pos"])
            self.cerrar_cronometro()
            self.cierre_ERROR(True, "Cancelando Orden")
        except Exception as e:
            log_error(str(e), "cancelar_orden")
            messagebox.showerror("Error", "Ha ocurrido un error al cancelar la orden.")
            
    def cancelar_orden_pasado_segundos(self):
        try:
            self.DICT_CONEXION["conexionAPI"].cancelarOrden(self.DICT_DATOS_ORDEN["external_id_pos"])
            self.cerrar_cronometro()
            self.NRO_ERROR = 23
            self.cierre_ERROR(False, "Cancelando Orden")
            self.DICT_WIDGETS["cerrar_ventana"]()
        except Exception as e:
            log_error(str(e), "cancelar_orden_pasado_segundos")
            
    def cerrar_cronometro(self):
        try:
            self.cronometro.detener_temporizador()
            self.DICT_WIDGETS["label_cronometro"].pack_forget()
            self.DICT_WIDGETS["boton_cancelar"].config(state=tk.DISABLED)
        except Exception as e:
            log_error(str(e), "cerrar_cronometro")
            self.cierre_ERROR()
            
            
    def obtener_diccionario_pbs(self): #AGREGADO 23/04/2025
        sentencia_traer_PBS_disponibles = """
            SELECT CDESPAGO, cMetodo_id, cMetodo_name, ctype_id
            FROM FPAGO
            WHERE NAPL1 = '2'
        """
        self.pbs_disponibles = self.DICT_CONEXION["conexionDBA"].ejecutar_consulta(sentencia_traer_PBS_disponibles)

        self.dict_pbs_disponibles = {}
        for item in self.pbs_disponibles:
            cdenspago, metodo_id, metodo_name, tipo_id = item
            self.dict_pbs_disponibles[cdenspago] = {
                "payment_method_id": metodo_id,
                "payment_metho_name": metodo_name,
                "payment_type_id": tipo_id
            }
        pprint(self.dict_pbs_disponibles)
        
    def comprobación_PBS(self):
        try:
            if not self.dict_pbs_disponibles:
                print("⚠️ No hay métodos PBS cargados.")
                return False

            encontrados = any(
                self.datos_pagos["payment_method_id"] == datos["payment_method_id"] and
                self.datos_pagos["payment_type_id"] == datos["payment_type_id"]
                for datos in self.dict_pbs_disponibles.values()
            )

            print(f"¿Método válido PBS?: {encontrados}")
            return encontrados

        except Exception as e:
            self.NRO_ERROR = 1001
            print("❌ Error en comprobación_PBS:", e)
            mostrar_error_y_cerrar(self.DICT_WIDGETS, f"Ocurrió un error inesperado: {e}", teclado_hasar=self.teclado_hasar)
            return False

            
            
    def finalizar_pago(self):
        try:
            datos = {
                'status': 1,
                'response': 0,
                'description': 'accredited',
                'IDMercadoPago': self.id_pago,
                'card_first_six_digits': self.card_first_six_digits,
                'card_last_four_digits': self.card_last_four_digits,
                'payment_method_id': self.payment_method_id,
                'payment_method_name': self.payment_method_name,
                'payment_type_id': self.payment_type_id,
            }
            self.DICT_WIDGETS["my_label_aviso"].config(text="Pago recibido")
            self.DICT_CONEXION["conexionDBA"].actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMAS", datos, "nro_factura", f"'{self.DICT_DATOS_ORDEN["nro_factura"]}'")
            self.DICT_CONEXION["conexionDBAServer"].actualizar_datos_condicion("MPQRCODE_OBTENERPAGOServer", self.datos_obtener_pago, "external_reference", f"'{self.DICT_DATOS_ORDEN["nro_factura"]}'")
            self.DICT_CONEXION["conexionDBA"].actualizar_datos_condicion("MPQRCODE_OBTENERPAGO", self.datos_obtener_pago, "external_reference", f"'{self.DICT_DATOS_ORDEN["nro_factura"]}'")
            log_error("Pago finalizado exitosamente, se actualiza base y se cierra ventana.", "finalizar_pago")
            self.DICT_WIDGETS["cerrar_ventana"]()
        except Exception as e:
            log_error(str(e), "finalizar_pago")
            #self.cierre_ERROR(paso_M=True)
            
    def es_fecha_aprovado(self, date_string):
        try:
            # Parsear la fecha que viene con zona horaria -04:00
            fecha_remota = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.000-04:00")

            # La fecha en la zona -04:00 (ya está en ese huso, sin necesidad de conversión)
            tz_remota = pytz.timezone("Etc/GMT+4")  # GMT+4 es UTC-04:00
            fecha_remota = tz_remota.localize(fecha_remota)

            # Hora actual en Argentina (UTC-03:00)
            tz_arg = pytz.timezone("America/Argentina/Buenos_Aires")
            ahora_arg = datetime.now(tz_arg)

            # Convertimos ambas fechas a UTC para comparar correctamente
            diferencia = abs((ahora_arg.astimezone(pytz.utc) - fecha_remota.astimezone(pytz.utc)).total_seconds())

            return diferencia
        except Exception as e:
            print(f"Error al verificar la fecha: {e}")
            return False
    
    
    
    def solicitar_clave_supervisor(self, callback_si_valida):
        # 🛑 Si la ventana ya está abierta, la enfocamos y salimos
        if hasattr(self, "ventana_clave_supervisor") and self.ventana_clave_supervisor.winfo_exists():
            self.ventana_clave_supervisor.lift()
            self.ventana_clave_supervisor.focus_force()
            return

        def verificar_clave():
            clave_ingresada = entry.get().strip()
            if clave_ingresada in self.DICT_WIDGETS["DICT_CLAVES_SUPERVISORES"]:
                print(f"[SUPERVISOR] Acceso autorizado por {self.cierre_supervisor_autorizante}")
                self.teclado_hasar.funciones_personalizadas.pop("4a", None)  # limpiamos
                msgbox = self.DICT_WIDGETS.get("variable_contendora_MensajeERROR")
                if msgbox and hasattr(msgbox, "close"):
                    msgbox.close()
                    self.DICT_WIDGETS["variable_contendora_MensajeERROR"] = None

                self.ventana_clave_supervisor.destroy()
                self.ventana_clave_supervisor = None  # ✅ limpieza
                self.DICT_PROGRESO["text_label_aviso"] = "Realizando reembolso"
                self.progreso(**self.DICT_PROGRESO)

                respuesta = self.DICT_CONEXION['conexionAPI'].crear_orden_reembolso(
                self.id_pago, self.datos_pagos["transaction_amount"]
                )
                self.ultima_actualizacion = self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion("MPQRCODE_OBTENERPAGOServer", "date_last_updated", "external_reference", self.datos_pagos["external_reference"], False)
                print(self.ultima_actualizacion)

                respuesta_reembolso = respuesta.status_code >= 200 and respuesta.status_code <= 299
                print(respuesta_reembolso)
                callback_si_valida()
            else:
                label_info.config(text="❌ Clave incorrecta", foreground="red")

        # Crear ventana (solo si no existe)
        self.ventana_clave_supervisor = ttk.Toplevel(self.DICT_WIDGETS["root"])
        self.ventana_clave_supervisor.title("Clave de Supervisor")
        center_window(self.ventana_clave_supervisor, 400, 150)
        self.ventana_clave_supervisor.grab_set()

        frame = ttk.Frame(self.ventana_clave_supervisor, padding=20)
        frame.pack(expand=True, fill="both")

        label = ttk.Label(frame, text="Ingrese la clave de supervisor:")
        label.pack(pady=(0, 10))

        entry = ttk.Entry(frame, show="*", font=("Arial", 14))
        self.teclado_hasar.asignar_entry(entry)
        entry.pack(pady=(0, 10))
        entry.focus()

        label_info = ttk.Label(frame, text="")
        label_info.pack()

        btn = ttk.Button(frame, text="Verificar", command=verificar_clave, bootstyle="success")
        btn.pack(pady=10)

        self.ventana_clave_supervisor.bind("<Return>", lambda e: verificar_clave())

        # ✅ Registrar combinación '4a'
        self.teclado_hasar.registrar_combinacion_personalizada("4a")
        self.teclado_hasar.asignar_funcion_personalizada("4a", lambda: self.ventana_clave_supervisor.after(0, verificar_clave))



    def activar_modo_supervisor(self):
        print("🔐 Supervisor pidió forzar validación")

        def continuar_a_pesar_de_error():
            self.DICT_WIDGETS["modo_supervisor_forzado"] = False
            self.DICT_WIDGETS["forzar_comparacion_factura"] = True
            print("🔓 Supervisor autorizó continuar a pesar del error de factura")
            self.NRO_ERROR = None
            self.reintentarpago = True
            self.esperando_comparacion = True
        if self.DICT_WIDGETS.get("modo_supervisor_forzado", False):
            self.solicitar_clave_supervisor(continuar_a_pesar_de_error)