import customtkinter
import json
from PIL import Image
from database import ConexionSybase
from tkinter import messagebox
from conexiones import Conexion_APP
from image_path import *

class GUIconexiones:
    def __init__(self, master=None):
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
            if self.conexionDBA.conectar() and self.conexionDBASERVER.conectar():
                messagebox.showinfo('Conectado', 'Conexion exitosa con el DBA')
                self.crear_ventana_principal(master)
            else:
                if not self.dsn_servidor_respaldo == None:
                    self.conexionDBASERVER = ConexionSybase(
                    user="dba",
                    password="gestion",
                    dsn=self.dsn_servidor_respaldo
                    )
                    if self.conexionDBA.conectar() and self.conexionDBASERVER.conectar():
                        messagebox.showinfo('¡¡IMPORTANTE!!', 'AVISO IMPORTANTE:\n Estas trabajando sobre una base de respaldo.')
                        messagebox.showinfo('Conectado', 'Conexion exitosa con el DBA')
                        self.crear_ventana_principal(master)
                    else:
                        messagebox.showerror('Error con el DBA', 'No se puede lograr conexion con ninguna base de datos')
                else:
                    messagebox.showerror('Error con el DBA', 'No se puede lograr conexion con ninguna base de datos')
        self.id_user = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'idUSER', 1)
        self.token  = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKEN', 1)
        self.tokenPOINT = self.conexionDBASERVER.specify_search("MPQRCODE_CLIENTE", 'AUTH_TOKENPOINT', 1)
        self.datos_connect = (self.id_user, self.token, self.tokenPOINT)
        self.ventana_principal = None
        self.conexionAPI = Conexion_APP(self.datos_connect, self.conexionDBA, self.conexionDBASERVER)
        self.rutadocumento = os.path.dirname(os.path.abspath(__file__))
        
        
        
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

    def crear_ventana_principal(self, master):
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")
        rutaicono = Icono_MercadoPago_Blue()
        if master == None:
            self.ventana_principal = customtkinter.CTk()            
            self.ventana_principal.iconbitmap(rutaicono)     
        else:
            self.ventana_principal = customtkinter.CTkToplevel()
            self.ventana_principal.after(250, lambda: self.ventana_principal.iconbitmap(rutaicono))
            self.ventana_principal.grab_set()
        self.ventana_principal.title("Manejo DBA")
        
        self.tacho_basura_png = customtkinter.CTkImage(Image.open(TACHO_BASURA()), size=(25, 25))
        self.agregar_png = customtkinter.CTkImage(Image.open(AGREGAR()), size=(25, 25))   
        
        self.label_name_top = customtkinter.CTkLabel(self.ventana_principal, text="Manejo del DBA", font=('Arial Black', 15))
        self.label_name_top.grid(row=0, column=0, pady=20)
        self.frame_top()
        self.label_name_bottom = customtkinter.CTkLabel(self.ventana_principal, text="Manejo de tablas Individuales", font=('Arial Black', 15))
        self.label_name_bottom.grid(row=2, column=0, pady=20)
        self.frame_botton()
        self.ventana_principal.resizable(False, False)
        self.centrar_ventana_principal()
        if master == None:
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
        
        self.button_tabla_mpqrcode_caja = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_CAJA", command=self.evento_tabla_mpqrcode_caja)
        self.button_tabla_mpqrcode_caja.grid(row=0, column=0, pady=5, sticky='nsew')
        self.button_tabla_mpqrcode_cajas = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_CAJAS", command=self.evento_tabla_mpqrcode_cajas)
        self.button_tabla_mpqrcode_cajas.grid(row=0, column=1, pady=5, sticky='nsew')
        self.button_tabla_mpqrcode_cajas_qr = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_CAJAS_qr", command=self.evento_tabla_mpqrcode_cajas_qr)
        self.button_tabla_mpqrcode_cajas_qr.grid(row=0, column=2, pady=5, sticky='nsew')

        self.button_tabla_mpqrcode_cliente = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_CLIENTE", command=self.evento_tabla_mpqrcode_cliente)
        self.button_tabla_mpqrcode_cliente.grid(row=1, column=0, pady=5, padx=5, sticky='nsew')
        self.button_tabla_mpqrcode_conexion_programas = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_CONEXIONPROGRAMAS", command=self.evento_tabla_mpqrcode_conexion_programas)
        self.button_tabla_mpqrcode_conexion_programas.grid(row=1, column=1, pady=5, padx=5, sticky='nsew')
        self.button_tabla_mpqrcode_conexion_servidor_api = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_CONEXIONSERVIRDORAPI", command=self.evento_tabla_mpqrcode_conexion_servidor_api)
        self.button_tabla_mpqrcode_conexion_servidor_api.grid(row=1, column=2, pady=5, padx=5, sticky='nsew')
        
        self.button_tabla_mpqrcode_obtener_pago = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_OBTENERPAGO", command=self.evento_tabla_mpqrcode_obtener_pago)
        self.button_tabla_mpqrcode_obtener_pago.grid(row=2, column=0, pady=5, padx=5, sticky='nsew')
        self.button_tabla_mpqrcode_obtener_pago_point = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_OBTENERPAGOPOINT", command=self.evento_tabla_mpqrcode_obtener_pago_point)
        self.button_tabla_mpqrcode_obtener_pago_point.grid(row=2, column=1, pady=5, padx=5, sticky='nsew')
        self.button_tabla_mpqrcode_obtener_pago_point_server = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_OBTENERPAGOPOINTServer", command=self.evento_tabla_mpqrcode_obtener_pago_point_server)
        self.button_tabla_mpqrcode_obtener_pago_point_server.grid(row=2, column=2, pady=5, padx=5, sticky='nsew')
        
        self.button_tabla_mpqrcode_obtener_pago_server = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_OBTENERPAGOServer", command=self.evento_tabla_mpqrcode_obtener_pago_server)
        self.button_tabla_mpqrcode_obtener_pago_server.grid(row=3, column=0, pady=5, padx=5, sticky='nsew')
        self.button_tabla_mpqrcode_respuesta_post = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_RESPUESTAPOST", command=self.evento_tabla_mpqrcode_respuesta_post)
        self.button_tabla_mpqrcode_respuesta_post.grid(row=3, column=1, pady=5, padx=5, sticky='nsew')
        self.button_tabla_mpqrcode_respuesta_post_point = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_RESPUESTAPOSTPOINT", command=self.evento_tabla_mpqrcode_respuesta_post_point)
        self.button_tabla_mpqrcode_respuesta_post_point.grid(row=3, column=2, pady=5, padx=5, sticky='nsew')
        
        self.button_tabla_mpqrcode_sucursal = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_SUCURSAL", command=self.evento_tabla_mpqrcode_sucursal)
        self.button_tabla_mpqrcode_sucursal.grid(row=4, column=0, pady=5, padx=5, sticky='nsew')
        self.button_tabla_mpqrcode_sucursal_bussines = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_SUCURSAL_bussines_hours", command=self.evento_tabla_mpqrcode_sucursal_bussines)
        self.button_tabla_mpqrcode_sucursal_bussines.grid(row=4, column=1, pady=5, padx=5, sticky='nsew')
        self.button_tabla_mpqrcode_location = customtkinter.CTkButton(self.frame_ventana_principal, text="MPQRCODE_location", command=self.evento_tabla_mpqrcode_location)
        self.button_tabla_mpqrcode_location.grid(row=4, column=2, pady=5, padx=5, sticky='nsew')
        
        self.status_botones()

        self.frame_ventana_principal.columnconfigure(0, weight=1)
        self.frame_ventana_principal.columnconfigure(1, weight=1)
        self.frame_ventana_principal.columnconfigure(2, weight=1)
        self.frame_ventana_principal.rowconfigure([0, 1, 2, 3], weight=1)
        
        
    def status_botones(self):
        self.status_tabla_mpqrcode_caja()
        self.status_tabla_mpqrcode_cajas()
        self.status_tabla_mpqrcode_cajas_qr()
        self.status_tabla_mpqrcode_cliente()
        self.status_tabla_mpqrcode_conexion_programas()
        self.status_tabla_mpqrcode_conexion_servidor_api()
        self.status_tabla_mpqrcode_obtener_pago()
        self.status_tabla_mpqrcode_obtener_pago_point()
        self.status_tabla_mpqrcode_obtener_pago_point_server()
        self.status_tabla_mpqrcode_obtener_pago_server()
        self.status_tabla_mpqrcode_respuesta_post()
        self.status_tabla_mpqrcode_respuesta_post_point()
        self.status_tabla_mpqrcode_sucursal()
        self.status_tabla_mpqrcode_sucursal_bussines()
        self.status_tabla_mpqrcode_location()
    
    def status_tabla_mpqrcode_caja(self):
        if self.conexionDBA.check_table_existence('MPQRCODE_CAJA'):
            self.button_tabla_mpqrcode_caja.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_caja.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_caja(self):
        if self.conexionDBA.check_table_existence('MPQRCODE_CAJA'):
            self.conexionDBA.eliminar_tabla("MPQRCODE_CAJA")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_CAJA ha sido eliminada')
        else:
            self.conexionDBA.crear_tabla_MPQRCODE_CAJA()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_CAJA ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_cajas(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_CAJAS'):
            self.button_tabla_mpqrcode_cajas.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_cajas.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_cajas(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_CAJAS'):
            self.conexionDBASERVER.eliminar_tabla("MPQRCODE_CAJAS")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_CAJAS ha sido eliminada')
        else:
            self.conexionDBASERVER.crear_tabla_MPQRCODE_CAJAS()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_CAJAS ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_cajas_qr(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_CAJAS_qr'):
            self.button_tabla_mpqrcode_cajas_qr.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_cajas_qr.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_cajas_qr(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_CAJAS_qr'):
            self.conexionDBASERVER.eliminar_tabla("MPQRCODE_CAJAS_qr")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_CAJAS_qr ha sido eliminada')
        else:
            self.button_tabla_mpqrcode_cajas_qr.configure(command=lambda:self.conexionDBASERVER.crear_tabla_MPQRCODE_CAJAS_qr(), fg_color='#666A6C')
            messagebox.showinfo('Status', 'La tabla MPQRCODE_CAJAS_qr ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_cliente(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_CLIENTE'):
            self.button_tabla_mpqrcode_cliente.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_cliente.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_cliente(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_CLIENTE'):
            self.conexionDBASERVER.eliminar_tabla("MPQRCODE_CLIENTE")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_CLIENTE ha sido eliminada')
        else:
            self.conexionDBASERVER.crear_tabla_MPQRCODE_CLIENTE()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_CLIENTE ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_conexion_programas(self):
        if self.conexionDBA.check_table_existence('MPQRCODE_CONEXIONPROGRAMAS'):
            self.button_tabla_mpqrcode_conexion_programas.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_conexion_programas.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_conexion_programas(self):
        if self.conexionDBA.check_table_existence('MPQRCODE_CONEXIONPROGRAMAS'):
            self.conexionDBA.eliminar_tabla("MPQRCODE_CONEXIONPROGRAMAS")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_CONEXIONPROGRAMAS ha sido eliminada')
        else:
            self.conexionDBA.crear_tabla_MPQRCODE_CONEXIONPROGRAMAS()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_CONEXIONPROGRAMAS ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_conexion_servidor_api(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_CONEXIONSERVIDORAPI'):
            self.button_tabla_mpqrcode_conexion_servidor_api.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_conexion_servidor_api.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_conexion_servidor_api(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_CONEXIONSERVIDORAPI'):
            self.conexionDBASERVER.eliminar_tabla("MPQRCODE_CONEXIONSERVIDORAPI")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_CONEXIONSERVIDORAPI ha sido eliminada')
        else:
            self.conexionDBASERVER.crear_tabla_MPQRCODE_CONEXIONSERVIDORAPI()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_CONEXIONSERVIDORAPI ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_obtener_pago(self):
        if self.conexionDBA.check_table_existence('MPQRCODE_OBTENERPAGO'):
            self.button_tabla_mpqrcode_obtener_pago.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_obtener_pago.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_obtener_pago(self):
        if self.conexionDBA.check_table_existence('MPQRCODE_OBTENERPAGO'):
            self.conexionDBA.eliminar_tabla("MPQRCODE_OBTENERPAGO")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_OBTENERPAGO ha sido eliminada')
        else:
            self.conexionDBA.crear_tabla_MPQRCODE_OBTENERPAGO()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_OBTENERPAGO ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_obtener_pago_point(self):
        if self.conexionDBA.check_table_existence('MPQRCODE_OBTENERPAGOPOINT'):
            self.button_tabla_mpqrcode_obtener_pago_point.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_obtener_pago_point.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_obtener_pago_point(self):
        if self.conexionDBA.check_table_existence('MPQRCODE_OBTENERPAGOPOINT'):
            self.conexionDBA.eliminar_tabla("MPQRCODE_OBTENERPAGOPOINT")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_OBTENERPAGOPOINT ha sido eliminada')
        else:
            self.conexionDBA.crear_tabla_MPQRCODE_OBTENERPAGOPOINT()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_OBTENERPAGOPOINT ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_obtener_pago_point_server(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_OBTENERPAGOPOINTServer'):
            self.button_tabla_mpqrcode_obtener_pago_point_server.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_obtener_pago_point_server.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_obtener_pago_point_server(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_OBTENERPAGOPOINTServer'):
            self.conexionDBASERVER.eliminar_tabla("MPQRCODE_OBTENERPAGOPOINTServer")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_OBTENERPAGOPOINTServer ha sido eliminada')
        else:
            self.conexionDBASERVER.crear_tabla_MPQRCODE_OBTENERPAGOPOINTServer()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_OBTENERPAGOPOINTServer ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_obtener_pago_server(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_OBTENERPAGOServer'):
            self.button_tabla_mpqrcode_obtener_pago_server.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_obtener_pago_server.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_obtener_pago_server(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_OBTENERPAGOServer'):
            self.conexionDBASERVER.eliminar_tabla("MPQRCODE_OBTENERPAGOServmessagebox.showinfo('Status', 'La tabla ha MPQRCODE_OBTENERPAGOServer ha sido eliminada')er")
            messagebox.showinfo('Status', 'La tabla ha MPQRCODE_OBTENERPAGOServer sido creada')
        else:
            self.conexionDBASERVER.crear_tabla_MPQRCODE_OBTENERPAGOServer()
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_respuesta_post(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_RESPUESTAPOST'):
            self.button_tabla_mpqrcode_respuesta_post.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_respuesta_post.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_respuesta_post(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_RESPUESTAPOST'):
            self.conexionDBASERVER.eliminar_tabla("MPQRCODE_RESPUESTAPOST")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_RESPUESTAPOST ha sido eliminada')
        else:
            self.conexionDBASERVER.crear_tabla_MPQRCODE_RESPUESTAPOST()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_RESPUESTAPOST ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_respuesta_post_point(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_RESPUESTAPOSTPOINT'):
            self.button_tabla_mpqrcode_respuesta_post_point.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_respuesta_post_point.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_respuesta_post_point(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_RESPUESTAPOSTPOINT'):
            self.conexionDBASERVER.eliminar_tabla("MPQRCODE_RESPUESTAPOSTPOINT")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_RESPUESTAPOSTPOINT ha sido eliminada')
        else:
            self.conexionDBASERVER.crear_tabla_MPQRCODE_RESPUESTAPOSTPOINT()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_RESPUESTAPOSTPOINT ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_sucursal(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_SUCURSAL'):
            self.button_tabla_mpqrcode_sucursal.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_sucursal.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_sucursal(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_SUCURSAL'):
            self.conexionDBASERVER.eliminar_tabla("MPQRCODE_SUCURSAL")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_SUCURSAL ha sido eliminada')
        else:
            self.conexionDBASERVER.crear_tabla_MPQRCODE_SUCURSAL()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_SUCURSAL ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_sucursal_bussines(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_SUCURSAL_business_hours'):
            self.button_tabla_mpqrcode_sucursal_bussines.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_sucursal_bussines.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_sucursal_bussines(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_SUCURSAL_business_hours'):
            self.conexionDBASERVER.eliminar_tabla("MPQRCODE_SUCURSAL_business_hours")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_SUCURSAL_business_hours ha sido eliminada')
        else:
            self.conexionDBASERVER.crear_tabla_MPQRCODE_SUCURSAL_business_hours()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_SUCURSAL_business_hours ha sido creada')
        self.status_botones()
            
            
            
    def status_tabla_mpqrcode_location(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_SUCURSAL_location'):
            self.button_tabla_mpqrcode_location.configure(fg_color='#e31b1b', hover_color='#b81414')
        else:
            self.button_tabla_mpqrcode_location.configure(fg_color='#11d945', hover_color='#17b841')
            
    def evento_tabla_mpqrcode_location(self):
        if self.conexionDBASERVER.check_table_existence('MPQRCODE_SUCURSAL_location'):
            self.conexionDBA.eliminar_tabla("MPQRCODE_SUCURSAL_location")
            messagebox.showinfo('Status', 'La tabla MPQRCODE_SUCURSAL_location ha sido eliminada')
        else:
            self.conexionDBA.crear_tabla_MPQRCODE_SUCURSAL_location()
            messagebox.showinfo('Status', 'La tabla MPQRCODE_SUCURSAL_location ha sido creada')
        self.status_botones()
    
    def crear_tabla_server(self):        
        self.conexionDBASERVER.crearTablasSERVER()
        messagebox.showinfo("Éxito", "Se han creado las tablas del Server")
        self.button_crear_tabla_SERVER.configure(state=customtkinter.DISABLED)
        self.button_eliminar_tabla_SERVER.configure(state=customtkinter.NORMAL)
        self.status_botones()
        self.ventana_principal.update()

    def crear_tabla_pos(self):
        self.conexionDBA.crearTablasPOS()
        messagebox.showinfo("Éxito", "Se han creado las tablas del POS")
        self.button_crear_tabla_POS.configure(state=customtkinter.DISABLED)
        self.button_eliminar_tabla_POS.configure(state=customtkinter.NORMAL)
        self.status_botones()

    def eliminar_tabla_server(self):
        choice_mktableserver = messagebox.askquestion(message="Vas a eliminar las tablas de MERCADOPAGO en servidor. Esto podría traer errores a la hora de las creaciones de las ordenes. \n ¿Seguro que deseas continuar?", title="¿Deseas continuar?")
        
        if choice_mktableserver == 'yes':
            self.conexionDBASERVER.eliminarTablasSERVER()
            messagebox.showinfo("Éxito", "Se han eliminado las tablas del Server")
            self.button_crear_tabla_SERVER.configure(state=customtkinter.NORMAL)
            self.button_eliminar_tabla_SERVER.configure(state=customtkinter.DISABLED)
            self.status_botones()
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
            self.status_botones()
        else:
            messagebox.showerror("Abortar", "Se ha cancelado la operación")                   
        self.ventana_principal.update()
        
    def centrar_ventana_principal(self):
        self.width = self.ventana_principal.winfo_reqwidth()
        self.height = self.ventana_principal.winfo_reqheight()

        if self.ventana_principal is not None:
            screen_width = self.ventana_principal.winfo_screenwidth()
            screen_height = self.ventana_principal.winfo_screenheight()

            spawn_x = int((screen_width - self.width) / 2)
            spawn_y = int((screen_height - self.height) / 2)

            self.ventana_principal.geometry("+{}+{}".format(spawn_x, spawn_y))
        else:
            print("La ventana es None, no se puede centrar.")