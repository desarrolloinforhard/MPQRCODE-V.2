import threading
import time
import os
import json
import pytz
from ctk_components import CTkNotification
from dateutil import parser
from tkinter import Tk, messagebox
from database import ConexionSybase
from datetime import datetime

class ConexionEnvioServerCentral:
    def __init__(self):
        self.dsn_caja = None
        self.dsn_servidor = None
        self.dsn_servidor_central = None
        self.conexion = False
        self.cargar_configuracion()
        
        if self.dsn_caja and self.dsn_servidor:
            try:
                self.conexionDBASERVER = ConexionSybase(
                    user="dba",
                    password="gestion",
                    dsn=self.dsn_servidor
                )
                
                if self.dsn_servidor_central:
                    self.conexionDBACENTRAL = ConexionSybase(
                        user="dba",
                        password="gestion",
                        dsn=self.dsn_servidor_central
                    )
                    if self.conexionDBASERVER.conectar() and self.conexionDBACENTRAL.conectar():
                        self.conexion = True
                    else:
                        self.conexion = False
                else:
                    self.mostrar_error("No hay conexión con Servidor Central. Fíjese en la configuración de los DSN")
            except Exception as e:
                self.mostrar_error(f"Error al conectar con la base de datos: {str(e)}")
        else:
            self.mostrar_error("No hay conexión con ningún Servidor")
        
    def cargar_configuracion(self):
        try:
            directorio_script_json = os.path.dirname(os.path.abspath(__file__))
            ruta_relativaJSON = os.path.join(directorio_script_json, "configuracion.json")
            
            with open(ruta_relativaJSON, "r") as file:
                configuracion = json.load(file)
                self.dsn_caja = configuracion.get("dsn_caja")
                self.dsn_servidor = configuracion.get("dsn_servidor")
                self.dsn_servidor_central = configuracion.get("dsn_servidor_central")
                
            print(self.dsn_caja, self.dsn_servidor)
            self.tipo_operador = self.dsn_caja == self.dsn_servidor
        except FileNotFoundError:
            self.mostrar_error("El archivo de configuración no existe.")
        except json.JSONDecodeError:
            self.mostrar_error("Error al leer el archivo de configuración.")
        except Exception as e:
            self.mostrar_error(f"Error inesperado: {str(e)}")
    
    def mostrar_error(self, mensaje):
        root = Tk()
        root.withdraw()
        messagebox.showerror("Error", mensaje)
        root.destroy()
        
    def conexiones_dba(self):
        return self.conexionDBASERVER, self.conexionDBACENTRAL
        
class EnvioServerCentral:
    def __init__(self, conexionDBACENTRAL, datos, label_aviso_actulizar=None, ventana_envio=None):
        self.conexionDBACENTRAL = conexionDBACENTRAL
        datos_env = 0
        for dato in datos:
            if not label_aviso_actulizar == None:
                label_aviso_actulizar.configure(text=f"Enviando datos de la Factura {dato[0]}")
            time.sleep(1)
            datos_dict = {
                "external_reference": dato[0], 
                "external_idPOS": dato[1],
                "collector_id": dato[2],
                "coupon_amount": dato[3],
                "currency_id": dato[4],
                "date_approved": dato[5],
                "date_created": dato[6],
                "date_last_updated": dato[7],
                "date_of_expiration": dato[8],
                "deduction_schema": dato[9],
                "description": dato[10],
                "id": dato[11],
                "installments": dato[12],
                "integrator_id": dato[13],
                "issuer_id": dato[14],
                "live_mode": dato[15],
                "marketplace_owner": dato[16],
                "merchant_account_id": dato[17],
                "merchant_number": dato[18],
                "order_id": dato[19],
                "order_type": dato[20],
                "payer_id": dato[21],
                "payment_metodo_id": dato[22],
                "payment_metodo_issuer_id": dato[23],
                "payment_metodo_type": dato[24],
                "pos_id": dato[25],
                "processing_mode": dato[26],
                "shipping_amount": dato[27],
                "sponsor_id": dato[38],
                "status": dato[29],
                "status_detail": dato[30],
                "store_id": dato[31],
                "taxes_amount": dato[32],
                "transaction_amount": dato[33],
                "transaction_amount_refunded": dato[34],
                "transaction_details_total_paid_amount": dato[35],
                "NomCaja": dato[35],
                "NumCajero": dato[36],
                "NombreCajero": dato[37]
            }
            
            status = self.conexionDBACENTRAL.insertar_datos_sin_obtener_id("MPQRCODE_OBTENERPAGO", datos_dict)
            if status:
                datos_env += 1
                if not label_aviso_actulizar == None:
                    if status:
                        label_aviso_actulizar.configure(text=f"Datos de la Factura {dato[0]} enviados correctamente")
                        time.sleep(0.5)
                    else:
                        label_aviso_actulizar.configure(text=f"Error al Enviarla Factura {dato[0]}")        
        if not label_aviso_actulizar == None:
            label_aviso_actulizar.configure(text=f"Se han enviado {datos_env} datos correctamente.")
            time.sleep(0.5)
            label_aviso_actulizar.configure(text=f"Cerrando Conexión")
            time.sleep(3)
            ventana_envio.destroy()
        else:
            if datos_env > 0:
                messagebox.showinfo("Archivos enviados AUTO", f"Se han enviado {datos_env} datos correctamente.")
                self.actualizar_ultimo_aviso()
            else:
                messagebox.showerror("Archivos enviados AUTO", f"No se encontro ni un dato a enviar.")
        
    def actualizar_ultimo_aviso(self):
        dia_actual = datetime.now()
        dia_actual = dia_actual.strftime("%d-%m-%Y %H:%M")
        # Carga el archivo JSON
        with open("configuracion.json", 'r', encoding='utf-8') as archivo:
            try:
                data = json.load(archivo)
            except json.JSONDecodeError:
                data = {}

        # Actualiza o agrega el elemento "ultimo_aviso"
        data["ultimo_envio"] = dia_actual

        # Guarda el archivo JSON actualizado
        with open("configuracion.json", 'w', encoding='utf-8') as archivo:
            json.dump(data, archivo, ensure_ascii=False, indent=4)

