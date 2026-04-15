import keyboard
import json
import threading
import time
import traceback
import pytz
import tkinter as tk
import ttkbootstrap as ttk
from datetime import datetime
from pprint import pprint
from tkinter import messagebox
from GUI.BarraProgreso import BarraProgreso
from GUI.BuscarOrdenPago import Ventana_BuscarPagoManual
from GUI.MessageBox import mostrar_error_y_cerrar
from Func.window_position import center_window
from Func.log_errorsV2 import log_error



class CrearOrdenPagoPOINT(BarraProgreso):
    def __init__(self, frame, DICT_WIDGETS, DICT_DATOS_ORDEN, DICT_CONEXION):
        try:
            # Inicializar correctamente la clase base ttk.Progressbar
            super().__init__(frame)
            
            self.error_flags = {
                "focus_in": False,
                "focus_out": False,
                "click_outside": False
            }
            
            #self.mostrar_error = None
            self.NRO_ERROR = None
            self.id_pago = None
            self.datos_dispositivo = None
            self.esperando_pago = True
            self.intencion = None
            self.pago_manual = True
            self.ventana_buscarpagomanual = None
            self.ventana_buscarpagomanual_abierta = False
            self.datos_pagos = None
            self.combination = []
            self.variable_contendora_MensajeERROR = None
            self.Monto_Recargo = 0
            self.Nro_Cuotas = 1
            
            

            
            #------------------------------------------- DICCIONARIOS CON DATOS -------------------------------------------
            self.DICT_WIDGETS = DICT_WIDGETS
            self.DICT_CONEXION = DICT_CONEXION
            self.DICT_DATOS_ORDEN = DICT_DATOS_ORDEN
            self.condicion_teclado = str(self.DICT_CONEXION["conexionDBA"].specify_search_condicion("SPDIR", "ID", "GRID", "teclado_km84", False)).strip().lower() == "true"
            print(f"condicion_teclado: {self.condicion_teclado}")
            if self.condicion_teclado:
                self.teclado_hasar = DICT_CONEXION.get("teclado")
                print(f"teclado_hasar: {self.teclado_hasar}")
                self.teclado_hasar.registrar_combinacion_personalizada("98")
                self.teclado_hasar.asignar_funcion_personalizada("98", self.llamado_taskkill)
            pprint(self.DICT_DATOS_ORDEN)
            
            self.obtener_diccionario_pbs() #AGREGADO 23/04/2025
            
            self.datos_obtener_pago = {
                'NomCaja': self.DICT_DATOS_ORDEN["NomCaja"],
                'NumCajero': self.DICT_DATOS_ORDEN["NumCajero"],
                'NombreCajero': self.DICT_DATOS_ORDEN["NombreCajero"]
            }
            
            self.DICT_PROGRESO = {
                "widgets": DICT_WIDGETS,
                "text_label_aviso": f"Buscando POINT de {self.datos_obtener_pago["NomCaja"]}",
                "carga": 15,
                "command": self.buscar_point
            }
            
            self.progreso(**self.DICT_PROGRESO)
            
            
        except Exception as e:
            log_error(e, "CrearOrdenPago")
            
    def buscar_point(self):
        try:
            # Obtener la lista de dispositivos
            dispositivos_data = self.DICT_CONEXION["conexionAPIPOINT"].obtenerALLPointPOS()
            
            # Verificar si contiene dispositivos
            if "devices" in dispositivos_data:
                dispositivos = dispositivos_data["devices"]
                
                # Buscar si existe un dispositivo con el external_pos_id especificado
                encontrado = False
                for dispositivo in dispositivos:
                    if dispositivo["external_pos_id"] == self.DICT_DATOS_ORDEN["external_id_pos"]:
                        self.datos_dispositivo = dispositivo
                        print(f"Dispositivo encontrado: {dispositivo['external_pos_id']}")
                        encontrado = True
                        break  # Detener la búsqueda al encontrar el dispositivo
                
                # Si no se encuentra ningún dispositivo
                if not encontrado:
                    self.NRO_ERROR = 24
                    self.cierre_ERROR(True)
                else:
                    self.DICT_PROGRESO["text_label_aviso"] = f"Dispositivo {self.datos_dispositivo["id"]} encontrado"
                    self.DICT_PROGRESO["carga"] = 30
                    self.DICT_PROGRESO["command"] = None
                    self.progreso(**self.DICT_PROGRESO)
                    
                    if self.datos_dispositivo["operating_mode"] == "STANDALONE":
                        self.NRO_ERROR = 25
                        self.cierre_ERROR(True)
                    else:
                        self.DICT_PROGRESO["text_label_aviso"] = f"Generando orden para {self.DICT_DATOS_ORDEN["nro_factura"]}"
                        self.DICT_PROGRESO["carga"] = 40
                        self.DICT_PROGRESO["command"] = self.generar_orden_POINT
                        self.progreso(**self.DICT_PROGRESO)
            else:
                self.NRO_ERROR = 24
                self.cierre_ERROR(True)
                #print("No se encontraron dispositivos en los datos proporcionados por la API.")
        
        except Exception as e:
            print(f"Error al buscar el dispositivo: {e}")
            error_traceback = traceback.format_exc()
            print(f"Error al recargar dispositivos: {e}\nTraceback:\n{error_traceback}")
            
            
    def generar_orden_POINT(self):
        try:
            IMPRIME_TICKET = self.pregunta_imprime()
            print(IMPRIME_TICKET)
            reintentos = 3
            intento = 0
            self.respuesta_orden = None

            while intento < reintentos:
                try:
                    self.respuesta_orden = self.DICT_CONEXION["conexionAPIPOINT"].crearIntencionPAGOPoint(
                        self.datos_dispositivo["id"],
                        self.DICT_DATOS_ORDEN["nro_factura"],
                        self.eliminar_decimal(self.DICT_DATOS_ORDEN["monto_pagar"]),
                        IMPRIME_TICKET
                    )
                    if 200 <= self.respuesta_orden.status_code < 300:
                        log_error(f"Orden POINT creada correctamente en el intento #{intento + 1}", "generar_orden_POINT")
                        break
                    else:
                        log_error(f"Error en intento #{intento + 1}: {self.respuesta_orden.status_code} - {self.respuesta_orden.text}", "generar_orden_POINT")
                        intento += 1
                        time.sleep(1.5)
                    print(self.respuesta_orden.status_code)
                except Exception as e:
                    log_error(f"Excepción en intento #{intento + 1}: {str(e)}", "generar_orden_POINT")
                    intento += 1
                    time.sleep(1.5)
            
            if self.respuesta_orden and 200 <= self.respuesta_orden.status_code < 300:
                self.DICT_PROGRESO["text_label_aviso"] = f"Enviando Orden al POINT {self.datos_dispositivo["id"]}"
                self.DICT_PROGRESO["carga"] = 48
                self.DICT_PROGRESO["command"] = None
                self.progreso(**self.DICT_PROGRESO)
                self.DICT_PROGRESO["text_label_aviso"] = f"Orden enviada"
                self.DICT_PROGRESO["carga"] = 49
                self.DICT_PROGRESO["command"] = self.orden_enviada
                self.progreso(**self.DICT_PROGRESO)
            else:
                self.NRO_ERROR = 26
                self.cierre_ERROR(False)
            
        except Exception as e:
            log_error(str(e), "generar_orden_POINT")
            self.NRO_ERROR = 26
            self.cierre_ERROR(False)
            self.DICT_WIDGETS["cerrar_con_taskill"]()
            
            
    def llamado_taskkill(self):
        self.DICT_WIDGETS["cerrar_con_taskill"](self.DICT_DATOS_ORDEN['nro_factura'])

            
    def orden_enviada(self):
        try:
            time.sleep(2)
            log_error("Orden enviada, esperando pago...", "orden_enviada")
            self.DICT_PROGRESO["text_label_aviso"] = "Esperando Pago."
            self.DICT_PROGRESO["carga"] = 50
            self.DICT_PROGRESO["command"] = None
            self.progreso(**self.DICT_PROGRESO)
            self.nro_punto = 2
            if self.condicion_teclado:
                self.teclado_hasar.registrar_combinacion_personalizada("a6")
                self.teclado_hasar.asignar_funcion_personalizada("a6", self.buscar_pago_manual)
                self.teclado_hasar.registrar_combinacion_personalizada("ab")
                self.teclado_hasar.asignar_funcion_personalizada("ab", self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["cerrar_ventana_buscar_pago_manual"])
            else:
                keyboard.add_hotkey('ctrl+alt+s', self.buscar_pago_manual)
            threading.Thread(target=self.buscar_intencion_pago, daemon=True).start()
            while self.esperando_pago and self.pago_manual:
                print(1)
                if self.nro_punto == 1:
                    self.nro_punto += 1
                    self.DICT_WIDGETS["my_label_aviso"].config(text="Esperando Respuesta del POINT.")
                elif self.nro_punto == 2:
                    self.nro_punto += 1
                    self.DICT_WIDGETS["my_label_aviso"].config(text="Esperando Respuesta del POINT..")
                elif self.nro_punto == 3:
                    self.nro_punto = 1
                    self.DICT_WIDGETS["my_label_aviso"].config(text="Esperando Respuesta del POINT...")
                time.sleep(1.50)
            try:    
                self.DICT_WIDGETS["def_ventana_buscar_pago_manual"]["cerrar_ventana_buscar_pago_manual"]()
            except:
                pass
            if not self.NRO_ERROR == None:
                print(self.NRO_ERROR)
                self.cierre_ERROR(True, "Orden Cancelada")
            else:
                if self.pago_manual:
                    self.DICT_PROGRESO["text_label_aviso"] = "Respuesta recibida"
                    self.DICT_PROGRESO["carga"] = 60
                    self.DICT_PROGRESO["command"] = None
                else:
                    self.DICT_PROGRESO["text_label_aviso"] = "El pago manual ha sido encontrado con éxito"
                    self.DICT_PROGRESO["carga"] = 60
                    self.DICT_PROGRESO["command"] = None
                self.progreso(**self.DICT_PROGRESO)
                self.DICT_PROGRESO["text_label_aviso"] = " Procesando el pago."
                self.DICT_PROGRESO["carga"] = 70
                self.DICT_PROGRESO["command"] = self.proceso_pago_mp
                self.progreso(**self.DICT_PROGRESO)
        except Exception as e:
            print(e)
            
    
            
    def buscar_intencion_pago(self):
        intencion_encontrada = True
        while intencion_encontrada and self.pago_manual:
            print(3)
            self.intencion = self.DICT_CONEXION["conexionDBAServer"].obtener_datos_por_id("MPQRCODE_INTENCIONES_POINT", "id", self.respuesta_orden.json()["id"])
            if self.intencion == None:
                pass
            else:
                intencion_encontrada = False
            time.sleep(1)
        pprint(self.intencion)
        if self.pago_manual:
            if self.intencion["state"] == "CANCELED":
                print(self.NRO_ERROR)
                self.NRO_ERROR = 1
            elif self.intencion["state"] == "FINISHED" and not self.intencion["payment"]["id"] == 0:
                self.id_pago = self.intencion["payment"]["id"]
        
        self.esperando_pago = False
                

    def buscar_pago_mp(self):
        try:
            self.datos_pagos = self.DICT_CONEXION["conexionAPIPOINT"].obtenerPAGO(self.id_pago)
            self.DICT_DATOS_ORDEN["respuesta"] = self.datos_pagos
            self.DICT_DATOS_ORDEN["idINTEGRACION"] = 1

            respuesta = self.DICT_CONEXION["conexionAPIPOINT"].obtenerPago_manual(self.DICT_DATOS_ORDEN)

            # Si es un objeto Response → todo bien
            if hasattr(respuesta, "status_code"):  
                pass  # éxito, no haces nada extra
            else:
                # Es un string con error → mostrar
                mostrar_error_y_cerrar(
                    self.DICT_WIDGETS,
                    respuesta,
                    teclado_hasar=self.teclado_hasar,
                    remarcar=False
                )
                self.NRO_ERROR = 1001
            self.esperando_pago = False
        except KeyError as key_error:
            print(f"Error clave faltante: {key_error}")
        except Exception as e:
            error_detallado = traceback.format_exc()
            print(f"Error inesperado: {error_detallado}")
            self.NRO_ERROR = 1  # Incrementar el número de errores
        finally:
            # Limpiar cualquier recurso o conexión si es necesario
            print("Finalizando el método 'buscar_pago_mp'.")
            
            
    def buscar_pago_manual(self):
        log_error("Ventana de búsqueda de pago manual abierta por el usuario.", "buscar_pago_manual")
        if self.ventana_buscarpagomanual_abierta  == False:
            self.ventana_buscarpagomanual_abierta  = True
            ventana_buscarpagomanual = Ventana_BuscarPagoManual(self.DICT_WIDGETS, self.DICT_DATOS_ORDEN, self.DICT_CONEXION)
            threading.Thread(target=self.esperar_respuesta_mp, args=(ventana_buscarpagomanual, ), daemon=True).start()
        else:
            print("TATATA")
        
    def esperar_respuesta_mp(self, ventana_buscarpagomanual):
        while ventana_buscarpagomanual.return_respuesta_mp() == None:
            print(ventana_buscarpagomanual.return_respuesta_mp())
            time.sleep(1)
        print(ventana_buscarpagomanual.return_respuesta_mp())
        if not ventana_buscarpagomanual.return_respuesta_mp() == False:
            if ventana_buscarpagomanual.return_respuesta_mp() == "CERRANDO":
                self.ventana_buscarpagomanual_abierta = False
                return
            else:
                self.datos_pagos = ventana_buscarpagomanual.return_respuesta_mp()
        else:
            self.NRO_ERROR = 101
        self.esperando_pago = False
        self.pago_manual = False

    

    def convertir_a_json(self, cadena_json):
        """
        Convierte un string JSON almacenado en un formato de texto a un diccionario de Python.
        
        Parámetros:
            cadena_json (str): El string que contiene el JSON.
        
        Retorno:
            dict: El contenido del string como un diccionario.
        """
        try:
            # Intentar cargar el string como JSON
            resultado = json.loads(cadena_json)
            return resultado
        except json.JSONDecodeError as e:
            print(f"Error al convertir el string a JSON: {e}")
            return None
        
    def proceso_pago_mp(self):
        self.esperando_pago = True
        self.nro_punto = 2
        self.DICT_PROGRESO["command"] = None
        if self.pago_manual:
            threading.Thread(target=self.buscar_pago_mp, daemon=True).start()
            while self.esperando_pago:
                print(5)
                if self.nro_punto == 1:
                    self.nro_punto += 1
                    self.DICT_WIDGETS["my_label_aviso"].config(text="Buscando Pago.")
                elif self.nro_punto == 2:
                    self.nro_punto += 1
                    self.DICT_WIDGETS["my_label_aviso"].config(text="Buscando Pago..")
                elif self.nro_punto == 3:
                    self.nro_punto = 1
                    self.DICT_WIDGETS["my_label_aviso"].config(text="Buscando Pago...")
                time.sleep(1.50)
        self.esperando_pago = True
        threading.Thread(target=self.resultado_estado_pago, daemon=True).start()
        while self.esperando_pago:
            print(2)
            if self.nro_punto == 1:
                self.nro_punto += 1
                self.DICT_WIDGETS["my_label_aviso"].config(text="Procesando el pago.")
            elif self.nro_punto == 2:
                self.nro_punto += 1
                self.DICT_WIDGETS["my_label_aviso"].config(text="Procesando el pago..")
            elif self.nro_punto == 3:
                self.nro_punto = 1
                self.DICT_WIDGETS["my_label_aviso"].config(text="Procesando el pago...")
            time.sleep(1.50)
        self.progreso(**self.DICT_PROGRESO)
        
        
    def resultado_estado_pago(self):
        try:
            self.datos_pagos = self.datos_pagos.json()
            self.id_pago = self.datos_pagos["id"]
            """if self.datos_pagos["external_reference"] != self.DICT_DATOS_ORDEN["nro_factura"]:
                print("#BUSCA SI COINCIDEN LOS NÚMEROS DE FACTURAS")
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
                        "Si desea continuar, ingrese la clave de supervisor."
                    )

                    self.variable_contendora_MensajeERROR = mostrar_error_y_cerrar(
                        self.DICT_WIDGETS,
                        mensaje,
                        teclado_hasar=self.teclado_hasar,
                        type_msg="warning",
                        remarcar=True
                    )

                    # Activar modo supervisor para permitir continuar luego
                    self.esperando_comparacion = True
                    self.reintentarpago = False
                    return"""
                
            if self.datos_pagos["transaction_amount"] != self.DICT_DATOS_ORDEN["monto_pagar"]:
                self.NRO_ERROR = 10
            elif self.datos_pagos["status"] == "refunded":
                self.NRO_ERROR = 12
            if int(self.DICT_DATOS_ORDEN["response"]) == 98:
                print("PAGO PBS")
                if self.comprobación_PBS():  # <-- Si coincide, OMITIR devolución
                    print("Método PBS válido, continuar sin reembolso.")
                else:
                    if not self.NRO_ERROR == 1001:
                        self.NRO_ERROR = 15
                        mostrar_error_y_cerrar(self.DICT_WIDGETS, f"Error {self.NRO_ERROR}\n{self.LISTADO_ERRORES()}", teclado_hasar=self.teclado_hasar, remarcar=True)
                        self.NRO_ERROR = 17
                        mostrar_error_y_cerrar(self.DICT_WIDGETS, f"Error {self.NRO_ERROR}\n{self.LISTADO_ERRORES()}", teclado_hasar=self.teclado_hasar, remarcar=True)
                    return
            print(self.NRO_ERROR)
            if self.NRO_ERROR == None:
                if self.datos_pagos["status"] == "approved":
                    if self.datos_pagos["status_detail"] == "accredited":
                        self.DICT_PROGRESO["text_label_aviso"] = "¡¡¡Pago Exitoso!!!"
                        self.DICT_PROGRESO["carga"] = 99
                        self.DICT_PROGRESO["command"] = self.finalizar_pago                    
                elif self.datos_pagos["status"] == "rejected" or self.datos_pagos["status"] == 'cancelled':
                    self.NRO_ERROR = "ERROR_TARJETA"
                    self.DICT_PROGRESO["text_label_aviso"] = "Error en el pago"
                    self.DICT_PROGRESO["carga"] = 99
                    self.DICT_PROGRESO["command"] = self.error_pago
                else:
                    print(self.datos_pagos["status"], self.datos_pagos["status"])
            else:
                self.DICT_PROGRESO["text_label_aviso"] = "Error en el pago"
                self.DICT_PROGRESO["carga"] = 99
                self.DICT_PROGRESO["command"] = self.error_pago
                
            self.esperando_pago = False
        except Exception as e:
            print(e)
            
            
    def error_pago(self):
        self.cierre_ERROR(True, "Error en el pago")

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

                # 👇 NUEVOS CÓDIGOS
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
                return [100, "Error no registrado"]
        except Exception as e:
            # Captura el traceback completo y lo registra
            error_detallado = traceback.format_exc()
            print(label_error, error_detallado)
            log_error(error_detallado, "ERROR_API")  # Registro del error completo

        
    def pregunta_imprime(self):
        try: 
            print_TICKET = self.DICT_CONEXION["conexionDBA"].specify_search_condicion("SPDIR", "ID", "GRID", "MP_POINT_PRINT", False)
            if not print_TICKET == None:
                print_TICKET.lower()
                if print_TICKET == "auto":
                    return messagebox.askyesno("Imprime ticket", "¿Desea imprimir comprobante de pago?")
                else:
                    if print_TICKET == "false":
                        return False
                    elif print_TICKET == "true":
                        return True
            else:
                return messagebox.askyesno("Imprime ticket", "¿Desea imprimir comprobante de pago?")
        except Exception as e:
            print(e)
            return messagebox.askyesno("Imprime ticket", "¿Desea imprimir comprobante de pago?")
        
    def eliminar_decimal(self, numero):
        """
        Elimina el punto decimal de un número y devuelve un entero considerando siempre dos decimales.
        
        Args:
            numero (float): Número con decimal a procesar.
        
        Returns:
            int: Número convertido a entero sin punto decimal, garantizando dos decimales.
        """
        # Asegurar que el número tiene exactamente dos decimales
        numero_str = f"{numero:.2f}"  # Formatear a 2 decimales
        partes = numero_str.split(".")  # Dividir en parte entera y decimal

        # Concatenar las partes y convertirlas a entero
        return int(partes[0] + partes[1])

            
    def cierre_ERROR(self, paso_M, label_error=None ):
        print("cierre_ERROR")
        self.DICT_WIDGETS["ventana_tamano_400_550"]()
        if label_error == None:
            self.DICT_PROGRESO["text_label_aviso"] = "ERROR"
        else:
            self.DICT_PROGRESO["text_label_aviso"] = label_error
        self.DICT_PROGRESO["carga"] = 99
        self.DICT_PROGRESO["command"] = self.mostrar_error
        self.progreso(**self.DICT_PROGRESO)
        time.sleep(1)
        if paso_M:
            self.cerrar_ventana()
        self.DICT_CONEXION["conexionDBA"].desconectar()
        self.DICT_CONEXION["conexionDBAServer"].desconectar()
            
    def mostrar_error(self):
        print("mostrar_error")
        mostrar_error_y_cerrar(self.DICT_WIDGETS, f"Error {self.NRO_ERROR}\n{self.LISTADO_ERRORES()}", teclado_hasar=self.teclado_hasar, remarcar=True)
        self.DICT_CONEXION["conexionDBA"].actualizar_datos_condicion(
            "MPQRCODE_CONEXIONPROGRAMAS",
            self.datos_error,
            "nro_factura",
            f"'{self.DICT_DATOS_ORDEN['nro_factura']}'"  # Cambiado a comillas simples internas
        )
        
    def finalizar_pago(self):
        try:
            pagos_disponibles = self.DICT_CONEXION["conexionAPIPOINT"].obtenerTodosMediosPagos()
            name_tarjeta_encontrada = None
            for pagos in pagos_disponibles.json():
                if pagos["id"] == self.datos_pagos["payment_method_id"]:
                    name_tarjeta_encontrada = f"MP {pagos['name']}"
                    
            self.calcular_recargo_y_cuotas()
                    
            datos = {
                'status': 1,
                'response': 0,
                'description': 'accredited',
                'IDMercadoPago': self.id_pago,
                'card_first_six_digits':self.datos_pagos['card']["first_six_digits"],
                'card_last_four_digits':self.datos_pagos['card']["last_four_digits"],
                'payment_method_id':self.datos_pagos['payment_method_id'],
                'payment_method_name':name_tarjeta_encontrada,
                'payment_type_id':self.datos_pagos['payment_type_id'],
                'Monto_Recargo': self.Monto_Recargo,
                'Nro_Cuotas': self.Nro_Cuotas
            }            
            #messagebox.showinfo("Pago recibido", f"Pago recibido\nNro Factura: {self.DICT_DATOS_ORDEN["nro_factura"]}\nNro Operación: {self.datos_pagos["id"]}\nMonto recibido: {float(self.datos_pagos["transaction_amount"])}")
            self.DICT_WIDGETS["my_label_aviso"].config(text="Pago recibido")
            self.DICT_CONEXION["conexionDBA"].actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMAS", datos, "nro_factura", f"'{self.DICT_DATOS_ORDEN["nro_factura"]}'")
            #guardar_json_respuesta(self.datos_pagos)
            log_error("Pago recibido correctamente, cerrando ventana.", "finalizar_pago")
            self.cerrar_ventana()
                
        except Exception as e:
            log_error(str(e), "finalizar_pago")
            
    def estado_de_la_intencion_API(self):
        respuesta = self.DICT_CONEXION["conexionAPIPOINT"].buscarIntencionPAGOPoint(self.respuesta_orden["id"]).json()
        print(respuesta)
        
        if respuesta["state"] == "CANCELED" or respuesta["state"] == "FINISHED":
            return True
        else:
            return False
        
        
        
        
    def LISTADO_ERRORES(self):
        try:
            Monto_recibido = None  # Inicializar la variable antes del if

            if self.NRO_ERROR != "ERROR_TARJETA":
                if self.NRO_ERROR != 1:
                    if self.datos_pagos is not None and "transaction_amount" in self.datos_pagos:
                        Monto_recibido = self.datos_pagos["transaction_amount"]
                else:
                    Monto_recibido = 0

                if Monto_recibido is not None:
                    Monto_recibido = float(Monto_recibido)
                else:
                    Monto_recibido = 0

                # Verificaciones antes de usar self.datos_dispositivo y self.datos_obtener_pago
                dispositivo_id = self.datos_dispositivo["id"] if self.datos_dispositivo and "id" in self.datos_dispositivo else "DESCONOCIDO"
                nom_caja = self.datos_obtener_pago["NomCaja"] if self.datos_obtener_pago and "NomCaja" in self.datos_obtener_pago else "DESCONOCIDO"

                DICT_ERRORES = {
                    1: "Orden Cancelada desde el POINT",
                    10: (
                        "El monto esperado no es el mismo recibido en MercadoPago\n"
                        f"Monto esperado: *(${self.DICT_DATOS_ORDEN['monto_pagar']}{{green}})*\n"
                        f"Monto recibido: *(${Monto_recibido}{{red}})*"
                    ),
                    11: f"El ID *({self.id_pago}{{red}})* no coincide",
                    12:  f"El ID *({self.id_pago}{{red}})* ya tiene una devolución hecha",
                    13: "El Número de factura no coincide con el ID Obtenido",
                    15: (
                        "Este medio de pago no está disponible para realizar el descuento del PBS.\n"
                        f"Medios Disponibles: {list(self.dict_pbs_disponibles.keys())}"
                    ),
                    16: f"No se pudo realizar el reembolso del ID {self.id_pago}\n Por favor, verificar con el supervisor si se necesita más información sobre el reembolso.",  #AGREGADO 23/04/2025
                    17: "Realizar reeembolso desde el dispositivo de pago",
                    21: "El pago no está aprobado",
                    23: "No hemos recibido respuesta de MercadoPago",
                    24: f"No hay dispositivos vinculados con la caja {nom_caja}.",
                    25: f"El dispositivo {dispositivo_id} no está habilitado como PDV",
                    26: f"El dispositivo {dispositivo_id} ya se encuentra con una orden. Cancelar y volver a enviar orden.",
                    100: "Error a la hora de buscar pago manual",
                    101: "Error en la búsqueda en MercadoPago",
                    1001: "Error no registrado",
                }

                self.datos_error = {
                    'status': 0,
                    'response': self.NRO_ERROR,
                    'description': DICT_ERRORES[self.NRO_ERROR]
                }
                print(DICT_ERRORES[self.NRO_ERROR])
                return DICT_ERRORES[self.NRO_ERROR]

            else:
                error_tarjeta_traducido = self.ERROR_API(self.datos_pagos["status_detail"]) if self.datos_pagos and "status_detail" in self.datos_pagos else ("ERROR", "Error desconocido")
                self.datos_error = {
                    'status': 0,
                    'response': error_tarjeta_traducido[0],
                    'description': error_tarjeta_traducido[1]
                }
                print(self.datos_error)
                return error_tarjeta_traducido[1]

        except Exception as e:
            # Captura el traceback completo y lo registra
            error_detallado = traceback.format_exc()
            print(self.NRO_ERROR, error_detallado)
            log_error(error_detallado, "LISTADO_ERRORES")  # Registro del error completo
            self.datos_error = {
                'status': 0,
                'response': 1000,
                'description': "¡¡¡CRITICO!!!"
            }
            
    def cerrar_ventana(self): #RECUERDA QUE EN BUSCARORDENPAGO TAMBIEN HAY QUE CAMBIAR
        if not self.pago_manual:
            mostrar_error_y_cerrar(self.DICT_WIDGETS, "¡¡¡RECORDATORIO!!!\nRECUERDA CANCELAR LA ORDEN EN EL POINT YA QUE HAS USADO EL METODO PARA ID MANUAL", teclado_hasar=self.teclado_hasar, type_msg="warning")
            #CustomMessageBox(self.DICT_WIDGETS["root"], "IMPORTANTE", "¡¡¡RECORDATORIO!!!\nRECUERDA CANCELAR LA ORDEN EN EL POINT YA QUE HAS USADO EL METODO PARA ID MANUAL", "warning", teclado_hasar=self.teclado_hasar)
            #messagebox.showwarning("IMPORTANTE", "¡¡¡RECORDATORIO!!!\nRECUERDA CANCELAR LA ORDEN EN EL POINT YA QUE HAS USADO EL METODO PARA ID MANUAL")
        self.DICT_WIDGETS["cerrar_ventana"]()
                
                
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
        
    def comprobación_PBS(self): #AGREGADO 23/04/2025
        try:
            # Verifica si el método y tipo de pago están en alguno de los valores del diccionario
            encontrados = any(
                self.datos_pagos["payment_method_id"] == datos["payment_method_id"] and
                self.datos_pagos["payment_type_id"] == datos["payment_type_id"]
                for datos in self.dict_pbs_disponibles.values()
            )
            print(f"encontrados: {encontrados}")

            if not encontrados:
                return False
            return True

        except Exception as e:
            self.NRO_ERROR = 1001
            mostrar_error_y_cerrar(self.DICT_WIDGETS, f"Ocurrió un error inesperado: {e}", teclado_hasar=self.teclado_hasar)
            return False
        
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