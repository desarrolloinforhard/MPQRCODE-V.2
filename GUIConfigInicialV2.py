import customtkinter as CTk
import os
import json
import socket
import keyboard
import requests
import image_path as RutaImagenes
from ctk_components.ctk_components import *
from CTkMessagebox import CTkMessagebox
from GUIConfigDBA import GUIconexiones
from GUICrearSucursalV3 import CrearSucursalApp
from GUICrearCajaV2 import GUIEliminarSucursal
from GUITopLevelCargaCREARORDEN import TopLevelCargaCREARORDEN
from GUICrearOrden import CrearOrdenApp
from GUIDSN import InterfazGrafica
from window_position import center_window
from tkinter import ttk, simpledialog, messagebox
from PIL import Image
from datetime import datetime
from database import ConexionSybase
from conexiones import Conexion_APP

# Obtener la fecha y hora actual
fecha_actual = datetime.now()

# Formatear la fecha y hora actual
fecha_formateada = fecha_actual.strftime("%d-%m-%Y %H:%M:%S")


class ConfigInicialMPQRCODE:
    def __init__(self):
        conexion_internet = self.verificar_conexion_internet()
        if conexion_internet:
            self.user_id = None
            self.access_token = None     
            self.dsn_caja = None
            self.dsn_servidor = None
            self.dsn_servidor_respaldo = None
            self.resultado = None
            self.cargar_configuracion()
            self.rutaicono = os.path.dirname(os.path.abspath(__file__))
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
                if self.conexionDBASERVER.check_table_existence('MPQRCODE_CONEXIONSERVIDORAPI'):
                    pass
                else:
                    self.conexionDBASERVER.crear_tabla_MPQRCODE_CONEXIONSERVIDORAPI()
                    self.conexionDBASERVER.insertar_datos_sin_obtener_id('MPQRCODE_CONEXIONSERVIDORAPI', {'id': 1})
                fecha_api = self.conexionDBASERVER.specify_search_condicion('MPQRCODE_CONEXIONSERVIDORAPI', 'ultima_actualizacion', 'id', 1, False)
                if self.comparacion_fechas(fecha_formateada, fecha_api):
                    if self.conexionDBA.conectar() and self.conexionDBASERVER.conectar():
                        self.validar_password()
                    else:
                        if not self.dsn_servidor_respaldo == None:
                            self.conexionDBASERVER = ConexionSybase(
                            user="dba",
                            password="gestion",
                            dsn=self.dsn_servidor_respaldo
                            )
                            if self.conexionDBA.conectar() and self.conexionDBASERVER.conectar():
                                messagebox.showinfo('¡¡IMPORTANTE!!', 'AVISO IMPORTANTE:\n Estas trabajando sobre una base de respaldo.')
                                self.validar_password()
                            else:
                                messagebox.showerror('Error con el DBA', 'No se puede lograr conexion con ninguna base de datos')
                        else:
                            messagebox.showerror('Error con el DBA', 'No se puede lograr conexion con ninguna base de datos')
                else:
                    messagebox.showerror('Sin conexión', 'No nos pudimos conectar al servidor API de Inforhard')
            else:
                messagebox.showerror("Error", "DSN NO CONFIGURADOS. Habra el configurador de DSN e introduzcalos.")
                directorio_script = os.path.dirname(os.path.abspath(__file__))
                root = CTk.CTk()
                rutaicono = RutaImagenes.Icono_MercadoPago_Blue()
                root.iconbitmap(rutaicono)
                app = InterfazGrafica(root)
                root.mainloop()  
        else:
            messagebox.showerror('No hay conexión', 'Sin conexión a internet')
            
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
            
    def verificar_conexion_internet(self):
        try:
            # Intenta conectarte a un servidor externo (en este caso, google.com) en el puerto 80
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            # Si hay un error al conectar, devuelve False
            return False
        
    def comparacion_fechas(self, fecha_python, fecha_api):
        try:
            lista_fecha_python = self.separar_fechas(fecha_python)
            lista_fecha_api = self.separar_fechas(fecha_api)
            print(lista_fecha_python, lista_fecha_api)
            return self.sacar_diferencia_fechas(lista_fecha_python, lista_fecha_api)
            
                
        except Exception as e:
            if self.conexionDBASERVER.tabla_vacia('MPQRCODE_CLIENTE'):
                messagebox.showerror('Error fechas', 'No se ha levantado el servidor APIRest de INFORHARD S.R.L\n Ingrese a continuacón los datos de MercadoPago.\n USER-ID, ACCESS-TOKEN (QR y POINT)')
                self.crear_interfaz()
                if  self.resultado:
                    messagebox.showinfo('OK', 'EL cliente se ha agregado, puede levantar el server, local y host.')
                else:
                    messagebox.showerror('No agregado', 'No se pudo agregar ni un cliente, no puedes acceder a la Interfaz de Pago')
            else:
                if self.conexionDBASERVER.check_table_existence('MPQRCODE_CLIENTE'):
                    messagebox.showinfo('Aviso', 'Los datos del clientes se encuentran cargados pero no se levanto el servidor APIRest de INFORHARD S.R.L')
                else:
                    self.conexionDBASERVER.crear_tabla_MPQRCODE_CLIENTE()
                    self.crear_interfaz()
            
            
    def separar_fechas(self, fecha):
        caracteres = []  # Lista para almacenar los caracteres de la fecha
        lista_fechas = []  # Lista para almacenar las fechas separadas

        for caracter in fecha:
            if caracter != '-' and caracter != ':' and caracter != ' ':
                caracteres.append(caracter)  # Agregar el caracter a la lista
            else:
                if caracteres:  # Verificar si hay caracteres en la lista
                    fecha_separada = int(''.join(caracteres))  # Convertir la lista de caracteres a entero
                    lista_fechas.append(fecha_separada)  # Agregar la fecha separada a la lista de fechas
                    caracteres = []  # Reiniciar la lista de caracteres para la próxima fecha

        # Agregar la última fecha si hay caracteres en la lista
        if caracteres:
            fecha_separada = int(''.join(caracteres))
            lista_fechas.append(fecha_separada)

        return lista_fechas   
    
    def sacar_diferencia_fechas(self, listas_fecha_python, lista_fecha_api):
        # Verificar si las posiciones 0, 1 y 2 de ambas listas coinciden
        if listas_fecha_python[0] == lista_fecha_api[0] and \
        listas_fecha_python[1] == lista_fecha_api[1] and \
        listas_fecha_python[2] == lista_fecha_api[2]:
            
            # Calcular la diferencia entre las posiciones 3 y 4 de ambas listas
            diferencia_posicion3 = abs(listas_fecha_python[3] - lista_fecha_api[3])
            diferencia_posicion4 = abs(listas_fecha_python[4] - lista_fecha_api[4])
            # Verificar si la diferencia no es mayor a uno
            if diferencia_posicion3 == 0 and diferencia_posicion4 <= 1:
                # Verificar si la posición 5 de la primer lista es mayor o igual a la de la segunda lista,
                # o si la diferencia es de 5 o -5
                if listas_fecha_python[5] >= lista_fecha_api[5] and abs(listas_fecha_python[5] - lista_fecha_api[5]) <= 5:
                    return True
                # Verificar si la diferencia de la posición 4 de la primera lista es de uno
                elif abs(listas_fecha_python[4] - lista_fecha_api[4]) == 1:
                    # Calcular el resultado de la resta
                    resultado_resta = 59 - lista_fecha_api[5] + listas_fecha_python[5]
                    # Verificar si el resultado no es mayor a 5
                    if resultado_resta <= 5:
                        return True
        return False

            

    def validar_password(self):
        try:
            condicion = True
            while condicion == True:
                password_ingresado = simpledialog.askstring("Password", "Ingrese el password:", show='*')
                if password_ingresado is None:
                    # Usuario canceló la operación, salir del bucle
                    break
                password_correcto = "*123*"
                if password_ingresado == password_correcto:
                    if self.tabla_clientes_vacia():
                        self.conexionDBASERVER.crear_tabla_MPQRCODE_CLIENTE()
                        self.crear_interfaz()
                        messagebox.showinfo("Información", "Cliente cargado.")
                        GUIConfigInicialV2(self.conexionDBA, self.conexionDBASERVER)
                    else:
                        messagebox.showinfo("Información", "Ya hay un cliente cargado.")
                        GUIConfigInicialV2(self.conexionDBA, self.conexionDBASERVER)  
                elif password_ingresado == "DATABASE":
                    GUIconexiones()
                elif password_ingresado == "CONNECTDSN":
                    directorio_script = os.path.dirname(os.path.abspath(__file__))
                    root = CTk.CTk()
                    rutaicono = RutaImagenes.Icono_MercadoPago_Blue()
                    root.iconbitmap(rutaicono)
                    app = InterfazGrafica(root)
                    root.mainloop()
                elif password_ingresado == "DLTTABLEFULLPS":
                    self.conexionDBA.eliminarTablasPOS()
                    self.conexionDBASERVER.eliminarTablasSERVER()
                    messagebox.showinfo("Exito", "Se elimino las tablas del Server y el POS")
                elif password_ingresado == "RSTTABLECAJA":
                    self.conexionDBA.eliminar_tabla("MPQRCODE_CAJA")
                    self.conexionDBA.crear_tabla_MPQRCODE_CAJA()
                    messagebox.showinfo("Exito", "Se elimino los datos de  la Caja")
                elif password_ingresado == "RSTOBPAGOServer":
                    self.conexionDBASERVER.eliminar_tabla("MPQRCODE_RESPUESTAPOST")
                    self.conexionDBASERVER.eliminar_tabla("MPQRCODE_OBTENERPAGOServer")
                    self.conexionDBASERVER.crear_tabla_MPQRCODE_RESPUESTAPOST()
                    self.conexionDBASERVER.crear_tabla_MPQRCODE_OBTENERPAGOServer()
                elif password_ingresado == "IPN":
                    self.ventana_actualizarIPN()
                elif password_ingresado == "MKTABLEPOS":
                    messagebox.showinfo("Exito", "Se han creado las tabla del POS")
                    self.conexionDBA.crearTablasPOS()
                elif password_ingresado == "RSTOBPAGOS":
                    messagebox.showinfo("Exito", "Se han creado las tabla del POS")
                    self.conexionDBASERVER.eliminar_tabla("MPQRCODE_OBTENERPAGOServer")
                    self.conexionDBASERVER.crear_tabla_MPQRCODE_OBTENERPAGOServer()
                elif password_ingresado == "MKTABLESERVER":
                    self.conexionDBASERVER.crearTablasSERVER()
                    messagebox.showinfo("Exito", "Se han creado las tabla del Server")
                elif password_ingresado == "DLTTABLESPOS":
                    self.conexionDBA.eliminarTablasPOS()
                    messagebox.showinfo("Exito", "Se han eliminado las tabla del POS")
                elif password_ingresado == "DLTTABLESSERVER":
                    self.conexionDBASERVER.eliminarTablasSERVER()
                    messagebox.showinfo("Exito", "Se han eliminado las tabla del Server")
                elif password_ingresado == "RSTTABLESRESPUESTA":
                    self.conexionDBA.eliminarOrdenesPostDBA()
                    messagebox.showinfo("Exito", "Se restaurado las Ordenes")
                elif password_ingresado == "RSTCLIENTE":
                    self.conexionDBASERVER.eliminar_tabla("MPQRCODE_CLIENTE")
                    self.conexionDBASERVER.crear_tabla_MPQRCODE_CLIENTE()
                    messagebox.showinfo("Exito", "Se reiniciado el cliente")
                elif password_ingresado == "TESTBUY":
                    datos = {
                        "nro_factura": "00000-1111571432",
                        "tipo_factura": 1,
                        "monto_pagar": 2134.00,
                        "status": 0
                    }
                    self.conexionDBA.insertar_datos_sin_obtener_id("MPQRCODE_CONEXIONPROGRAMAS", datos)
                    messagebox.showinfo("Exito", "Se reiniciado la tabla CONEXIONPROGRAMAS")
                elif password_ingresado == "DLTTESTBUY":
                    self.conexionDBA.eliminar_tabla("MPQRCODE_CONEXIONPROGRAMAS")
                    self.conexionDBA.crear_tabla_MPQRCODE_CONEXIONPROGRAMAS()
                else:
                    messagebox.showerror("Error", "Password incorrecto.")
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")

    def tabla_clientes_vacia(self):
        try:
            return self.conexionDBASERVER.contar_registros("MPQRCODE_CLIENTE") == 0
        except Exception as e:
            messagebox.showerror("Error", f"Error al contar registros: {str(e)}")

    def crear_interfaz(self):
        self.conexionDBASERVER.insertar_datos_sin_obtener_id('MPQRCODE_CONEXIONSERVIDORAPI', {'id': 1})
        self.root = CTk.CTk()
        self.root.title("Configuración inicial MPQRCODE")
        rutaicono = RutaImagenes.Icono_MercadoPago_Blue()
        self.root.iconbitmap(rutaicono)

        CTk.CTkLabel(self.root, text="User ID de MercadoPago:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        CTk.CTkLabel(self.root, text="Access Token de MercadoPago:").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        CTk.CTkLabel(self.root, text="Access Token POINT de MercadoPago:").grid(row=2, column=0, padx=10, pady=5, sticky='w')

        self.entry_user_id = CTk.CTkEntry(self.root, font=('Helvetica', 12))
        self.entry_access_token = CTk.CTkEntry(self.root, show='*', font=('Helvetica', 12))
        self.entry_access_tokenPOINT = CTk.CTkEntry(self.root, show='*', font=('Helvetica', 12))

        self.entry_user_id.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        self.entry_access_token.grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        self.entry_access_tokenPOINT.grid(row=2, column=1, padx=10, pady=5, sticky='ew')

        CTk.CTkButton(self.root, text="Agregar", command=self.validar_y_agregar).grid(row=3, column=0, columnspan=2, pady=10)

        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)  # Vincular el cierre de la ventana

        center_window(self.root, 500, 165)
        self.root.mainloop()

    def validar_y_agregar(self):
        user_id = self.entry_user_id.get()
        access_token = self.entry_access_token.get()
        access_tokenPOINT = self.entry_access_tokenPOINT.get()

        if not user_id or not access_token:
            messagebox.showerror("Error", "Ambas casillas deben estar completas.")
        else:
            self.user_id = user_id
            self.access_token = access_token
            self.access_tokenPOINT = access_tokenPOINT
            datos_user = {
                'idUSER': self.user_id,
                'AUTH_TOKEN': self.access_token,
                'AUTH_TOKENPOINT': self.access_tokenPOINT
                
            }            
            try:
                self.conexionDBASERVER.insertar_datos_sin_obtener_id("MPQRCODE_CLIENTE", datos_user)
                self.root.destroy()
                print("DATOS AGREGADOS")
                self.resultado = True
            except Exception as e:
                messagebox.showerror("Error", f"Error al insertar datos en la base de datos: {str(e)}")
                self.resultado = False

    def cerrar_ventana(self):
        self.root.destroy()
        
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
        
            
        
        
    def cargar_configuracion(self):
        try:
            directorio_script_json = os.path.dirname(os.path.abspath(__file__))
            ruta_relativaJSON = os.path.join(directorio_script_json, "configuracion.json")
            
            with open(ruta_relativaJSON, "r") as file:
                configuracion = json.load(file)
                self.dsn_caja = configuracion.get("dsn_caja", "")
                self.dsn_servidor = configuracion.get("dsn_servidor", "")
                
                
                # Verificar si existe la clave "dsn_servidor_respaldo"
                if "dsn_servidor_respaldo" in configuracion:
                    self.dsn_servidor_respaldo = configuracion["dsn_servidor_respaldo"]
            print(self.dsn_caja, self.dsn_servidor)
        except FileNotFoundError:
            # El archivo de configuración no existe, es normal la primera vez
            pass

        
    def ventana_actualizarIPN(self):
        self.rootWindowsIPN = CTk.CTk()
        self.rootWindowsIPN.title("UPDATE IPN URL")
        rutaicono = RutaImagenes.Icono_MercadoPago_Blue()
        self.rootWindowsIPN.iconbitmap(rutaicono)
        
        
        CTk.CTkLabel(self.rootWindowsIPN, text="Nuevo url IPN:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        entry_nombre_pos = ttk.Entry(self.rootWindowsIPN)
        entry_nombre_pos.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        
        CTk.CTkButton(self.rootWindowsIPN, text="Actualizar IPN", command=lambda:self.actulizarIPN(entry_nombre_pos.get())).grid(row=1, column=0, columnspan=2, pady=10)
        self.rootWindowsIPN.mainloop()
    def actulizarIPN(self, newIPN):
        self.conexionDBASERVER.actualizar_todos_valores_columna("MPQRCODE_CAJAS", "IPN_url", newIPN)
        valor = True
        if not valor == False:
            messagebox.showinfo("Exito", "Valores Actualizados")
            self.rootWindowsIPN.destroy()
            valor = False
        


class GUIConfigInicialV2:
    def __init__(self, conexionDBA, conexionDBASERVER):
        CTk.set_appearance_mode("dark")
        CTk.set_default_color_theme("green")
        self.conexionDBA = conexionDBA
        self.conexionDBASERVER = conexionDBASERVER
        self.esc_presionado = False
        self.iniciar_escucha()
        self.id_user = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'idUSER', 1)
        self.token  = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKEN', 1)
        self.tokenPOINT = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKENPOINT', 1)
        self.datos_connect = (self.id_user, self.token, self.tokenPOINT)
        self.ventana_principal = None
        self.carga_frame = False
        self.paginador = 0
        self.conexionAPI = Conexion_APP(self.datos_connect, self.conexionDBA, self.conexionDBASERVER)
        self.rutadocumento = os.path.dirname(os.path.abspath(__file__))
        self.ventana_config_inicial = CTk.CTk()
        self.ventana_config_inicial.title('Configuración MPQRCODE')
        self.ventana_config_inicial.iconbitmap(RutaImagenes.Icono_MercadoPago_Blue())
        
        # set grid layout 1x2
        self.ventana_config_inicial.grid_rowconfigure(0, weight=1)
        self.ventana_config_inicial.grid_columnconfigure(1, weight=1)
        
        self.logo_inforhard = CTk.CTkImage(Image.open(RutaImagenes.LOGO_INFORHARD()), size=(130, 80))
        self.logo_inforhard_horizontal = CTk.CTkImage(Image.open(RutaImagenes.LOGO_INFORHARD_horizontal()), size=(200, 50))
        self.home_image = CTk.CTkImage(Image.open(RutaImagenes.HOME()), size=(45, 45))
        self.sucursal_png = CTk.CTkImage(Image.open(RutaImagenes.SUCURSAL()), size=(45, 45))
        self.pdv_png = CTk.CTkImage(Image.open(RutaImagenes.CAJERO1()), size=(45, 45))
        self.point_png = CTk.CTkImage(Image.open(RutaImagenes.POINTPOS()), size=(45, 45))
        
        self.navigation_frame = CTk.CTkFrame(self.ventana_config_inicial, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(5, weight=1)

        self.navigation_frame_label = CTk.CTkLabel(self.navigation_frame, text="", image=self.logo_inforhard,
                                                             compound="left", font=CTk.CTkFont(size=15, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        """self.home_button = CTk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Home", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), image=self.home_image, anchor="w", command=self.home_button_event)
        self.home_button.grid(row=1, column=0, sticky="ew")"""

        self.frame_sucursal_button = CTk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Sucursal", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), image=self.sucursal_png, anchor="w", command=self.frame_sucursal_button_event)
        self.frame_sucursal_button.grid(row=1, column=0, sticky="ew")

        self.frame_pos_button = CTk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="PDV", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), image=self.pdv_png, anchor="w", command=self.pos_frame_event)
        self.frame_pos_button.grid(row=2, column=0, sticky="ew")

        self.frame_pos_point_button = CTk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Points MP", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), image=self.point_png, anchor="w", command=self.frame_pos_point_button_event)
        self.frame_pos_point_button.grid(row=3, column=0, sticky="ew")
        
        self.homeframe()        
        # create second frame
        self.sucursalframe()

        # create third frame
        self.posframe()
        
        self.point_pos_frame = CTk.CTkFrame(self.ventana_config_inicial, corner_radius=0, fg_color="transparent")

        # select default frame
        self.select_frame_by_name("home")
        
        # Obtiene la resolución de la pantalla
        ancho_pantalla = self.ventana_config_inicial.winfo_screenwidth()
        alto_pantalla = self.ventana_config_inicial.winfo_screenheight()
        #self.ventana_config_inicial.geometry(f"{ancho_pantalla}x{alto_pantalla}")
        center_window(self.ventana_config_inicial, ancho_pantalla, alto_pantalla)    
        self.ventana_config_inicial.mainloop()
        
        
    def select_frame_by_name(self, name):
        # set button color for selected button
        self.frame_sucursal_button.configure(fg_color=("gray75", "gray25") if name == "sucursal_frame" else "transparent")
        self.frame_pos_button.configure(fg_color=("gray75", "gray25") if name == "pos_frame" else "transparent")
        self.frame_pos_point_button.configure(fg_color=("gray75", "gray25") if name == "pos_point_frame" else "transparent")

        # show selected frame
        if name == "home":
            self.paginador = 0
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        if name == "sucursal_frame":
            self.sucursal_frame.destroy()
            self.sucursalframe()
            self.name_frame = name
            self.precarga_carga()
            # create second frame
        else:
            self.sucursal_frame.grid_forget()
        if name == "pos_frame":
            self.pos_frame.destroy()
            self.posframe()
            self.name_frame = name
            self.precarga_carga()           
        else:
            self.pos_frame.grid_forget()
        if name == "pos_point_frame":
            self.point_pos_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.point_pos_frame.grid_forget()
        
        
    def home_button_event(self):
        self.select_frame_by_name('home')

    def frame_sucursal_button_event(self):
        if self.paginador != 1:
            self.esc_presionado = False  # Reiniciar el contador
            self.select_frame_by_name('sucursal_frame')

    def pos_frame_event(self):
        if self.paginador != 2:
            self.esc_presionado = False  # Reiniciar el contador
            self.select_frame_by_name('pos_frame')

    def frame_pos_point_button_event(self):
        if self.paginador != 3:
            self.esc_presionado = False  # Reiniciar el contador
            self.select_frame_by_name('pos_point_frame')
            
    def on_esc_press(self, e):
        if e.name == 'esc':
            if self.esc_presionado:
                # Realizar acción cuando se presiona 'esc' dos veces
                self.evento_salir_de_mpqrcode()
                self.esc_presionado = False  # Reiniciar el contador
            else:
                self.home_button_event()
                self.esc_presionado = True
                
    def combinar_teclas(self, e):
        if keyboard.is_pressed('shift + tab + enter'):
            GUIconexiones(master=self.ventana_config_inicial)

    def iniciar_escucha(self):
        keyboard.on_press(self.on_esc_press)
        keyboard.on_press_key('shift', self.combinar_teclas)
        keyboard.on_press_key('tab', self.combinar_teclas)
        keyboard.on_press_key('enter', self.combinar_teclas)

    def detener_escucha(self):
        keyboard.unhook_all()
        
    def evento_salir_de_mpqrcode(self):
        msg = CTkMessagebox(title='Cerrar MPQRCODE', message=f'¿Desea salir del MPQRCODE?',
                icon="question", option_1="Si", option_2="No")
        print(msg)
        if msg.get() ==  "Si":
            self.ventana_config_inicial.destroy()
        else:
            pass
        
    def homeframe(self):
        self.home_frame = CTk.CTkFrame(self.ventana_config_inicial, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)
        
        self.inner_frame = CTk.CTkFrame(self.home_frame, fg_color='transparent')        
        self.inner_frame.place(relx=0.5, rely=0.5, anchor=CTk.CENTER)

        
        self.logoMPyInfor()
        # Elementos de la página 1
        self.framaPresentacionWord = CTk.CTkFrame(self.inner_frame, fg_color='transparent')
        self.labelInfo = CTk.CTkLabel(self.framaPresentacionWord, text="Bienvenido al menú de configuración de MercadoPago\n a travez del Sistema de:", font=("Arial", 16), text_color="#8E8484")
        self.labelWord_inforhard = CTk.CTkLabel(self.framaPresentacionWord, text='Inforhard Servicos SRL', font=("Arial", 16), text_color='#008a46')
        # Mostrar elementos de la página 1
        self.frameLOGOSCompany.pack()
        self.logo_mp_img_label.grid(row=1, column=0, padx=20, sticky="e")
        self.labelSignoMas.grid(row=1, column=1, padx=20, sticky="e")
        self.logo_inforhard_img_label.grid(row=1, column=2, padx=20, sticky="e")
        self.framaPresentacionWord.pack(pady=50)
        self.labelInfo.pack()
        self.labelWord_inforhard.pack()
        
    def precarga_carga(self):
        self.frame_carga = CTk.CTkFrame(self.ventana_config_inicial, fg_color='transparent')
        self.frame_carga.grid(row=0, column=1, sticky="nsew")
        self.carga_icono = CTkLoader(master=self.frame_carga, opacity=0.8, width=40, height=40)
        self.ventana_config_inicial.after(3000, self.name_precarga)
        
        
    def name_precarga(self):
        self.carga_icono.stop_loader()
        self.frame_carga.destroy()
        if self.name_frame == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        if self.name_frame == "sucursal_frame":
            self.sucursal_frame.grid(row=0, column=1, sticky="nsew")
        if self.name_frame == "pos_frame":
            self.pos_frame.grid(row=0, column=1, sticky="nsew")
        if self.name_frame == "pos_point_frame":
            self.point_pos_frame.grid(row=0, column=1, sticky="nsew")
        
        
        
    def sucursalframe(self):
        self.paginador = 1
        self.sucursal_frame = CTk.CTkFrame(self.ventana_config_inicial, corner_radius=0, fg_color="transparent")
        CrearSucursalApp(self.ventana_config_inicial, self.sucursal_frame, self.conexionAPI)       
        
    def posframe(self):
        self.paginador = 2
        self.pos_frame = CTk.CTkFrame(self.ventana_config_inicial, corner_radius=0, fg_color="transparent")
        GUIEliminarSucursal(self.pos_frame, self.conexionDBA, self.conexionDBASERVER, self.conexionAPI)
        
        
    def logoMPyInfor(self):
        path_img_inforhard = RutaImagenes.LOGO_INFORHARD()
        
        self.frameLOGOSCompany = CTk.CTkFrame(self.inner_frame, fg_color='transparent')
        
        self.logo_inforhard_img_horizontal = CTk.CTkImage(Image.open(RutaImagenes.LOGO_INFORHARD_horizontal()),
                                            size=(200, 50))
        self.logo_inforhard_img_horizontal_label = CTk.CTkLabel(self.frameLOGOSCompany, image=self.logo_inforhard_img_horizontal, text="")      
        self.logo_mp_img = CTk.CTkImage(Image.open(RutaImagenes.LOGO_MP()),
                                            size=(200, 170))
        self.logo_mp_img_label = CTk.CTkLabel(self.frameLOGOSCompany, image=self.logo_mp_img, text="")        
        self.labelSignoMas = CTk.CTkLabel(self.frameLOGOSCompany, text="+", text_color="#8E8484", font=('Arial', 100))        
        self.logo_inforhard_img = CTk.CTkImage(Image.open(path_img_inforhard),
                                            size=(200, 150))
        self.logo_inforhard_img_label = CTk.CTkLabel(self.frameLOGOSCompany, image=self.logo_inforhard_img, text="")