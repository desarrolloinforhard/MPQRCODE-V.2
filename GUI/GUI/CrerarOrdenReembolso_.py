import time
import keyboard
import ttkbootstrap as ttk
import json
import threading
import traceback
from datetime import datetime
from tkinter import messagebox
from GUI.BarraProgreso import BarraProgreso
from GUI.MessageBox import mostrar_error_y_cerrar
from Func.log_errorsV2 import log_error

class CrearOrdenReembolso(BarraProgreso):
    def __init__(self, frame, DICT_WIDGETS, DICT_DATOS_ORDEN, DICT_CONEXION):
        try:
            super().__init__(frame)
            
            #------------------------------------------- DICCIONARIOS CON DATOS -------------------------------------------
            self.DICT_WIDGETS = DICT_WIDGETS
            self.DICT_CONEXION = DICT_CONEXION
            self.DICT_DATOS_ORDEN = DICT_DATOS_ORDEN
            #---------------------------------------- VARIABLES INICIADORAS ----------------------------------------
            self.id_factura = None
            self.NRO_ERROR = None
            self.respuesta_mp = None
            self.datos_pago = None
            self.detalle_respuesta_mp = None
            self.SELECCION_TIPO_BUSQUEDA = None
            self.teclado_hasar = self.DICT_CONEXION.get("teclado")
            self.condicion_teclado = str(self.DICT_CONEXION["conexionDBA"].specify_search_condicion("SPDIR", "ID", "GRID", "teclado_km84", False)).strip().lower() == "true"
            
            
            self.datos_obtener_pago = {
                'NomCaja': self.DICT_DATOS_ORDEN["NomCaja"],
                'NumCajero': self.DICT_DATOS_ORDEN["NumCajero"],
                'NombreCajero': self.DICT_DATOS_ORDEN["NombreCajero"]
            }
            
            self.DICT_PROGRESO = {
                "widgets": DICT_WIDGETS,
                "text_label_aviso": "Buscando tipo de pago",
                "carga": 15,
                "command": self.tipo_eleccion_buscar
            }
            self.progreso(**self.DICT_PROGRESO)
        except Exception as e:
            log_error(e, "CrearOrdenReembolso")
            


    def _parse_iso(self, s: str):
        """Devuelve datetime aware a partir de ISO (acepta 'Z'). Si falla, None."""
        if not s:
            return None
        try:
            s = s.replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        except Exception:
            return None

    def _fetch_point_pagos_by_extref(self, external_reference: str):
        """
        Trae TODAS las filas de MPQRCODE_OBTENERPAGOPOINTServer para la external_reference
        y devuelve una lista de dicts (cada uno es el JSON de 'datos_pago' convertido).
        """
        sql = f"""
            SELECT datos_pago
            FROM MPQRCODE_OBTENERPAGOPOINTServer
            WHERE external_reference = '{external_reference}';
        """
        filas = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(sql) or []
        pagos = []
        for r in filas:
            raw = r.get("datos_pago") or r.get("DATOS_PAGO")
            try:
                pagos.append(self.convertir_a_json(raw))
            except Exception:
                # Si alguna fila viene corrupta, la ignoramos
                continue
        return pagos

    def _seleccionar_pago_point_por_monto(self, pagos: list, monto_objetivo: float, tol: float = 0.01):
        """
        De una lista de pagos POINT (dicts), elige el que coincide por monto con tolerancia.
        Prefiere status 'approved'/'authorized'. Si hay varios, el más reciente por date_last_updated.
        Si ninguno coincide, devuelve None.
        """
        def status_ok(p):
            st = str(p.get("status", "")).lower()
            return st in {"approved", "authorized"}

        def fecha_pago(p):
            return (self._parse_iso(self, p.get("date_last_updated"))
                    or self._parse_iso(self, p.get("date_created"))
                    or datetime.min)

        # Normalizamos el monto objetivo a 2 decimales
        try:
            monto_objetivo = float(monto_objetivo)
        except Exception:
            # Si no se puede convertir, abortamos
            return None

        # 1) Filtrar por status válido
        pagos_validos = [p for p in pagos if status_ok(p)]
        if not pagos_validos:
            pagos_validos = pagos[:]  # si no hay 'approved/authorized', usamos todos

        # 2) Coincidencia por monto con tolerancia
        candidatos = []
        for p in pagos_validos:
            try:
                ta = float(p.get("transaction_amount", 0))
                if abs(ta - monto_objetivo) <= tol:
                    candidatos.append(p)
            except Exception:
                continue

        if len(candidatos) == 1:
            return candidatos[0]
        if len(candidatos) > 1:
            # Elegir el más reciente
            candidatos.sort(key=fecha_pago, reverse=True)
            return candidatos[0]

        # 3) Sin coincidencia exacta por monto → no seleccionamos para evitar errores
        return None

            
            
    def buscar_id_factura(self):
        try:
            if self.SELECCION_TIPO_BUSQUEDA == True:
                self.id_factura = self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion("MPQRCODE_OBTENERPAGOServer", "id", "external_reference", f'{self.DICT_DATOS_ORDEN["nro_factura"]}', False)
                self.DICT_PROGRESO["text_label_aviso"] = "ID Encontrada"
                self.DICT_PROGRESO["carga"] = 30
                self.DICT_PROGRESO["command"] = None
                self.progreso(**self.DICT_PROGRESO)
                self.DICT_PROGRESO["text_label_aviso"] = f"Número de ID > {self.id_factura}"
                self.DICT_PROGRESO["carga"] = 45
                self.DICT_PROGRESO["command"] = self.iniciar_reembolso
                self.progreso(**self.DICT_PROGRESO)
            else:
                self.id_factura = self.datos_pago["id"]
                self.DICT_PROGRESO["text_label_aviso"] = "ID Encontrada"
                self.DICT_PROGRESO["carga"] = 30
                self.DICT_PROGRESO["command"] = None
                self.progreso(**self.DICT_PROGRESO)
                self.DICT_PROGRESO["text_label_aviso"] = f"Número de ID > {self.id_factura}"
                self.DICT_PROGRESO["carga"] = 45
                self.DICT_PROGRESO["command"] = self.buscar_reembolso_POINT
                self.progreso(**self.DICT_PROGRESO)
        except Exception as e:
            log_error(e, "buscar_id_factura")
            
    def convertir_a_json(self, cadena_json):
        try:
            # Intentar cargar el string como JSON
            resultado = json.loads(cadena_json)
            return resultado
        except json.JSONDecodeError as e:
            print(f"Error al convertir el string a JSON: {e}")
            return None 
        
        
    def tipo_eleccion_buscar(self):
        try:
            consulta_qr = f"""SELECT COUNT(*) AS existe
                FROM MPQRCODE_OBTENERPAGOServer
                WHERE external_reference = '{self.DICT_DATOS_ORDEN["nro_factura"]}';
            """

            consulta_point = f"""SELECT COUNT(*) AS existe
                FROM MPQRCODE_OBTENERPAGOPOINTServer
                WHERE external_reference = '{self.DICT_DATOS_ORDEN["nro_factura"]}';
            """

            # Ejecutar consulta
            resultado_qr_row = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(consulta_qr)[0]
            resultado_point_row = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(consulta_point)[0]

            # Normalizar
            resultado_qr = int(resultado_qr_row.get("existe", 0) if resultado_qr_row else 0)
            resultado_point = int(resultado_point_row.get("existe", 0) if resultado_point_row else 0)

            # Decidir por QR vs POINT
            if resultado_qr > 0:
                self.SELECCION_TIPO_BUSQUEDA = True  # QR
            elif resultado_point > 0:
                self.SELECCION_TIPO_BUSQUEDA = False  # POINT
            else:
                self.NRO_ERROR = 1
                self.cierre_ERROR()
                return

            # Si es POINT
            if self.SELECCION_TIPO_BUSQUEDA is False:
                extref = self.DICT_DATOS_ORDEN["nro_factura"]

                if resultado_point == 1:
                    # Caso actual (1 solo)
                    self.datos_pago = self.convertir_a_json(
                        self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion(
                            "MPQRCODE_OBTENERPAGOPOINTServer", "datos_pago", "external_reference", f"{extref}", False
                        )
                    )
                else:
                    # **NUEVO**: hay más de uno → elegimos por monto
                    pagos = self._fetch_point_pagos_by_extref(extref)
                    monto_objetivo = float(self.DICT_DATOS_ORDEN["monto_pagar"])  # ya te llega como float(Decimal(...))
                    elegido = self._seleccionar_pago_point_por_monto(pagos, monto_objetivo, tol=0.01)

                    if not elegido:
                        # No hay match por monto → no seguimos (evitar elegir mal)
                        self.NRO_ERROR = 2
                        msg = (f"No se encontró un pago POINT con transaction_amount == {monto_objetivo:.2f} "
                            f"para la factura {extref}. Se detectaron {resultado_point} pagos. "
                            f"Verifique en el POINT o ajuste el monto.")
                        mostrar_error_y_cerrar(self.DICT_WIDGETS, mensaje=msg, type_msg="warning", teclado_hasar=self.teclado_hasar)
                        self.NRO_ERROR = 1
                        self.cierre_ERROR()
                        return

                    self.datos_pago = elegido

                # Mensaje al operador (usa self.datos_pago ya seteado)
                try:
                    serial = self.datos_pago["point_of_interaction"]["device"]["serial_number"]
                except Exception:
                    serial = "DESCONOCIDO"
                mostrar_error_y_cerrar(
                    self.DICT_WIDGETS,
                    mensaje=(f"REALIZA LA DEVOLUCIÓN DEL PAGO DESDE EL POINT {serial}.\n"
                            f"UNA VEZ REALIZADA LA DEVOLUCIÓN DESDE EL POINT, PRESIONE OK."),
                    type_msg="info",
                    teclado_hasar=self.teclado_hasar
                )

            # Continuar flujo
            self.DICT_PROGRESO["text_label_aviso"] = "Buscando ID de Operación"
            self.DICT_PROGRESO["carga"] = 25
            self.DICT_PROGRESO["command"] = threading.Thread(target=self.buscar_id_factura, daemon=True).start
            self.progreso(**self.DICT_PROGRESO)

        except Exception as e:
            print(e)

        
        
    """def tipo_eleccion_buscar(self):
        try:
            consulta_qr = fSELECT COUNT(*) AS existe
                FROM MPQRCODE_OBTENERPAGOServer
                WHERE external_reference = '{self.DICT_DATOS_ORDEN["nro_factura"]}';
            

            consulta_point = fSELECT COUNT(*) AS existe
                FROM MPQRCODE_OBTENERPAGOPOINTServer
                WHERE external_reference = '{self.DICT_DATOS_ORDEN["nro_factura"]}';
            

            # Ejecutar consulta
            resultado_qr = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(consulta_qr)[0]
            resultado_point = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(consulta_point)[0]
            
            print(resultado_qr, resultado_point)
            
            resultado_qr = resultado_qr.get("existe", 0) if resultado_qr else 0
            resultado_point = resultado_point.get("existe", 0) if resultado_point else 0


            # Convertir a entero para evitar errores
            resultado_qr = int(resultado_qr)
            resultado_point = int(resultado_point)
            

            # Verificar existencia de registros
            if resultado_qr > 0:  
                self.SELECCION_TIPO_BUSQUEDA = True
            elif resultado_point > 0:  
                self.SELECCION_TIPO_BUSQUEDA = False
            else:
                self.NRO_ERROR = 1
                self.cierre_ERROR()
                return  

            if self.SELECCION_TIPO_BUSQUEDA == False:
                self.datos_pago = self.convertir_a_json(self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion("MPQRCODE_OBTENERPAGOPOINTServer", "datos_pago", "external_reference", f'{self.DICT_DATOS_ORDEN["nro_factura"]}', False))
                mostrar_error_y_cerrar(self.DICT_WIDGETS, mensaje=f"REALIZA LA DEVOLUCIÓN DEL PAGO DESDE EL POINT {self.datos_pago["point_of_interaction"]["device"]["serial_number"]}.\nUNA VEZ REALIZADO LA DEVOLUCIÓN DESDE EL POINT PRESIONE EL BOTON OK.", type_msg="info", teclado_hasar=self.teclado_hasar)
                #messagebox.showinfo(mensaje=f"REALIZA LA DEVOLUCIÓN DEL PAGO DESDE EL POINT {self.datos_pago["point_of_interaction"]["device"]["serial_number"]}.\nUNA VEZ REALIZADO LA DEVOLUCIÓN DESDE EL POINT PRESIONE EL BOTON ACEPTAR.")

            self.DICT_PROGRESO["text_label_aviso"] = "Buscando ID de Operación"
            self.DICT_PROGRESO["carga"] = 25
            self.DICT_PROGRESO["command"] = threading.Thread(target=self.buscar_id_factura, daemon=True).start
            self.progreso(**self.DICT_PROGRESO)
        except Exception as e:
            print(e)"""

            
            
    def iniciar_reembolso(self):
        try:
            log_error(f"Iniciando reembolso para ID {self.id_factura}", "iniciar_reembolso")
            self.DICT_PROGRESO["text_label_aviso"] = f"Iniciando Reembolso de Op > {self.id_factura}"
            self.DICT_PROGRESO["carga"] = 55
            self.DICT_PROGRESO["command"] = None
            self.progreso(**self.DICT_PROGRESO)
            self.DICT_PROGRESO["text_label_aviso"] = f"Procesando Reembolso de Op > {self.id_factura}"
            self.DICT_PROGRESO["carga"] = 70
            self.DICT_PROGRESO["command"] = self.mandar_orden_reembolso
            self.progreso(**self.DICT_PROGRESO)
        except Exception as e:
            log_error(e, "iniciar_reembolso")
            
    def buscar_reembolso_POINT(self):
        try:
            self.DICT_PROGRESO["text_label_aviso"] = f"Consultando con MERCADOPAGO por el pago > {self.id_factura}"
            self.DICT_PROGRESO["carga"] = 55
            self.DICT_PROGRESO["command"] = None
            self.progreso(**self.DICT_PROGRESO)
            self.DICT_DATOS_ORDEN["respuesta"] = self.DICT_CONEXION["conexionAPIPOINT"].obtenerPAGO(self.id_factura)
            self.datos_pago = self.DICT_CONEXION["conexionAPIPOINT"].obtenerPago_manual(self.DICT_DATOS_ORDEN)
            if not isinstance(self.datos_pago, str):
                self.datos_pago = self.datos_pago.json()
                if self.datos_pago["status"] == "refunded":
                    self.DICT_PROGRESO["text_label_aviso"] = f"Reembolso encontrado"
                    self.DICT_PROGRESO["carga"] = 75
                    self.DICT_PROGRESO["command"] = None
                    self.progreso(**self.DICT_PROGRESO)
                    self.DICT_PROGRESO["text_label_aviso"] = f"Avisando al Facturador"
                    self.DICT_PROGRESO["carga"] = 99
                    self.DICT_PROGRESO["command"] = self.finalizar_pago
                    self.progreso(**self.DICT_PROGRESO)
                else:
                    mostrar_error_y_cerrar(self.DICT_WIDGETS, "TODAVIA NO SEA HA HECHO LA DEVOLUCIÓN DESDE EL POINT", type_msg="error", teclado_hasar=self.teclado_hasar)
                    #messagebox.showerror("ERROR", "TODAVIA NO SEA HA HECHO LA DEVOLUCIÓN DESDE EL POINT")
                    self.NRO_ERROR = 21
                    self.cierre_ERROR()
            else:
                mostrar_error_y_cerrar(self.DICT_WIDGETS, self.datos_pago, type_msg="error", teclado_hasar=self.teclado_hasar)
                messagebox.showerror("ERROR", self.datos_pago)
                self.NRO_ERROR = 21
                self.cierre_ERROR()
        except Exception as e:
            print(e)
            self.NRO_ERROR = 21
            self.cierre_ERROR()
                
    
            
    def mandar_orden_reembolso(self):
        try:
            threading.Thread(target=self.conexion_con_mp_reembolso, daemon=True).start()
            while self.respuesta_mp == None:
                print("Esperando Respueta")
                time.sleep(1)
            if not self.respuesta_mp == False:
                self.DICT_PROGRESO["text_label_aviso"] = f"Actualizando Datos en el DBA"
                self.DICT_PROGRESO["carga"] = 85
                self.DICT_PROGRESO["command"] = self.actaulizar_nuevos_datos
                self.progreso(**self.DICT_PROGRESO)
                log_error("Reembolso exitoso, actualizando datos...", "mandar_orden_reembolso")
            else:
                mostrar_error_y_cerrar(self.DICT_WIDGETS, self.detalle_respuesta_mp, type_msg="error", teclado_hasar=self.teclado_hasar)
                #messagebox.showerror("Error Repuesta MP", self.detalle_respuesta_mp)
                self.NRO_ERROR = 3
                self.cierre_ERROR()
                log_error(f"Fallo el reembolso: {self.detalle_respuesta_mp}", "mandar_orden_reembolso")
        except Exception as e:
            log_error(e, "mandar_orden_reembolso")
            
    def conexion_con_mp_reembolso(self):
        try:
            self.DICT_PROGRESO["text_label_aviso"] = f"Aguardando Respuesta..."
            self.DICT_PROGRESO["carga"] = 75
            self.DICT_PROGRESO["command"] = None
            self.progreso(**self.DICT_PROGRESO)
            reintentos = 3
            intento = 0
            respuesta = None

            while intento < reintentos:
                try:
                    if self.SELECCION_TIPO_BUSQUEDA:
                        respuesta = self.DICT_CONEXION["conexionAPI"].crear_orden_reembolso(
                            self.id_factura,
                            self.DICT_DATOS_ORDEN["monto_pagar"]
                        )
                    else:
                        respuesta = self.DICT_CONEXION["conexionAPIPOINT"].crear_orden_reembolso(
                            self.id_factura,
                            self.DICT_DATOS_ORDEN["monto_pagar"]
                        )

                    if not 'message' in respuesta.json():
                        log_error(f"Reembolso creado correctamente en el intento #{intento + 1}", "conexion_con_mp_reembolso")
                        self.respuesta_mp = respuesta.json()
                        break
                    else:
                        self.detalle_respuesta_mp = respuesta.json()["message"]
                        log_error(f"Intento #{intento + 1} fallido: {self.detalle_respuesta_mp}", "conexion_con_mp_reembolso")
                        self.respuesta_mp = False
                        intento += 1
                        time.sleep(1.5)

                except Exception as e:
                    log_error(f"Excepción en intento #{intento + 1}: {str(e)}", "conexion_con_mp_reembolso")
                    self.respuesta_mp = False
                    intento += 1
                    time.sleep(1.5)
        except Exception as e:
            log_error(e, "conexion_con_mp_reembolso")
            
            
    def actaulizar_nuevos_datos(self):
        try:
            self.DICT_DATOS_ORDEN["respuesta"] = self.DICT_CONEXION["conexionAPI"].obtenerPAGO(self.id_factura)
            self.DICT_CONEXION["conexionAPI"].obtenerPago_manual(self.DICT_DATOS_ORDEN)
        
            self.DICT_PROGRESO["text_label_aviso"] = f"Datos actualizados"
            self.DICT_PROGRESO["carga"] = 99
            self.DICT_PROGRESO["command"] = self.finalizar_pago
            self.progreso(**self.DICT_PROGRESO)
        except Exception as e:
            log_error(str(e), "actaulizar_nuevos_datos")

            
    def finalizar_pago(self):
        try:
            
            datos = {
                'status': 1,
                'response': 0,
                'description': 'refunded',
                'IDMercadoPago': self.id_factura,
            }
            
            self.DICT_WIDGETS["my_label_aviso"].config(text="Reembolso logrado") 
            if self.SELECCION_TIPO_BUSQUEDA:
                self.DICT_CONEXION["conexionDBAServer"].actualizar_datos_condicion("MPQRCODE_OBTENERPAGOServer", self.datos_obtener_pago, "external_reference", f"'{self.DICT_DATOS_ORDEN["nro_factura"]}'")
                self.DICT_CONEXION["conexionDBA"].actualizar_datos_condicion("MPQRCODE_OBTENERPAGO", self.datos_obtener_pago, "external_reference", f"'{self.DICT_DATOS_ORDEN["nro_factura"]}'")
                #messagebox.showinfo("Reembolso logrado", f"Reembolso logrado a:\nNro Factura: {self.DICT_DATOS_ORDEN["nro_factura"]}\nNro Operación: {self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion("MPQRCODE_OBTENERPAGOServer", "id", "external_reference", f"{self.DICT_DATOS_ORDEN["nro_factura"]}", False)}\nMonto devuelto: {float(self.DICT_CONEXION["conexionDBAServer"].specify_search_condicion("MPQRCODE_OBTENERPAGOServer", "transaction_details_total_paid_amount", "external_reference", f"{self.DICT_DATOS_ORDEN["nro_factura"]}", False))}")
            else:
                #messagebox.showinfo("Reembolso logrado", f"Reembolso logrado a:\nNro Factura: {self.DICT_DATOS_ORDEN["nro_factura"]}\nNro Operación: {self.datos_pago["id"]}\nMonto devuelto: {float(self.datos_pago["transaction_amount_refunded"])}")
                self.DICT_CONEXION["conexionDBA"].actualizar_datos_condicion("MPQRCODE_OBTENERPAGOPOINT", self.datos_obtener_pago, "external_reference", f"'{self.DICT_DATOS_ORDEN["nro_factura"]}'")
                self.DICT_CONEXION["conexionDBAServer"].actualizar_datos_condicion("MPQRCODE_OBTENERPAGOPOINTServer", self.datos_obtener_pago, "external_reference", f"'{self.DICT_DATOS_ORDEN["nro_factura"]}'")
            self.DICT_CONEXION["conexionDBA"].actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMAS", datos, "nro_factura", f"'{self.DICT_DATOS_ORDEN["nro_factura"]}'")
            log_error("Reembolso finalizado y datos actualizados correctamente.", "finalizar_pago")
            self.DICT_WIDGETS["cerrar_ventana"]()
        except Exception as e:
            print(e)
            log_error(str(e), "finalizar_pago")
            #self.cierre_ERROR(paso_M=True)
