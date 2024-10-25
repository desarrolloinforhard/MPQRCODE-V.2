import customtkinter as CTk
import traceback
import os
import json
import socket
import keyboard
import requests
import image_path as RutaImagenes
from ctk_components.ctk_components import *
from GUIConfigDBA import GUIconexiones
from GUICrearSucursalV3 import CrearSucursalApp
from GUICrearCajaV2 import GUIEliminarSucursal
from GUITopLevelCargaCREARORDEN import TopLevelCargaCREARORDEN
from GUICrearOrden import CrearOrdenApp
from GUIDSN import InterfazGrafica
from GUIVentas_MP import GUIVentas_MP
from window_position import center_window
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import simpledialog, messagebox
from PIL import Image
from datetime import datetime
from database import ConexionSybase
from conexiones import Conexion_APP

# Obtener la fecha y hora actual
fecha_actual = datetime.now()

# Formatear la fecha y hora actual
fecha_formateada = fecha_actual.strftime("%d-%m-%Y %H:%M:%S")

class ConfigInicialMPQRCODE:
    def __init__(self, version):
        conexion_internet = self.verificar_conexion_internet()
        if conexion_internet:
            self.user_id = None
            self.access_token = None     
            self.dsn_caja = None
            self.dsn_servidor = None
            self.tipo_operador = None
            self.dsn_servidor_central = None
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
                if not self.dsn_servidor_central == False:
                    self.conexionDBACENTRAL = ConexionSybase(
                        user="dba",
                        password="gestion",
                        dsn=self.dsn_servidor_central
                    )
                if self.conexionDBA.conectar() and self.conexionDBASERVER.conectar():
                    if not self.dsn_servidor_central == False:
                        if self.conexionDBACENTRAL.conectar():
                            pass
                        else:
                            messagebox.showinfo("Sin conexión", "No se pudo conectar a la central. No realize envios de datos a la central.")
                    if self.pedido_API_online():
                        self.validar_password(version)
                else:
                        messagebox.showerror('Error con el DBA', 'No se puede lograr conexion con ninguna base de datos')
            else:
                messagebox.showerror("Error", "DSN NO CONFIGURADOS. Habra el configurador de DSN e introduzcalos.")
                root = CTk.CTk()
                rutaicono = RutaImagenes.Icono_MercadoPago_Blue()
                root.iconbitmap(rutaicono)
                app = InterfazGrafica(root)
                root.mainloop()  
        else:
            messagebox.showerror('No hay conexión', 'Sin conexión a internet')

    def llamar_crear_orden(self):
        self.id_user = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'idUSER', 1)
        self.token = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKEN', 1)
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
            if caracter not in '-: ':
                caracteres.append(caracter)  # Agregar el caracter a la lista
            else:
                if caracteres:  # Verificar si hay caracteres en la lista
                    fecha_separada = int(''.join(caracteres))  # Convertir la lista de caracteres a entero
                    lista_fechas.append(fecha_separada)  # Agregar la fecha separada a la lista de fechas
                    caracteres = []  # Reiniciar la lista de caracteres para la próxima fecha
        if caracteres:  # Agregar la última fecha si hay caracteres en la lista
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

    def validar_password(self, version):
        try:
            condicion = True
            windows = ttk.Window(themename="darkly")
            windows.state('zoomed')
            windows.title('Sistema MercadoPago')
            windows.iconbitmap(RutaImagenes.Icono_MercadoPago_Blue())
            
            while condicion:
                password_ingresado = simpledialog.askstring("Password", "Ingrese el password:", show='*', parent=windows)
                if password_ingresado is None:
                    # Usuario canceló la operación, salir del bucle
                    break
                
                password_correcto = "*123*"
                if password_ingresado == password_correcto:
                    condicion = False  # Salir del bucle
                    
                    if not self.dsn_servidor_central == False:
                        if self.tabla_clientes_vacia():
                            self.conexionDBASERVER.crear_tabla_MPQRCODE_CLIENTE()
                            self.crear_interfaz()
                            messagebox.showinfo("Información", "Cliente cargado.")
                            GUIConfigInicialV2(windows, self.conexionDBA, self.conexionDBASERVER, self.tipo_operador, self.conexionDBACENTRAL, version=version)
                        else:
                            messagebox.showinfo("Información", "Ya hay un cliente cargado.")
                            GUIConfigInicialV2(windows, self.conexionDBA, self.conexionDBASERVER, self.tipo_operador, self.conexionDBACENTRAL, version=version)
                    else:
                        if self.tabla_clientes_vacia():
                            self.conexionDBASERVER.crear_tabla_MPQRCODE_CLIENTE()
                            self.crear_interfaz()
                            messagebox.showinfo("Información", "Cliente cargado.")
                            GUIConfigInicialV2(windows, self.conexionDBA, self.conexionDBASERVER, self.tipo_operador, version=version)
                        else:
                            messagebox.showinfo("Información", "Ya hay un cliente cargado.")
                            GUIConfigInicialV2(windows, self.conexionDBA, self.conexionDBASERVER, self.tipo_operador, version=version)  
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
                    messagebox.showinfo("Exito", "Se eliminaron las tablas del Server y el POS")
                elif password_ingresado == "RSTTABLECAJA":
                    self.conexionDBA.eliminar_tabla("MPQRCODE_CAJA")
                    self.conexionDBA.crear_tabla_MPQRCODE_CAJA()
                    messagebox.showinfo("Exito", "Se eliminaron los datos de la Caja")
                elif password_ingresado == "RSTOBPAGOServer":
                    self.conexionDBASERVER.eliminar_tabla("MPQRCODE_RESPUESTAPOST")
                    self.conexionDBASERVER.eliminar_tabla("MPQRCODE_OBTENERPAGOServer")
                    self.conexionDBASERVER.crear_tabla_MPQRCODE_RESPUESTAPOST()
                    self.conexionDBASERVER.crear_tabla_MPQRCODE_OBTENERPAGOServer()
                elif password_ingresado == "IPN":
                    self.ventana_actualizarIPN()
                elif password_ingresado == "MKTABLEPOS":
                    messagebox.showinfo("Exito", "Se han creado las tablas del POS")
                    self.conexionDBA.crearTablasPOS()
                elif password_ingresado == "RSTOBPAGOS":
                    messagebox.showinfo("Exito", "Se han creado las tablas del POS")
                    self.conexionDBASERVER.eliminar_tabla("MPQRCODE_OBTENERPAGOServer")
                    self.conexionDBASERVER.crear_tabla_MPQRCODE_OBTENERPAGOServer()
                elif password_ingresado == "MKTABLESERVER":
                    self.conexionDBASERVER.crearTablasSERVER()
                    messagebox.showinfo("Exito", "Se han creado las tablas del Server")
                elif password_ingresado == "DLTTABLESPOS":
                    self.conexionDBA.eliminarTablasPOS()
                    messagebox.showinfo("Exito", "Se han eliminado las tablas del POS")
                elif password_ingresado == "DLTTABLESSERVER":
                    self.conexionDBASERVER.eliminarTablasSERVER()
                    messagebox.showinfo("Exito", "Se han eliminado las tablas del Server")
                elif password_ingresado == "RSTTABLESRESPUESTA":
                    self.conexionDBA.eliminarOrdenesPostDBA()
                    messagebox.showinfo("Exito", "Se restauraron las Ordenes")
                elif password_ingresado == "RSTCLIENTE":
                    self.conexionDBASERVER.eliminar_tabla("MPQRCODE_CLIENTE")
                    self.conexionDBASERVER.crear_tabla_MPQRCODE_CLIENTE()
                    messagebox.showinfo("Exito", "Se reinició el cliente")
                elif password_ingresado == "TESTBUY":
                    datos = {
                        "nro_factura": "00000-1111571432",
                        "tipo_factura": 1,
                        "monto_pagar": 2134.00,
                        "status": 0
                    }
                    self.conexionDBA.insertar_datos_sin_obtener_id("MPQRCODE_CONEXIONPROGRAMAS", datos)
                    messagebox.showinfo("Exito", "Se reinició la tabla CONEXIONPROGRAMAS")
                elif password_ingresado == "DLTTESTBUY":
                    self.conexionDBA.eliminar_tabla("MPQRCODE_CONEXIONPROGRAMAS")
                    self.conexionDBA.crear_tabla_MPQRCODE_CONEXIONPROGRAMAS()
                else:
                    messagebox.showerror("Error", "Password incorrecto.")
        except Exception as e:
            # Mostrar el mensaje de error con detalles de la línea
            traceback_msg = traceback.format_exc()
            print(traceback_msg)
            messagebox.showerror('Error validación', f'Error en la validación de password:\n{traceback_msg}')

            
    def tabla_clientes_vacia(self):
        if self.conexionDBASERVER.tabla_vacia('MPQRCODE_CLIENTE'):
            return True
        else:
            return False

    def pedido_API_online(self):
        try:
            lista_id_increment = self.conexionDBASERVER.specify_search_columna('MPQRCODE_CAJAS', 'idINCREMENT')
            print(lista_id_increment)
            if lista_id_increment:
                url_de_DBA = self.conexionDBASERVER.specify_search_condicion('MPQRCODE_CAJAS', 'IPN_url', 'idINCREMENT', lista_id_increment[0], False)
                print(url_de_DBA)
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
                if self.dsn_caja == self.dsn_servidor:
                    return True
                else:
                    messagebox.showerror("Error", "No se encontro caja activa")
                    return False
        except Exception as e:
            if self.conexionDBASERVER.tabla_vacia('MPQRCODE_CLIENTE'):
                messagebox.showerror('No se pudo conectar', f'No se puede conectar con la API.\n{e}')
                self.crear_interfaz()
                if self.resultado:
                    messagebox.showinfo('OK', 'El cliente se ha agregado, puede levantar el server, local y host.')
                else:
                    messagebox.showerror('No agregado', 'No se pudo agregar ni un cliente, no puedes acceder a la Interfaz de Pago')
            else:
                messagebox.showinfo('Aviso', 'Los datos del cliente se encuentran cargados pero no se levantó el servidor APIRest de INFORHARD S.R.L')
            return False

    def cargar_configuracion(self):
        try:
            directorio_script_json = os.path.dirname(os.path.abspath(__file__))
            ruta_relativaJSON = os.path.join(directorio_script_json, "configuracion.json")
            
            with open(ruta_relativaJSON, "r") as file:
                configuracion = json.load(file)
                self.dsn_caja = configuracion.get("dsn_caja", "")
                self.dsn_servidor = configuracion.get("dsn_servidor", "")
                
                
                # Verificar si existe la clave "dsn_servidor_central"
                if "dsn_servidor_central" in configuracion:
                    self.dsn_servidor_central = configuracion["dsn_servidor_central"]
            print(self.dsn_caja, self.dsn_servidor)
            self.tipo_operador = self.dsn_caja == self.dsn_servidor
        except FileNotFoundError:
            messagebox.showerror('Error', 'El archivo de configuración no existe.')
        except json.JSONDecodeError:
            messagebox.showerror('Error', 'Error al analizar el archivo de configuración JSON.')
        except Exception as e:
            messagebox.showerror('Error', f'Ocurrió un error al cargar la configuración: {e}')

    def crear_interfaz(self):
        # Crear una ventana emergente para el formulario de inicio de sesión
        dialog = simpledialog.Dialog(None, title="Datos de MercadoPago")
        dialog.geometry("400x300")

        # Variables para los campos de entrada
        user_id = ttk.StringVar()
        access_token = ttk.StringVar()
        auth_token_point = ttk.StringVar()

        # Función para manejar el envío del formulario
        def enviar():
            self.user_id = user_id.get()
            self.access_token = access_token.get()
            self.auth_token_point = auth_token_point.get()
            self.resultado = self.conexionDBASERVER.insertar_cliente_MPQRCODE_CLIENTE(self.user_id, self.access_token, self.auth_token_point)
            dialog.destroy()  # Cerrar el formulario

        # Crear los widgets del formulario
        label_user_id = ttk.Label(dialog, text="User ID:")
        entry_user_id = ttk.Entry(dialog, textvariable=user_id)

        label_access_token = ttk.Label(dialog, text="Access Token:")
        entry_access_token = ttk.Entry(dialog, textvariable=access_token)

        label_auth_token_point = ttk.Label(dialog, text="Auth Token Point:")
        entry_auth_token_point = ttk.Entry(dialog, textvariable=auth_token_point)

        button_enviar = ttk.Button(dialog, text="Enviar", command=enviar)

        # Colocar los widgets en la ventana usando un grid
        label_user_id.grid(row=0, column=0, padx=10, pady=10)
        entry_user_id.grid(row=0, column=1, padx=10, pady=10)

        label_access_token.grid(row=1, column=0, padx=10, pady=10)
        entry_access_token.grid(row=1, column=1, padx=10, pady=10)

        label_auth_token_point.grid(row=2, column=0, padx=10, pady=10)
        entry_auth_token_point.grid(row=2, column=1, padx=10, pady=10)

        button_enviar.grid(row=3, columnspan=2, pady=10)

        dialog.wait_window()  # Esperar a que se cierre el formulario
        
    

