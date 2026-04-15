from Conf.GUIENLACECREARORDENV2 import EnlaceCrearOrden

__version__ = "5.10.7"
print(f"__version__ = {__version__}")


if __name__ == "__main__":
    config = EnlaceCrearOrden(__version__)
    
    
"""
2.0.0 Nueva version, mejor funcionamiento, se agregaroon la funcionalidad de threading, se usa tkbootstrap. Solo
se puede crear un orden de pago.

3.0.0 Se agrega la funcion de reembolso ademas del pago.

4.0.0 Se agrega la funcion para generar ordenes al POINT y Obtener ordenes, comparar los resultados y asegurar lo recibido...

4.5.0 Se agrega la funcion para buscar una Orden Manual x ID.

4.6.0 La funcion para busqueda Manual y Reembolso han cambiado ahora preguntan el tipo de pago que desean buscar o delvolver.
    NUEVA VARIABLE = MP_POINT >
    MP_POINT_PRINT >
    pref_tkt_MP > POR DEFECTO ES TKT. SIRVE PARA INDICAR EL PREFIJO EN EL NªTICKET. MIN 1 CARACTER MAX 5 CARACTERES. OBS AGREGAR 6 CARACTERES 
4.6.32 Se agrego el aviso a la BASE para los errores tendria que notificar y cancelar.
4.6.33 Errores al dar NoteType en el Point >  Monto_recibido = self.datos_pagos["transaction_amount"]
4.6.38 Errores que no tomaba el MP_POINT_PRINT, se cambio que las variables vallan a la base de las cajas
4.7.9 En el reembolso ya no pregunta mas de donde es el reembolso automaticamente va y lo busca en la base
4.7.16 En la busqueda manual de un pago mandando la opcion 9, ya no pregunta más solo pide ID.
4.8.25 Se agrego el modulo personalizado de Messagebox, para poder definir los font y el geomtry
4.9.12 Se agrego el modulo de tecladohasar, para poder dar uso a los teclado viejos y nuevos, y tiene mas versatilidad el modulo
4.10.0 Se implementó reintento automático de hasta 3 veces en el envío de órdenes de pago, órdenes al POINT y reembolsos para mejorar la estabilidad del sistema ante errores de conexión o API.  
        Se agregaron logs detallados en los principales puntos de interacción del usuario y errores críticos para mejorar el seguimiento y depuración.  
        Se mejoró la gestión de cierres forzados, permitiendo matar el proceso incluso si hay hilos en ejecución.  
        Se añadieron mejoras menores en validaciones internas y mensajes al usuario.
4.10.1 Solucion a bugs que no avisaba al facturador...
4.11.4 Solucion cuando se corta ARCA y se guarda con la factura del CAE y tiene que cambiar a CAE-A
4.12.0 Validación de medios de pago PBS:
    Se agregó una función de verificación (comprobación_PBS) que valida si el método y tipo de pago son compatibles con los disponibles para PBS.
    En caso de no ser válidos, el sistema devuelve el error 15 e interrumpe la operación con un mensaje explicativo.

    Nuevo código de error 15:
    Se agregó al listado de errores un mensaje que informa al usuario si el medio de pago no está habilitado para descuentos de PBS.
    Se incluyen los métodos de pago válidos detectados dinámicamente.

    Refactor en flujo de comparación de pagos:
    La validación PBS fue integrada al inicio del proceso de comparación para asegurar coherencia antes de validar monto, fecha y referencia externa.

    Manejo de errores mejorado:
    Se agregó control de excepción para error
    es internos al validar PBS y se asigna el código 1001 en caso de error no registrado.
4.12.1 Se corrigio error de funcion mal llamada, "ejecutar_sentencia" en modulo QR
4.12.2 Se corrigio error de funcion mal llamada, "ejecutar_sentencia" en Modulo POINT y BuscarPago
5.0.0 Se agrega en conjunto del modulo de Clover para trabajar con ellos.
5.0.1 Corrección de modulo mal margeados (casi pierdo lo del PBS)
5.1.1 Va con la version 1.0.6 del modulo de Clover
5.1.2 Va con la version 1.0.8 del modulo de Clover
5.1.3 Va con la version 1.0.9 del modulo de Clover
5.1.17 Va con la version 1.0.10 del modulo de Clover y con mejoras del teclado hasar. Como el Subtotal o PagoEfectivo. En los CustomMessagebox
5.1.20 Va con la version 1.1.12 del modulo de Clover y con mejoras del teclado hasar
5.1.21 Va con la version 1.2.8 del modulo de Clover y para verificación del PBS
5.1.24 Mejorars en el Flujo de PBS
5.2.1 Esta va incluido con lectura del archivo DBF para conectarse a la base, Ya no se necesito configurar los DNS
5.2.2 va con Clover 1.2.15
5.2.3 va con Clover 1.2.12
5.2.4 Se agrega comparacion de estado canceled para pagos QR y POINT
5.5.5 va con Clover 1.2.23
5.5.6 Solucionado problema no abre ventana de BuscarPagoMP en Tarjetas
5.5.7 Solucionado problema Cuando salta cancelado y cancela la orden cerraba igual
5.5.8 Error de modeulos de importacion
5.6.10 Va con Clover 1.3.15. Tambien se realizaron cambios grandes en tecladohaso, y va con la V3, Cambio de Logica. Tambien se actulizo el MessageBox(Clover y MP son distintos)
5.6.11 Se agrega la fucnion automatizada en tecladohasar para agregar y dectectar automitacmetne y mandar escaneer.
5.6.12 Bug solucionado del POINT, mal la vairbale NOMCAJA
5.7.0 Se cambia modulo de CrearOrdenPagoV2 por CrearOrdenPagoV3.
5.7.1 En nuevo modulo CrearOrdenPagoV3 se cambia el flujo de pagos
5.7.2 En modulo CustomMessagebox se agrega mas ventanas de para interactuar nueva versiones. Reintentar y Continuar.
5.7.3 Solucion bug de funcion ejecutar_datos_pbs trae de manera correctas los medias disponibles en todos los modulos
5.7.7 Se cambio funcionalidad en el POINT para que se pueden tamar los pagos deslas Inteciones de Pago y asi poder Generar mas ordenes con un mismo nro de factura
5.7.8 Se cambio funcionalidad en EL MODULO DE REEMBOLSOS cuando se tiene que ser por POINT ya que puede tener varias factuar asi que haroa cmpara tambien el monto que pide. TIENE QUE SER MONTO TOTAL
5.8.1 Se agrega la tabla PAGOSMERCADOPAGO y PAGOSMERCADOPAGORECHAZADOS ya que se cambio forma de trabar las tablas y los datos que guardan.
    Ya no se guedan los pagos del QR y POINT separados, mas bien se reorganizo la tabla de MPQRCODE_OBTENERPAGO y MPQRCODE_OBTERNERPAGOServer en PAGOSMERCADOPAGO, se guardan los pagos alli y se diferencian por idINTEGRACION (0 QR y 1 POINT)
    Se modificaron los modulos de CrearOrdenPagoV3, CrearOrdenPagoPOINT y CrearOrdenReembolso que se adaptan a esta nueva modalidad.
5.8.2 Bug de walletNAME
5.9.0 Esta Version va con CrearOrdenPagoV4 que ya introduce la nueva creacion de QR desde la nueva API de MercadoPagos
5.9.1 Se agrega las variebles  self.Monto_Recargo y self.Nro_Cuotas CrearOrdenPagoV4 y en CrearOrdenPOINT junto con la nueva funcio para calcular las cuotas y monto de recargo.
5.9.2 Va con clover 1.3.20
5.9.3 Va con clover 1.3.21
5.9.4 Va con clover     
5.9.5 Se resuelve Bug de pagos devuelto a Jose en los reembolsos. Ahora pas de forma correcta el medio de pago de cada Orden de Reembolso
5.10.0 Va con clover 1.3.26 y ademas trabaja con version web_server 3.6.0 que agregas funcion de token_refresh
5.10.1 Va con clover 1.4.0
5.10.2 Va con clover 1.4.5 y actulizacion de tabla CLOVER_PAGO_QR
5.10.3 Va con clover 1.4.6
5.10.4 Va con clover 1.4.7 
5.10.5 Va con clover 1.4.8
5.10.6 Va con clover 1.4.9
5.10.8 Va con clover 1.4.10
"""