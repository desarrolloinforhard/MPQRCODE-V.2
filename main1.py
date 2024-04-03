import os
import sys
import mercadopago
import threading
import time
import keyboard
import datetime
directorio_script = os.path.dirname(os.path.abspath(__file__))
# Construir la ruta relativa al directorio que deseas agregar
ruta_relativa = os.path.join(directorio_script, "..")
sys.path.append(ruta_relativa)
from database import ConexionSybase
from Conexion_APIs_MP import Conexion_Api
from conexiones import Conexion_APP
import uuid
import json

datenow = datetime.datetime.now()
fechamodificadaSumandoC = datetime.timedelta(minutes=1)
fechamodificadaSumando = datenow + fechamodificadaSumandoC
fechamodificada = datetime.datetime.strftime(fechamodificadaSumando, '%Y-%m-%dT%H:%M:%S-04:00')
print(fechamodificada)

#-----------------------------------------------------------------------------------------------------------------
#CONEXION A BASE DE DATOS
#Ejemplo de uso
if __name__ == "__main__":
    # Reemplaza los valores con la información correcta para tu conexión Sybase
    configuracion_sybase = {
        "dsn": "GestionIH0101",
        "user": "dba",
        "password": "gestion",
        # Agrega otros parámetros según sea necesario
    }
    
    configuracion_sybaseServer = {
        "user": "dba",
        "password": "gestion",
        "dsn": "GestionIH01"
        # Agrega otros parámetros según sea necesario
    }

    conexion_sybase = ConexionSybase(**configuracion_sybase)
    conexion_sybaseSERVER = ConexionSybase(**configuracion_sybaseServer)

#CONEXION A INTERFAZ MPQRCODE
"""if __name__ == "__main__":
    app = InterfazMercadoPago()
    app.mainloop()"""
    
#print(uuid.uuid4())
print(f"LOCAL = {conexion_sybase.conectar()}")
print(f"SERVER = {conexion_sybaseSERVER.conectar()}")

conexion_sybaseSERVER.crear_tabla_MPQRCODE_CONEXIONSERVIDORAPI()


"""
conexion_sybaseSERVER.actualizar_todos_valores_columna("MPQRCODE_CAJAS", "IPN_url", 'Hola')
"""
"""conexion_sybase.eliminarTablasPOS()
conexion_sybaseSERVER.eliminarTablasSERVER()
"""

