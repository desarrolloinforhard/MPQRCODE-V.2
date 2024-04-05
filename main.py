import os
import json
import customtkinter
import socket
from tkinter import ttk, simpledialog, messagebox
from assets.image_path import *
from GUI.GUICrearSucursalV2 import CrearSucursalApp # --CREAR SUCURSAL V.2.0
#from GUI.GUICrearSucursal import CrearSucursalApp --CREAR SUCURSAL V.1.0
from GUI.GUICrearCaja import CrearCajaApp
from GUI.GUICrearOrden import CrearOrdenApp
from GUI.GUIConfigCaja import ConfigurarCajaApp
from GUI.GUIDSN import InterfazGrafica
from GUI.GUIMainPOS import ConfigInicialMPQRCODEPOS
from GUI.GUIEliminarSucursal import GUIEliminarSucursal
from database import ConexionSybase
from conexiones import Conexion_APP
from datetime import datetime

# Obtener la fecha y hora actual
fecha_actual = datetime.now()

# Formatear la fecha y hora actual
fecha_formateada = fecha_actual.strftime("%d-%m-%Y %H:%M:%S")

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("green")

class ConfigInicialMPQRCODE:
    def __init__(self):
        conexion_internet = self.verificar_conexion_internet()
        if conexion_internet:
            self.user_id = None
            self.access_token = None     
            self.dsn_caja = None
            self.dsn_servidor = None
            self.dsn_servidor_respaldo = None
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
                print(self.comparacion_fechas(fecha_formateada, fecha_api))
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
                root = customtkinter.CTk()
                rutaicono = Icono_MercadoPago_Blue()
                root.iconbitmap(rutaicono)
                app = InterfazGrafica(root)
                root.mainloop()  
        else:
            messagebox.showerror('No hay conexión', 'Sin conexión a internet')
            
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
            messagebox.showerror('Error fechas', e)
            
            
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
                password_correcto = "***"
                if password_ingresado == password_correcto:
                    if self.tabla_clientes_vacia():
                        self.conexionDBASERVER.crear_tabla_MPQRCODE_CLIENTE()
                        self.crear_interfaz()
                        messagebox.showinfo("Información", "Cliente cargado.")
                        gui_conexiones = GUIconexiones(self.conexionDBA, self.conexionDBASERVER)
                        gui_conexiones.crear_ventana_principal()
                    else:
                        messagebox.showinfo("Información", "Ya hay un cliente cargado.")
                        gui_conexiones = GUIconexiones(self.conexionDBA, self.conexionDBASERVER)
                        gui_conexiones.crear_ventana_principal()                
                elif password_ingresado == "6a" or password_ingresado == "":
                    condicion = False
                    ConfigInicialMPQRCODEPOS()
                elif password_ingresado == "CONNECTDSN":
                    directorio_script = os.path.dirname(os.path.abspath(__file__))
                    root = customtkinter.CTk()
                    rutaicono = Icono_MercadoPago_Blue()
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
        self.root = customtkinter.CTk()
        self.root.title("Configuración inicial MPQRCODE")
        rutaicono = Icono_MercadoPago_Blue()
        self.root.iconbitmap(rutaicono)

        customtkinter.CTkLabel(self.root, text="User ID de MercadoPago:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        customtkinter.CTkLabel(self.root, text="Access Token de MercadoPago:").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        customtkinter.CTkLabel(self.root, text="Access Token POINT de MercadoPago:").grid(row=2, column=0, padx=10, pady=5, sticky='w')

        self.entry_user_id = customtkinter.CTkEntry(self.root, font=('Helvetica', 12))
        self.entry_access_token = customtkinter.CTkEntry(self.root, show='*', font=('Helvetica', 12))
        self.entry_access_tokenPOINT = customtkinter.CTkEntry(self.root, show='*', font=('Helvetica', 12))

        self.entry_user_id.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        self.entry_access_token.grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        self.entry_access_tokenPOINT.grid(row=2, column=1, padx=10, pady=5, sticky='ew')

        customtkinter.CTkButton(self.root, text="Agregar", command=self.validar_y_agregar).grid(row=3, column=0, columnspan=2, pady=10)

        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)  # Vincular el cierre de la ventana

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
            except Exception as e:
                messagebox.showerror("Error", f"Error al insertar datos en la base de datos: {str(e)}")

    def cerrar_ventana(self):
        self.root.destroy()
        
        
    def cargar_configuracion(self):
        try:
            directorio_script_json = os.path.dirname(os.path.abspath(__file__))
            ruta_relativaGUI = os.path.join(directorio_script_json, "GUI")
            ruta_relativaJSON = os.path.join(ruta_relativaGUI, "configuracion.json")
            
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
        self.rootWindowsIPN = customtkinter.CTk()
        self.rootWindowsIPN.title("UPDATE IPN URL")
        rutaicono = Icono_MercadoPago_Blue()
        self.rootWindowsIPN.iconbitmap(rutaicono)
        
        
        customtkinter.CTkLabel(self.rootWindowsIPN, text="Nuevo url IPN:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        entry_nombre_pos = ttk.Entry(self.rootWindowsIPN)
        entry_nombre_pos.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        
        customtkinter.CTkButton(self.rootWindowsIPN, text="Actualizar IPN", command=lambda:self.actulizarIPN(entry_nombre_pos.get())).grid(row=1, column=0, columnspan=2, pady=10)
        self.rootWindowsIPN.mainloop()
    def actulizarIPN(self, newIPN):
        self.conexionDBASERVER.actualizar_todos_valores_columna("MPQRCODE_CAJAS", "IPN_url", newIPN)
        valor = True
        if not valor == False:
            messagebox.showinfo("Exito", "Valores Actualizados")
            self.rootWindowsIPN.destroy()
            valor = False
        
        

class GUIconexiones:
    def __init__(self, conexionDBA, conexionDBASERVER):
        self.conexionDBA = conexionDBA
        self.conexionDBASERVER = conexionDBASERVER
        self.id_user = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'idUSER', 1)
        self.token  = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKEN', 1)
        self.tokenPOINT = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKENPOINT', 1)
        self.datos_connect = (self.id_user, self.token, self.tokenPOINT)
        self.ventana_principal = None
        self.conexionAPI = Conexion_APP(self.datos_connect, self.conexionDBA, self.conexionDBASERVER)
        self.rutadocumento = os.path.dirname(os.path.abspath(__file__))

    def crear_ventana_principal(self):
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")
        self.ventana_principal = customtkinter.CTk()
        self.centrar_ventana_principal()
        self.ventana_principal.title("Menú Principal")
        rutaicono = Icono_MercadoPago_Blue()
        self.ventana_principal.iconbitmap(rutaicono)        
        
        self.label_name_top = customtkinter.CTkLabel(self.ventana_principal, text="Manejo del DBA", font=('Arial Black', 15))
        self.label_name_top.grid(row=0, column=0, pady=20)
        self.frame_top()
        self.label_name_bottom = customtkinter.CTkLabel(self.ventana_principal, text="Manejo de MercadoPago", font=('Arial Black', 15))
        self.label_name_bottom.grid(row=2, column=0, pady=20)
        self.frame_botton()

        self.ventana_principal.geometry("540x350")
        self.ventana_principal.resizable(False, False)
        self.ventana_principal.mainloop()
        
    def frame_top(self):
        self.frame_ventana_principal_top = customtkinter.CTkFrame(self.ventana_principal, height=50, fg_color='transparent')
        self.frame_ventana_principal_top.grid(row=1, column=0, padx=120)
        
        self.button_crear_tabla_POS = customtkinter.CTkButton(self.frame_ventana_principal_top, text="Crear Tablas POS", command=self.crear_tabla_pos)
        self.button_crear_tabla_POS.grid(row=0, column=0, padx=5, pady=5)
        self.button_crear_tabla_SERVER = customtkinter.CTkButton(self.frame_ventana_principal_top, text="Crear Tablas Server", command=self.crear_tabla_server)
        self.button_crear_tabla_SERVER.grid(row=0, column=1, padx=5, pady=5)
        self.button_eliminar_tabla_POS = customtkinter.CTkButton(self.frame_ventana_principal_top, text="Eliminar Tablas POS", command=self.eliminar_tabla_pos)
        self.button_eliminar_tabla_POS.grid(row=1, column=0, padx=5, pady=5)
        self.button_eliminar_tabla_SERVER = customtkinter.CTkButton(self.frame_ventana_principal_top, text="Eliminar Tablas Server", command=self.eliminar_tabla_server)
        self.button_eliminar_tabla_SERVER.grid(row=1, column=1, padx=5, pady=5)
        
        if self.conexionDBA.check_table_existence("MPQRCODE_OBTENERPAGO"):
            self.button_crear_tabla_POS.configure(state=customtkinter.DISABLED)
            self.button_eliminar_tabla_POS.configure(state=customtkinter.NORMAL)
        else:
            self.button_crear_tabla_POS.configure(state=customtkinter.NORMAL)
            self.button_eliminar_tabla_POS.configure(state=customtkinter.DISABLED)
        
        if self.conexionDBASERVER.check_table_existence("MPQRCODE_OBTENERPAGOServer"):
            self.button_crear_tabla_SERVER.configure(state=customtkinter.DISABLED)
            self.button_eliminar_tabla_SERVER.configure(state=customtkinter.NORMAL)
        else:
            self.button_crear_tabla_SERVER.configure(state=customtkinter.NORMAL)
            self.button_eliminar_tabla_SERVER.configure(state=customtkinter.DISABLED)

    def frame_botton(self):
        self.frame_ventana_principal = customtkinter.CTkFrame(self.ventana_principal, height=350, fg_color='transparent')
        self.frame_ventana_principal.grid(row=3, column=0, sticky='nsew', padx=50)
        
        self.button_crear_sucursal = customtkinter.CTkButton(self.frame_ventana_principal, text="Crear Sucursal", command=self.crear_sucursal_app)
        self.button_crear_sucursal.grid(row=0, column=0, pady=5, sticky='nsew')
        customtkinter.CTkButton(self.frame_ventana_principal, text="Crear Caja", command=self.crear_caja_app,).grid(row=1, column=0, pady=5, sticky='nsew')
        customtkinter.CTkButton(self.frame_ventana_principal, text="Ordenes", command=self.crear_orden_app,).grid(row=2, column=0, pady=5, sticky='nsew')

        customtkinter.CTkButton(self.frame_ventana_principal, text="Eliminar Sucursal", command=self.eliminar_sucursal_app).grid(row=0, column=1, pady=5, padx=5, sticky='nsew')
        customtkinter.CTkButton(self.frame_ventana_principal, text="Configurar Caja", command=self.config_caja_app,).grid(row=1, column=1, pady=5, padx=5, sticky='nsew')
        customtkinter.CTkButton(self.frame_ventana_principal, text="Eliminar Orden", command=self.mostrar_ventana_creacion_orden,).grid(row=2, column=1, pady=5, padx=5, sticky='nsew')

        self.frame_ventana_principal.columnconfigure(0, weight=1)
        self.frame_ventana_principal.columnconfigure(1, weight=1)
        self.frame_ventana_principal.rowconfigure([0, 1], weight=1)
    

    def crear_sucursal_app(self):
        try:
            CrearSucursalApp(self.ventana_principal, self.conexionAPI)
        except Exception as e:
            print(e)
            messagebox.showerror("Error", f"Error al crear la instancia de CrearSucursalApp: {str(e)}")

    def crear_caja_app(self):
        try:
            crear_caja_app_instance = CrearCajaApp(self.conexionAPI, self.conexionDBASERVER)
        except Exception as e:
            print(f"Error: {e}")
            
    def crear_orden_app(self):
        try:
            crear_orden_app_instance = CrearOrdenApp(self.conexionAPI, self.conexionDBA, self.conexionDBASERVER)
        except Exception as e:
                print(f"Error: {e}")
                
    def config_caja_app(self):
        try:
            config_orden_app_instance = ConfigurarCajaApp(self.conexionAPI, self.conexionDBA, self.conexionDBASERVER)
        except Exception as e:
                print(f"Error: {e}")
                
    def eliminar_sucursal_app(self):
        try:
            GUIEliminarSucursal(self.ventana_principal, self.conexionDBASERVER, self.conexionAPI)
        except Exception as e:
                print(f"Error: {e}")
    
    def mostrar_ventana_creacion_orden(self):
        # Código para la ventana de creación de orden
        pass
    
    def crear_tabla_server(self):        
        self.conexionDBASERVER.crearTablasSERVER()
        messagebox.showinfo("Éxito", "Se han creado las tablas del Server")
        self.button_crear_tabla_SERVER.configure(state=customtkinter.DISABLED)
        self.button_eliminar_tabla_SERVER.configure(state=customtkinter.NORMAL)
        self.ventana_principal.update()

    def crear_tabla_pos(self):
        self.conexionDBA.crearTablasPOS()
        messagebox.showinfo("Éxito", "Se han creado las tablas del POS")
        self.button_crear_tabla_POS.configure(state=customtkinter.DISABLED)
        self.button_eliminar_tabla_POS.configure(state=customtkinter.NORMAL)
        self.ventana_principal.update()

    def eliminar_tabla_server(self):
        choice_mktableserver = messagebox.askquestion(message="Vas a eliminar las tablas de MERCADOPAGO en servidor. Esto podría traer errores a la hora de las creaciones de las ordenes. \n ¿Seguro que deseas continuar?", title="¿Deseas continuar?")
        
        if choice_mktableserver == 'yes':
            self.conexionDBASERVER.eliminarTablasSERVER()
            messagebox.showinfo("Éxito", "Se han eliminado las tablas del Server")
            self.button_crear_tabla_SERVER.configure(state=customtkinter.NORMAL)
            self.button_eliminar_tabla_SERVER.configure(state=customtkinter.DISABLED)
            self.ventana_principal.destroy()
        else:
            messagebox.showinfo("Abortar", "Se ha cancelado la operación")
        self.ventana_principal.update()

    def eliminar_tabla_pos(self):
        choice_mktablePOS = messagebox.askquestion(message="Vas a eliminar las tablas de MERCADOPAGO en el POS. Esto podría traer errores a la hora de las creaciones de las ordenes. \n ¿Seguro que deseas continuar?", title="¿Deseas continuar?")        
        if choice_mktablePOS == 'yes':
            self.conexionDBA.eliminarTablasPOS()  
            messagebox.showinfo("Éxito", "Se han eliminado las tablas del POS")
            self.button_crear_tabla_POS.configure(state=customtkinter.NORMAL)
            self.button_eliminar_tabla_POS.configure(state=customtkinter.DISABLED)
        else:
            messagebox.showerror("Abortar", "Se ha cancelado la operación")                   
        self.ventana_principal.update()
        
    def centrar_ventana_principal(self):
        self.ventana_principal.update_idletasks()
        ancho = self.ventana_principal.winfo_width()
        alto = self.ventana_principal.winfo_height()
        x = (self.ventana_principal.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.ventana_principal.winfo_screenheight() // 2) - (alto // 2)
        self.ventana_principal.geometry('+{}+{}'.format(x, y))


    
if __name__ == "__main__":
    config = ConfigInicialMPQRCODE()