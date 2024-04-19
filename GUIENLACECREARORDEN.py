import os
import json
import requests
import sys
path_directorio = os.getcwd()
path_enlaces= os.path.join(path_directorio, "..")
sys.path.append(path_enlaces)
from database import ConexionSybase
from conexiones import Conexion_APP
from GUICrearOrden import CrearOrdenApp
from GUITopLevelCargaCREARORDEN import TopLevelCargaCREARORDEN
from tkinter import messagebox


class EnlaceCrearOrden:
    def __init__(self):
        self.dsn_caja = None
        self.dsn_servidor = None
        self.dsn_servidor_respaldo = None
        self.cargar_configuracion()
        self.conectar_dba()
        
        
        
    def conectar_dba(self):
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
            if self.conexionDBA.conectar() and self.conexionDBASERVER.conectar():
                if self.pedido_API_online():
                    self.llamar_crear_orden()
            else:
                if not self.dsn_servidor_respaldo == None:
                    self.conexionDBASERVER = ConexionSybase(
                    user="dba",
                    password="gestion",
                    dsn=self.dsn_servidor_respaldo
                    )
                    if self.conexionDBA.conectar() and self.conexionDBASERVER.conectar():
                        messagebox.showinfo('¡¡IMPORTANTE!!', 'AVISO IMPORTANTE:\n Estas trabajando sobre una base de respaldo.')
                        if self.pedido_API_online():
                            self.llamar_crear_orden()
                    else:
                        messagebox.showerror('Error con el DBA', 'No se puede lograr conexion con ninguna base de datos')
                else:
                    messagebox.showerror('Error con el DBA', 'No se puede lograr conexion con ninguna base de datos')
        else:
            messagebox.showerror('Sin conexión', 'No nos pudimos conectar al servidor API de Inforhard')
        
        
    def cargar_configuracion(self):
        try:
            ruta_relativaJSON = os.path.join(path_enlaces, "configuracion.json")
            print(ruta_relativaJSON)
            
            with open(ruta_relativaJSON, "r") as file:
                configuracion = json.load(file)
                self.dsn_caja = configuracion.get("dsn_caja", "")
                self.dsn_servidor = configuracion.get("dsn_servidor", "")
                print(self.dsn_caja, self.dsn_servidor)
                
                
                # Verificar si existe la clave "dsn_servidor_respaldo"
                if "dsn_servidor_respaldo" in configuracion:
                    self.dsn_servidor_respaldo = configuracion["dsn_servidor_respaldo"]
                print(self.dsn_caja, self.dsn_servidor_respaldo)
            print(self.dsn_caja, self.dsn_servidor)
        except FileNotFoundError:
            # El archivo de configuración no existe, es normal la primera vez
            pass
        
    def llamar_crear_orden(self):
        self.id_user = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'idUSER', 1)
        self.token  = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKEN', 1)
        self.tokenPOINT = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKENPOINT', 1)
        self.datos_connect = (self.id_user, self.token)
        self.datos_connectPOINT = (self.id_user, self.tokenPOINT)
        self.ventana_principal = None 
        self.conexionAPI = Conexion_APP(self.datos_connect, self.conexionDBA, self.conexionDBASERVER)
        self.conexionAPIPOINT = Conexion_APP(self.datos_connectPOINT, self.conexionDBA, self.conexionDBASERVER)
        TopLevelCargaCREARORDEN()
        CrearOrdenApp(self.conexionAPI, self.conexionAPIPOINT, self.conexionDBA, self.conexionDBASERVER)
        
        
    def pedido_API_online(self):
        
        lista_id_increment = self.conexionDBASERVER.specify_search_columna('MPQRCODE_CAJAS', 'idINCREMENT')
        print(lista_id_increment)
        if lista_id_increment:
            url_de_DBA = self.conexionDBASERVER.specify_search_condicion('MPQRCODE_CAJAS', 'IPN_url', 'idINCREMENT', lista_id_increment[0], False)
            if not url_de_DBA == None:
                headers = {
                    "Content-Type": 'application/json'
                }            
                response = requests.get(url=url_de_DBA, headers=headers)
                
                if response.status_code == 200:
                    return True
                else:
                    messagebox.showerror("Error", "El servidor no se encuentra en linea")
                    return False
        else:
            messagebox.showerror("Error", "No se encontro caja activa")
            return False
        
EnlaceCrearOrden()