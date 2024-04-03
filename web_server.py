from flask import Flask, request
import os
import sys
import json
import traceback
directorio_script = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directorio_script)
from database import ConexionSybase
from Conexion_APIs_MP import Conexion_Api
import threading
from datetime import datetime, timedelta


# Obtener la fecha y hora actual
now = datetime.now()

# Calcular la fecha y hora hace 24 horas
twenty_four_hours_ago = now - timedelta(hours=24)

# Formatear las fechas
formato_fecha = now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] 


app = Flask(__name__)

# Variable local para almacenar el valor de "id"
id_value = None
lock = threading.Lock()
#directorio_superior = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
try:
    ruta_configuracioncarpeta = os.path.join(directorio_script, "IPN_Local")
    ruta_configuracion = os.path.join(ruta_configuracioncarpeta, "configuracion.json")
except:
    print("No se encontro la ruta")
print(ruta_configuracion)
try:
    with open(ruta_configuracion, "r") as file:
        configuracion = json.load(file)
        dsn_servidor = configuracion.get("dsn_servidor", "")
except FileNotFoundError:
    # El archivo de configuración no existe, es normal la primera vez
        pass
# Configuración de Sybase
configuracion_sybase = {
    "dsn": dsn_servidor,
    "user": "dba",
    "password": "gestion",
    # Agrega otros parámetros según sea necesario
    }
conexion_sybase = ConexionSybase(**configuracion_sybase)


id_user = conexion_sybase.specify_search("MPQRCODE_CLIENTE", 'idUSER', 1)
token  = conexion_sybase.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKEN', 1)
tokenPOINT = conexion_sybase.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKENPOINT', 1)

conexionMP = Conexion_Api(id_user, token)
conexionMPPOINT = Conexion_Api(id_user, tokenPOINT  )

print(conexion_sybase.conectar())

def obtenerPago(idPago, Existe, nroFactura, tipo_POST):
    if tipo_POST == True:
        respuestaObtenerPago = conexionMP.obtener_pago(idPago)
    else:
        respuestaObtenerPago = conexionMPPOINT.obtener_pago(idPago)
    
    try:
        # Verifica si la respuesta es un objeto JSON válido
        json_response = respuestaObtenerPago.json()
        print(json_response)
    except ValueError as e:
        print(f"Error al parsear la respuesta JSON: {str(e)}")
        return

    datos = {}
                            
    datos['data'] = idPago

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
                    print(valor_json)
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
            if tipo_POST == True:
                columnas = conexion_sybase.obtener_nombres_columnas("MPQRCODE_OBTENERPAGOServer")
            else:
                columnas = conexion_sybase.obtener_nombres_columnas("MPQRCODE_OBTENERPAGOPOINTServer")
            for colum_name in columnas:
                if clave_json == colum_name:
                    datos[clave_json] = valor_json
                else:
                    pass
    print(f"DATOS = {datos}")
    
    if Existe == True:
        if tipo_POST == True:
            print(datos['pos_id'])
            print(conexion_sybase.specify_search_condicionID("MPQRCODE_OBTENERPAGOServer", 'pos_id', 'external_reference', nroFactura, 'pos_id', str(datos['pos_id']), False))
            if datos['pos_id'] == conexion_sybase.specify_search_condicionID("MPQRCODE_OBTENERPAGOServer", 'pos_id', 'external_reference', nroFactura, 'pos_id', str(datos['pos_id']), False):
                print("\nTrue 1\n")
                conexion_sybase.actualizar_datos_condicionID("MPQRCODE_OBTENERPAGOServer", datos, 'external_reference', nroFactura, 'pos_id', datos['pos_id'])
            else:
                print("\nTrue 2\n")
                conexion_sybase.insertar_datos_sin_obtener_id("MPQRCODE_OBTENERPAGOServer", datos)
        else:
            print(datos['pos_id'])
            print(conexion_sybase.specify_search_condicionID("MPQRCODE_OBTENERPAGOPOINTServer", 'pos_id', 'external_reference', nroFactura, 'pos_id', str(datos['pos_id']), False))
            if datos['pos_id'] == conexion_sybase.specify_search_condicionID("MPQRCODE_OBTENERPAGOPOINTServer", 'pos_id', 'external_reference', nroFactura, 'pos_id', str(datos['pos_id']), False):
                print("\nTrue 1\n")
                conexion_sybase.actualizar_datos_condicionID("MPQRCODE_OBTENERPAGOPOINTServer", datos, 'external_reference', nroFactura, 'pos_id', datos['pos_id'])
            else:
                print("\nTrue 2\n")
                conexion_sybase.insertar_datos_sin_obtener_id("MPQRCODE_OBTENERPAGOPOINTServer", datos)
    else:
        if tipo_POST == True:
            print("\nFalse\n")
            conexion_sybase.insertar_datos_sin_obtener_id("MPQRCODE_OBTENERPAGOServer", datos)
        else:
            conexion_sybase.insertar_datos_sin_obtener_id("MPQRCODE_OBTENERPAGOPOINTServer", datos)
        