class BuscarDatosEnvios:
    def __init__(self, dia_mandar, label_aviso_actulizar=None, ventana_envio=None):
        DBA_CONEXION = ConexionEnvioServerCentral().conexiones_dba()
        self.conexionDBASERVER = DBA_CONEXION[0]
        self.conexionDBACENTRAL = DBA_CONEXION[1]
        if not dia_mandar:
            self.dia_actual = datetime.now()
            self.dia_actual = self.dia_actual.strftime("%Y-%m-%d")  # Formato de fecha: Año-Mes-Día
        else:
            self.dia_actual = str(dia_mandar)
        self.ALL_DATOS = self.conexionDBASERVER.seleccionar_tabla("MPQRCODE_OBTENERPAGO")
        self.datos_actuales = []
        for i in self.ALL_DATOS:
            if self.parsear_hs_buenos_aires(i[5], self.dia_actual):
                self.datos_actuales.append(i)
                if not label_aviso_actulizar == None:
                    label_aviso_actulizar.configure(text=f"Factura {i[0]} coincide con la fecha")
                time.sleep(1)
        if self.datos_actuales:
            if not label_aviso_actulizar == None:
                EnvioServerCentral(self.conexionDBACENTRAL, self.datos_actuales, label_aviso_actulizar, ventana_envio)
            else:
                EnvioServerCentral(self.conexionDBACENTRAL, self.datos_actuales)
        else:
            if not label_aviso_actulizar == None:
                label_aviso_actulizar.configure(text=f"No se han encontrado datos")
                time.sleep(3)
                ventana_envio.destroy()
        
    def parsear_hs_buenos_aires(self, HS_ISO, Dia_actual):
        # Parsear la fecha y hora usando dateutil.parser
        fecha_hora_utc = parser.parse(HS_ISO)

        # Definir la zona horaria de Buenos Aires
        zona_horaria_buenos_aires = pytz.timezone('America/Argentina/Buenos_Aires')

        # Convertir la fecha y hora a la zona horaria de Buenos Aires
        fecha_hora_buenos_aires = fecha_hora_utc.astimezone(zona_horaria_buenos_aires)

        # Formatear la fecha y hora en un formato legible
        fecha_hora_formateada = fecha_hora_buenos_aires.strftime('%Y-%m-%d')
        return Dia_actual == fecha_hora_formateada

def es_hora_exacta():
    ahora = datetime.now()
    return ahora.minute == 0 and ahora.second == 0

def es_hora_concreta(hora, minuto):
    ahora = datetime.now()
    return ahora.hour == hora and ahora.minute == minuto and ahora.second == 0

def ejecutar_clase():
    status_conexion = ConexionEnvioServerCentral()
    if status_conexion.conexion:
        BuscarDatosEnvios(False)
    else:
        messagebox.showerror('Error Conexión Central', "No hay conexión con la central. No se enviaron los datos.")
        print("No hay conexión con la central. Intente reconectar.")

def comprobar_y_ejecutar(master):
    ahora = datetime.now()
    
    if es_hora_exacta():
        print(f"Comprobando conexión a las {ahora.strftime('%H:%M:%S')}")
        status_conexion = ConexionEnvioServerCentral()
        print(f"Estado de la conexión: {'Conectado' if status_conexion.conexion else 'Desconectado'}")
        
        if ahora.hour == 23:
            ejecutar_clase()
        elif ahora.hour == 22:
            if not master == None:
                CTkNotification(master=master, message="Dentro de 1 hora se enviarán los datos a la central.")
            print("Dentro de 1 hora se enviarán los datos a la central.")
        elif ahora.hour == 9:
            if not master == None:
                CTkNotification(master=master, message="Dentro de 1 hora se enviarán los datos a la central.")
            print("Dentro de 1 hora se enviarán los datos a la central.")
    elif es_hora_concreta(10, 59):
        ejecutar_clase()
        if not master == None:
            CTkNotification(master=master, message="Dentro de 30 minutos se enviarán los datos a la central.")
        print("Dentro de 30 minutos se enviarán los datos a la central.")
    elif es_hora_concreta(22, 55):
        if not master == None:
            CTkNotification(master=master, message="Dentro de 5 minutos se enviarán los datos a la central.")
        print("Dentro de 5 minutos se enviarán los datos a la central.")
    else:
        print(f"Comprobación realizada a las {ahora.strftime('%H:%M:%S')}")

class ProgramadorComprobacion:
    def __init__(self):
        self.timer = None
        self.continuar = True

    def iniciar(self, master=None):
        self.programar_comprobacion_minuto(master)

    def programar_comprobacion_minuto(self, master):
        if self.continuar:
            comprobar_y_ejecutar(master)
            self.timer = threading.Timer(1, self.programar_comprobacion_minuto, args=(master,))  # Comprobar cada segundo
            self.timer.start()


    def detener(self):
        self.continuar = False
        if self.timer is not None:
            self.timer.cancel()
"""
# Crear y iniciar el programador
programador = ProgramadorComprobacion()
programador.iniciar()

# Mantener el programa en ejecución
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Programa terminado por el usuario.")
    programador.detener()
"""