import pypyodbc
import json
import traceback


def dsn_configurados():
    try:
        # Obtener una lista de DSNs
        dsn_list = pypyodbc.dataSources()
        return dsn_list
    except pypyodbc.Error as ex:
        print("Error al obtener la lista de DSNs:", ex)

class ConexionSybase:
    def __init__(self, **kwargs):
        self.conexion = None
        self.cursor = None
        self.usuario = kwargs["UID"]
        self.contrasena = kwargs["PWD"]
        self.dsn_name = kwargs["DSN"]

    #CONEXION DE LA BASE DE DATOS
    def conectar(self):
        try:
            self.conexion = pypyodbc.connect(
                DSN=self.dsn_name,
                user=self.usuario,
                password=self.contrasena,
                Driver="{Adaptive Server Anywhere 9.0}",                
            )
            self.cursor = self.conexion.cursor()  # Crea el cursor
            return True
        except pypyodbc.Error as err:
            print(f"Error al conectar a Sybase: {err}")
            return False
        
    def ejecutar_consulta(self, sentencia_sql):
        try:
            # Intentar conectar si no se ha hecho antes
            if not self.conexion:
                self.conectar()

            # Crear un cursor para ejecutar la sentencia SQL
            with self.conexion.cursor() as cursor:
                # Verificación antes de ejecutar la consulta para asegurarse de que la conexión esté activa
                try:
                    # Intentar ejecutar una consulta de prueba (como un SELECT vacío)
                    cursor.execute('SELECT 1')
                except pypyodbc.Error:
                    # Si la conexión se ha cerrado, reconectar
                    self.conectar()
                
                # Ahora ejecutar la consulta principal
                cursor.execute(sentencia_sql)
                
                # Obtener los resultados si la consulta es un SELECT
                if sentencia_sql.strip().upper().startswith('SELECT'):
                    resultados = cursor.fetchall()
                    return resultados
                else:
                    # Para otros tipos de consultas (INSERT, UPDATE, DELETE)
                    self.conexion.commit()
                    return "Operación exitosa"

        except pypyodbc.Error as e:
            error_traceback = traceback.format_exc()
            print(f"Error al recargar dispositivos: {e}\nTraceback:\n{error_traceback}")
            print(f"Error al ejecutar la consulta: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado: {e}")
            return None



        
    def conectarServer(self):
        try:
            self.conexion = pypyodbc.connect(
                DSN=self.dsn_name,  # Nombre del DSN configurado en tu sistema
                user=self.usuario,
                password=self.contrasena,
                Driver="{Adaptive Server Anywhere 9.0}"                
            )
            self.cursor = self.conexion.cursor()  # Crea el cursor
            return True
        except pypyodbc.Error as err:
            print(f"Error al conectar a Sybase: {err}")
            return False
        
        
    #MANEJO A LA BASE DE DATOS
    def eliminar_base_de_datos(self, nombre_bd):
        try:
            with self.conexion.cursor() as cursor:
                consulta = f"DROP DATABASE {nombre_bd}"
                cursor.execute(consulta)
                print(f"Base de datos '{nombre_bd}' eliminada exitosamente.")
        except pypyodbc.Error as err:
            print(f"Error al eliminar la base de datos: {err}")
            
        
    #MANEJOS DE TABLAS 
    
    def crear_tabla_MPQRCODE_CONEXIONSERVIDORAPI(self):
        try:
            self.conectar()
            query = f"""
                CREATE TABLE MPQRCODE_CONEXIONSERVIDORAPI (
                    id INT PRIMARY KEY NOT NULL,
                    status VARCHAR(15),
                    ultima_actualizacion VARCHAR(30)
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print(f'Tabla MPQRCODE_CONEXIONSERVIDORAPI creada con éxito.')
        except Exception as e:
            print(f'Error al crear la tabla: {e}')   
    
    def crear_tabla_MPQRCODE_CONEXIONPROGRAMAS(self):
        try:
            self.conectar()
            query = f"""
                CREATE TABLE MPQRCODE_CONEXIONPROGRAMAS (
                    nro_factura VARCHAR(16),
                    tipo_factura INT,
                    monto_pagar MONEY,
                    status BIT,
                    response FLOAT,
                    description VARCHAR(255),
                    tipo_point INT,
                    IDMercadoPago VARCHAR(255),
                    NOMCAJA VARCHAR(255),
                    NUMCAJERO VARCHAR(255),
                    NOMBRECAJERO VARCHAR(255)
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print(f'Tabla MPQRCODE_CONEXIONPROGRAMAS creada con éxito.')
        except Exception as e:
            print(f'Error al crear la tabla: {e}')
    
    def crear_tabla_MPQRCODE_CLIENTE(self):
        try:
            self.conectar()
            query = f"""
                CREATE TABLE MPQRCODE_CLIENTE (
                    idINCREMENT INT IDENTITY PRIMARY KEY,
                    idUSER VARCHAR(255),
                    AUTH_TOKEN VARCHAR(255),
                    AUTH_TOKENPOINT VARCHAR(255)
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print(f'Tabla MPQRCODE_CLIENTE creada con éxito.')
        except Exception as e:
            print(f'Error al crear la tabla: {e}')

    def crear_tabla_MPQRCODE_SUCURSAL(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_SUCURSAL (
                    idINCREMENT INT IDENTITY PRIMARY KEY, 
                    id VARCHAR(255), 
                    name VARCHAR(255), 
                    date_creation VARCHAR(255),
                    external_id VARCHAR(255),
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_SUCURSAL creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
            
    def crear_tabla_MPQRCODE_SUCURSAL_business_hours(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_SUCURSAL_business_hours (
                    idSUC VARCHAR(255),
                    DIA VARCHAR(255),
                    open_business_hours VARCHAR(255),
                    close_business_hours VARCHAR(255)                    
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_SUCURSAL creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
            
    def crear_tabla_MPQRCODE_SUCURSAL_location(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_SUCURSAL_location (
                    idSUC VARCHAR(255),
                    address_line VARCHAR(255),
                    reference_location VARCHAR(255),
                    latitude FLOAT,
                    longitude FLOAT,
                    id VARCHAR(255),
                    type VARCHAR(255),
                    city VARCHAR(255),
                    state_id VARCHAR(255)                    
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_SUCURSAL creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
        
    
    def crear_tabla_MPQRCODE_CAJAS(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_CAJAS (
                    idINCREMENT INT IDENTITY PRIMARY KEY, 
                    id BIGINT, 
                    status VARCHAR(255), 
                    date_created VARCHAR(255), 
                    date_last_updated VARCHAR(255), 
                    uuid VARCHAR(255), 
                    user_id BIGINT, 
                    name VARCHAR(255), 
                    fixed_amount VARCHAR(255), 
                    category BIGINT, 
                    store_id VARCHAR(255), 
                    external_store_id VARCHAR(255), 
                    external_id VARCHAR(255), 
                    site VARCHAR(255), 
                    qr_code VARCHAR(255),
                    picture_url VARCHAR(255),
                    IPN_url VARCHAR(255)
                ) 
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_CAJAS creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
            
    def crear_tabla_MPQRCODE_CAJAS_qr(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_CAJAS_qr (
                    id_POS BIGINT,
                    external_id VARCHAR(255),
                    image VARCHAR(255),
                    template_document VARCHAR(255),
                    template_image VARCHAR(255)
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_CAJAS_qr creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
            
    def crear_tabla_MPQRCODE_CAJA(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_CAJA (
                    idINCREMENT INT IDENTITY PRIMARY KEY,
                    sucNAME VARCHAR(255),
                    posNAME VARCHAR(255),
                    external_id_pos VARCHAR(255),
                    IPN_url VARCHAR(255)
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_CAJA creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")

    def crear_tabla_MPQRCODE_CREARORDEN(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_CREARORDEN (
                    idINCREMENT INT IDENTITY, 
                    date_creation DATETIME,
                    external_reference VARCHAR(255) PRIMARY KEY,
                    external_idPOS VARCHAR(255),
                    id VARCHAR(255),
                    collector_id BIGINT, 
                    collector VARCHAR(255), 
                    total_amount FLOAT, 
                    amount FLOAT, 
                    operation_type VARCHAR(255),
                    marketplace VARCHAR(255), 
                    marketplace_fee VARCHAR(255), 
                    sponsor_id BIGINT, 
                    notification_url VARCHAR(255), 
                    expiration_date_to VARCHAR(255),                    
                    expires VARCHAR(255), 
                    additional_info VARCHAR(255), 
                    site_id VARCHAR(255), 
                    client_id BIGINT, 
                    processing_modes VARCHAR(255),
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_CREARORDEN creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
            
    def crear_tabla_MPQRCODE_CREARORDEN_items(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_CREARORDEN_items (
                    external_reference VARCHAR(255),
                    idMERCADERIA VARCHAR(255),
                    category_id VARCHAR(255),
                    title VARCHAR(255),
                    quantity BIGINT,
                    currency_id VARCHAR(255),
                    unit_price FLOAT,
                    description VARCHAR(255),
                    picture_url VARCHAR(255)
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_CREARORDEN_items creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
            
    def crear_tabla_MPQRCODE_RESPUESTAPOST(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_RESPUESTAPOST (
                    action VARCHAR(255), 
                    api_version VARCHAR(255), 
                    data VARCHAR(255) PRIMARY KEY, 
                    date_created VARCHAR(255), 
                    id BIGINT, 
                    live_mode VARCHAR(255), 
                    type VARCHAR(255), 
                    user_id VARCHAR(255)
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_RESPUESTAPOST creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
            
    def crear_tabla_MPQRCODE_RESPUESTAPOSTPOINT(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_RESPUESTAPOSTPOINT (
                    action VARCHAR(255), 
                    api_version VARCHAR(255), 
                    data VARCHAR(255) PRIMARY KEY, 
                    date_created VARCHAR(255), 
                    id BIGINT, 
                    live_mode VARCHAR(255), 
                    type VARCHAR(255), 
                    user_id VARCHAR(255)                    
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_RESPUESTAPOSTPOINT creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
            
    def crear_tabla_MPQRCODE_OBTENERPAGO(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_OBTENERPAGO (
                    external_reference VARCHAR(255),
                    external_idPOS VARCHAR(255),
                    collector_id BIGINT, 
                    coupon_amount BIGINT, 
                    currency_id VARCHAR(255), 
                    date_approved VARCHAR(255), 
                    date_created VARCHAR(255), 
                    date_last_updated VARCHAR(255), 
                    date_of_expiration VARCHAR(255), 
                    deduction_schema VARCHAR(255), 
                    description VARCHAR(255),
                    id BIGINT, 
                    installments INT, 
                    integrator_id VARCHAR(255), 
                    issuer_id VARCHAR(255), 
                    live_mode VARCHAR(255), 
                    marketplace_owner VARCHAR(255), 
                    merchant_account_id VARCHAR(255), 
                    merchant_number VARCHAR(255),
                    order_id VARCHAR(255),
                    order_type VARCHAR(255),
                    payer_id VARCHAR(255),
                    payment_metodo_id VARCHAR(255),
                    payment_metodo_issuer_id VARCHAR(255),
                    payment_metodo_type VARCHAR(255),
                    pos_id  VARCHAR(255), 
                    processing_mode  VARCHAR(255),
                    shipping_amount BIGINT, 
                    sponsor_id  VARCHAR(255), 
                    status  VARCHAR(255), 
                    status_detail  VARCHAR(255), 
                    store_id  VARCHAR(255),
                    taxes_amount BIGINT, 
                    transaction_amount FLOAT, 
                    transaction_amount_refunded FLOAT,
                    net_received_amount FLOAT, 
                    transaction_details_total_paid_amount VARCHAR(255),
                    NomCaja VARCHAR(255),
                    NumCajero VARCHAR(255),
                    NombreCajero VARCHAR(255)
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_OBTENERPAGO creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
            
    def recrear_tabla_MPQRCODE_OBTENERPAGO(self): #05-11-24
        try:
            self.conectar()

            # Paso 1: Renombrar la tabla actual a _old
            self.cursor.execute("ALTER TABLE MPQRCODE_OBTENERPAGO RENAME MPQRCODE_OBTENERPAGO_old;")
            self.conexion.commit()

            # Paso 2: Crear la nueva tabla
            self.crear_tabla_MPQRCODE_OBTENERPAGO()

            # Paso 3: Copiar los datos de la tabla antigua a la nueva
            query_copy = """
                INSERT INTO MPQRCODE_OBTENERPAGO (external_reference, external_idPOS, collector_id, coupon_amount, 
                                                currency_id, date_approved, date_created, date_last_updated, 
                                                date_of_expiration, deduction_schema, description, id, installments, 
                                                integrator_id, issuer_id, live_mode, marketplace_owner, 
                                                merchant_account_id, merchant_number, order_id, order_type, payer_id, 
                                                payment_metodo_id, payment_metodo_issuer_id, payment_metodo_type, pos_id, 
                                                processing_mode, shipping_amount, sponsor_id, status, status_detail, 
                                                store_id, taxes_amount, transaction_amount, transaction_amount_refunded,
                                                transaction_details_total_paid_amount, NomCaja, 
                                                NumCajero, NombreCajero)
                SELECT external_reference, external_idPOS, collector_id, coupon_amount, currency_id, date_approved, 
                    date_created, date_last_updated, date_of_expiration, deduction_schema, description, id, 
                    installments, integrator_id, issuer_id, live_mode, marketplace_owner, merchant_account_id, 
                    merchant_number, order_id, order_type, payer_id, payment_metodo_id, payment_metodo_issuer_id, 
                    payment_metodo_type, pos_id, processing_mode, shipping_amount, sponsor_id, status, status_detail, 
                    store_id, taxes_amount, transaction_amount, transaction_amount_refunded, transaction_details_total_paid_amount, NomCaja, NumCajero, NombreCajero 
                FROM MPQRCODE_OBTENERPAGO_old;
            """
            self.cursor.execute(query_copy)
            self.conexion.commit()

            # Paso 4: Eliminar la tabla antigua
            self.cursor.execute("DROP TABLE MPQRCODE_OBTENERPAGO_old;")
            self.conexion.commit()

            print("Tabla MPQRCODE_OBTENERPAGO recreada con éxito.")
        except Exception as e:
            print(f"Error al recrear la tabla: {e}")

    
    def crear_tabla_MPQRCODE_OBTENERPAGOPOINT(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_OBTENERPAGOPOINT (
                    external_reference VARCHAR(255),
                    external_idPOS VARCHAR(255),
                    collector_id BIGINT, 
                    coupon_amount BIGINT, 
                    currency_id VARCHAR(255), 
                    date_approved VARCHAR(255), 
                    date_created VARCHAR(255), 
                    date_last_updated VARCHAR(255), 
                    date_of_expiration VARCHAR(255), 
                    deduction_schema VARCHAR(255), 
                    description VARCHAR(255),
                    id BIGINT, 
                    installments INT, 
                    integrator_id VARCHAR(255), 
                    issuer_id VARCHAR(255), 
                    live_mode VARCHAR(255), 
                    marketplace_owner VARCHAR(255), 
                    merchant_account_id VARCHAR(255), 
                    merchant_number VARCHAR(255),
                    order_id VARCHAR(255),
                    order_type VARCHAR(255),
                    payer_id VARCHAR(255),
                    payment_metodo_id VARCHAR(255),
                    payment_metodo_issuer_id VARCHAR(255),
                    payment_metodo_type VARCHAR(255),
                    pos_id  VARCHAR(255), 
                    processing_mode  VARCHAR(255),
                    shipping_amount BIGINT, 
                    sponsor_id  VARCHAR(255), 
                    status  VARCHAR(255), 
                    status_detail  VARCHAR(255), 
                    store_id  VARCHAR(255),
                    taxes_amount BIGINT, 
                    transaction_amount FLOAT, 
                    transaction_amount_refunded FLOAT,
                    net_received_amount FLOAT, 
                    transaction_details_total_paid_amount VARCHAR(255),
                    NomCaja VARCHAR(255),
                    NumCajero VARCHAR(255),
                    NombreCajero VARCHAR(255)
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_OBTENERPAGOPOINT creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
            
            
    def crear_tabla_MPQRCODE_OBTENERPAGOServer(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_OBTENERPAGOServer (
                    external_reference VARCHAR(255),
                    data VARCHAR(255),
                    collector_id BIGINT, 
                    coupon_amount BIGINT, 
                    currency_id VARCHAR(255), 
                    date_approved VARCHAR(255), 
                    date_created VARCHAR(255), 
                    date_last_updated VARCHAR(255), 
                    date_of_expiration VARCHAR(255), 
                    deduction_schema VARCHAR(255), 
                    description VARCHAR(255),
                    id BIGINT, 
                    installments INT, 
                    integrator_id VARCHAR(255), 
                    issuer_id VARCHAR(255), 
                    live_mode VARCHAR(255), 
                    marketplace_owner VARCHAR(255), 
                    merchant_account_id VARCHAR(255), 
                    merchant_number VARCHAR(255),
                    order_id VARCHAR(255),
                    order_type VARCHAR(255),
                    payer_id VARCHAR(255),
                    payment_metodo_id VARCHAR(255),
                    payment_metodo_issuer_id VARCHAR(255),
                    payment_metodo_type VARCHAR(255),
                    pos_id  VARCHAR(255), 
                    processing_mode  VARCHAR(255),
                    shipping_amount BIGINT, 
                    sponsor_id  VARCHAR(255), 
                    status  VARCHAR(255), 
                    status_detail  VARCHAR(255), 
                    store_id  VARCHAR(255),
                    taxes_amount BIGINT, 
                    transaction_amount FLOAT, 
                    transaction_amount_refunded FLOAT,
                    net_received_amount FLOAT,  
                    transaction_details_total_paid_amount VARCHAR(255),
                    NomCaja VARCHAR(255),
                    NumCajero VARCHAR(255),
                    NombreCajero VARCHAR(255)
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_OBTENERPAGOServer creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
            
    def recrear_tabla_MPQRCODE_OBTENERPAGOServer(self):
        try:
            self.conectar()

            # Paso 1: Renombrar la tabla actual a _old
            self.cursor.execute("ALTER TABLE MPQRCODE_OBTENERPAGOServer RENAME MPQRCODE_OBTENERPAGOServer_old;")
            self.conexion.commit()

            # Paso 2: Crear la nueva tabla
            self.crear_tabla_MPQRCODE_OBTENERPAGOServer()

            # Paso 3: Copiar los datos de la tabla antigua a la nueva
            query_copy = """
                INSERT INTO MPQRCODE_OBTENERPAGOServer (external_reference, data, collector_id, coupon_amount, 
                                                        currency_id, date_approved, date_created, date_last_updated, 
                                                        date_of_expiration, deduction_schema, description, id, 
                                                        installments, integrator_id, issuer_id, live_mode, 
                                                        marketplace_owner, merchant_account_id, merchant_number, 
                                                        order_id, order_type, payer_id, payment_metodo_id, 
                                                        payment_metodo_issuer_id, payment_metodo_type, pos_id, 
                                                        processing_mode, shipping_amount, sponsor_id, status, 
                                                        status_detail, store_id, taxes_amount, transaction_amount, 
                                                        transaction_amount_refunded,
                                                        transaction_details_total_paid_amount, NomCaja, NumCajero, 
                                                        NombreCajero)
                SELECT external_reference, data, collector_id, coupon_amount, currency_id, date_approved, 
                    date_created, date_last_updated, date_of_expiration, deduction_schema, description, id, 
                    installments, integrator_id, issuer_id, live_mode, marketplace_owner, merchant_account_id, 
                    merchant_number, order_id, order_type, payer_id, payment_metodo_id, payment_metodo_issuer_id, 
                    payment_metodo_type, pos_id, processing_mode, shipping_amount, sponsor_id, status, status_detail, 
                    store_id, taxes_amount, transaction_amount, transaction_amount_refunded,
                    transaction_details_total_paid_amount, NomCaja, NumCajero, NombreCajero 
                FROM MPQRCODE_OBTENERPAGOServer_old;
            """
            self.cursor.execute(query_copy)
            self.conexion.commit()

            # Paso 4: Eliminar la tabla antigua
            self.cursor.execute("DROP TABLE MPQRCODE_OBTENERPAGOServer_old;")
            self.conexion.commit()

            print("Tabla MPQRCODE_OBTENERPAGOServer recreada con éxito.")
        except Exception as e:
            print(f"Error al recrear la tabla: {e}")

            
    def crear_tabla_MPQRCODE_OBTENERPAGOPOINTServer(self):
        try:
            self.conectar()
            query = """
                CREATE TABLE MPQRCODE_OBTENERPAGOPOINTServer (
                    external_reference VARCHAR(255),
                    data_pagos TEXT,
                    NomCaja VARCHAR(255),
                    NumCajero VARCHAR(255),
                    NombreCajero VARCHAR(255)
                )
            """
            self.cursor.execute(query)
            self.conexion.commit()
            print("Tabla MPQRCODE_OBTENERPAGOPOINTServer creada con éxito.")
        except Exception as e:
            print(f"Error al crear la tabla: {e}")
            
            
    # DESCONECTAR DE LA BASE DE DATOS
    def desconectar(self):
        try:
            if self.conexion and self.conexion.connected:
                self.conexion.close()
            else:
                print("La conexión ya estaba cerrada.")
        except pypyodbc.Error as err:
            print(f"Error al cerrar la conexión: {err}")