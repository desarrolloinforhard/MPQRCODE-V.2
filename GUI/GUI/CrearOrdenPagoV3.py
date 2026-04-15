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
from GUI.MessageBox import mostrar_error_y_cerrar, mostrar_cancelar_continuar, mostrar_reintentar_cancelar
from Func.qrcode_mpV2 import crear_qr_data
from Func.log_errorsV2 import log_error
from Func.window_position import center_window

from datetime import datetime
from zoneinfo import ZoneInfo  # Py ≥ 3.9

AR_TZ = ZoneInfo("America/Argentina/Cordoba")

def now_ar_str_ms():
    # Devuelve 'YYYY-MM-DD HH:MM:SS.000' en hora de Argentina
    return datetime.now(AR_TZ).strftime("%Y-%m-%d %H:%M:%S.000")

def _sql_str(v: str) -> str:
    """Devuelve 'valor' escapado para SQL (dobla comillas simples)."""
    s = str(v).strip()
    # si viene rodeado de comillas, quitarlas
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        s = s[1:-1].strip()
    return "'" + s.replace("'", "''") + "'"

def _sql_literal_auto(v):
    """Si es int válido -> sin comillas; si no -> string escapado."""
    try:
        return str(int(str(v).strip().strip("'").strip('"')))
    except Exception:
        return _sql_str(v)


print("Clase: CrearOrdenPagoV3")

