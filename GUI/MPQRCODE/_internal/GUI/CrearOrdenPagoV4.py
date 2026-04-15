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
    
def _get_val_case_insensitive(row: dict, *candidates):
    """Devuelve el valor del primer nombre de columna que exista (case-insensitive)."""
    if not isinstance(row, dict):
        return None
    low = {k.lower(): v for k, v in row.items()}
    for c in candidates:
        v = low.get(c.lower())
        if v is not None:
            return v
    return None



print("Clase: CrearOrdenPagoV4")

class CrearOrdenPago(BarraProgreso):
    def __init__(self, frame, DICT_WIDGETS, DICT_DATOS_ORDEN, DICT_CONEXION):
        try:
        
            # Inicializar correctamente la clase base ttk.Progressbar
            super().__init__(frame)
            
            #---------------------------------------- VARIABLES INICIADORAS ----------------------------------------
            self.crearorden = True
            self.orden_creada = False
            self.id_pago = None
            self.id_order = None
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
            self.Monto_Recargo = 0
            self.Nro_Cuotas = 1
            
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
                    self.qr_data = self.DICT_CONEXION["conexionAPI"].QR_Crear_order(self.DICT_DATOS_ORDEN)
                    print(self.qr_data, self.qr_data.status_code, type(self.qr_data.status_code))
                    pprint(self.qr_data.json())
                    if self.qr_data is not None and self.qr_data.status_code < 300:
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

            if self.qr_data is not None and self.qr_data.status_code < 300:
                self.fecha_orden_creada_ar = now_ar_str_ms()

                data_qr = self.qr_data.json()['type_response']['qr_data']
                self.id_order = self.qr_data.json()['id']
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

            # 🔹 Iniciar ambos hilos: DBA + API (polling de orden)
            threading.Thread(target=self.buscar_pago, daemon=True).start()

            self.nro_punto = 1
            self.cronometro.start_cronometro()
            self.DICT_WIDGETS["boton_cancelar"].config(command=self.aviso_cancelar_orden, state=tk.NORMAL)
            self.pago_capturado = None

            if self.condicion_teclado:
                self.teclado_hasar.registrar_combinacion_personalizada("a6")
                self.teclado_hasar.asignar_funcion_personalizada("a6", self.buscar_pago_manual)
                self.teclado_hasar.registrar_combinacion_personalizada("a7")
                self.teclado_hasar.asignar_funcion_personalizada("a7", self.cancelar_orden)
                self.teclado_hasar.registrar_combinacion_personalizada("ab")
                self.teclado_hasar.asignar_funcion_personalizada(
                    "ab",
                    self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["cerrar_ventana_buscar_pago_manual"]
                )
            else:
                keyboard.add_hotkey('ctrl+alt+s', self.buscar_pago_manual)

            # 🔹 Loop visual "Esperando Pago..."
            nro_factura = self.DICT_DATOS_ORDEN.get('nro_factura', '')
            while self.pago_capturado is None and self.DICT_PROGRESO.get("text_label_aviso") != "Cancelando Orden":
                if self.nro_punto == 1:
                    self.nro_punto += 1
                    self.DICT_WIDGETS["my_label_aviso"].config(text="Esperando Pago.")
                    print(f"Esperando Pago. {nro_factura}")
                elif self.nro_punto == 2:
                    self.nro_punto += 1
                    self.DICT_WIDGETS["my_label_aviso"].config(text="Esperando Pago..")
                    print(f"Esperando Pago.. {nro_factura}")
                elif self.nro_punto == 3:
                    self.nro_punto = 1
                    self.DICT_WIDGETS["my_label_aviso"].config(text="Esperando Pago...")
                    print(f"Esperando Pago... {nro_factura}")
                time.sleep(1)

            # 🔹 Post-Esperar
            if self.DICT_PROGRESO.get("text_label_aviso") != "Cancelando Orden":
                self.cerrar_cronometro()
                self.DICT_WIDGETS["ventana_tamano_400_550"]()

                self.DICT_PROGRESO["text_label_aviso"] = "Notificación Recibida"
                self.DICT_PROGRESO["carga"] = 51
                self.DICT_PROGRESO["command"] = None
                self.progreso(**self.DICT_PROGRESO)
                time.sleep(1)
                self.DICT_WIDGETS["label_cronometro"].pack_forget()

                if self.id_pago is not None:
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

                threading.Thread(target=self.realizar_comparacion, daemon=True).start()
                self.progreso(**self.DICT_PROGRESO)

                while not self.esperando_comparacion:
                    time.sleep(1)
                    print("Esperando Comparación")

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
            
    def buscar_pago(self):
        try:
            # Asegurar timestamp de creación (zona AR, milisegundos)
            if not getattr(self, "fecha_orden_creada_ar", None):
                self.fecha_orden_creada_ar = now_ar_str_ms()

            # Tomar claves de búsqueda
            external_reference = self.DICT_DATOS_ORDEN.get("nro_factura")

            pago_id = self.esperar_payment_id(
                idorder=self.id_order,
                fecha_creacion_ar=self.fecha_orden_creada_ar,
                external_reference=external_reference,
                timeout_s=180,
                intervalo_s=1.0
            )
            print(f"PAGO ENCONTRADO: {pago_id}")

            if pago_id:
                print("Buscando info de pago...")
                # Si todavía querés traer el detalle desde tu API/MP, dejá estas dos:
                self.buscar_pago_en_MP()
                self.DICT_CONEXION["conexionAPI"].obtenerPago_manual(self.DICT_DATOS_ORDEN)

                self.pago_capturado = True
                return
            else:
                # manejar timeout / cancelación
                return

        except Exception as e:
            log_error(e, "buscar_pago_en_dba")
            
            
    def poll_order_status_api(self, intervalo_s: int = 5, timeout_s: int = 180):
        """
        - SOLO fija self.id_pago cuando la operación está aprobada
        y hay transactions.payments[0].reference_id (o reference.id).
        - Si orden = cancelled/expired => reintentarpago=False y sale.
        - Al fijar self.id_pago, marcamos self.pago_capturado=True para que continúe el flujo.
        """
        try:
            id_order = getattr(self, "idorder", None) or getattr(self, "id_order", None)
            if not id_order:
                log_error("poll_order_status_api: idORDER ausente.", "poll_order_status_api")
                return

            t0 = time.time()
            while True:
                # Cortes
                if self.pago_capturado is True:
                    return
                if self.DICT_PROGRESO.get("text_label_aviso") == "Cancelando Orden" or getattr(self, "PAGO_MANUAL", False):
                    return
                if time.time() - t0 > timeout_s:
                    return

                try:
                    resp = self.DICT_CONEXION["conexionAPI"].QR_Obtener_order_por_ID(id_order)
                    try:
                        data = resp.json() if hasattr(resp, "json") else resp
                    except Exception:
                        data = resp
                    if not isinstance(data, dict):
                        data = {}

                    # Estado de la ORDEN (nivel raíz)
                    status_orden  = (data.get("status") or "").lower()             # p.ej. 'processed'
                    detail_orden  = (data.get("status_detail") or "").lower()      # p.ej. 'accredited'
                    external_ref  = data.get("external_reference")
                    total_amount  = data.get("total_amount")

                    # Primer pago (si viene)
                    payments = data.get("transactions", {}).get("payments", [])
                    p0 = payments[0] if isinstance(payments, list) and payments else {}
                    pay_status     = (p0.get("status") or "").lower()              # p.ej. 'processed'
                    pay_detail     = (p0.get("status_detail") or "").lower()       # p.ej. 'accredited'

                    # 👇 ID de referencia del pago (dos variantes posibles)
                    ref_id = (
                        p0.get("reference_id")
                        or (p0.get("reference", {}) or {}).get("id")
                        or (p0.get("referenceId"))  # por si viniera en camelCase
                    )

                    print(f"[QR][API] idORDER={id_order} ord={status_orden}/{detail_orden} "
                        f"pay={pay_status}/{pay_detail} ref_id={ref_id} "
                        f"ext_ref={external_ref} total={total_amount}")

                    # Estados terminales negativos -> cortar
                    if status_orden in ("cancelled", "expired"):
                        self.reintentarpago = False
                        self.DICT_PROGRESO["text_label_aviso"] = f"Orden {status_orden}"
                        return

                    # ¿Aprobado?
                    aprobado = (
                        status_orden in ("processed", "approved")
                        or detail_orden == "accredited"
                        or pay_status in ("processed", "approved")
                        or pay_detail == "accredited"
                    )

                    # ✅ Solo si aprobado y tenemos ref_id -> fijar id_pago y salir del loop de espera
                    if aprobado and ref_id:
                        self.id_pago = ref_id                 # ej. "124804376703"
                        self.pago_capturado = True            # rompe el while de func_orden_creada
                        # (Opcional) si querés disparar comparación inmediata desde el hilo principal:
                        # self.root.after(0, lambda: threading.Thread(target=self.realizar_comparacion, daemon=True).start())
                        return

                    # Si no está aprobado todavía -> seguir polling

                except Exception as e_call:
                    log_error(e_call, "poll_order_status_api: llamada/parsing API")

                time.sleep(intervalo_s)

        except Exception as e:
            log_error(e, "poll_order_status_api")



            
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
                self.calcular_recargo_y_cuotas()
                
                
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
            self.DICT_CONEXION["conexionAPI"].QR_Cancelar_order_por_ID(self.id_order)
            self.cerrar_cronometro()
            self.cierre_ERROR(True, "Cancelando Orden")
        except Exception as e:
            log_error(str(e), "cancelar_orden")
            messagebox.showerror("Error", "Ha ocurrido un error al cancelar la orden.")
            
    def cancelar_orden_pasado_segundos(self):
        try:
            self.DICT_CONEXION["conexionAPI"].QR_Cancelar_order_por_ID(self.id_order)
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
                'Monto_Recargo': self.Monto_Recargo,
                'Nro_Cuotas': self.Nro_Cuotas
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

    def esperar_payment_id(
        self,
        idorder: str,
        fecha_creacion_ar: str,
        external_reference: str,
        timeout_s: int = 180,
        intervalo_s: float = 1.0,
    ):
        """
        Polling que busca el payment_id consultando:
        - MPQRCODE_RESPUESTAQR (webhook QR) por (idORDER o external_reference) y dFechaU >= fecha_creacion_ar
        - PAGOSMERCADOPAGO por external_reference
        - API de Órdenes (cada 5s): si aprobado, toma transactions.payments[0].reference_id (o reference.id)

        Corta por:
        * self.id_pago presente
        * cancelación del usuario
        * timeout
        * orden cancelada/expirada (API)
        """
        import time

        t0 = time.time()
        solo_qr = False  # si el usuario decide esperar solo webhook
        ultimo_ping_api = 0.0
        api_intervalo = 5.0  # ← cada 5s consultamos la API

        while True:
            # 0) Cortes globales
            if getattr(self, "id_pago", None):
                return self.id_pago
            if self.DICT_PROGRESO.get("text_label_aviso") == "Cancelando Orden" or getattr(self, "PAGO_MANUAL", False):
                return None
            if time.time() - t0 > timeout_s:
                return None

            # 1) RESPUESTAQR (webhook persistido)
            try:
                pid = self.buscar_en_respuestaqr(
                    idorder=idorder,
                    external_reference=external_reference,
                    fecha_creacion_ar=fecha_creacion_ar
                )
                # print(f"[DEBUG] RESPUESTAQR -> {pid}")
            except Exception:
                pid = None

            if pid:
                self.id_pago = pid
                try:
                    self.avisar_pago_encontrado("RESPUESTAQR", pid)
                except Exception as e:
                    log_error(e, "avisar_pago_encontrado")
                return pid

            # 2) PAGOSMERCADOPAGO (si no forzamos esperar webhook)
            if not solo_qr and getattr(self, "reintentarpago", None) is None:
                try:
                    pid = self.buscar_en_obtenerpago_por_external(external_reference)
                    # print(f"[DEBUG] PAGOSMERCADOPAGO -> {pid}")
                except Exception:
                    pid = None

                if pid:
                    # Preguntar si continuar con ese pago ya consolidado
                    try:
                        mensaje = (
                            f"Se encontró un cobro asociado a la factura {external_reference}.\n\n"
                            f"ID de pago: {pid}\n\n"
                            "¿Desea continuar con este pago ya registrado?"
                        )
                        decision = mostrar_cancelar_continuar(
                            self.DICT_WIDGETS, mensaje,
                            teclado_hasar=self.teclado_hasar, remarcar=False, title="Pago encontrado"
                        )
                    except Exception as e:
                        log_error(e, "mostrar_cancelar_continuar")
                        decision = False

                    if decision:
                        self.id_pago = pid
                        try:
                            self.avisar_pago_encontrado("PAGOSMERCADOPAGO", pid)
                        except Exception as e:
                            log_error(e, "avisar_pago_encontrado")
                        return pid
                    else:
                        solo_qr = True  # desde ahora ignoramos PAGOSMERCADOPAGO

            # 3) API Órdenes (cada 5s): si Aprobado → tomar reference_id
            ahora = time.time()
            if (ahora - ultimo_ping_api) >= api_intervalo:
                ultimo_ping_api = ahora
                try:
                    resp = self.DICT_CONEXION["conexionAPI"].QR_Obtener_order_por_ID(self.id_order)
                    try:
                        data = resp.json() if hasattr(resp, "json") else resp
                    except Exception:
                        data = resp
                    if not isinstance(data, dict):
                        data = {}

                    status_orden  = (data.get("status") or "").lower()
                    detail_orden  = (data.get("status_detail") or "").lower()

                    # terminales negativos
                    if status_orden in ("cancelled", "expired"):
                        self.reintentarpago = False
                        self.DICT_PROGRESO["text_label_aviso"] = f"Orden {status_orden}"
                        return None

                    # aprobado (orden o pago)
                    payments = data.get("transactions", {}).get("payments", [])
                    p0 = payments[0] if isinstance(payments, list) and payments else {}
                    pay_status     = (p0.get("status") or "").lower()
                    pay_detail     = (p0.get("status_detail") or "").lower()

                    aprobado = (
                        status_orden in ("processed", "approved")
                        or detail_orden == "accredited"
                        or pay_status in ("processed", "approved")
                        or pay_detail == "accredited"
                    )

                    if aprobado:
                        ref_id = (
                            p0.get("reference_id")
                            or (p0.get("reference", {}) or {}).get("id")
                            or p0.get("referenceId")
                        )
                        if ref_id:
                            self.id_pago = ref_id
                            try:
                                self.avisar_pago_encontrado("API", ref_id)
                            except Exception as e:
                                log_error(e, "avisar_pago_encontrado")
                            return ref_id
                except Exception as e_api:
                    log_error(e_api, "esperar_payment_id: API Órdenes")

            time.sleep(intervalo_s)






    def buscar_en_respuestaqr(self, idorder: str, external_reference: str, fecha_creacion_ar: str):
        idorder_sql = _sql_literal_auto(idorder) if idorder is not None else None
        extref_sql = _sql_str(external_reference) if external_reference is not None else None
        fecha_sql = _sql_str(fecha_creacion_ar)

        where_parts, id_or_ext = [], []
        if idorder_sql is not None:
            id_or_ext.append(f'"idORDER" = {idorder_sql}')
        if extref_sql is not None:
            id_or_ext.append(f'"external_reference" = {extref_sql}')
        if not id_or_ext:
            return None

        where_parts.append("(" + " OR ".join(id_or_ext) + ")")
        where_parts.append(f'"dFechaU" >= {fecha_sql}')

        sentencia = (
            'SELECT TOP 1 "idPAGO" '
            'FROM "DBA"."MPQRCODE_RESPUESTAQR" '
            f'WHERE {" AND ".join(where_parts)} '
            'ORDER BY "dFechaU" DESC'
        )

        filas = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(sentencia, params=None, as_dict=True)
        # print(f"[DEBUG RESPUESTAQR] filas={filas}")  # <- descomentar si necesitás ver claves

        if filas:
            return _get_val_case_insensitive(filas[0], "idPAGO", "idpago", "IDPAGO", "id_pago")
        return None




    def buscar_en_obtenerpago_por_external(self, external_reference: str):
        extref_sql = _sql_str(external_reference) if external_reference is not None else None
        if extref_sql is None:
            return None

        sentencia = (
            'SELECT TOP 1 "idPAGO" '
            'FROM "DBA"."PAGOSMERCADOPAGO" '
            f'WHERE ("external_reference" = {extref_sql}) '
            'ORDER BY "dFechaU" DESC'
        )

        filas = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(sentencia, params=None, as_dict=True)
        # print(f"[DEBUG PAGOSMERCADOPAGO] filas={filas}")  # <- descomentar para ver claves

        if filas:
            return _get_val_case_insensitive(filas[0], "idPAGO", "idpago", "IDPAGO", "id_pago")
        return None
    
    def calcular_recargo_y_cuotas(self):
        """
        Extrae de self.datos_pagos:
        - El recargo al cliente (fee_details con fee_payer == "payer")
        - El número de cuotas (installments)
        Si algo falla, deja los valores iniciales.
        """
        try:
            # --- Recargo del cliente ---
            fee_details = self.datos_pagos.get("fee_details", [])
            if isinstance(fee_details, list):
                for fee in fee_details:
                    if fee.get("fee_payer") == "payer" and fee.get("type") == "financing_fee":
                        self.Monto_Recargo = float(fee.get("amount", 0))
                        break  # solo el primero relevante
            # --- Número de cuotas ---
            self.Nro_Cuotas = int(self.datos_pagos.get("installments", self.Nro_Cuotas))
        except Exception as e:
            log_error(f"Error en calcular_recargo_y_cuotas: {str(e)}")
            # se mantienen los valores iniciales