"""class InterfazGrafica:
    def __init__(self, master):
        self.master = master
        self.master.title("Configuración de DSN")
        self.master.geometry("400x200")

        # Crear las variables para los campos de entrada
        self.dsn_caja = tk.StringVar()
        self.dsn_servidor = tk.StringVar()
        self.dsn_servidor_central = tk.StringVar()
        self.tipo_operador = tk.StringVar()

        # Crear los widgets del formulario
        label_dsn_caja = tk.Label(master, text="DSN Caja:")
        entry_dsn_caja = tk.Entry(master, textvariable=self.dsn_caja)

        label_dsn_servidor = tk.Label(master, text="DSN Servidor:")
        entry_dsn_servidor = tk.Entry(master, textvariable=self.dsn_servidor)

        label_dsn_servidor_central = tk.Label(master, text="DSN Servidor Central:")
        entry_dsn_servidor_central = tk.Entry(master, textvariable=self.dsn_servidor_central)

        label_tipo_operador = tk.Label(master, text="Tipo Operador:")
        entry_tipo_operador = tk.Entry(master, textvariable=self.tipo_operador)

        button_guardar = tk.Button(master, text="Guardar", command=self.guardar_configuracion)

        # Colocar los widgets en la ventana usando un grid
        label_dsn_caja.grid(row=0, column=0, padx=10, pady=10)
        entry_dsn_caja.grid(row=0, column=1, padx=10, pady=10)

        label_dsn_servidor.grid(row=1, column=0, padx=10, pady=10)
        entry_dsn_servidor.grid(row=1, column=1, padx=10, pady=10)

        label_dsn_servidor_central.grid(row=2, column=0, padx=10, pady=10)
        entry_dsn_servidor_central.grid(row=2, column=1, padx=10, pady=10)

        label_tipo_operador.grid(row=3, column=0, padx=10, pady=10)
        entry_tipo_operador.grid(row=3, column=1, padx=10, pady=10)

        button_guardar.grid(row=4, columnspan=2, pady=10)

    def guardar_configuracion(self):
        configuracion = {
            "dsn_caja": self.dsn_caja.get(),
            "dsn_servidor": self.dsn_servidor.get(),
            "dsn_servidor_central": self.dsn_servidor_central.get(),
            "tipo_operador": self.tipo_operador.get()
        }
        with open("configuracion.json", "w") as archivo:
            json.dump(configuracion, archivo)
        messagebox.showinfo("Información", "Configuración guardada exitosamente.")
        self.master.destroy()  # Cerrar la ventana

        
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
        """


