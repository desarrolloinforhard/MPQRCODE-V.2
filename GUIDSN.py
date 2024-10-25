
import os
import json
import customtkinter
from tkinter import ttk, messagebox
directorio_script = os.path.dirname(os.path.abspath(__file__))
from database import ConexionSybase, dsn_configurados
class InterfazGrafica:
    def __init__(self, root):
        self.root = root
        self.centrar_ventana_DSN()
        self.root.title("Configuración de DSN")
        self.dsnLISTA = None
        self.obtener_listaDSN()
        self.combobox_dsn()

        """# Etiqueta y campo de entrada para el DSN de la caja
        customtkinter.CTkLabel(root, text="DSN de la Caja:").grid(row=0, column=0, padx=10, pady=10)
        self.entry_dsn_caja = customtkinter.CTkEntry(root)
        self.entry_dsn_caja.grid(row=0, column=1, padx=10, pady=10)

        # Etiqueta y campo de entrada para el DSN del servidor
        ttk.Label(root, text="DSN del Servidor:").grid(row=1, column=0, padx=10, pady=10)
        self.entry_dsn_servidor = ttk.Entry(root)
        self.entry_dsn_servidor.grid(row=1, column=1, padx=10, pady=10)

        # Botón para realizar la prueba
        test_button = ttk.Button(root, text="Test", command=self.realizar_prueba)
        test_button.grid(row=2, column=0, padx=10, pady=10)

        # Botón para guardar los DSN
        guardar_button = ttk.Button(root, text="Guardar DSN", command=self.guardar_dsn)
        guardar_button.grid(row=2, column=1, padx=10, pady=10)"""
        
    def combobox_dsn(self):
        self.frame_contenido = customtkinter.CTkFrame(self.root, fg_color="transparent")
        self.frame_contenido.pack()
        self.frame = customtkinter.CTkFrame(self.frame_contenido, fg_color="transparent")
        self.frame.pack(padx=20, pady=15)
        self.frameSERVER = customtkinter.CTkFrame(self.frame_contenido, fg_color="transparent")
        self.frameSERVER.pack(padx=20, pady=15)    
        self.frameSERVERrespaldo = customtkinter.CTkFrame(self.frame_contenido, fg_color="transparent") 
        
        
        self.label_DSNdelPDV = customtkinter.CTkLabel(self.frame, text="DSN del PDV", fg_color="transparent")
        self.label_DSNdelPDV.pack(side="left", padx=10, pady=5)
        self.combobox_var = customtkinter.StringVar(value="option 2")
        self.combobox = customtkinter.CTkComboBox(self.frame, values=self.dsnLIST,
                                            command=self.combobox_callback, variable=self.combobox_var, state="readonly")        
        self.combobox_var.set(self.dsnLIST[0])
        self.combobox.pack(side="right", padx=10, pady=5)
        
        self.label_DSNdelSERVER = customtkinter.CTkLabel(self.frameSERVER, text="DSN del SERVER", fg_color="transparent")
        self.combobox_var_delSERVER = customtkinter.StringVar(value="option 2")
        self.comboboxdelSERVER = customtkinter.CTkComboBox(self.frameSERVER, values=self.dsnLIST,
                                            command=self.combobox_callback, variable=self.combobox_var_delSERVER, state="readonly")
        self.combobox_var_delSERVER.set(self.dsnLIST[0])
        self.label_DSNdelSERVER.pack(side="left", padx=10, pady=5)
        self.comboboxdelSERVER.pack(side="right", padx=10, pady=5)
        
        self.label_DSNdelServer = customtkinter.CTkLabel(self.frameSERVERrespaldo, text="DSN del Servidor Central", fg_color="transparent")
        self.combobox_var_delSERVERrespaldo = customtkinter.StringVar(value=None) 
        self.combobox_delSERVERrespaldo = customtkinter.CTkComboBox(self.frameSERVERrespaldo, values=self.dsnLIST,
                                                    command=self.combobox_callback, variable=self.combobox_var_delSERVERrespaldo, state="readonly") 
        self.combobox_var_delSERVERrespaldo.set(None)
        
        
        self.check_var_referencia = customtkinter.StringVar(value="off")        
        self.checkbox_referencia = customtkinter.CTkCheckBox(self.root, text="Agregar Servidor Central", command=self.servidor_de_respaldo,
                                    variable=self.check_var_referencia, onvalue="on", offvalue="off")
        self.checkbox_referencia.pack()
                
        self.frame_buttom = customtkinter.CTkFrame(self.root, fg_color='transparent')
        self.frame_buttom.pack()        
        self.button = customtkinter.CTkButton(self.frame_buttom, text="Guardar", command=self.guardar_dsn)
        self.button.pack(side="right", pady=10, padx=10)
        test_button = customtkinter.CTkButton(self.frame_buttom, text="Test", command=self.realizar_prueba)
        test_button.pack(side="left", pady=10, padx=10)
        
    def obtener_listaDSN(self):
        datos = dsn_configurados()
        self.dsnLIST = []
        for dsnNAME, dsnDRIVER in datos.items():
            cadena = dsnNAME.decode('utf-8')
            self.dsnLIST.append(cadena)
        for dsnNAME in self.dsnLIST:
            print(dsnNAME)
    
    def combobox_callback(self, choice):
        print("combobox dropdown clicked:", choice)
        
    def servidor_de_respaldo(self):        
        if self.check_var_referencia.get() == 'off':
            print("Salio")
            self.combobox_var_delSERVERrespaldo.set(None)
            self.frameSERVERrespaldo.pack_forget()
            self.label_DSNdelServer.pack_forget()
            self.combobox_delSERVERrespaldo.pack_forget()
        elif self.check_var_referencia.get() == 'on': 
            print("Entro")
            print(self.combobox_var_delSERVERrespaldo.get())
            self.frameSERVERrespaldo.pack(padx=20, pady=15)              
            self.label_DSNdelServer.pack(side="left", padx=10, pady=5)      
            self.combobox_delSERVERrespaldo.pack(side="right", padx=10, pady=5)
            self.root.update_idletasks()        
    def datosDBA(self):
        # Acción al presionar el botón de prueba
        dsn_caja = self.combobox_var.get()
        dsn_servidor = self.combobox_var_delSERVER.get()
        configuracion_sybase = {
            "dsn": dsn_caja,
            "user": "dba",
            "password": "gestion",
            # Agrega otros parámetros según sea necesario
        }
        
        configuracion_sybaseServer = {
            "user": "dba",
            "password": "gestion",
            "dsn": dsn_servidor
            # Agrega otros parámetros según sea necesario
        }
        
        conexion_sybase = ConexionSybase(**configuracion_sybase)
        conexion_sybaseSERVER = ConexionSybase(**configuracion_sybaseServer)
        
        if self.combobox_var_delSERVERrespaldo.get() == 'None':            
            return conexion_sybase, conexion_sybaseSERVER
        else:
            dsn_servidor_central = self.combobox_var_delSERVERrespaldo.get()
            configuracion_sybaseServerRespaldo = {
            "user": "dba",
            "password": "gestion",
            "dsn": dsn_servidor_central
            # Agrega otros parámetros según sea necesario
            }
            conexion_sybase_ServerRespaldo = ConexionSybase(**configuracion_sybaseServerRespaldo)
            return conexion_sybase, conexion_sybaseSERVER, conexion_sybase_ServerRespaldo
    def realizar_prueba(self):        
        DBAdatos = self.datosDBA()
        if self.combobox_var_delSERVERrespaldo.get() == 'None':         
            conexion_sybase = DBAdatos[0]        
            conexion_sybaseSERVER = DBAdatos[1]  
            messagebox.showinfo("Test", f"POS = {conexion_sybase.conectar()}\n SERVER = {conexion_sybaseSERVER.conectar()}")  
        else:
            conexion_sybase = DBAdatos[0]        
            conexion_sybaseSERVER = DBAdatos[1]   
            conexion_sybaseSERVERrespaldo = DBAdatos[2]   
            messagebox.showinfo("Test", f"POS = {conexion_sybase.conectar()}\n SERVER = {conexion_sybaseSERVER.conectar()}\n SERVER Central = {conexion_sybaseSERVERrespaldo.conectar()}")  
                


    def guardar_dsn(self):
        # Acción al presionar el botón de guardar
        dsn_caja = self.combobox_var.get()
        dsn_servidor = self.combobox_var_delSERVER.get()

        # Guardar la configuración en un archivo JSON
        rutaGUI =  os.path.join(directorio_script,"configuracion.json")
        rutaWEB_SERVER = os.path.join(directorio_script, "paquete-webserver")
        rutaIPN = os.path.join(rutaWEB_SERVER, "configuracion.json")
        if self.combobox_var_delSERVERrespaldo.get() == 'None':
            configuracion = {"dsn_caja": dsn_caja, "dsn_servidor": dsn_servidor, "dsn_servidor_central": False}
        else: 
            dsn_servidor_central = self.combobox_var_delSERVERrespaldo.get()
            configuracion = {"dsn_caja": dsn_caja, "dsn_servidor": dsn_servidor, "dsn_servidor_central": dsn_servidor_central}
        with open(rutaGUI, "w") as file:
            json.dump(configuracion, file)
        with open(rutaIPN, "w") as file:
            json.dump(configuracion, file)

        messagebox.showinfo("Exito", "DSN guardados con éxito.")
        self.root.destroy()
        
    def centrar_ventana_DSN(self):
        self.root.update_idletasks()
        ancho = self.root.winfo_width()
        alto = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.root.winfo_screenheight() // 2) - (alto // 2)
        self.root.geometry('+{}+{}'.format(x, y))
