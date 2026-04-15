import os
import json
from pprint import pprint
import requests
import traceback
import sys
from tkinter import messagebox
from Func.tecladohasarV4 import TecladoHasar
from Func.log_errorsV2 import log_error

path_directorio = os.getcwd()
path_enlaces = os.path.join(path_directorio, "..")
sys.path.append(path_enlaces)
from DB.databaseV2 import ConexionSybase
from DB.DBFManager import DBFManager
from Conf.conexionesV3 import Conexion_APP
from GUI.GUIORDENES import GUIMAIN
#from GUI.GUITopLevelCargaCREARORDENV2 import TopLevelCargaCREARORDEN


def _hay_internet():
    """Devuelve True si hay conexión a Internet, False si no."""
    try:
        requests.get("http://clients3.google.com/generate_204", timeout=3)
        return True
    except Exception:
        return False


class EnlaceCrearOrden:
    def __init__(self, __version__):
        log_error(f"INICIO ENLACE: ----------------------------------------------------------------------------------------", function_name='__init__')
        self.datos_dbf_local = None
        self.datos_dbf_server = None
        self.dict_config_KM84 = {}
        self.__version__ = __version__
        try:
            self.cargar_configuracion()
            self.conectar_dba()
        except Exception as e:
            log_error(f"Error al inicializar EnlaceCrearOrden: {str(e)}")
            log_error(f"FIN ENLACE: ----------------------------------------------------------------------------------------", function_name='__init__')
        log_error(f"FIN ENLACE: ----------------------------------------------------------------------------------------\n", function_name='__init__')
        # Iniciar teclado Hasar una sola vez

        
        
    def conectar_dba(self):
        try:
            if self.datos_dbf_local is not None and self.datos_dbf_server is not None:
                self.conexionDBA = ConexionSybase(**self.datos_dbf_local)
                self.conexionDBASERVER = ConexionSybase(**self.datos_dbf_server)
                if self.conexionDBA.conectar() and self.conexionDBASERVER.conectar():
                    # 🔎 Verificar Internet ANTES de iniciar teclado/orden
                    if not _hay_internet():
                        log_error("No hay conexión a Internet")
                        messagebox.showerror("Sin conexión", "No se detecta conexión a Internet")
                        self.mostrar_error_pago()
                        return  # ⬅️ cortamos aquí

                    try:
                        print(f"EL TECLADO ESTA {self.tipo_teclado()}")
                        self.traer_config_teclas_KM84()
                        self.teclado = TecladoHasar(self.dict_config_KM84, self.tipo_teclado())
                    except Exception as e:
                        log_error(f"Error al iniciar el teclado Hasar: {str(e)}")

                    self.llamar_crear_orden()
                else:
                    log_error('No se puede lograr conexión con ninguna base de datos')
                    messagebox.showerror('Error con el DBA', 'No se puede lograr conexión con ninguna base de datos')
            else:
                log_error("El servidor no se encuentra en línea")
                messagebox.showerror("Error", "El servidor no se encuentra en línea")
        except Exception as e:
            log_error(f"Error en conectar_dba: {str(e)}")
            
    def traer_config_teclas_KM84(self):
        query = 'SELECT nnumtecla, funcion FROM "DBA"."KM_84_LETER"'
        filas = self.conexionDBA.ejecutar_consulta(query)  # <- lista de dicts
        # Limpio y normalizo: claves int -> valores str
        self.dict_config_KM84 = {
            int(r["nnumtecla"]): str(r["funcion"])
            for r in filas
            if isinstance(r, dict)
            and "nnumtecla" in r and "funcion" in r
            and str(r["nnumtecla"]).isdigit()
        }
        print(self.dict_config_KM84)  # {64:'A', 65:'B', ..., 160:'X', 161:'Y', 162:'Z', 163:' '}

    
    """def traer_config_teclas_KM84(self):
        query = 'SELECT nnumtecla, funcion FROM "DBA"."KM_84_LETER"'
        list_teclas = self.conexionDBA.ejecutar_consulta(query)
        print(list_teclas)
        for numtecla, funcion in list_teclas:
            self.dict_config_KM84[numtecla] = funcion  # ✅ forma correcta
        print(self.dict_config_KM84)"""


    def tipo_teclado(self) -> bool:
        query = 'SELECT id FROM "DBA"."spdir" WHERE grid = \'teclado_km84\''
        valor = self.conexionDBA.ejecutar_consulta(query, scalar=True)  # <-- devuelve None si no hay filas

        if valor is None:
            return False

        v = str(valor).strip().lower()
        return v in ("1", "true", "t", "yes", "y", "s", "si", "sí")



        
    def cargar_configuracion(self):
        try:
            # Carga configuración local
            self.datos_dbf_local = DBFManager(r"F:\Sp\FacturaP\Dbf\SYBASE.dbf").extraer_parametros_dns()[0]
            print(self.datos_dbf_local)
        except FileNotFoundError:
            log_error("Archivo de configuración local SYBASE.dbf no encontrado")
            return
        except Exception as e:
            log_error(f"Error al cargar configuración local: {str(e)}")
            return

        ruta_sybase6 = r"F:\Sp\FacturaP\Dbf\SYBASE6.dbf"
        ruta_sybase10 = r"F:\Sp\FacturaP\Dbf\SYBASE10.dbf"

        try:
            if os.path.exists(ruta_sybase6):
                self.datos_dbf_server = DBFManager(ruta_sybase6).extraer_parametros_dns()[0]
                print(self.datos_dbf_server, 6)
            elif os.path.exists(ruta_sybase10):
                self.datos_dbf_server = DBFManager(ruta_sybase10).extraer_parametros_dns()[0]
                print(self.datos_dbf_server, 10)
            else:
                log_error("Ninguno de los archivos SYBASE6.dbf ni SYBASE10.dbf fue encontrado")
        except Exception as e:
            log_error(f"Error al procesar archivo SYBASE.dbf: {str(e)}")


    def llamar_crear_orden(self):
        try:
            self.id_user = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'idUSER', 1)
            self.token = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKEN', 1)
            self.tokenPOINT = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKENPOINT', 1)

            self.datos_connect = (self.id_user, self.token)
            self.datos_connectPOINT = (self.id_user, self.tokenPOINT)
            self.ventana_principal = None

            self.conexionAPI = Conexion_APP(self.datos_connect, self.conexionDBA, self.conexionDBASERVER)
            self.conexionAPIPOINT = Conexion_APP(self.datos_connectPOINT, self.conexionDBA, self.conexionDBASERVER)

            log_error(
                "PASE A SISTEMA: ----------------------------------------------------------------------------------------",
                function_name='llamar_crear_orden'
            )

            DICT_CONEXION = {
                "conexionAPI": self.conexionAPI,
                "conexionAPIPOINT": self.conexionAPIPOINT,
                "conexionDBA": self.conexionDBA,
                "conexionDBAServer": self.conexionDBASERVER,
                "teclado": self.teclado
            }

            GUIMAIN(self.__version__, DICT_CONEXION)

        except Exception as e:
            error_completo = traceback.format_exc()
            log_error(
                f"Error en llamar_crear_orden: {str(e)}\nTraceback completo:\n{error_completo}",
                function_name='llamar_crear_orden'
            )
        
        
    def pedido_API_online(self):
        try:
            if not self.conexionDBASERVER.specify_search_condicion("SPDIR", "ID", "GRID", "MP_NUEVA_VERSION", False) == None:
                if self.conexionDBASERVER.specify_search_condicion("SPDIR", "ID", "GRID", "MP_NUEVA_VERSION", False).lower() == "true":
                    url_de_DBA = self.conexionDBASERVER.specify_search_condicion("SPDIR", "ID", "GRID", "url_api_NGROK", False)
                    url_de_API_AWS = self.conexionDBASERVER.specify_search_condicion("SPDIR", "ID", "GRID", "url_api_AWS", False)
                    print(url_de_DBA)
                    if url_de_DBA is not None:
                        if url_de_API_AWS is not None:
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
                            messagebox.showerror("Error", "Variable Inexistente: url_de_API_AWS")
                    else:
                        messagebox.showerror("Error", "Variable Inexistente: url_api_NGROK")
                elif self.conexionDBASERVER.specify_search_condicion("SPDIR", "ID", "GRID", "MP_NUEVA_VERSION", False).lower() == "false":
                    url_de_DBA = self.conexionDBASERVER.specify_search_condicion("SPDIR", "ID", "GRID", "url_api_NGROK", False)
                    print(url_de_DBA)
                    if url_de_DBA is not None:
                        headers = {
                            "Content-Type": 'application/json'
                        }            
                        response_url_de_DBA = requests.get(url=url_de_DBA, headers=headers)
                        #response_url_de_API_AWS = requests.get(url=url_de_API_AWS, headers=headers)
                        
                        if response_url_de_DBA.status_code == 200:
                            return True
                        else:
                            log_error('No nos pudimos conectar al servidor API local')
                            messagebox.showerror('Sin conexión', 'No nos pudimos conectar al servidor API local')
                            self.mostrar_error_pago()
                            return False
                    else:
                        messagebox.showerror("Error", "Variable Inexistente: url_api_NGROK")
                else:
                    messagebox.showerror("Error", "Valor variable incorrecto")
            else:
                messagebox.showerror("Error", "Variable Inexistente: MP_NUEVA_VERSION")
        except Exception as e:
            log_error(f"Error en pedido_API_online: {str(e)}")
            messagebox.showerror("Error en pedido_API_online", e)
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
        
#EnlaceCrearOrden()