"""
conexion_sybaseSERVER.eliminarTablasSERVER()
conexion_sybase.eliminarTablasPOS()
conexion_sybaseSERVER.crearTablasSERVER()
conexion_sybase.crearTablasPOS()
"""
#CONEXION A MODULO API
"""

token_produccion = "APP_USR-1738038690841826-030510-927efd8987f335aae9f84b1e893ea2c9-216258049"
app = (216258049, token_produccion)
mpqr = Conexion_Api(216258049, token_produccion)
#allpoint = mpqr.obtener_dispositivo_POINTALL().json();
#print(allpoint)
respuesta = mpqr.cambiar_modo_operacion('PAX_A910__SMARTPOS1493043847');
print(respuesta.json())"""
"""
# Verifica si la solicitud fue exitosa antes de guardar la respuesta
if respuesta.status_code == 200:
    # Convierte la respuesta JSON en una cadena y formatea para indentar
    json_str = json.dumps(respuesta.json(), indent=4)

    # Guarda la cadena en un archivo
    with open('respuesta.json', 'w') as file:
        file.write(json_str)
    print("Respuesta guardada correctamente en respuesta.json.")
else:
    print("Error al obtener la respuesta:", respuesta.status_code)

"""
"""
token_testPoint = "TEST-6676361482778384-021410-0137c63574899efc84d886a223199d91-1662461858"


token_producccionPoint = "APP_USR-6676361482778384-021410-02393c4d31d08c395a01337ab05fb484-1662461858"
app = (1662461858 , token_producccionPoint)
mppoint = Conexion_APP(app, conexion_sybase, conexion_sybaseSERVER)
respuesta = mppoint.obtenerALLPointPOS()
try:
    print(respuesta)
except IndexError as e:
    print("No se encontro el dispositivo")
"""
"""
c47efc6d-0d2d-402c-ad9f-c32c1de26e32
respuestaPDV = app.cambiar_modo_operacion(pointid)
print(respuestaPDV.json())"""
"""

Obtener Orden 

curl -X GET \
      'https://api.mercadopago.com/instore/qr/seller/collectors/1638020925/pos/SUC002POS001/orders'\
       -H 'Content-Type: application/json' \
       -H 'Authorization: Bearer APP_USR-7733999735236172-011511-5f5ec54efd9876b15a58f185e7cded55-1638020925' \
       


curl -X GET \
      'https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc&external_reference=00000-1113698504&range=date_created&begin_date=NOW-30DAYS&end_date=NOW&store_id=59704658&pos_id=94753127'\
       -H 'Content-Type: application/json' \
       -H 'Authorization: Bearer APP_USR-7733999735236172-011511-5f5ec54efd9876b15a58f185e7cded55-1638020925' \
       

curl -X POST \
      'https://api.mercadopago.com/v1/payments/71532376960/refunds'\
       -H 'Content-Type: application/json' \
       -H 'X-Idempotency-Key: e36859bc-c102-4a8d-8578-1c88e6b05d93' \
       -H 'Authorization: Bearer TEST-7733999735236172-011511-c7b5889198d04f1b1ebd5cd91e87fa3a-1638020925' \

1602259163

curl -X GET \
      'https://api.mercadopago.com/v1/payments/71519312536'\
       -H 'Content-Type: application/json' \
       -H 'Authorization: Bearer APP_USR-7733999735236172-011511-5f5ec54efd9876b15a58f185e7cded55-1638020925' \
           
curl -X GET \
      'https://api.mercadopago.com/v1/payments/71480720616/refunds/1602259163'\
       -H 'Content-Type: application/json' \
       -H 'Authorization: Bearer APP_USR-7733999735236172-011511-5f5ec54efd9876b15a58f185e7cded55-1638020925' \

#print(app.eliminar_orden("SUC002POS001"))
#print(app.reembolso_orden(1456.23, 'SUC002', 'SUC002POS001'))
#print(app.crear_ordenV2(1456.23, 'SUC002', 'SUC002POS001'))
#print(app.crear_orden_dinamico(1234.56, 'SUC002POS001'))
#print(app.obtener_reembolso("15212127111", "70947519443"))
#print(app.crear_cancelacion_compra("70998365349"))
#print(app.crear_reembolso("15212127111", 2134.65))
#print(app.obtener_pago("70998365349").json())

#conexion_sybase.eliminar_tabla("MPQRCODE_CONEXIONPROGRAMAS")
#conexion_sybase.crear_tabla_MPQRCODE_CONEXIONPROGRAMAS()

curl -X GET \
      'https://api.mercadopago.com/v1/payments/15212127111/refunds/1032332129'\
       -H 'Content-Type: application/json' \
       -H 'Authorization: Bearer TEST-7733*********172-01151*********198d04f1b*********e87fa3a-1*********' \
       

curl -X POST \
      'https://api.mercadopago.com/v1/payments/71595570394/refunds'\
       -H 'Content-Type: application/json' \
       -H 'X-Idempotency-Key: 77e1c83b-7bb0-437b-bc50-a7a58e5660ac' \
       -H 'Authorization: Bearer APP_USR-5375149535268319-013107-b85db0849c0e748321c19924762d56da-1662461858' \


curl -X PUT \
      'https://api.mercadopago.com/instore/orders/qr/seller/collectors/1662461858/pos/SUC001POS001/qrs'\
       -H 'Content-Type: application/json' \
       -H 'Authorization: Bearer TEST-5375149535268319-013107-3bdfb97d4a68030b2180942b7e75c8f3-1662461858' \
       -d '{
  "cash_out": {
    "amount": 0
  },
  "description": "Purchase description.",
  "external_reference": "reference_1111112",
  "items": [
    {
      "sku_number": "A123K9191938",
      "category": "marketplace",
      "title": "Point Mini",
      "description": "This is the Point Mini",
      "unit_price": 100,
      "quantity": 1,
      "unit_measure": "unit",
      "total_amount": 100
    }
  ],
  "notification_url": "https://9108-186-122-104-145.ngrok-free.app/",
  "title": "Product order",
  "total_amount": 100
}'
curl -X GET \
      'https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc&external_reference=reference_1111112&range=date_created&begin_date=NOW-30DAYS&end_date=NOW&store_id=59405895&pos_id=95691612'\
       -H 'Content-Type: application/json' \
       -H 'Authorization: Bearer TEST-5375149535268319-013107-3bdfb97d4a68030b2180942b7e75c8f3-1662461858' \

       
curl -X GET \
      'https://api.mercadopago.com/v1/payments/71386689197'\
       -H 'Content-Type: application/json' \
       -H 'Authorization: Bearer APP_USR-5375149535268319-013107-b85db0849c0e748321c19924762d56da-1662461858' \
       

2024-01-31T07:46:13.000-04:00
2024-03-01T08:45:17.000-04:00


curl -X GET \
      'https://api.mercadopago.com/v1/payments/71595176302'\
       -H 'Content-Type: application/json' \
       -H 'Authorization: Bearer APP_USR-5375149535268319-013107-b85db0849c0e748321c19924762d56da-1662461858' \
       

datos = {
    "nro_factura": "00000-11111111",
    "tipo_factura": 1,
    "monto_pagar": 1000,
    "status": 0
}
"""
"""
conexion_sybase.insertar_datos_sin_obtener_id("MPQRCODE_CONEXIONPROGRAMAS", datos)

conexion_sybase.specify_search_all_columns_nocondicion("MPQRCODE_CONEXIONPROGRAMAS")
""""""
conexion_sybaseSERVER.eliminar_tabla("MPQRCODE_OBTENERPAGOServer")
conexion_sybaseSERVER.crear_tabla_MPQRCODE_OBTENERPAGOServer()
"""