class GUIConfigInicialV2:
    def __init__(self, root, conexionDBA, conexionDBASERVER, tipo_operador, version, conexionDBACentral=False):
        self.conexionDBA = conexionDBA
        self.conexionDBASERVER = conexionDBASERVER
        self.conexionDBACentral = conexionDBACentral
        self.esc_presionado = False
        self.tipo_operador = tipo_operador
        self.activado_envio_automatico = False
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
        self.ventana_config_inicial = root
        # Opcional: configurar manejo de cierre de ventana
        self.ventana_config_inicial.protocol("WM_DELETE_WINDOW", self.confirmar_salida)
        print(tipo_operador)
        if tipo_operador:
            self.ventana_config_inicial.title(f'Configuración MPQRCODE (Servidor) - version {version}')
        else:
            suc_pos = self.conexionDBA.specify_search("MPQRCODE_CAJA", "sucNAME", 1)
            pos_name = self.conexionDBA.specify_search("MPQRCODE_CAJA", "posNAME", 1)
            if not suc_pos == None and not pos_name == None:
                self.ventana_config_inicial.title(f'Configuración MPQRCODE ({suc_pos}, {pos_name}) - version {version}')
            else:
                self.ventana_config_inicial.title(f'Configuración MPQRCODE (NEW POS) - version {version}')
        
        self.ventana_config_inicial.grid_rowconfigure(0, weight=1)
        self.ventana_config_inicial.grid_columnconfigure(1, weight=1)

        self.logo_inforhard = ImageTk.PhotoImage(Image.open(RutaImagenes.LOGO_INFORHARD()).resize((130, 80)))
        self.logo_inforhard_horizontal = ImageTk.PhotoImage(Image.open(RutaImagenes.LOGO_INFORHARD_horizontal()).resize((200, 50)))
        self.home_image = ImageTk.PhotoImage(Image.open(RutaImagenes.HOME()).resize((45, 45)))
        self.sucursal_png = ImageTk.PhotoImage(Image.open(RutaImagenes.SUCURSAL()).resize((45, 45)))
        self.pdv_png = ImageTk.PhotoImage(Image.open(RutaImagenes.CAJERO1()).resize((45, 45)))
        self.point_png = ImageTk.PhotoImage(Image.open(RutaImagenes.POINTPOS()).resize((45, 45)))
        self.stadistica_png = ImageTk.PhotoImage(Image.open(RutaImagenes.ESTADISTICA()).resize((45, 45)))
        
        self.navigation_frame = ttk.Frame(self.ventana_config_inicial)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(5, weight=1)

        self.navigation_frame_label = ttk.Label(self.navigation_frame, text="", image=self.logo_inforhard, compound="left", font=("Arial", 15, "bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.frame_sucursal_button = ttk.Button(self.navigation_frame, bootstyle="success", text="Sucursal", image=self.sucursal_png, compound="left", command=self.frame_sucursal_button_event)
        self.frame_sucursal_button.grid(row=1, column=0, sticky="ew")

        self.frame_pos_button = ttk.Button(self.navigation_frame, bootstyle="success", text="PDV", image=self.pdv_png, compound="left", command=self.pos_frame_event)
        self.frame_pos_button.grid(row=2, column=0, sticky="ew")

        self.frame_pos_point_button = ttk.Button(self.navigation_frame, bootstyle="success", text="Points MP", image=self.point_png, compound="left", command=self.frame_pos_point_button_event)
        self.frame_pos_point_button.grid(row=3, column=0, sticky="ew")
        
        self.frame_ventas_mp_button = ttk.Button(self.navigation_frame, bootstyle="success", text="Ventas", image=self.stadistica_png, compound="left", command=self.frame_ventas_mp_button_event)
        self.frame_ventas_mp_button.grid(row=4, column=0, sticky="ew")

        self.homeframe()        
        self.sucursalframe()
        self.posframe()
        self.ventasmpframe()

        self.point_pos_frame = ttk.Frame(self.ventana_config_inicial)

        self.select_frame_by_name("home")
        
        ancho_pantalla = self.ventana_config_inicial.winfo_screenwidth()
        alto_pantalla = self.ventana_config_inicial.winfo_screenheight()
        self.ventana_config_inicial.geometry(f"{ancho_pantalla}x{alto_pantalla}")
        center_window(self.ventana_config_inicial, ancho_pantalla, alto_pantalla)
        
        root.mainloop()


    def confirmar_salida(self):
        if not self.activado_envio_automatico:
            if messagebox.askquestion("Confirmar salida", "¿Estás seguro que deseas salir?") == "yes":
                self.ventana_config_inicial.destroy()
        else:
            messagebox.showerror("Error", "No puedes salir mientras el envío automático está activado")

    def select_frame_by_name(self, name):

        # show selected frame
        if name == "home":
            self.paginador = 0
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        if name == "sucursal_frame":
            self.name_frame = name
            self.precarga_carga()
        else:
            self.sucursal_frame.grid_forget()
        if name == "pos_frame":
            self.name_frame = name
            self.precarga_carga()           
        else:
            self.pos_frame.grid_forget()
        if name == "pos_point_frame":
            self.point_pos_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.point_pos_frame.grid_forget()
        if name == 'ventas_frame':
            self.name_frame = name
            self.precarga_carga()
        else:
            self.ventas_mp_frame.grid_forget()

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
            
    def frame_ventas_mp_button_event(self):
        if self.paginador != 4:
            self.esc_presionado = False  # Reiniciar el contador
            self.select_frame_by_name('ventas_frame')

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
        if messagebox.askquestion("Cerrar MPQRCODE", "¿Desea salir del MPQRCODE?") == "yes":
            self.ventana_config_inicial.destroy()

        
    def homeframe(self):
        self.home_frame = ttk.Frame(self.ventana_config_inicial)
        self.home_frame.grid_columnconfigure(0, weight=1)
        
        self.inner_frame = ttk.Frame(self.home_frame,)        
        self.inner_frame.place(relx=0.5, rely=0.5, anchor=ttk.CENTER)

        self.logoMPyInfor()
        # Elementos de la página 1
        self.framaPresentacionWord = ttk.Frame(self.inner_frame,)
        self.labelInfo = ttk.Label(self.framaPresentacionWord, text="Bienvenido al menú de configuración de MercadoPago\n a través del Sistema de:", font=("Arial", 16), foreground="#8E8484",)
        self.labelWord_inforhard = ttk.Label(self.framaPresentacionWord, text='Inforhard Servicios SRL', font=("Arial", 16), foreground='#008a46',)
        # Mostrar elementos de la página 1
        self.frameLOGOSCompany.pack()

        # Aquí usas solo pack dentro de frameLOGOSCompany
        self.logo_mp_img_label.pack(side=ttk.LEFT, padx=20)
        self.labelSignoMas.pack(side=ttk.LEFT, padx=20)
        self.logo_inforhard_img_label.pack(side=ttk.LEFT, padx=20)

        self.framaPresentacionWord.pack(pady=50)
        self.labelInfo.pack()
        self.labelWord_inforhard.pack()

    def precarga_carga(self):
        self.frame_carga = ttk.Frame(self.ventana_config_inicial,)
        self.frame_carga.grid(row=0, column=1, sticky="nsew")
        self.carga_icono = ttk.Label(self.frame_carga, text="Cargando...",)  # Reemplaza CTkLoader con un Label
        self.carga_icono.pack()
        self.ventana_config_inicial.after(3000, self.name_precarga)

    def name_precarga(self):
        self.carga_icono.destroy()
        self.frame_carga.destroy()
        if self.name_frame == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        if self.name_frame == "sucursal_frame":
            self.sucursal_frame.grid(row=0, column=1, sticky="nsew")
        if self.name_frame == "pos_frame":
            self.pos_frame.grid(row=0, column=1, sticky="nsew")
        if self.name_frame == "pos_point_frame":
            self.point_pos_frame.grid(row=0, column=1, sticky="nsew")
        if self.name_frame == "ventas_frame":
            self.ventas_mp_frame.grid(row=0, column=1, sticky="nsew")

    def sucursalframe(self):
        self.paginador = 1
        self.sucursal_frame = ttk.Frame(self.ventana_config_inicial,)
        if self.tipo_operador:
            CrearSucursalApp(self.ventana_config_inicial, self.sucursal_frame, self.conexionAPI)
        else:
            self.label_aviso_no_servidor = ttk.Label(self.sucursal_frame, text="Este es un PDV, no puedes crear Sucursales desde aquí. Créalo desde el Servidor.", wraplength=500,)       
            self.label_aviso_no_servidor.place(relx=0.5, rely=0.5, anchor=ttk.CENTER)

    def posframe(self):
        self.paginador = 2
        self.pos_frame = ttk.Frame(self.ventana_config_inicial,)
        GUIEliminarSucursal(self.pos_frame, self.conexionDBA, self.conexionDBASERVER, self.conexionAPI)

    def ventasmpframe(self):
        self.paginador = 4
        self.ventas_mp_frame = ttk.Frame(self.ventana_config_inicial,)
        if self.tipo_operador:
            if self.conexionDBACentral:
                GUIVentas_MP(self.ventana_config_inicial, self.ventas_mp_frame, self.conexionDBASERVER, self.conexionDBACentral)
            else:
                GUIVentas_MP(self.ventana_config_inicial, self.ventas_mp_frame, self.conexionDBASERVER)
        else:
            self.label_aviso_no_servidor = ttk.Label(self.ventas_mp_frame, text="Este es un PDV, no puedes ver las Ventas desde aquí. Velo desde el Servidor.", wraplength=500,)       
            self.label_aviso_no_servidor.place(relx=0.5, rely=0.5, anchor=ttk.CENTER)

        
        
        
    
    def logoMPyInfor(self):
        path_img_inforhard = RutaImagenes.LOGO_INFORHARD()
        
        self.frameLOGOSCompany = ttk.Frame(self.inner_frame,)
        
        # Keep references to the images in the class instance
        self.logo_inforhard_horizontal_img = Image.open(RutaImagenes.LOGO_INFORHARD_horizontal())
        self.logo_inforhard_img_horizontal = ImageTk.PhotoImage(self.logo_inforhard_horizontal_img.resize((200, 50), Image.LANCZOS))
        self.logo_inforhard_img_horizontal_label = ttk.Label(self.frameLOGOSCompany, image=self.logo_inforhard_img_horizontal,)
        
        self.logo_mp_img = Image.open(RutaImagenes.LOGO_MP())
        self.logo_mp_img = ImageTk.PhotoImage(self.logo_mp_img.resize((200, 170), Image.LANCZOS))
        self.logo_mp_img_label = ttk.Label(self.frameLOGOSCompany, image=self.logo_mp_img,)
        
        self.labelSignoMas = ttk.Label(self.frameLOGOSCompany, text="+", foreground="#8E8484", font=('Arial', 100),)
        
        self.logo_inforhard_img = Image.open(path_img_inforhard)
        self.logo_inforhard_img = ImageTk.PhotoImage(self.logo_inforhard_img.resize((200, 150), Image.LANCZOS))
        self.logo_inforhard_img_label = ttk.Label(self.frameLOGOSCompany, image=self.logo_inforhard_img,)

        # Packing the labels
        self.logo_inforhard_img_horizontal_label.pack(side="left")
        self.logo_mp_img_label.pack(side="left")
        self.labelSignoMas.pack(side="left")
        self.logo_inforhard_img_label.pack(side="left")

        self.frameLOGOSCompany.pack()  # Pack the frame to make it visible