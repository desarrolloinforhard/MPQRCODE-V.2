from Conf.Conexion_APIs_MPV3 import Conexion_Api
from datetime import datetime, timedelta
from tkinter import messagebox
from pprint import pprint
import json
import traceback
import random
import string

# Obtener la fecha y hora actual
now = datetime.now()

# Calcular la fecha y hora hace 24 horas
twenty_four_hours_ago = now - timedelta(hours=24)

# Formatear las fechas
formato_fecha = now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Se omiten los últimos 3 caracteres para tener solo los milisegundos

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    ZoneInfo = None

def _fecha_argentina(iso_str: str):
    """
    Convierte string ISO de MP (ej: 2025-09-02T08:11:13.000-04:00)
    a datetime en zona horaria de Argentina, devuelto como 'YYYY-MM-DD HH:MM:SS'.
    """
    if not iso_str:
        return None
    try:
        iso_str = iso_str.replace("Z", "+00:00")  # cubrir caso UTC
        dt = datetime.fromisoformat(iso_str)      # respeta offset
        if ZoneInfo:
            dt = dt.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_str  # fallback: guardo como texto

def _get(d: dict, path, default=None):
    cur = d
    for k in path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur


class Conexion_APP():
    def __init__(self, conexionAPI, conexionDBA, conexionDBAServer):
        self.conexionAPI = Conexion_Api(conexionAPI[0], conexionAPI[1])
        self.conexionDBA =  conexionDBA
        self.conexionDBAServer = conexionDBAServer
        #/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/**/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/
        #UNION DE LAS CLASES Y FUNCIONES PARA LA CREACION DE SUCURSALES. Recorrer e insertar los datos
    def creacionSUC(self, datosSUC):
        try:
            response_MPQRCODE_RESPUESTA_SUCURSAL = self.conexionAPI.crear_sucursal(datosSUC)
            print(response_MPQRCODE_RESPUESTA_SUCURSAL)
            if response_MPQRCODE_RESPUESTA_SUCURSAL.status_code >= 200 and response_MPQRCODE_RESPUESTA_SUCURSAL.status_code < 300:
                MPQRCODE_RESPUESTA_SUCURSAL = response_MPQRCODE_RESPUESTA_SUCURSAL.json()
                variable_iniciadora = MPQRCODE_RESPUESTA_SUCURSAL["id"]
                nro_idINCREMENT = self.conexionDBAServer.inicializar_tabla_MPQRCODE_SUCURSAL(variable_iniciadora)
                nombre_tabla = "MPQRCODE_SUCURSAL"
                # Recorre cada clave y valor en el JSON
                for clave_json, valor_json in MPQRCODE_RESPUESTA_SUCURSAL.items():
                    if isinstance(valor_json, dict):
                        if clave_json == 'business_hours':
                            datos_business_hours = []
                            idSUC = self.conexionDBAServer.obtener_valor_id_por_idINCREMENT(nro_idINCREMENT, nombre_tabla)
                            for dia, horarios in valor_json.items():
                                datos_business_hours.append(dia)
                                for horario in horarios:
                                    datos_business_hours.append(horario)
                                self.conexionDBAServer.insertar_datos_MPQRCODE_SUCURSAL_business_hours(idSUC, datos_business_hours[0], datos_business_hours[1]["open"], datos_business_hours[1]["close"])
                                datos_business_hours.clear()
                        elif clave_json == 'location':
                            datos_location = []
                            idSUC = self.conexionDBAServer.obtener_valor_id_por_idINCREMENT(nro_idINCREMENT, nombre_tabla)
                            for clave, valor in valor_json.items():
                                datos_location.append(valor)
                            self.conexionDBAServer.insertar_datos_MPQRCODE_SUCURSAL_location(idSUC, datos_location[0], datos_location[1], datos_location[2], datos_location[3], datos_location[4], datos_location[5], datos_location[6], datos_location[7])
                    else:        
                        #Llama a la función insertar_dato_en_tabla con los parámetros correspondientes
                        self.conexionDBAServer.insertar_dato_en_tabla(nombre_tabla, clave_json, nro_idINCREMENT, valor_json)
                print("Se guardar todos los datos en el BDA")
            return response_MPQRCODE_RESPUESTA_SUCURSAL
        except Exception as e:
            messagebox.showerror("Error al crear Sucursal", f"{e}")
            print(f"ERROR EN LA CREACION DE LA SUCURSAL: {str(e)}")
            return response_MPQRCODE_RESPUESTA_SUCURSAL
    
    def eliminarSUC(self, external_IDSUC, dict_cajas):
        for clave, valor in dict_cajas.items():
            if clave == 'PDV':
                for nombre, valor in clave.items():
                    self.eliminarCaja(valor['external_id'])
            else:
                pass
        valor_idSUC = self.conexionDBAServer.obtener_valor_id_por_external_id(external_IDSUC, "MPQRCODE_SUCURSAL")
        respuesta = self.conexionAPI.eliminar_sucursal(valor_idSUC)
        if respuesta >= 200 and respuesta < 300:
            self.conexionDBAServer.eliminar_filas("MPQRCODE_SUCURSAL_location", "idSUC", int(valor_idSUC))
            self.conexionDBAServer.eliminar_filas("MPQRCODE_SUCURSAL_business_hours", "idSUC", int(valor_idSUC))
            self.conexionDBAServer.eliminar_filas("MPQRCODE_SUCURSAL", "id", int(valor_idSUC))
            self.conexionDBAServer.desconectar()
            print("SUCURSAL ELIMINADA")
            return True
        else:
            print("NO SE PUDO ELIMINAR LA SUCURSAL")
            return False
        

    
    def limpieza_tabla_TOTALsucursal(self):
        self.conexionDBAServer.eliminar_tabla("MPQRCODE_SUCURSAL")
        self.conexionDBAServer.eliminar_tabla("MPQRCODE_SUCURSAL_business_hours")
        self.conexionDBAServer.eliminar_tabla("MPQRCODE_SUCURSAL_location")
        self.conexionDBAServer.crear_tabla_MPQRCODE_SUCURSAL()
        self.conexionDBAServer.crear_tabla_MPQRCODE_SUCURSAL_business_hours()
        self.conexionDBAServer.crear_tabla_MPQRCODE_SUCURSAL_location()
    
    def limpieza_tabla_sucursal(self):
        self.conexionDBAServer.limpiar_tabla("MPQRCODE_SUCURSAL")
        self.conexionDBAServer.limpiar_tabla("MPQRCODE_SUCURSAL_business_hours")
        self.conexionDBAServer.limpiar_tabla("MPQRCODE_SUCURSAL_location")
    

    #/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/**/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/
    #UNION DE LAS CLASES Y FUNCIONES PARA LA CREACION DE LAS CAJAS PARA LAS SUCURSALES. Recorrer e insertar los datos
    def crearCaja(self, id_externoSUC, datosLISTPOS, IPN_url):
        try:
            nombre_tabla = "MPQRCODE_CAJAS"
            #CREAR UNA VARIABLE EN EL CUAL SE PUEDA INGRESE EL external_id Y REEMPLAZARLAS en idSUC y MPQRCODE_RESPUESTA_CAJA
            idSUC = self.conexionDBAServer.obtener_valor_id_por_external_id(id_externoSUC, "MPQRCODE_SUCURSAL")
            datosPOS = {
                "category": int(datosLISTPOS[0]),  # Convertir el conjunto a lista
                "external_id": str(datosLISTPOS[1]),  # Asegurarse de que los datos sean strings si es necesario
                "external_store_id": id_externoSUC,
                "fixed_amount": True,
                "name": str(datosLISTPOS[2]),
                "store_id": int(idSUC),
            }
            MPQRCODE_RESPUESTA_CAJA = self.conexionAPI.crear_caja(datosPOS)
            MPQRCODE_RESPUESTA_CAJA_JSON = MPQRCODE_RESPUESTA_CAJA.json()
            print(MPQRCODE_RESPUESTA_CAJA_JSON)
            if MPQRCODE_RESPUESTA_CAJA.status_code >= 200 and MPQRCODE_RESPUESTA_CAJA.status_code < 300:
                variable_iniciadora = MPQRCODE_RESPUESTA_CAJA_JSON["id"]
                nro_idINCREMENT = self.conexionDBAServer.inicializar_tabla_MPQRCODE_CAJAS(variable_iniciadora)
                picture__urldatos = {
                    'external_store_id': id_externoSUC,
                    'IPN_url': IPN_url
                }
                self.conexionDBAServer.actualizar_datos("MPQRCODE_CAJAS", picture__urldatos, nro_idINCREMENT)
                for clave_json, valor_json in MPQRCODE_RESPUESTA_CAJA_JSON.items():
                    if isinstance(valor_json, dict):
                        if clave_json == "qr":
                            datos_qr = []
                            idPOS = self.conexionDBAServer.obtener_valor_id_por_idINCREMENT(nro_idINCREMENT, nombre_tabla)
                            for clave_qr, valor_qr in valor_json.items():
                                datos_qr.append(valor_qr)
                            self.conexionDBAServer.insertar_datos_MPQRCODE_CAJAS_qr(idPOS, datos_qr[0], datos_qr[1], datos_qr[2])
                    else:
                        self.conexionDBAServer.insertar_dato_en_tabla(nombre_tabla, clave_json, nro_idINCREMENT, valor_json)
                idPOS = self.conexionDBAServer.obtener_valor_id_por_idINCREMENT(nro_idINCREMENT, nombre_tabla)
                external_pos_id = self.conexionDBAServer.obtener_valor_external_idPOS_por_idINCREMENT(nro_idINCREMENT, nombre_tabla)
                self.conexionDBAServer.insertar_datos_MPQRCODE_CAJAS_qrFALTANTE(external_pos_id, idPOS)
                print("Se guardar todos los datos en el BDA")
                return MPQRCODE_RESPUESTA_CAJA
            else:
                return MPQRCODE_RESPUESTA_CAJA_JSON
        
        #DEFINIR BIEN LA LOGICA CON GUICrearCaja.py
        except Exception as e:
            messagebox.showerror("Error al crear la Caja", f"{e}")
            print(f"ERROR EN LA CREACION DE LA CAJA: {e}")
            return MPQRCODE_RESPUESTA_CAJA_JSON
            
    def eliminarCaja(self, valor_idPOS):
        respuesta = self.conexionAPI.eliminar_caja(valor_idPOS)
        if respuesta.status_code >= 200 and respuesta.status_code < 300:
            self.conexionDBAServer.eliminar_filas("MPQRCODE_CAJAS_qr", "id_POS", valor_idPOS)
            self.conexionDBAServer.eliminar_filas("MPQRCODE_CAJAS", "id", valor_idPOS)
            self.conexionDBAServer.desconectar()
            print(f"CAJA {valor_idPOS}: ELIMINADA")
        else:
            print("NO SE PUDO ELIMINAR LA CAJA")
        return respuesta            
    
    def limpieza_tabla_TOTALcaja(self):
        self.conexionDBAServer.eliminar_tabla("MPQRCODE_CAJAS")
        self.conexionDBAServer.eliminar_tabla("MPQRCODE_CAJAS_qr")
        self.conexionDBAServer.crear_tabla_MPQRCODE_CAJAS()
        self.conexionDBAServer.crear_tabla_MPQRCODE_CAJAS_qr()
    
    def limpieza_tabla_caja(self):
        self.conexionDBAServer.limpiar_tabla("MPQRCODE_CAJAS")
        self.conexionDBAServer.limpiar_tabla("MPQRCODE_CAJAS_qr")
        
        #/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/**/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/
        #UNIÓN PARA CREAR ORDENES
    def crearOrden(self, external_idPOS, nro_factura, sucNAME, monto_pagar, picture_url, IPN_url):
        tabla = 'MPQRCODE_CREARORDEN'
        crear_ORDEN = self.conexionAPI.crear_orden(external_idPOS, nro_factura, sucNAME, monto_pagar, picture_url, IPN_url)
        print(crear_ORDEN.json())
        if crear_ORDEN.status_code >= 200 and crear_ORDEN.status_code < 300:
            external_reference = None
            for clave_json, valor_json in crear_ORDEN.json().items():
                if clave_json == 'external_reference':
                    external_reference = valor_json
                else:
                    pass
            valor1 = {
                'external_reference' : external_reference,
                'date_creation': formato_fecha
            }
            id_increment = self.conexionDBA.insertar_datos_obtener_idINCREMENT(tabla, valor1)
            self.conexionDBA.insertar_dato_en_tabla(tabla, 'external_idPOS', id_increment, external_idPOS)
            try:
                valor_DICT = {}
                for clave_json, valor_json in crear_ORDEN.json().items():
                    if clave_json == 'items' and isinstance(valor_json, list):
                        # Tu código aquí si clave_json es 'items' y valor_json es una lista
                        for recorre_lista in valor_json:
                            valor_dictITEMS = {}
                            for clave_dict, valor_dict in recorre_lista.items():
                                if clave_dict == 'id':
                                    valor_dictITEMS['external_reference'] = external_reference
                                    valor_dictITEMS['idMERCADERIA'] = valor_dict
                                else:
                                    valor_dictITEMS[clave_dict] = valor_dict
                            self.conexionDBA.insertar_datos_sin_obtener_id("MPQRCODE_CREARORDEN_items", valor_dictITEMS)
                            print(valor_dictITEMS)
                    elif not isinstance(valor_json, (list, dict)) and not clave_json == 'external_reference':
                        valor_DICT[clave_json] = valor_json
                    else:
                        pass
                self.conexionDBA.actualizar_datos(tabla, valor_DICT, id_increment)
                return external_reference, external_idPOS
            except Exception as e:
                messagebox.showerror("Error al crear la orden", f"{e}")
                print(f"Error: {e}")
                # Manejo de errores o cualquier otra acción necesaria
            finally:
                self.conexionDBA.desconectar()
                
    def crearOrdenDinamico(self, external_idPOS, nro_factura, sucNAME, monto_pagar, IPN_URL):
        try:
            crear_ORDEN = self.conexionAPI.crear_orden_dinamico(external_idPOS, nro_factura, sucNAME, monto_pagar, IPN_URL)
            print(crear_ORDEN)
            return crear_ORDEN
        except Exception as e:
            messagebox.showerror("Error al crear la orden", f"{e}")
            print(f"Error: {e}")
            # Manejo de errores o cualquier otra acción necesaria
        finally:
            self.conexionDBA.desconectar()
            
            
    def crearOrdenDinamicoV2(self, external_idPOS, nro_factura, sucNAME, monto_pagar, IPN_URL):
        try:
            crear_ORDEN = self.conexionAPI.crear_orden_dinamicoV2(external_idPOS, nro_factura, sucNAME, monto_pagar, IPN_URL)
            print(crear_ORDEN)
            return crear_ORDEN
        except Exception as e:
            messagebox.showerror("Error al crear la orden", f"{e}")
            print(f"Error: {e}")
            # Manejo de errores o cualquier otra acción necesaria
        finally:
            self.conexionDBA.desconectar()
            
    def QR_Crear_order(self, datos_orden):
        return self.conexionAPI.QR_Crear_order(datos_orden)
    
    
    def QR_Obtener_order_por_ID(self, id_order):
        return self.conexionAPI.QR_Obtener_order_por_ID(id_order)
    
    def QR_Cancelar_order_por_ID(self, id_order):
        return self.conexionAPI.QR_Cancelar_order_por_ID(id_order)
    """
    def obteneridOrder(self, external_reference, status_cancel):
        obtener_ID = None
        while obtener_ID is None:
            obtener_ID = self.conexionDBAServer.specify_search_condicion("MPQRCODE_OBTENERPAGOServer", "data", "external_reference", external_reference, True)       
            if obtener_ID is None:
                if status_cancel == 0:
                    print("Esperando confirmación del pago...")
                    time.sleep(1)  # Puedes ajustar el tiempo de espera según sea necesario
                else:
                    break
        print("Pago Realizado. ID obtenido:", obtener_ID[0])
        return obtener_ID[0], True
    """    
    def obtenerPago(self, id_pago, external_reference, external_idPOS, insertar, tipo_pago):
        print("BUSCANDO STATUS DEL PAGO: ")
        datos = {
            'external_reference': external_reference,
            'external_idPOS': external_idPOS
        }
        if insertar and tipo_pago == 0:
            self.conexionDBA.insertar_datos_sin_obtener_id("MPQRCODE_OBTENERPAGO", datos)
            self.conexionDBAServer.insertar_datos_sin_obtener_id("MPQRCODE_OBTENERPAGO", datos)
        elif insertar and tipo_pago == 1:
            self.conexionDBA.insertar_datos_sin_obtener_id("MPQRCODE_OBTENERPAGOPOINT", datos)
            self.conexionDBAServer.insertar_datos_sin_obtener_id("MPQRCODE_OBTENERPAGOPOINT", datos)
        else:
            pass

        # Asegúrate de que obtienes la respuesta correctamente
        respuesta = self.conexionAPI.obtener_pago(id_pago)

        try:
            # Verifica si la respuesta es un objeto JSON válido
            json_response = respuesta.json()
            print(json_response)
        except ValueError as e:
            print(f"Error al parsear la respuesta JSON: {str(e)}")
            return

        datos = {}

        for clave_json, valor_json in json_response.items():
            if clave_json == 'order' and isinstance(valor_json, dict):
                for recorre_dict, valordict in valor_json.items():
                    if recorre_dict == 'id':
                        datos['order_id'] = valordict
                    else:
                        datos['order_type'] = valordict
            elif clave_json == 'payer' and isinstance(valor_json, dict):
                for recorre_dict, valordict in valor_json.items():
                    if recorre_dict == 'id':
                        datos['payer_id'] = valordict
                    else:
                        print("Se encontró una respuesta no esperada.")
            elif clave_json == 'payment_method' and isinstance(valor_json, dict):
                for recorre_dict, valordict in valor_json.items():  # Corregir aquí a valordict
                    if recorre_dict == 'id':
                        datos['payment_metodo_id'] = valordict
                    elif recorre_dict == 'issuer_id':
                        datos['payment_metodo_issuer_id'] = valordict
                    else:
                        datos['payment_metodo_type'] = valordict
            elif clave_json == 'transaction_details' and isinstance(valor_json, dict):
                for recorre_dict, valordict in valor_json.items():  # Corregir aquí a valordict
                    if recorre_dict == 'total_paid_amount':
                        datos['transaction_details_total_paid_amount'] = valordict
                    else:
                        pass
            else:
                if tipo_pago == 0:
                    columnas = self.conexionDBA.obtener_nombres_columnas("MPQRCODE_OBTENERPAGO")
                elif tipo_pago == 1:
                    columnas = self.conexionDBA.obtener_nombres_columnas("MPQRCODE_OBTENERPAGOPOINT")
                for colum_name in columnas:
                    if clave_json == colum_name and not clave_json == 'external_reference':
                        datos[clave_json] = valor_json
                    else:
                        pass
        if tipo_pago == 0:
            self.conexionDBA.actualizar_datos_condicion("MPQRCODE_OBTENERPAGO", datos, 'external_reference', f"'{external_reference}'")
            self.conexionDBAServer.actualizar_datos_condicion("MPQRCODE_OBTENERPAGO", datos, 'external_reference', f"'{external_reference}'")
            status = self.conexionDBA.specify_search_condicion("MPQRCODE_OBTENERPAGO", 'status', 'external_reference', external_reference, False)
            status_detail = self.conexionDBA.specify_search_condicion("MPQRCODE_OBTENERPAGO", 'status_detail', 'external_reference', external_reference, False)
            if status == 'approved' and status_detail == 'accredited':
                print("PAGO REALIZADO")
                return True
            else:
                print("NO SE PUDO OBTENER EL PAGO")
                return False
        elif tipo_pago == 1:
                self.conexionDBA.actualizar_datos_condicion("MPQRCODE_OBTENERPAGOPOINT", datos, 'external_reference', f"'{external_reference}'")
                self.conexionDBAServer.actualizar_datos_condicion("MPQRCODE_OBTENERPAGOPOINT", datos, 'external_reference', f"'{external_reference}'")
                status = self.conexionDBA.specify_search_condicion("MPQRCODE_OBTENERPAGOPOINT", 'status', 'external_reference', external_reference, False)
                status_detail = self.conexionDBA.specify_search_condicion("MPQRCODE_OBTENERPAGOPOINT", 'status_detail', 'external_reference', external_reference, False)
                if status == 'approved' and status_detail == 'accredited':
                    print("PAGO REALIZADO")
                    return True
                else:
                    print("NO SE PUDO OBTENER EL PAGO")
                    return False
                
    def obtenerPAGO(self, id_pago):
        return self.conexionAPI.obtener_pago(id_pago)
                
    """def obtenerPago_manual(self, external_idPOS, respuesta):
        try:
        
        
            if respuesta.status_code > 300 and respuesta.status_code < 500:
                return f"Error {respuesta.status_code, respuesta.json["message"]}"
            else:
                pass

            try:
                # Verifica si la respuesta es un objeto JSON válido
                json_response = respuesta.json()
                print(json_response)
            except ValueError as e:
                print(f"Error al parsear la respuesta JSON: {str(e)}")
                return  f"Error al parsear la respuesta JSON: {str(e)}"

            
            datos = {
                'external_reference': json_response["external_reference"],
                'external_idPOS': external_idPOS,
                "collector_id": json_response["collector_id"],
                "coupon_amount": json_response["coupon_amount"],
                "currency_id": json_response["currency_id"],
                "date_approved": json_response["date_approved"],
                "date_created": json_response["date_created"],
                "date_last_updated": json_response["date_last_updated"],
                "date_of_expiration": json_response["date_of_expiration"],
                "deduction_schema": json_response["deduction_schema"],
                "description": json_response["description"],
                "id": json_response["id"],
                "installments": json_response["installments"],
                "integrator_id": json_response["integrator_id"],
                "issuer_id": json_response["issuer_id"],
                "live_mode": json_response["live_mode"],
                "marketplace_owner": json_response["marketplace_owner"],
                "merchant_account_id": json_response["merchant_account_id"],
                "merchant_number": json_response["merchant_number"],
                "order_id": json_response["order"]["id"],
                "order_type": json_response["order"]["type"],
                "payer_id": json_response["payer"]["id"],
                "payment_metodo_id": json_response["payment_method"]["id"],
                "payment_metodo_issuer_id": json_response["payment_method"]["issuer_id"],
                "payment_metodo_type": json_response["payment_method"]["type"],
                "pos_id": json_response["pos_id"],
                "processing_mode": json_response["processing_mode"],
                "shipping_amount": json_response["shipping_amount"],
                "sponsor_id": json_response["sponsor_id"],
                "status": json_response["status"],
                "status_detail": json_response["status_detail"],
                "store_id": json_response["store_id"],
                "taxes_amount": json_response["taxes_amount"],
                "transaction_amount": json_response["transaction_amount"],
                "transaction_amount_refunded": json_response["transaction_amount_refunded"],
                "net_received_amount": json_response["transaction_details"]["net_received_amount"],
                "transaction_details_total_paid_amount": json_response["transaction_details"]["total_paid_amount"],
            }
            datos_server = {
                'external_reference': json_response["external_reference"],
                'data': json_response["id"],
                "collector_id": json_response["collector_id"],
                "coupon_amount": json_response["coupon_amount"],
                "currency_id": json_response["currency_id"],
                "date_approved": json_response["date_approved"],
                "date_created": json_response["date_created"],
                "date_last_updated": json_response["date_last_updated"],
                "date_of_expiration": json_response["date_of_expiration"],
                "deduction_schema": json_response["deduction_schema"],
                "description": json_response["description"],
                "id": json_response["id"],
                "installments": json_response["installments"],
                "integrator_id": json_response["integrator_id"],
                "issuer_id": json_response["issuer_id"],
                "live_mode": json_response["live_mode"],
                "marketplace_owner": json_response["marketplace_owner"],
                "merchant_account_id": json_response["merchant_account_id"],
                "merchant_number": json_response["merchant_number"],
                "order_id": json_response["order"]["id"],
                "order_type": json_response["order"]["type"],
                "payer_id": json_response["payer"]["id"],
                "payment_metodo_id": json_response["payment_method"]["id"],
                "payment_metodo_issuer_id": json_response["payment_method"]["issuer_id"],
                "payment_metodo_type": json_response["payment_method"]["type"],
                "pos_id": json_response["pos_id"],
                "processing_mode": json_response["processing_mode"],
                "shipping_amount": json_response["shipping_amount"],
                "sponsor_id": json_response["sponsor_id"],
                "status": json_response["status"],
                "status_detail": json_response["status_detail"],
                "store_id": json_response["store_id"],
                "taxes_amount": json_response["taxes_amount"],
                "transaction_amount": json_response["transaction_amount"],
                "transaction_amount_refunded": json_response["transaction_amount_refunded"],
                "net_received_amount": json_response["transaction_details"]["net_received_amount"],
                "transaction_details_total_paid_amount": json_response["transaction_details"]["total_paid_amount"],
            }
            
            if 'card' in json_response:
                card_texto = json.dumps(json_response['card'], ensure_ascii=False)
                datos['card'] = card_texto
                datos_server['card'] = card_texto
            self.conexionDBA.insertar_datos_o_actualizar("MPQRCODE_OBTENERPAGO", datos)
            self.conexionDBAServer.insertar_datos_o_actualizar("MPQRCODE_OBTENERPAGOServer", datos_server)
            return respuesta
        except Exception as e:
            print(e)"""
            
    def _parser_idMetodoPago(self, payment_method_id):
        if payment_method_id == 'interop_transfer':
            return "Billetera Virtual"
        elif payment_method_id == 'consumer_credits':
            return "Mercado Crédito"
        elif payment_method_id == 'account_money':
            return "MercadoPago"
        else:
            return "Metodo Pago No Reconocido"
        
    def _parser_cardTYPE(self, payment_type_id):
        if payment_type_id == 'debit_card':
            return "Tarjeta Débito"
        elif payment_type_id == 'credit_card':
            return "Tarjeta Crédito"
        elif payment_type_id == 'prepaid_card':
            return "Tarjeta Prepaga"
        else:
            return "Tarjeta NO CONOCIDA"
    def _parser_status(self, status: str, status_detail: str | None):
        """
        Devuelve (etiqueta_corta, descripcion_larga) en español
        a partir de (status, status_detail) de MercadoPago.
        """
        s = (status or "").strip().lower()
        d = (status_detail or "").strip().lower()

        # Normalizar variantes
        if s == "canceled":
            s = "cancelled"

        # Mapa específico (status, status_detail) -> (etiqueta, descripción)
        mapa = {
            ("approved", "accredited"): ("Aprobado", "¡Listo! Se acreditó tu pago."),
            ("approved", "partially_refunded"): ("Aprobado (parcial)", "Pago aprobado con al menos un reembolso parcial."),

            ("authorized", "pending_capture"): ("Autorizado", "Pago autorizado; pendiente de captura."),

            ("in_process", "offline_process"): ("En proceso", "Por falta de procesamiento online, se procesa de forma offline."),
            ("in_process", "pending_contingency"): ("En proceso", "Estamos procesando tu pago (contingencia)."),
            ("in_process", "pending_review_manual"): ("En proceso", "Estamos procesando tu pago (revisión manual)."),

            ("pending", "pending_waiting_transfer"): ("Pendiente", "Esperando que completes la transferencia bancaria."),
            ("pending", "pending_waiting_payment"): ("Pendiente", "Pago offline pendiente de que el usuario lo realice."),
            ("pending", "pending_challenge"): ("Pendiente", "Confirmación pendiente por challenge 3DS."),

            ("cancelled", "expired"): ("Cancelado", "Cancelado por expirar luego de 30 días en pendiente."),
            ("cancelled", "by_collector"): ("Cancelado", "Cancelado por el comercio."),
            ("cancelled", "by_payer"): ("Cancelado", "Cancelado por el pagador."),

            ("charged_back", "settled"): ("Contracargo (retenido)", "Dinero retenido tras contracargo."),
            ("charged_back", "reimbursed"): ("Contracargo (reembolsado)", "Dinero devuelto tras contracargo."),
            ("charged_back", "in_process"): ("Contracargo (en proceso)", "Recuperación en proceso por desconocimiento del pagador."),

            ("refunded", "refunded"): ("Reembolsado", "Pago devuelto por el comercio."),
            ("refunded", "by_admin"): ("Reembolsado", "Pago devuelto por el administrador."),

            ("rejected", "bank_error"): ("Rechazado", "Error del banco en transferencia."),
            ("rejected", "cc_rejected_3ds_challenge"): ("Rechazado", "No superó el challenge 3DS."),
            ("rejected", "cc_rejected_3ds_mandatory"): ("Rechazado", "Falta challenge 3DS obligatorio."),
            ("rejected", "cc_rejected_bad_filled_card_number"): ("Rechazado", "Número de tarjeta inválido."),
            ("rejected", "cc_rejected_bad_filled_date"): ("Rechazado", "Fecha de vencimiento inválida."),
            ("rejected", "cc_rejected_bad_filled_other"): ("Rechazado", "Datos incompletos o inválidos."),
            ("rejected", "cc_rejected_bad_filled_security_code"): ("Rechazado", "Código de seguridad inválido."),
            ("rejected", "cc_rejected_blacklist"): ("Rechazado", "No se pudo procesar el pago."),
            ("rejected", "cc_rejected_call_for_authorize"): ("Rechazado", "Debes autorizar el pago con el emisor."),
            ("rejected", "cc_rejected_card_disabled"): ("Rechazado", "Tarjeta deshabilitada; comunícate con el emisor."),
            ("rejected", "cc_rejected_card_error"): ("Rechazado", "No se pudo procesar el pago."),
            ("rejected", "cc_rejected_duplicated_payment"): ("Rechazado", "Ya existe un pago por ese valor."),
            ("rejected", "cc_rejected_high_risk"): ("Rechazado", "Alto riesgo; elige otro medio."),
            ("rejected", "cc_rejected_insufficient_amount"): ("Rechazado", "Fondos insuficientes."),
            ("rejected", "cc_rejected_invalid_installments"): ("Rechazado", "El medio no procesa esa cantidad de cuotas."),
            ("rejected", "cc_rejected_max_attempts"): ("Rechazado", "Límite de intentos alcanzado."),
            ("rejected", "cc_rejected_other_reason"): ("Rechazado", "El medio no procesó el pago."),
            ("rejected", "cc_amount_rate_limit_exceeded"): ("Rechazado", "Excedió el límite del medio de pago."),
            ("rejected", "rejected_insufficient_data"): ("Rechazado", "Falta información obligatoria."),
            ("rejected", "rejected_by_bank"): ("Rechazado", "Rechazado por el banco."),
            ("rejected", "rejected_by_regulations"): ("Rechazado", "Rechazado por regulaciones."),
            ("rejected", "insufficient_amount"): ("Rechazado", "Monto insuficiente."),
        }

        if (s, d) in mapa:
            return mapa[(s, d)]

        # Fallback por status solo (cuando no hay detail o es desconocido)
        fallback_label = {
            "approved": "Aprobado",
            "authorized": "Autorizado",
            "in_process": "En proceso",
            "pending": "Pendiente",
            "cancelled": "Cancelado",
            "charged_back": "Contracargo",
            "refunded": "Reembolsado",
            "rejected": "Rechazado",
        }
        etiqueta = fallback_label.get(s, "Desconocido")
        descripcion = f"Estado: {s or 'desconocido'}"
        if d:
            descripcion += f", detalle: {d}"
        return (etiqueta, descripcion)

    def obtenerPago_manual(self, respuesta):
        try:
            # Intentar parsear JSON (aun cuando haya error HTTP, muchos endpoints lo envían)
            try:
                payload = respuesta['respuesta'].json()
            except ValueError as e:
                payload = None

            # Errores 4xx
            if 400 <= respuesta['respuesta'].status_code < 500:
                msg = None
                if isinstance(payload, dict):
                    # Campos típicos de error en APIs
                    msg = payload.get("message") or payload.get("error") or payload.get("cause")
                return f"Error {respuesta['respuesta'].status_code}: {msg or 'Solicitud inválida'}"

            # Errores 5xx
            if respuesta['respuesta'].status_code >= 500:
                return f"Error {respuesta['respuesta'].status_code}: servidor remoto no disponible"

            # Validar payload
            if not isinstance(payload, dict):
                return f"Error: respuesta['respuesta'] no es JSON válido (status {respuesta['respuesta'].status_code})"

            j = payload

            # Getter seguro para anidados
            def g(d, path, default=None):
                cur = d
                for k in path.split("."):
                    if not isinstance(cur, dict) or k not in cur:
                        return default
                    cur = cur[k]
                return cur
            
            pagos_aceptados = self.obtenerTodosMediosPagos()
            pprint(pagos_aceptados.json())
            
            datos = {
                    'external_reference': g(j, "external_reference"),
                    'idINTEGRACION': respuesta["idINTEGRACION"],
                    'idPOS': g(j, "pos_id"),
                    'idSTORE': g(j, "store_id"),
                    'NomCaja': respuesta["NomCaja"],
                    'NumCajero': respuesta["NumCajero"],
                    'NombreCajero': respuesta["NombreCajero"],
                    'dFechaU': _fecha_argentina(g(j, "date_created"))
                }            
            datos['idPAGO'] = g(j, "id")
            
            if respuesta["idINTEGRACION"] == 1:
                datos["idINTENCION"] = g(j, "metadata.payment_intent_id")
                datos["idPOI"] =  g(j, "additional_info.poi_id")

            # Convertir 'card' a texto JSON si existe y NO está vacío
            card_obj = g(j, "card")

            if isinstance(card_obj, dict) and card_obj:   # dict no vacío
                pagos_aceptados = self.obtenerTodosMediosPagos()
                pprint(pagos_aceptados.json())
                datos["idMetodoPago"] = "Tarjeta"
                datos["cardBIN"] = g(j, "card.bin")
                datos["cardTYPE"] = self._parser_cardTYPE(g(j, "payment_type_id"))
                for pagos in pagos_aceptados.json():
                    if pagos["id"] == g(j, "payment_method_id"):
                        datos["cardNAME"] = pagos['name']
            else:
                datos["idMetodoPago"] = self._parser_idMetodoPago(g(j, "payment_method_id"))
                if datos["idMetodoPago"] == "Billetera Virtual":
                    datos["walletNAME"] = g(j, "point_of_interaction.transaction_data.bank_info.payer.long_name")
            datos["montoPAGO"] = g(j, "transaction_amount")
                
            # Extraer info de refunds (si existe)
            refunds = j.get("refunds") or []
            ultimo_refund = refunds[-1] if refunds else None   # o el primero, según tu criterio

            if ultimo_refund:
                datos["idREEMBOLSO"] = ultimo_refund.get("id") or 0
                # Fecha del refund (si querés que dFechaU represente la fecha del reembolso)
                datos["dFechaU"] = _fecha_argentina(ultimo_refund.get("date_created"))
                # Monto reembolsado: preferí el total del pago si viene; si no, el del último refund
                datos["montoREEMBOLSO"] = (
                    j.get("transaction_amount_refunded")
                    or ultimo_refund.get("amount")
                    or 0.0
                )
            else:
                # Si no hay entries en refunds, asegurá defaults numéricos
                datos["idREEMBOLSO"] = 0
                datos["montoREEMBOLSO"] = j.get("transaction_amount_refunded") or 0.0

                    
            datos["estadoPAGO"], datos["estadoDetallePAGO"] = self._parser_status(g(j, "status"), g(j, "status_detail"))
            
            pprint(datos)
            
            if g(j, "status") == 'rejected' or g(j, "status") == 'cancelled':
                self.conexionDBA.insertar_datos_o_actualizar("PAGOSMERCADOPAGORECHAZADOS", datos)
                self.conexionDBAServer.insertar_datos_o_actualizar("PAGOSMERCADOPAGORECHAZADOS", datos)
            else:
                # Persistencia
                self.conexionDBA.insertar_datos_o_actualizar("PAGOSMERCADOPAGO", datos)
                self.conexionDBAServer.insertar_datos_o_actualizar("PAGOSMERCADOPAGO", datos)

            return respuesta["respuesta"]  # o podés devolver 'datos' si preferís

        except Exception as e:
            tb = traceback.format_exc()
            print(f"obtenerPago_manual() error: {e}\nTraceback:\n{tb}")
            return f"Error interno: {e}"

    
            
            
    """def obtenerPago_manual(self, respuesta):
        try:
            # Intentar parsear JSON (aun cuando haya error HTTP, muchos endpoints lo envían)
            try:
                payload = respuesta.json()
            except ValueError as e:
                payload = None

            # Errores 4xx
            if 400 <= respuesta.status_code < 500:
                msg = None
                if isinstance(payload, dict):
                    # Campos típicos de error en APIs
                    msg = payload.get("message") or payload.get("error") or payload.get("cause")
                return f"Error {respuesta.status_code}: {msg or 'Solicitud inválida'}"

            # Errores 5xx
            if respuesta.status_code >= 500:
                return f"Error {respuesta.status_code}: servidor remoto no disponible"

            # Validar payload
            if not isinstance(payload, dict):
                return f"Error: respuesta no es JSON válido (status {respuesta.status_code})"

            j = payload

            # Getter seguro para anidados
            def g(d, path, default=None):
                cur = d
                for k in path.split("."):
                    if not isinstance(cur, dict) or k not in cur:
                        return default
                    cur = cur[k]
                return cur

            datos = {
                'external_reference': g(j, "external_reference"),
                "collector_id": g(j, "collector_id"),
                "coupon_amount": g(j, "coupon_amount"),
                "currency_id": g(j, "currency_id"),
                "date_approved": g(j, "date_approved"),
                "date_created": g(j, "date_created"),
                "date_last_updated": g(j, "date_last_updated"),
                "date_of_expiration": g(j, "date_of_expiration"),
                "deduction_schema": g(j, "deduction_schema"),
                "description": g(j, "description"),
                "id": g(j, "id"),
                "installments": g(j, "installments"),
                "integrator_id": g(j, "integrator_id"),
                "issuer_id": g(j, "issuer_id"),
                "live_mode": g(j, "live_mode"),
                "marketplace_owner": g(j, "marketplace_owner"),
                "merchant_account_id": g(j, "merchant_account_id"),
                "merchant_number": g(j, "merchant_number"),
                "order_id": g(j, "order.id"),
                "order_type": g(j, "order.type"),
                "payer_id": g(j, "payer.id"),
                "payment_metodo_id": g(j, "payment_method.id"),
                "payment_metodo_issuer_id": g(j, "payment_method.issuer_id"),
                "payment_metodo_type": g(j, "payment_method.type"),
                "pos_id": g(j, "pos_id"),
                "processing_mode": g(j, "processing_mode"),
                "shipping_amount": g(j, "shipping_amount"),
                "sponsor_id": g(j, "sponsor_id"),
                "status": g(j, "status"),
                "status_detail": g(j, "status_detail"),
                "store_id": g(j, "store_id"),
                "taxes_amount": g(j, "taxes_amount"),
                "transaction_amount": g(j, "transaction_amount"),
                "transaction_amount_refunded": g(j, "transaction_amount_refunded"),
                "net_received_amount": g(j, "transaction_details.net_received_amount"),
                "transaction_details_total_paid_amount": g(j, "transaction_details.total_paid_amount"),
            }

            datos_server = {
                'external_reference': g(j, "external_reference"),
                'data': g(j, "id"),
                "collector_id": g(j, "collector_id"),
                "coupon_amount": g(j, "coupon_amount"),
                "currency_id": g(j, "currency_id"),
                "date_approved": g(j, "date_approved"),
                "date_created": g(j, "date_created"),
                "date_last_updated": g(j, "date_last_updated"),
                "date_of_expiration": g(j, "date_of_expiration"),
                "deduction_schema": g(j, "deduction_schema"),
                "description": g(j, "description"),
                "id": g(j, "id"),
                "installments": g(j, "installments"),
                "integrator_id": g(j, "integrator_id"),
                "issuer_id": g(j, "issuer_id"),
                "live_mode": g(j, "live_mode"),
                "marketplace_owner": g(j, "marketplace_owner"),
                "merchant_account_id": g(j, "merchant_account_id"),
                "merchant_number": g(j, "merchant_number"),
                "order_id": g(j, "order.id"),
                "order_type": g(j, "order.type"),
                "payer_id": g(j, "payer.id"),
                "payment_metodo_id": g(j, "payment_method.id"),
                "payment_metodo_issuer_id": g(j, "payment_method.issuer_id"),
                "payment_metodo_type": g(j, "payment_method.type"),
                "pos_id": g(j, "pos_id"),
                "processing_mode": g(j, "processing_mode"),
                "shipping_amount": g(j, "shipping_amount"),
                "sponsor_id": g(j, "sponsor_id"),
                "status": g(j, "status"),
                "status_detail": g(j, "status_detail"),
                "store_id": g(j, "store_id"),
                "taxes_amount": g(j, "taxes_amount"),
                "transaction_amount": g(j, "transaction_amount"),
                "transaction_amount_refunded": g(j, "transaction_amount_refunded"),
                "net_received_amount": g(j, "transaction_details.net_received_amount"),
                "transaction_details_total_paid_amount": g(j, "transaction_details.total_paid_amount"),
            }

            # Convertir 'card' a texto JSON si existe
            card_obj = g(j, "card")
            if isinstance(card_obj, dict):
                card_texto = json.dumps(card_obj, ensure_ascii=False)
                datos['card'] = card_texto
                datos_server['card'] = card_texto

            # Persistencia
            self.conexionDBA.insertar_datos_o_actualizar("MPQRCODE_OBTENERPAGO", datos)
            self.conexionDBAServer.insertar_datos_o_actualizar("MPQRCODE_OBTENERPAGOServer", datos_server)

            return respuesta  # o podés devolver 'datos' si preferís

        except Exception as e:
            # Logueá y devolvé error claro
            print(f"obtenerPago_manual() error: {e}")
            return f"Error interno: {e}"
    """
    def obtenerPagoV2_POINT(self, idpago):
        return self.conexionAPI.obtener_pago(idpago)
    

    def obtenerPago_manualPOINT(self, respuesta, datos_orden):
        if respuesta.status_code < 300:
            try:
                body = respuesta.json()
                status = str(body.get("status", "")).lower()
                print("STATUS:", status)

                # ⛔ No insertar si está rechazado/cancelado
                if status in {"rejected", "cancelled", "canceled"}:
                    print("Pago rechazado/cancelado → no inserto en DB.")
                    return respuesta

                fila = {
                    "external_reference": datos_orden.get("nro_factura"),
                    "id_intencion": _get(body, ["metadata", "payment_intent_id"]),
                    # Evito out-of-range si tu columna es texto o el driver castea
                    "id_pago": str(body.get("id")) if body.get("id") is not None else None,
                    "datos_pago": json.dumps(body, ensure_ascii=False),
                    "NOMCAJA": datos_orden.get("NomCaja"),
                    "NUMCAJERO": datos_orden.get("NumCajero"),
                    "NOMBRECAJERO": datos_orden.get("NombreCajero"),
                    "dFechaU": _fecha_argentina(body.get("date_last_updated") or body.get("date_created")),
                }

                print("ACTUALIZANDO TABLAS: MPQRCODE_OBTENERPAGOPOINT, MPQRCODE_OBTENERPAGOPOINTServer")
                self.conexionDBA.insertar_datos_POINT("MPQRCODE_OBTENERPAGOPOINT", fila)
                self.conexionDBAServer.insertar_datos_POINT("MPQRCODE_OBTENERPAGOPOINTServer", fila)

                return respuesta

            except Exception as e:
                import traceback
                print(f"Error al insertar datos: {e}")
                print(traceback.format_exc())
                return "Error al momento de insertar los datos en el DBA"

        elif respuesta.status_code == 404:
            return "No se ha encontrado el número de operación"
        else:
            try:
                return f"Error {respuesta.status_code, respuesta.json()}"
            except Exception:
                return f"Error {respuesta.status_code}"

            
    def actualizarPago(self, id_pago, dict_datos_actualizar):
        return self.conexionAPI.actualizar_pago(id_pago, dict_datos_actualizar)
            
            
            
    def crearOrdenFULL(self, external_id_pos, nroFactura, sucNAME, montoPagar, pictureURL):
        pago = self.crearOrden(external_id_pos, nroFactura, sucNAME, montoPagar, pictureURL)
        id_pago = self.obteneridOrder(pago[0], pago[1])
        respuesta = self.obtenerPago(id_pago, pago[0], pago[1])
        return respuesta
    
    def crear_orden_reembolso(self, id_pago, monto_devolver):
        respuesta = self.conexionAPI.crear_reembolso(id_pago, monto_devolver)
        print(respuesta.json())
        return respuesta
    
    def cancelarOrden(self, external_id_pos):
        respuesta = self.conexionAPI.eliminar_ordenV2(external_id_pos)
        return respuesta
            
    def eliminarOrdenesPostDBA(self):
        try:
            self.conexionDBA.eliminar_tabla("MPQRCODE_CREARORDEN")
            self.conexionDBA.eliminar_tabla("MPQRCODE_CREARORDEN_items")
            self.conexionDBA.eliminar_tabla("MPQRCODE_RESPUESTAPOST")
            self.conexionDBA.eliminar_tabla("MPQRCODE_OBTENERPAGO")
            self.conexionDBA.crear_tabla_MPQRCODE_CREARORDEN()
            self.conexionDBA.crear_tabla_MPQRCODE_CREARORDEN_items()
            self.conexionDBA.crear_tabla_MPQRCODE_RESPUESTAPOST()
            self.conexionDBA.crear_tabla_MPQRCODE_OBTENERPAGO()
        except Exception as e:
            print(f"Eror: {e}")
            
    def eliminarCAJADBA(self):
        try:
            self.conexionDBA.eliminar_tabla("MPQRCODE_CAJA")
            self.conexionDBA.crear_tabla_MPQRCODE_CAJA()
        except Exception as e:
            print(f"Eror: {e}")            
    #*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*CONEXION MP POINT*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*
    
    def obtenerPointPOS(self, store_id, pos_id):
        respuesta = self.conexionAPI.obtener_dispositivo_POINT(store_id, pos_id).json()
        try:
            pointid = respuesta['devices'][0]['id']
            print(pointid)
            return pointid
        except Exception as e:
            messagebox.showerror("Error al obtener POINT", f"{e}")
            return "No se encontro el dispositivo"
        
    def obtenerALLPointPOS(self):
        respuesta = self.conexionAPI.obtener_dispositivo_POINTALL().json()
        pprint(respuesta)
        try:
            return respuesta
        except IndexError as e:
            messagebox.showerror("Error al obtener POINT", f"{e}")
            return "No se encontro el dispositivo"
        
    def cambiarModoOperacion(self, ID_DEVICE, tipo_operacion):
        respuesta = self.conexionAPI.cambiar_modo_operacion(ID_DEVICE, tipo_operacion)
        return respuesta        
    
    def crearIntencionPAGOPoint(self, deviceid, nro_factura, precio, imprime_ticket):
        TicketNUM = self.generar_ticket_number()
        respuesta = self.conexionAPI.crear_intencion_pago_POINT(deviceid, nro_factura, precio, imprime_ticket, TicketNUM)
        return respuesta
    
    def generar_ticket_number(self):
        prefijo = self.conexionDBA.specify_search_condicion("SPDIR", "ID", "GRID", "pref_tkt_MP", False) #"TKT"  # Opcional, puedes modificarlo
        if not prefijo == None:
            pass
        else:
            prefijo = "TKT"
        timestamp = datetime.now().strftime("%H%M")  # Hora, minutos y segundos
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
        ticket_number = f"{prefijo}{timestamp}{random_part}"
        return ticket_number[:20]  # Garantiza que no supere los 20 caracteres
    
    def cancelarIntencionPAGOPoint(self, deviceid, paymentintentid):
        respuesta = self.conexionAPI.cancelar_intencion_pago_POINT(deviceid, paymentintentid)
        return respuesta
    
    def buscarIntencionPAGOPoint(self, paymentintentid):
        respuesta = self.conexionAPI.buscar_intencion_pago_POINT(paymentintentid)
        print(respuesta)
        return respuesta
    
    def prueba(self):
        return True
    
    def obtenerTodosMediosPagos(self):
        return self.conexionAPI.obtener_todos_medios_pagos()