"""
/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*LIMPIEZA/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*
instanciacion.limpieza_tabla_sucursal()
instanciacion.limpieza_tabla_caja()
"""
#instanciacion.eliminarCAJADBA()
"""

conexion_sybase.eliminarTablasSERVER()
conexion_sybase.eliminarTablasPOS()
conexion_sybase.crearTablasPOS()
conexion_sybaseSERVER.eliminar_tabla("MPQRCODE_OBTENERPAGOServer")
conexion_sybaseSERVER.crear_tabla_MPQRCODE_OBTENERPAGOServer()


instanciacion.limpieza_tabla_TOTALsucursal()
instanciacion.limpieza_tabla_TOTALcaja()
"""
#instanciacion.eliminarOrdenesPostDBA()


"""
/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*SUCURSAL/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*
"""
#instanciacion.eliminarSUC("SUC002")
"""
datosSUC = {
    'business_hours': {
        'monday': [{'open': '08:00', 'close': '12:00'}], 
        'tuesday': [{'open': '08:00', 'close': '12:00'}], 
        'wednesday': [{'open': '08:00', 'close': '12:00'}], 
        'thursday': [{'open': '08:00', 'close': '12:00'}], 
        'friday': [{'open': '08:00', 'close': '12:00'}], 
        'saturday': [{'open': '08:00', 'close': '12:00'}], 
        'sunday': [{'open': '08:00', 'close': '12:00'}]}, 
    'external_id': 'SUC001', 
    'location': {
        'street_number': '197', 
        'street_name': 'Santa Fe', 
        'city_name': 'Resistencia', 
        'state_name': 'Chaco', 
        'latitude': -27.44817655900252, 
        'longitude': -58.986462728116216, 
        'reference': 'Esquina'}, 
    'name': ' Inforhard'}

instanciacion.creacionSUC(datosSUC)
"""
"""
/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*CAJAS/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*

#instanciacion.eliminarCaja("SUC001POS003")
"""
#instanciacion.crearCaja("SUC001")

#/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*CREAR ORDEN/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*
"""
pago = instanciacion.crearOrden("SUC001POS001", "00000-1111111", "Changuito", 1000, "https://media.istockphoto.com/id/1205419959/es/vector/verduras-en-el-carro-de-la-compra-carrito-logotipo-icono-icono-vector-de-dise%C3%B1o.jpg?s=612x612&w=0&k=20&c=SFUApESf7KXEOLaVQrjUEihs0D8CJOy5nnqmDPQebGg=")
id_pago = instanciacion.obteneridOrder(pago[0], pago[1])
instanciacion.obtenerPago(id_pago, pago[0], pago[1])
"""
"""
datos = {
    'picture_url': "https://media.istockphoto.com/id/1205419959/es/vector/verduras-en-el-carro-de-la-compra-carrito-logotipo-icono-icono-vector-de-dise%C3%B1o.jpg?s=612x612&w=0&k=20&c=SFUApESf7KXEOLaVQrjUEihs0D8CJOy5nnqmDPQebGg="
}

conexion_sybase.actualizar_datos("MPQRCODE_CAJAS", datos, 1)
"""

#print(conexion_sybase.specify_search_condicion("MPQRCODE_SUCURSAL", 'name', 'external_id', 'SUC004'))
"""
conexion_sybase.eliminar_tabla("MPQRCODE_CLIENTE")
conexion_sybase.crear_tabla_MPQRCODE_CLIENTE()
"""
#conexion_sybase.eliminar_filas("MPQRCODE_SUCURSAL", "id", 59270546)


#respuesta1 = app.crear_ordenV2("SUC002", "SUC002POS001")

#respuesta1 = app.obtener_ordenV2("SUC002POS001")
#print(respuesta1)

#Crear Orden DINAMICO
#app.crear_orden_dinamico(1800, "Anonimo", "Ca_0101")

"""
curl -X GET \
      'https://api.mercadopago.com/v1/payments/1317023790'\
       -H 'Content-Type: application/json' \
       -H 'Authorization: Bearer TEST-6676361482778384-021410-0137c63574899efc84d886a223199d91-1662461858' \
       
"""