def posObtnerPago(respuestaObtenerPago, valor_id, data, tipo_POST):
    if tipo_POST == True:
        existe = conexion_sybase.check_existence("MPQRCODE_OBTENERPAGOServer", 'external_reference', respuestaObtenerPago['external_reference'])
    else:
        existe = conexion_sybase.check_existence("MPQRCODE_OBTENERPAGOPOINTServer", 'external_reference', respuestaObtenerPago['external_reference'])
    print(existe)
    if existe and tipo_POST: #Existe en QRCODE
        obtenerPago(valor_id, existe, respuestaObtenerPago['external_reference'], tipo_POST)
        dict_valor = {}
        for clave_json, valor_json in data.items():
            if clave_json == 'data':
                dict_valor[clave_json] = valor_json['id']
            else:
                dict_valor[clave_json] = valor_json
        if conexion_sybase.check_existence("MPQRCODE_RESPUESTAPOST", "data", valor_id):
            del dict_valor['data']
            conexion_sybase.actualizar_datos_condicion("MPQRCODE_RESPUESTAPOST", dict_valor, 'data', valor_id)
        else:
            conexion_sybase.insertar_datos_sin_obtener_id("MPQRCODE_RESPUESTAPOST", dict_valor)
    elif existe and tipo_POST == False: #Existe en Point
        obtenerPago(valor_id, existe, respuestaObtenerPago['external_reference'], tipo_POST)
        dict_valor = {}
        for clave_json, valor_json in data.items():
            if clave_json == 'data':
                dict_valor[clave_json] = valor_json['id']
            else:
                dict_valor[clave_json] = valor_json
        if conexion_sybase.check_existence("MPQRCODE_RESPUESTAPOSTPOINT", "data", valor_id):
            del dict_valor['data']
            conexion_sybase.actualizar_datos_condicion("MPQRCODE_RESPUESTAPOSTPOINT", dict_valor, 'data', valor_id)
        else:
            conexion_sybase.insertar_datos_sin_obtener_id("MPQRCODE_RESPUESTAPOSTPOINT", dict_valor)
    elif existe == False and tipo_POST: #No Existe en QRCode
        dict_valor = {}
        for clave_json, valor_json in data.items():
            if clave_json == 'data':
                dict_valor[clave_json] = valor_json['id']
            else:
                dict_valor[clave_json] = valor_json
        obtenerPago(valor_id, False, None, tipo_POST)
        if conexion_sybase.check_existence("MPQRCODE_RESPUESTAPOST", "data", valor_id):
            del dict_valor['data']
            conexion_sybase.actualizar_datos_condicion("MPQRCODE_RESPUESTAPOST", dict_valor, 'data', valor_id)
        else:
            conexion_sybase.insertar_datos_sin_obtener_id("MPQRCODE_RESPUESTAPOST", dict_valor)
        print(dict_valor)
        print("AGREGADOS EN EL DBA")
    elif existe == False and tipo_POST == False:  #No existe en Point
        dict_valor = {}
        for clave_json, valor_json in data.items():
            if clave_json == 'data':
                dict_valor[clave_json] = valor_json['id']
            else:
                dict_valor[clave_json] = valor_json
        obtenerPago(valor_id, False, None, tipo_POST)
        if conexion_sybase.check_existence("MPQRCODE_RESPUESTAPOSTPOINT", "data", valor_id):
            del dict_valor['data']
            conexion_sybase.actualizar_datos_condicion("MPQRCODE_RESPUESTAPOSTPOINT", dict_valor, 'data', valor_id)
        else:
            conexion_sybase.insertar_datos_sin_obtener_id("MPQRCODE_RESPUESTAPOSTPOINT", dict_valor)
        print(dict_valor)
        print("AGREGADOS EN EL DBA")

