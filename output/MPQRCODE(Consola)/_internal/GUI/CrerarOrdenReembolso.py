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

def to_int(x, default=0):
    try:
        return int(x)
    except (TypeError, ValueError):
        return default

def to_float(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default

class CrearOrdenReembolso(BarraProgreso):
    def __init__(self, frame, DICT_WIDGETS, DICT_DATOS_ORDEN, DICT_CONEXION):
        try:
            print("CrearOrdenReembolso")
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
            


    def _parse_iso(self, s):
        """Devuelve datetime aware a partir de ISO (acepta 'Z' y datetime). Si falla, None."""
        if not s:
            return None
        try:
            if isinstance(s, datetime):
                return s
            s = str(s).replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        except Exception:
            return None


    # 1) FETCH UNIFICADO (opcionalmente filtrado por idINTEGRACION)
    def _fetch_pagos_by_extref(self, external_reference: str, id_integracion: int | None = None):
        """
        Devuelve una lista de dicts con estructura homogénea:
        { "id": idPAGO, "transaction_amount": float, "status": str, "date_last_updated": datetime/str, "idINTEGRACION": int }
        Lee siempre de PAGOSMERCADOPAGO. Si id_integracion es None, trae todos (QR y POINT).
        """
        where_integ = "" if id_integracion is None else f"AND idINTEGRACION = {int(id_integracion)}"

        sql = f"""
            SELECT idPAGO, montoPAGO, estadoPAGO, dFechaU, idINTEGRACION
            FROM PAGOSMERCADOPAGO
            WHERE external_reference = '{external_reference}' {where_integ};
        """
        filas = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(sql) or []
        print(filas)

        pagos = []
        for r in filas:
            pagos.append({
                "id": r.get("idPAGO"),
                "transaction_amount": float(r.get("montoPAGO") or 0),
                "status": str(r.get("estadoPAGO") or "").lower(),
                "date_last_updated": r.get("dFechaU"),     # puede venir como datetime o string
                "idINTEGRACION": int(r.get("idINTEGRACION") or 0),
            })
        return pagos


    # 2) SELECTOR POR MONTO (GENÉRICO: QR y POINT)
    def _seleccionar_pago_por_monto(self, pagos: list, monto_objetivo: float, tol: float = 0.01):
        """
        Filtra por monto con tolerancia y prioriza estados 'approved'/'authorized'.
        Si hay varios, el más reciente por date_last_updated/date_created.
        """
        def status_ok(p):
            st = str(p.get("status", "")).lower()
            return st in {"approved", "authorized"}

        def fecha_pago(p):
            return (
                self._parse_iso(p.get("date_last_updated"))
                or self._parse_iso(p.get("date_created"))
                or datetime.min
            )

        try:
            monto_objetivo = float(monto_objetivo)
        except Exception:
            return None

        pagos_validos = [p for p in pagos if status_ok(p)] or pagos[:]

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
            candidatos.sort(key=fecha_pago, reverse=True)
            return candidatos[0]

        return None


    # 3) WRAPPERS (compatibilidad con tu código actual)
    def _fetch_point_pagos_by_extref(self, external_reference: str):
        # antes: solo POINT; ahora delega al unificado
        return self._fetch_pagos_by_extref(external_reference, id_integracion=1)

    def _fetch_qr_pagos_by_extref(self, external_reference: str):
        # nuevo wrapper para QR
        return self._fetch_pagos_by_extref(external_reference, id_integracion=0)

    def _seleccionar_pago_point_por_monto(self, *args, **kwargs):
        # alias para no romper llamadas existentes
        return self._seleccionar_pago_por_monto(*args, **kwargs)
                
            
    def buscar_id_factura(self):
        try:
            extref = self.DICT_DATOS_ORDEN["nro_factura"]
            monto_objetivo = to_float(self.DICT_DATOS_ORDEN.get("monto_pagar"), 0.0)
            tol = 0.01  # tolerancia de monto

            # 0) Si ya lo fijó el selector, no lo pises
            if getattr(self, "_id_fijado_por_selector", False) and to_int(getattr(self, "id_factura", 0), 0) > 0:
                self.DICT_PROGRESO["text_label_aviso"] = "ID Encontrada"
                self.DICT_PROGRESO["carga"] = 30
                self.DICT_PROGRESO["command"] = None
                self.progreso(**self.DICT_PROGRESO)

                self.DICT_PROGRESO["text_label_aviso"] = f"Número de ID > {self.id_factura}"
                self.DICT_PROGRESO["carga"] = 45
                # siguiente paso según tipo
                self.DICT_PROGRESO["command"] = (self.iniciar_reembolso if self.SELECCION_TIPO_BUSQUEDA else self.buscar_reembolso_POINT)
                self.progreso(**self.DICT_PROGRESO)
                return

            # 1) Si no estaba fijado, resolvelo por SQL (filtrando)
            sql = f"""
                SELECT TOP 1 idPAGO
                FROM PAGOSMERCADOPAGO
                WHERE external_reference = '{extref}'
                AND UPPER(estadoPAGO) NOT IN ('REEMBOLSADO','REFUNDED')
                AND ABS(montoPAGO - {monto_objetivo}) <= {tol}
                ORDER BY dFechaU DESC;
            """
            rows = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(sql) or []

            if rows:
                # respetar casing que devuelva el driver
                r0 = rows[0]
                self.id_factura = to_int(r0.get("idPAGO") or r0.get("idpago"), 0)
            else:
                # Fallback 1: el más reciente aprobado/autorizado
                sql_fallback = f"""
                    SELECT TOP 1 idPAGO
                    FROM PAGOSMERCADOPAGO
                    WHERE external_reference = '{extref}'
                    AND UPPER(estadoPAGO) IN ('APROBADO','APPROVED','AUTHORIZED','AUTORIZADO')
                    ORDER BY dFechaU DESC;
                """
                rows_fb = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(sql_fallback) or []
                if rows_fb:
                    r0 = rows_fb[0]
                    self.id_factura = to_int(r0.get("idPAGO") or r0.get("idpago"), 0)
                else:
                    # Fallback 2: último registro (pero advertí)
                    sql_last = f"""
                        SELECT TOP 1 idPAGO
                        FROM PAGOSMERCADOPAGO
                        WHERE external_reference = '{extref}'
                        ORDER BY dFechaU DESC;
                    """
                    rows_last = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(sql_last) or []
                    if rows_last:
                        r0 = rows_last[0]
                        self.id_factura = to_int(r0.get("idPAGO") or r0.get("idpago"), 0)
                    else:
                        self.NRO_ERROR = 2
                        msg = (f"No se pudo determinar el ID de operación para {extref} "
                            f"(monto ≈ {monto_objetivo:.2f}).")
                        mostrar_error_y_cerrar(self.DICT_WIDGETS, mensaje=msg, type_msg="warning", teclado_hasar=self.teclado_hasar)
                        self.NRO_ERROR = 1
                        self.cierre_ERROR()
                        return

            # 2) Avanzar con el ID encontrado
            self.DICT_PROGRESO["text_label_aviso"] = "ID Encontrada"
            self.DICT_PROGRESO["carga"] = 30
            self.DICT_PROGRESO["command"] = None
            self.progreso(**self.DICT_PROGRESO)

            self.DICT_PROGRESO["text_label_aviso"] = f"Número de ID > {self.id_factura}"
            self.DICT_PROGRESO["carga"] = 45
            self.DICT_PROGRESO["command"] = (self.iniciar_reembolso if self.SELECCION_TIPO_BUSQUEDA else self.buscar_reembolso_POINT)
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
            extref = self.DICT_DATOS_ORDEN["nro_factura"]
            monto_objetivo = to_float(self.DICT_DATOS_ORDEN.get("monto_pagar"), 0.0)

            # 1) Traer todas las filas de la factura (ALIAS en minúsculas + ISNULL en idintegracion)
            sql_all = f"""
                SELECT
                idPAGO                        AS idpago,
                ISNULL(idINTEGRACION, 0)      AS idintegracion,
                montoPAGO                     AS montopago,
                estadoPAGO                    AS estadopago,
                dFechaU                       AS dfechau
                FROM PAGOSMERCADOPAGO
                WHERE external_reference = '{extref}'
                ORDER BY dFechaU DESC;
            """
            rows = self.DICT_CONEXION["conexionDBAServer"].ejecutar_consulta(sql_all) or []
            if not rows:
                self.NRO_ERROR = 1
                self.cierre_ERROR()
                return

            # 2) Decidir tipo por la fila más reciente (0=QR, 1=POINT)
            idint = to_int(rows[0].get("idintegracion"), 0)
            self.DICT_DATOS_ORDEN["idINTEGRACION"] = idint
            self.SELECCION_TIPO_BUSQUEDA = (idint == 0)  # True=QR, False=POINT

            # 3) Filtrar solo filas del tipo elegido (si todo viniera nulo, usar todas como fallback)
            rows_tipo = [r for r in rows if to_int(r.get("idintegracion"), -1) == idint] or rows[:]

            # 4) Elegir por monto y NO reembolsado
            elegido = self._elegir_id_por_monto_no_reembolsado(rows_tipo, monto_objetivo, tol=0.01)
            if not elegido:
                self.NRO_ERROR = 2
                msg = (f"No se encontró un pago con monto ≈ {monto_objetivo:.2f} y estado no Reembolsado "
                    f"para la factura {extref} en el tipo {('QR' if idint==0 else 'POINT')}.")
                mostrar_error_y_cerrar(self.DICT_WIDGETS, mensaje=msg, type_msg="warning", teclado_hasar=self.teclado_hasar)
                self.NRO_ERROR = 1
                self.cierre_ERROR()
                return

            # 5) Guardar el ID elegido y marcar que no debe sobreescribirse
            self.id_factura = to_int(elegido.get('idpago') or elegido.get('idPAGO'), 0)
            self._id_fijado_por_selector = True  # ← bandera para respetar este ID


            # 6) Aviso solo si es POINT
            if not self.SELECCION_TIPO_BUSQUEDA:
                try:
                    r = self.DICT_CONEXION["conexionAPIPOINT"].obtenerPAGO(self.id_factura)
                    j = r.json() if hasattr(r, "json") else r
                    serial = (j.get("point_of_interaction", {})
                            .get("device", {})
                            .get("serial_number", "DESCONOCIDO"))
                except Exception:
                    serial = "DESCONOCIDO"

                mostrar_error_y_cerrar(
                    self.DICT_WIDGETS,
                    mensaje=(f"REALIZA LA DEVOLUCIÓN DEL PAGO DESDE EL POINT {serial}.\n"
                            f"UNA VEZ REALIZADA LA DEVOLUCIÓN DESDE EL POINT, PRESIONE OK."),
                    type_msg="info",
                    teclado_hasar=self.teclado_hasar
                )

            # 7) Continuar flujo (como ya tenías)
            self.DICT_PROGRESO["text_label_aviso"] = "Buscando ID de Operación"
            self.DICT_PROGRESO["carga"] = 25
            self.DICT_PROGRESO["command"] = threading.Thread(target=self.buscar_id_factura, daemon=True).start
            self.progreso(**self.DICT_PROGRESO)

        except Exception as e:
            print(e)


    def _elegir_id_por_monto_no_reembolsado(self, rows: list, monto_objetivo, tol: float = 0.01):
        print(rows, monto_objetivo)
        """
        rows: lista de dicts de la DB con claves ALIAS:
            idpago (int), idintegracion (int), montopago (Decimal/float), estadopago (str), dfechau (datetime)
        Devuelve el dict elegido o None.
        """
        def estado(r):
            return (str(r.get('estadopago') or '')).strip().lower()

        def monto(r):
            return to_float(r.get('montopago'))

        def fecha(r):
            return r.get('dfechau') or datetime.min

        objetivo = to_float(monto_objetivo, None)
        if objetivo is None:
            return None

        # 1) fuera reembolsados
        no_refund = [r for r in rows if estado(r) not in {'reembolsado', 'refunded'}]
        if not no_refund:
            return None

        # 2) match por monto (con tolerancia)
        matches = [r for r in no_refund if (m := monto(r)) is not None and abs(m - objetivo) <= tol]
        if not matches:
            return None

        # 3) prioridad: aprobado/autorizado → más reciente
        def score(r):
            ok = 1 if estado(r) in {'aprobado', 'approved', 'authorized', 'autorizado'} else 0
            return (ok, fecha(r))

        matches.sort(key=score, reverse=True)
        return matches[0]



        
        
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