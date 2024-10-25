__version__ = "2.0.1"

import os
import json
import requests
import sys
from tkinter import messagebox
from log_errorsV2 import log_error

path_directorio = os.getcwd()
path_enlaces = os.path.join(path_directorio, "..")
sys.path.append(path_enlaces)
from databaseV2 import ConexionSybase
from conexionesV2 import Conexion_APP
from GUIORDENES import GUIMAIN
from GUITopLevelCargaCREARORDENV2 import TopLevelCargaCREARORDEN


class EnlaceCrearOrden:
    def __init__(self):
        log_error(f"INICIO ENLACE: ----------------------------------------------------------------------------------------", function_name='__init__')
        self.dsn_caja = None
        self.dsn_servidor = None
        self.dsn_servidor_central = None
        try:
            self.cargar_configuracion()
            self.conectar_dba()
        except Exception as e:
            log_error(f"Error al inicializar EnlaceCrearOrden: {str(e)}")
            log_error(f"FIN ENLACE: ----------------------------------------------------------------------------------------", function_name='__init__')
        log_error(f"FIN ENLACE: ----------------------------------------------------------------------------------------\n", function_name='__init__')
        
        
    def conectar_dba(self):
        try:
            if self.dsn_caja is not None and self.dsn_servidor is not None:
                self.conexionDBA = ConexionSybase(
                    user="dba",
                    password="gestion",
                    dsn=self.dsn_caja
                )
                self.conexionDBASERVER = ConexionSybase(
                    user="dba",
                    password="gestion",
                    dsn=self.dsn_servidor
                )
                if self.conexionDBA.conectar() and self.conexionDBASERVER.conectar():
                    if self.pedido_API_online():
                        self.llamar_crear_orden()
                else:
                    log_error('No se puede lograr conexión con ninguna base de datos')
                    messagebox.showerror('Error con el DBA', 'No se puede lograr conexión con ninguna base de datos')
            else:
                log_error("El servidor no se encuentra en línea")
                messagebox.showerror("Error", "El servidor no se encuentra en línea")
        except Exception as e:
            log_error(f"Error en conectar_dba: {str(e)}")
        
        
    def cargar_configuracion(self):
        try:
            ruta_relativaJSON = os.path.join(path_enlaces, "configuracion.json")
            print(ruta_relativaJSON)
            
            with open(ruta_relativaJSON, "r") as file:
                configuracion = json.load(file)
                self.dsn_caja = configuracion.get("dsn_caja", "")
                self.dsn_servidor = configuracion.get("dsn_servidor", "")
                print(self.dsn_caja, self.dsn_servidor)
                
                # Verificar si existe la clave "dsn_servidor_central"
                if "dsn_servidor_central" in configuracion:
                    self.dsn_servidor_central = configuracion["dsn_servidor_central"]
                print(self.dsn_caja, self.dsn_servidor_central)
            print(self.dsn_caja, self.dsn_servidor)
        except FileNotFoundError:
            log_error("Archivo de configuración no encontrado")
        except Exception as e:
            log_error(f"Error en cargar_configuracion: {str(e)}")
        
    def llamar_crear_orden(self):
        try:
            self.id_user = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'idUSER', 1)
            self.token  = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKEN', 1)
            self.tokenPOINT = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKENPOINT', 1)
            self.datos_connect = (self.id_user, self.token)
            self.datos_connectPOINT = (self.id_user, self.tokenPOINT)
            self.ventana_principal = None 
            self.conexionAPI = Conexion_APP(self.datos_connect, self.conexionDBA, self.conexionDBASERVER)
            self.conexionAPIPOINT = Conexion_APP(self.datos_connectPOINT, self.conexionDBA, self.conexionDBASERVER)
            log_error(f"PASE A SISTEMA: ----------------------------------------------------------------------------------------", function_name='__init__')
            TopLevelCargaCREARORDEN()
            DICT_CONEXION = {
                "conexionAPI": self.conexionAPI, 
                "conexionAPIPOINT": self.conexionAPIPOINT, 
                "conexionDBA": self.conexionDBA, 
                "conexionDBAServer": self.conexionDBASERVER
            }
            GUIMAIN(__version__, DICT_CONEXION)
        except Exception as e:
            log_error(f"Error en llamar_crear_orden: {str(e)}")
        
        
    def pedido_API_online(self):
        try:
            lista_id_increment = self.conexionDBASERVER.specify_search_columna('MPQRCODE_CAJAS', 'idINCREMENT')
            print(lista_id_increment)
            if lista_id_increment:
                url_de_DBA = self.conexionDBASERVER.specify_search_condicion('MPQRCODE_CAJAS', 'IPN_url', 'idINCREMENT', lista_id_increment[0], False)
                url_de_API_AWS = self.conexionDBASERVER.specify_search_condicion("SPDIR", "ID", "GRID", "url_api_AWS", False)
                print(url_de_DBA)
                if url_de_DBA is not None:
                    headers = {
                        "Content-Type": 'application/json'
                    }            
                    response_url_de_DBA = requests.get(url=url_de_DBA, headers=headers)
                    response_url_de_API_AWS = requests.get(url=url_de_API_AWS, headers=headers)
                    
                    if response_url_de_DBA.status_code == 200 and response_url_de_API_AWS.status_code == 200:
                        return True
                    else:
                        if not response_url_de_DBA.status_code == 200:
                            log_error('No nos pudimos conectar al servidor API local')
                            messagebox.showerror('Sin conexión', 'No nos pudimos conectar al servidor API local')
                            self.mostrar_error_pago()
                            return False
                        elif not response_url_de_API_AWS.status_code == 200:
                            log_error('No nos pudimos conectar al servidor API AWS de Inforhard')
                            messagebox.showerror('Sin conexión', 'No nos pudimos conectar al servidor API AWS de Inforhard')
                            self.mostrar_error_pago()
                            return False
                        else:
                            log_error('No obtuvimos respuestas de ningún servidor')
                            messagebox.showerror('Sin conexión', 'No obtuvimos respuestas de ningún servidor')
                            self.mostrar_error_pago()
            else:
                log_error("No se encontró caja activa")
                messagebox.showerror("Error", "No se encontró caja activa")
                return False
        except Exception as e:
            log_error(f"Error en pedido_API_online: {str(e)}")
            return False
        
    def mostrar_error_pago(self):
        try:
            datos = {
                'status': 0,
                'response': 10,
                'description': "orden-cancelada"
            }
            factura = self.conexionDBA.specify_search_columna("MPQRCODE_CONEXIONPROGRAMAS", "nro_factura")[0]
            print(factura)
            self.conexionDBA.actualizar_datos_condicion("MPQRCODE_CONEXIONPROGRAMAS", datos, "nro_factura", f"'{factura}'")
        except Exception as e:
            log_error(f"Error en mostrar_error_pago: {str(e)}")
        
EnlaceCrearOrden()
