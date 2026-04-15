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
            self.ID_PAGO = None
            self.pago_manual = True
            self.ventana_buscarpagomanual = None
            self.ventana_buscarpagomanual_abierta = False
            self.datos_pagos = None
            self.combination = []
            self.variable_contendora_MensajeERROR = None
            
            self.cierre_supervisor = False
            self.cierre_supervisor_autorizante = None
            self.cierre_supervisor_detalle = None
            

            
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
                self.teclado_hasar.registrar_combinacion_personalizada("49")
                self.teclado_hasar.asignar_funcion_personalizada("49", self.activar_modo_supervisor)
            pprint(self.DICT_DATOS_ORDEN)
            
            self.obtener_diccionario_pbs() #AGREGADO 23/04/2025
            
            self.datos_obtener_pago = {
                'NomCaja': self.DICT_DATOS_ORDEN["NomCaja"],
                'NumCajero': self.DICT_DATOS_ORDEN["NumCajero"],
                'NombreCajero': self.DICT_DATOS_ORDEN["NombreCajero"],
                'cierre_supervisor': self.cierre_supervisor,
                'cierre_supervisor_autorizante': self.cierre_supervisor_autorizante,
                'cierre_supervisor_detalle': self.cierre_supervisor_detalle
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
            intencion = self.DICT_CONEXION["conexionDBAServer"].obtener_datos_por_id("MPQRCODE_INTENCIONES_POINT", "id", self.respuesta_orden.json()["id"])
            if intencion == None:
                pass
            else:
                intencion_encontrada = False
            time.sleep(1)
        pprint(intencion)
        if self.pago_manual:
            if intencion["state"] == "CANCELED":
                print(self.NRO_ERROR)
                self.NRO_ERROR = 1
            elif intencion["state"] == "FINISHED" and not intencion["payment"]["id"] == 0:
                print("hola2")
                self.id_pago = intencion["payment"]["id"]
        
        self.esperando_pago = False
                

    def buscar_pago_mp(self):
        try:
            pago_encontrado = True
            while pago_encontrado:
                print(4)
                self.datos_pagos = self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion("MPQRCODE_OBTENERPAGOPOINTServer", "datos_pago", "external_reference", f'{self.DICT_DATOS_ORDEN['nro_factura']}', False)
                if self.datos_pagos == None:
                    pass
                else:
                    pago_encontrado = False
                time.sleep(1)
                
            
            self.datos_pagos = self.convertir_a_json(self.datos_pagos)
            pprint(self.datos_pagos)
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
                self.datos_pagos = self.datos_pagos.json()
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
        if self.pago_manual:
            threading.Thread(target=self.buscar_pago_mp, daemon=True).start()
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
            self.resultado_estado_pago()
        else:
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
        if self.datos_pagos["external_reference"] != self.DICT_DATOS_ORDEN["nro_factura"]:
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
                self.DICT_WIDGETS["modo_supervisor_forzado"] = True
                self.esperando_comparacion = True
                self.reintentarpago = False
                return
            
        elif self.datos_pagos["transaction_amount"] != self.DICT_DATOS_ORDEN["monto_pagar"]:
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
                return
            else:
                print(self.datos_pagos["status"], self.datos_pagos["status"])
        else:
            self.DICT_PROGRESO["text_label_aviso"] = "Error en el pago"
            self.DICT_PROGRESO["carga"] = 99
            self.DICT_PROGRESO["command"] = self.error_pago
        if not self.pago_manual:
            self.esperando_pago = False
            
            
    def error_pago(self):
        self.cierre_ERROR(True, "Error en el pago")

    def ERROR_API(self, label_error):
        try:
            ERRORES_API =  {
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
                    },
                    'cc_rejected_card_disabled': {
                        'nro_error': 20.7,
                        'description': 'Rechazado por tarjeta deshabilitada',
                    },
                    'cc_rejected_bad_filled_card_number': {
                        'nro_error': 20.8,
                        'description': 'Tu pago fue rechazado porque el número de la tarjeta es incorrecto',
                    },
                    'cc_rejected_invalid_installments': {
                        'nro_error': 20.9,
                        'description': 'Tu pago fue rechazado porque la tarjeta no acepta el número de cuotas elegido',
                    },
                    'cc_rejected_duplicated_payment': {
                        'nro_error': 21.0,
                        'description': 'Rechazamos el pago porque se realizó 2 veces',
                    },
                    'cc_rejected_card_type_not_allowed': {
                        'nro_error': 21.1,
                        'description': 'Rechazado por tipo de tarjeta no permitida',
                    },
                    'cc_rejected_max_attempts': {
                        'nro_error': 21.2,
                        'description': 'Rechazado debido a intentos excedidos del pin de la tarjeta	',
                    },
                    'cc_rejected_blacklist': {
                        'nro_error': 21.3,
                        'description': 'Tarjeta bloqueada',
                    },
                    'cc_rejected_high_risk': {
                        'nro_error': 21.4,
                        'description': 'Transacción rechazada: alto riesgo detectado',
                    }
                    
                    
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
            }
            

            
            #messagebox.showinfo("Pago recibido", f"Pago recibido\nNro Factura: {self.DICT_DATOS_ORDEN["nro_factura"]}\nNro Operación: {self.datos_pagos["id"]}\nMonto recibido: {float(self.datos_pagos["transaction_amount"])}")
            self.DICT_WIDGETS["my_label_aviso"].config(text="Pago recibido") 
            self.DICT_CONEXION["conexionDBA"].actualizar_datos_condicion("MPQRCODE_OBTENERPAGOPOINT", self.datos_obtener_pago, "external_reference", f"'{self.DICT_DATOS_ORDEN["nro_factura"]}'")
            self.DICT_CONEXION["conexionDBAServer"].actualizar_datos_condicion("MPQRCODE_OBTENERPAGOPOINTServer", self.datos_obtener_pago, "external_reference", f"'{self.DICT_DATOS_ORDEN["nro_factura"]}'")
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
        
    def solicitar_clave_supervisor(self, callback_si_valida):
        def verificar_clave():
            clave_ingresada = entry.get().strip()
            if clave_ingresada in self.DICT_WIDGETS["DICT_CLAVES_SUPERVISORES"]:
                self.variable_contendora_MensajeERROR.close()
                self.cierre_supervisor = True
                self.cierre_supervisor_autorizante = self.DICT_WIDGETS["DICT_CLAVES_SUPERVISORES"][clave_ingresada]
                self.cierre_supervisor_detalle = f"Cierre forzado por supervisor: {self.cierre_supervisor_autorizante}. Dicho pago corresponde a comprobante {self.datos_pagos["external_reference"]}"
                print(f"[SUPERVISOR] Acceso autorizado por {self.cierre_supervisor_autorizante}")
                self.teclado_hasar.funciones_personalizadas.pop("4a", None)  # limpiamos
                ventana.destroy()
                callback_si_valida()
            else:
                label_info.config(text="❌ Clave incorrecta", foreground="red")

        ventana = ttk.Toplevel(self.DICT_WIDGETS["root"])
        ventana.title("Clave de Supervisor")
        center_window(ventana, 400, 150)
        ventana.grab_set()

        frame = ttk.Frame(ventana, padding=20)
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

        ventana.bind("<Return>", lambda e: verificar_clave())

        # ✅ REGISTRAR COMBINACIÓN '4a'
        self.teclado_hasar.registrar_combinacion_personalizada("4a")
        self.teclado_hasar.asignar_funcion_personalizada("4a", lambda: ventana.after(0, verificar_clave))


    def activar_modo_supervisor(self):
        print("🔐 Supervisor pidió forzar validación")

        def continuar_a_pesar_de_error():
            self.DICT_WIDGETS["modo_supervisor_forzado"] = False
            self.DICT_WIDGETS["forzar_comparacion_factura"] = True
            print("🔓 Supervisor autorizó continuar a pesar del error de factura")
            self.NRO_ERROR = None
            self.esperando_comparacion = False
            self.reintentarpago = False

            # 🔁 Volver a ejecutar las validaciones posteriores
            self.realizar_comparacion()

        if self.DICT_WIDGETS.get("modo_supervisor_forzado", False):
            self.solicitar_clave_supervisor(continuar_a_pesar_de_error)