#------------------------------------------------------------ CIERRES --------------------------------------------------------------
    def cierre_ERROR(self, paso_M=True, label_error=None ):
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
            self.DICT_WIDGETS["cerrar_ventana"]()
            
    def mostrar_error(self):
        try:
            mostrar_error_y_cerrar(self.DICT_WIDGETS, mensaje=self.LISTADO_ERRORES(), type_msg="error", teclado_hasar=self.teclado_hasar, remarcar=True)
            #messagebox.showerror(f"Error {self.NRO_ERROR}", self.LISTADO_ERRORES())
            self.DICT_CONEXION["conexionDBA"].actualizar_datos_condicion(
                "MPQRCODE_CONEXIONPROGRAMAS",
                self.datos_error,
                "nro_factura",
                f"'{self.DICT_DATOS_ORDEN['nro_factura']}'"  # Cambiado a comillas simples internas
            )
        except Exception as e:
            print(e)
            
    def LISTADO_ERRORES(self):
        try:
            Monto_recibido = self.DICT_CONEXION['conexionDBAServer'].specify_search_condicion('MPQRCODE_OBTENERPAGOServer', 'transaction_details_total_paid_amount', 'external_reference', self.DICT_DATOS_ORDEN['nro_factura'], False)
            if not Monto_recibido == None:
                Monto_recibido = float(Monto_recibido)
            DICT_ERRORES = {
                1: f"No se encontro ID de Operacion para la factura {self.DICT_DATOS_ORDEN["nro_factura"]}",
                2: f"No se encontro ID de Operacion en el servidor",
                3: f"Ya existe una devolución para el ID de Operacion > {self.id_factura}",
                10: (
                    "El monto esperado no es el mismo recibido en MercadoPago\n"
                    f"Monto esperado: *(${self.DICT_DATOS_ORDEN['monto_pagar']}{{green}})*\n"
                    f"Monto recibido: *(${Monto_recibido}{{red}})*"
                ),
                11: f"El ID *({self.id_factura}{{red}})* no coincide",
                12:  f"El ID *({self.id_factura}{{red}})* ya tiene una devolución hecha",
                20: "LA DEVOLUCIÓN TODAVIA NO FUE HECHA DESDE EL POINT",
                21: "La devolución no está aprobada",
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
            
    def on_8_and_6(self):
        try:
            if keyboard.is_pressed('8') and keyboard.is_pressed('6'):
                if self.SELECCION_TIPO_BUSQUEDA == None:
                    self.cuadro_dialogo_eleccion_buscar_seleccion_mpqr()
        except Exception as e:
            log_error(str(e), "on_8_and_6")
            messagebox.showerror("Error", "Ha ocurrido un error al detectar las teclas '8' y '6'.")
            
    def on_a_and_6(self):
        try:
            if keyboard.is_pressed('a') and keyboard.is_pressed('6'):
                if self.SELECCION_TIPO_BUSQUEDA == None:
                    self.cuadro_dialogo_eleccion_buscar_seleccion_mppoint()
        except Exception as e:
            log_error(str(e), "on_a_and_6")
            messagebox.showerror("Error", "Ha ocurrido un error al detectar las teclas 'a' y '6'.")
            
    def llamado_taskkill(self):
        self.DICT_WIDGETS["cerrar_con_taskill"](self.DICT_DATOS_ORDEN['nro_factura'])