class CrearOrdenPago(BarraProgreso):
    def __init__(self, frame, DICT_WIDGETS, DICT_DATOS_ORDEN, DICT_CONEXION):
        try:
        
            # Inicializar correctamente la clase base ttk.Progressbar
            super().__init__(frame)
            
            #---------------------------------------- VARIABLES INICIADORAS ----------------------------------------
            self.crearorden = True
            self.orden_creada = False
            self.id_pago = None
            self.pago_capturado = None
            self.datos_error = None
            self.detalle_error = None
            self.ultima_actualizacion = None
            self.datos_pagos = None
            self.NRO_ERROR = None
            self.PAGO_MANUAL = False
            self.reintentarpago = None
            self.ventana_buscarpagomanual_abierta = False
            self.fecha_orden_creada_ar = None
            
            
            self.card_first_six_digits = None
            self.card_last_four_digits = None
            self.payment_method_id = None
            self.payment_method_name = None
            self.payment_type_id = None
            
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
            
            pprint(self.DICT_DATOS_ORDEN)
            self.DICT_DATOS_ORDEN["idINTEGRACION"] = 0
            
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
                # ⬇️ guarda sello de tiempo para comparar luego con RESPUESTAPOST
                self.fecha_orden_creada_ar = now_ar_str_ms()

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
            self.pago_capturado = None
            if self.condicion_teclado:
                self.teclado_hasar.registrar_combinacion_personalizada("a6")
                self.teclado_hasar.asignar_funcion_personalizada("a6", self.buscar_pago_manual)
                self.teclado_hasar.registrar_combinacion_personalizada("a7")
                self.teclado_hasar.asignar_funcion_personalizada("a7", self.cancelar_orden)
                self.teclado_hasar.registrar_combinacion_personalizada("ab")
                self.teclado_hasar.asignar_funcion_personalizada("ab", self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["cerrar_ventana_buscar_pago_manual"])
            else:
                keyboard.add_hotkey('ctrl+alt+s', self.buscar_pago_manual)
            while self.pago_capturado is None and not self.DICT_PROGRESO["text_label_aviso"] == "Cancelando Orden":
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
        
        self.DICT_DATOS_ORDEN["respuesta"] = self.DICT_CONEXION["conexionAPI"].obtenerPAGO(self.id_pago)
        pprint(self.DICT_DATOS_ORDEN["respuesta"])
        self.datos_pagos = self.DICT_DATOS_ORDEN["respuesta"].json()
            
    def buscar_pago_en_dba(self):
        try:
            pos_id = self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion(
                "MPQRCODE_CAJAS", "id", "external_id",
                self.DICT_DATOS_ORDEN["external_id_pos"], False
            )
            if not getattr(self, "fecha_orden_creada_ar", None):
                self.fecha_orden_creada_ar = now_ar_str_ms()

            pago_id = self.esperar_payment_id(
                pos_id=pos_id,
                fecha_creacion_ar=self.fecha_orden_creada_ar,
                external_reference=self.DICT_DATOS_ORDEN["nro_factura"],
                timeout_s=180,
                intervalo_s=1.0
            )

            if pago_id:
                print("bucando info pago")
                self.buscar_pago_en_MP()
                self.DICT_CONEXION["conexionAPI"].obtenerPago_manual(self.DICT_DATOS_ORDEN)
                self.pago_capturado = True
                return
            else:
                # manejar timeout / cancelación
                return

        except Exception as e:
            log_error(e, "buscar_pago_en_dba")


            
            
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
                self.pago_capturado = True
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
            Monto_recibido = self.DICT_CONEXION['conexionDBAServer'].specify_search_condicion('PAGOSMERCADOPAGO', 'montoPAGO', 'idPAGO', self.id_pago, False)
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
                            )

                            mostrar_error_y_cerrar(
                                self.DICT_WIDGETS,
                                mensaje,
                                teclado_hasar=self.teclado_hasar,
                                type_msg="warning",
                                remarcar=True
                            )
                            self.reintentarpago = False
                            self.esperando_comparacion = True
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
                            self.ultima_actualizacion = self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion("PAGOSMERCADOPAGO", "dFechaU", "idPAGO", self.id_pago, False)
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
                    # Construir mensaje (usar .get o claves entre comillas simples para evitar errores)
                    self.fecha_orden_creada_ar = now_ar_str_ms()
                    detalle = self.ERROR_API(self.datos_pagos.get('status_detail'))[1]  # si tu ERROR_API devuelve (codigo, desc)
                    mensaje = (
                        "No se ha recibido el pago.\n"
                        "ERROR:\n"
                        f"DETALLE: {self.datos_pagos.get('status')} {detalle}\n\n"
                        "¿Desea reintentar el pago?"
                    )

                    # Mostrar diálogo Reintentar / Cancelar (True=reintentar, False=cancelar)
                    resp = mostrar_reintentar_cancelar(
                        self.DICT_WIDGETS,
                        mensaje,
                        teclado_hasar=self.teclado_hasar,
                        remarcar=True,
                        title="Error de Pago"
                    )

                    if resp:
                        print("Respuesta: Reintentar")
                        self.reintentarpago = True
                        self.esperando_comparacion = True
                        self.ultima_actualizacion = self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion("PAGOSMERCADOPAGO", "dFechaU", "idPAGO", self.id_pago, False)
                        return
                    else:
                        print("Respuesta: Cancelada")
                        """self.DICT_CONEXION["conexionDBAServer"].actualizar_datos_condicion(
                            "MPQRCODE_OBTENERPAGOServer",
                            self.datos_obtener_pago,
                            "external_reference",
                            f"'{self.DICT_DATOS_ORDEN['nro_factura']}'"   # si tu método espera la comilla acá
                        )"""
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
            
            
    def obtener_diccionario_pbs(self, incluir_vacios=False):  # AGREGADO 23/04/2025
        sql = """
            SELECT CDESPAGO, cMetodo_id, cMetodo_name, ctype_id
            FROM FPAGO
            WHERE NAPL1 = '2'
        """
        rows = self.DICT_CONEXION["conexionDBA"].ejecutar_consulta(sql)

        d = {}
        for row in (rows or []):
            if isinstance(row, dict):
                cdespago   = (row.get('cdespago')     or '').strip()
                metodo_id  = (row.get('cmetodo_id')   or '').strip()
                metodo_nom = (row.get('cmetodo_name') or '').strip()
                tipo_id    = (row.get('ctype_id')     or '').strip()
            else:
                # Lista/tupla en el mismo orden del SELECT
                CDESPAGO, cMetodo_id, cMetodo_name, ctype_id = row
                cdespago   = (CDESPAGO       or '').strip() if isinstance(CDESPAGO, str) else CDESPAGO or ''
                metodo_id  = (cMetodo_id     or '').strip() if isinstance(cMetodo_id, str) else cMetodo_id or ''
                metodo_nom = (cMetodo_name   or '').strip() if isinstance(cMetodo_name, str) else cMetodo_name or ''
                tipo_id    = (ctype_id       or '').strip() if isinstance(ctype_id, str) else ctype_id or ''

            if not incluir_vacios and not metodo_id:
                continue  # salteá “Tecla para PBS”, “PBS CLOVER”, etc.

            d[cdespago] = {
                "payment_method_id":   metodo_id,
                "payment_method_name": metodo_nom,
                "payment_type_id":     tipo_id,
            }

        self.dict_pbs_disponibles = d
        print(self.dict_pbs_disponibles)
        return d  # ← devolvés el dict directamente

        
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

    def esperar_payment_id(self, pos_id, fecha_creacion_ar: str, external_reference: str,
                       timeout_s: int = 180, intervalo_s: float = 1.0):
        """
        Pooling que busca el payment_id (columna 'data') consultando:
        1) MPQRCODE_RESPUESTAPOST por pos_id + date_created > fecha_creacion_ar
        2) MPQRCODE_OBTENERPAGOServer por external_reference (+ pos_id opcional)
        Si aparece primero en OBTENERPAGOServer, pregunta si continuar; si el usuario cancela,
        desde allí sólo espera el webhook (RESPUESTAPOST).
        """
        t0 = time.time()
        solo_resp_post = False  # cuando el usuario elije "Cancelar" en la pregunta

        while True:
            # Cancelación / timeout
            if self.DICT_PROGRESO.get("text_label_aviso") == "Cancelando Orden" or self.PAGO_MANUAL is True:
                return None
            if time.time() - t0 > timeout_s:
                return None

            # 1) RESPUESTAPOST (siempre lo chequeamos)
            try:
                pid = self.buscar_en_resp_post_por_posid(pos_id, fecha_creacion_ar)
            except Exception as e:
                pid = None
            if pid:
                self.id_pago = pid
                try:
                    self.avisar_pago_encontrado("RESPUESTAPOST", pid)
                except Exception as e:
                    log_error(e, "avisar_pago_encontrado")
                return pid

            # 2) OBTENERPAGOServer (solo si NO nos limitaron a esperar el webhook)
            if not solo_resp_post and self.reintentarpago is None:
                try:
                    pid = self.buscar_en_obtenerpago_por_external(external_reference, pos_id=pos_id)
                except Exception as e:
                    pid = None

                if pid:
                    # Preguntar si desea continuar con el pago ya registrado
                    try:
                        mensaje = (
                            f"Se encontró un cobro asociado a la factura {external_reference}.\n\n"
                            f"ID de pago: {pid}\n\n"
                            "¿Desea continuar con este pago ya registrado?"
                        )
                        decision = mostrar_cancelar_continuar(
                            self.DICT_WIDGETS,
                            mensaje,
                            teclado_hasar=self.teclado_hasar,
                            remarcar=False,
                            title="Pago encontrado"
                        )
                    except Exception as e:
                        # si el diálogo falla por alguna razón, elegimos esperar el webhook
                        log_error(e, "mostrar_cancelar_continuar")
                        decision = False

                    if decision:
                        self.id_pago = pid
                        try:
                            self.avisar_pago_encontrado("OBTENERPAGOServer", pid)
                        except Exception as e:
                            log_error(e, "avisar_pago_encontrado")
                        return pid
                    else:
                        # Usuario prefirió esperar el webhook => desde ahora
                        # ignoramos OBTENERPAGOServer y seguimos sólo con RESPUESTAPOST
                        solo_resp_post = True

            time.sleep(intervalo_s)



    def buscar_en_resp_post_por_posid(self, pos_id, fecha_creacion_ar: str):
        """
        Devuelve payment_id (columna 'data') o None.
        Requiere date_created TIMESTAMP. Si fuera VARCHAR, cambialo según tu esquema.
        """
        sql = """
            SELECT TOP 1 "data"
            FROM MPQRCODE_RESPUESTAPOST
            WHERE "pos_id" = ?
            AND "date_created" > ?
            ORDER BY "date_created" ASC
        """
        # Si usás TIMESTAMP real en DB: convertir a datetime naive (formato 'YYYY-MM-DD HH:MM:SS.000')
        try:
            dt = datetime.strptime(fecha_creacion_ar, "%Y-%m-%d %H:%M:%S.%f")
            params = (int(pos_id), dt)
        except ValueError:
            # Si no tenés milisegundos en el string ('... %S'), probá sin %f
            dt = datetime.strptime(fecha_creacion_ar, "%Y-%m-%d %H:%M:%S")
            params = (int(pos_id), dt)

        filas = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(sql, params=params, as_dict=True)
        if filas:
            fila = filas[0]
            return fila.get("data") or fila.get("DATA")
        return None


    def buscar_en_obtenerpago_por_external(self, external_reference: str, pos_id=None):
        """
        Devuelve payment_id (columna 'data') o None, buscando por external_reference
        y (opcional) pos_id. SIN parámetros ODBC (evita HY090).
        """
        # usar el parámetro recibido (no self.DICT_DATOS_ORDEN)
        extref_sql = _sql_str(external_reference)
        pos_sql = _sql_literal_auto(pos_id) if pos_id is not None else None

        sql = [
            'SELECT TOP 1 "idPAGO"',
            'FROM PAGOSMERCADOPAGO',
            f'WHERE "external_reference" = {extref_sql}',
        ]
        if pos_sql is not None:
            sql.append(f'AND "idPOS" = {pos_sql}')
        sql.append('ORDER BY "dFechaU" DESC')

        sentencia = "\n".join(sql)

        filas = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(
            sentencia, params=None, as_dict=True
        )
        if filas:
            fila = filas[0]
            return fila.get("data") or fila.get("DATA")
        return None