@app.route('/', methods=['POST'])
def index():
    try:
        data = request.get_json()
        print("Received JSON:", data)  # Agrega esta línea para imprimir el JSON en la consola

        with lock:  # Utiliza el lock para operaciones seguras en subprocesos
            # Verifica si existe la clave "data" y su valor tiene la clave "id"
            if 'data' in data and 'id' in data['data']:
                valor_id = data['data']['id']
                print(valor_id)
                respuestaObtenerPago = conexionMP.obtener_pago(valor_id).json()
                print(respuestaObtenerPago['message'])
                try:
                    if respuestaObtenerPago['message'] == 'Payment not found':
                        print("Entro If")
                        respuestaObtenerPago = conexionMPPOINT.obtener_pago(valor_id).json()
                        print(respuestaObtenerPago['message'])
                        posObtnerPago(respuestaObtenerPago, valor_id, data)
                except:
                    posObtnerPago(respuestaObtenerPago, valor_id, data)
        return 'OK'
    except Exception as e:
        traceback.print_exc()  # Imprime el traceback en caso de error
        print(f"Error al procesar la solicitud: {str(e)}")
        return 'Error', 500
    finally:
        conexion_sybase.desconectar()  # Asegúrate de cerrar la conexión en cualquier caso
        
@app.route('/MPQRCODE', methods=['POST'])
def mpqrcode():
    try:
        data = request.get_json()
        print("Received JSON at /MPQRCODE:", data)  # Agrega esta línea para imprimir el JSON en la consola

        with lock:  # Utiliza el lock para operaciones seguras en subprocesos
            # Verifica si existe la clave "data" y su valor tiene la clave "id"
            if 'data' in data and 'id' in data['data']:
                valor_id = data['data']['id']
                print(valor_id)
                respuestaObtenerPago = conexionMP.obtener_pago(valor_id).json()
                if not 'message' in respuestaObtenerPago:
                    print(respuestaObtenerPago)
                    print(valor_id, data)
                    posObtnerPago(respuestaObtenerPago, valor_id, data, True)
                else:
                    print(respuestaObtenerPago['message'])
        return 'OK'
    except Exception as e:
        traceback.print_exc()  # Imprime el traceback en caso de error
        print(f"Error al procesar la solicitud: {str(e)}")
        return 'Error', 500
    finally:
        conexion_sybase.desconectar()  # Asegúrate de cerrar la conexión en cualquier caso

@app.route('/MPPOINT', methods=['POST'])
def mppoint():
    try:
        data = request.get_json()
        print("Received JSON at /MPPOINT:", data)  # Agrega esta línea para imprimir el JSON en la consola
        if 'data' in data:
            id_pago_point = data['data']['id']
            respuestaObtenerPago = conexionMPPOINT.obtener_pago(id_pago_point).json()
            if not 'message' in respuestaObtenerPago:
                print(respuestaObtenerPago)
                print(id_pago_point, data)
                posObtnerPago(respuestaObtenerPago, id_pago_point, data, False)
            else:
                print(respuestaObtenerPago['message'])
        elif 'state' in data and data['state'] == 'CANCELED':
            infoIDPOINT = conexionMPPOINT.buscar_intencion_pago_POINT(data['id']).json()
            infoPOINTALL = conexionMPPOINT.obtener_dispositivo_POINTALL().json()
            for key, value in infoPOINTALL.items():
                # Si el valor asociado a la clave es una lista
                if isinstance(value, list):
                    # Iteramos sobre cada elemento de la lista
                    for entryLista in value:
                        # Verificamos si 'id' está presente en el diccionario y si coincide con el valor deseado
                        if 'id' in entryLista and entryLista['id'] == infoIDPOINT['device_id']:
                            print("ID encontrado:", entryLista['id'])
                            # Podemos detener el bucle si encontramos el ID deseado
                            break
                    else:
                        # Este bloque se ejecuta si el bucle for no se detuvo con break, es decir, el ID no se encontró
                        print("ID no encontrado en la lista:", key)
        # Tu lógica para manejar solicitudes POST a la ruta /MPQRCODE aquí

        return 'OK'
    except Exception as e:
        traceback.print_exc()  # Imprime el traceback en caso de error
        print(f"Error al procesar la solicitud en /MPQRCODE: {str(e)}")
        return 'Error', 500


if __name__ == '__main__':
    app.run(port=5000)