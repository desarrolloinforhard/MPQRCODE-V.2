import sys
import os
import json
import time
import tkinter as tk
directorio_script = os.path.dirname(os.path.abspath(__file__))
# Construir la ruta relativa al directorio que deseas agregar
ruta_relativa = os.path.join(directorio_script, "..")
sys.path.append(ruta_relativa)
from database import ConexionSybase
from conexiones import Conexion_APP
from tkinter import ttk, messagebox
from GUI.GUICrearOrden import CrearOrdenApp


class ConfigInicialMPQRCODEPOS:
    def __init__(self):
        self.user_id = None
        self.access_token = None     
        self.dsn_caja = None
        self.dsn_servidor = None
        self.cargar_configuracion()
        if not self.dsn_caja == None and not self.dsn_servidor == None:
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
            GUIconexiones(self.conexionDBA, self.conexionDBASERVER)
        else:
            messagebox.showerror("Error", "DSN NO CONFIGURADOS. Se abra el configurador de DSN.") 
        
        
    def cargar_configuracion(self):
        try:
            ruta_relativa_JSON = os.path.join(directorio_script, "configuracion.json")
            with open(ruta_relativa_JSON, "r") as file:
                configuracion = json.load(file)
                self.dsn_caja = configuracion.get("dsn_caja", "")
                self.dsn_servidor = configuracion.get("dsn_servidor", "")
        except FileNotFoundError:
            # El archivo de configuración no existe, es normal la primera vez
            pass
        
class GUIconexiones:
    def __init__(self, conexionDBA, conexionDBASERVER):
        self.conexionDBA = conexionDBA
        self.conexionDBASERVER = conexionDBASERVER
        self.id_user = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'idUSER', 1)
        self.token  = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKEN', 1)
        self.tokenPOINT = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKENPOINT', 1)
        self.datos_connect = (self.id_user, self.token)
        self.datos_connectPOINT = (self.id_user, self.tokenPOINT)
        self.ventana_principal = None 
        self.conexionAPI = Conexion_APP(self.datos_connect, self.conexionDBA, self.conexionDBASERVER)
        self.conexionAPIPOINT = Conexion_APP(self.datos_connectPOINT, self.conexionDBA, self.conexionDBASERVER)
        CrearOrdenApp(self.conexionAPI, self.conexionAPIPOINT, self.conexionDBA, self.conexionDBASERVER)
                
if __name__ == "__main__":
    config = ConfigInicialMPQRCODEPOS()