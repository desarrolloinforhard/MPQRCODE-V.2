import customtkinter
import os
path_directorio = os.path.dirname(os.path.abspath(__file__))
path_assets = os.path.join(path_directorio, "..", "assets")
import sys
import time
sys.path.append(path_directorio)
sys.path.append(path_assets)
import image_path as RutaDeImagenes
from PIL import Image
from tkinter import messagebox
from GUITopLevelCarga import TopLevelCargaMenu
from CTkScrollableDropdown import *
from geoact import obtener_ubicacion_actual


class CrearSucursalApp:
    def __init__(self, master, conexionAPI):
        self.conexionAPI = conexionAPI
        self.colorwindows()
        self.rootCrearSucursal =  customtkinter.CTkToplevel(master)
        # Establecer el icono del CTkToplevel
        self.icon()
        # Establecer otros atributos
        self.rootCrearSucursal.focus()
        self.rootCrearSucursal.grab_set()
        self.rootCrearSucursal.resizable(False, False)
        self.rootCrearSucursal.title("Crear Sucursal")
        #self.rootCrearSucursal.overrideredirect(True)
        self.toplevel_window = None
        self.listDireccion = None
        self.listDiasSemana = []
        self.listHsAperturaCierre = ['00:00', '00:00']
        self.Volver = False
        self.Siguiente = True
        self.Buscar = False
        self.Cerrar = False
        self.page_1_INIT()       
        self.page_2_INIT()
        self.page_3_INIT() 
        self.page_4_INIT()
        self.page_5_INIT()
        self.page_1()
        
    def icon(self):
        rutaicono = RutaDeImagenes.Icono_MercadoPago_Blue()
        self.rootCrearSucursal.iconbitmap(rutaicono)
        
    def encabezado_ventana(self):
        self.frameEncabezaVentana = customtkinter.CTkFrame(self.rootCrearSucursal, fg_color="gray")
        self.frameEncabezaVentana.pack(side='top', fill="x")
        
        self.frame_titulo = customtkinter.CTkFrame(self.frameEncabezaVentana, fg_color="gray")
        self.frame_titulo.pack(side="left")
        
        self.label_titulo = customtkinter.CTkLabel(self.frame_titulo, text="Crear Sucursal", fg_color="gray")
        self.label_titulo.pack(side="left", padx=10)

        self.frame_botones = customtkinter.CTkFrame(self.frameEncabezaVentana, fg_color="gray")
        self.frame_botones.pack(side="right", fill='y')
        
        self.boton_minimizar = customtkinter.CTkButton(self.frame_botones, text="_", command=self.minimizar_ventana, width=40, corner_radius=0)
        self.boton_minimizar.pack(side="left", padx=1)
        
        self.boton_cerrar = customtkinter.CTkButton(self.frame_botones, text="X", command=self.cerrar_ventana, width=40, corner_radius=0)
        self.boton_cerrar.pack(side="right", padx=1)



    def minimizar_ventana(self):
        self.rootCrearSucursal.overrideredirect(False)
        self.rootCrearSucursal.iconify()

    def cerrar_ventana(self):
        respuesta = messagebox.askyesno("¿Deseas cerrar?", 'Vas a salir del menu de Creación de Sucursal, si lo haces se eliminaran todos los datos.')
        print(respuesta)
        if respuesta:
            self.rootCrearSucursal.destroy()
        
    def center_window(self):
        self.rootCrearSucursal.update_idletasks()
        width = self.rootCrearSucursal.winfo_width()
        height = self.rootCrearSucursal.winfo_height()
        screen_width = self.rootCrearSucursal.winfo_screenwidth()
        screen_height = self.rootCrearSucursal.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.rootCrearSucursal.geometry(f"{width}x{height}+{x}+{y}")
        
    def on_map(self, event):
        # Centrar la ventana cuando se mapea por completo
        self.center_window()

        
    def colorwindows(self):
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")
        
#////////////////////////////////////////////////   PAGINA 1 ////////////////////////////////////////////////
    def page_1_INIT(self):
        self.logoMPyInfor()
        # Elementos de la página 1
        self.framaPresentacionWord = customtkinter.CTkFrame(self.rootCrearSucursal, fg_color='transparent')
        self.framaPresentacionWord.pack()
        self.labelInfo = customtkinter.CTkLabel(self.framaPresentacionWord, text="Bienvenido al menú de configuración de Sucursal de MercadoPago\n a travez del Sistema de:", font=("Arial", 16), text_color="#8E8484")
        self.labelInfo.pack()
        self.labelWord_inforhard = customtkinter.CTkLabel(self.framaPresentacionWord, text='Inforhard Servicos SRL', font=("Arial", 16), text_color='#008a46')
        self.labelWord_inforhard.pack()
        self.frameButtom = customtkinter.CTkFrame(self.rootCrearSucursal, fg_color="transparent")
        self.frameButtom.pack(side='bottom', pady=10)
        self.butonNEXT =  customtkinter.CTkButton(self.frameButtom, text="Siguiente", command=self.page_2)
        self.butonNEXT.pack()
        
    def page_1_FORGET(self):
        self.logo_mp_img_label.grid_forget()
        self.labelSignoMas.grid_forget()
        self.logo_inforhard_img_label.grid_forget()
        self.framaPresentacionWord.pack_forget()     
    
    def page_1(self):
        self.rootCrearSucursal.geometry("700x485")
        self.rootCrearSucursal.bind("<Map>", self.on_map)
        if self.Volver == True:
            self.logo_mp_img_label.grid(row=1, column=0, padx=20, sticky="e")
            self.labelSignoMas.grid(row=1, column=1, padx=20, sticky="e")
            self.logo_inforhard_img_label.grid(row=1, column=2, padx=20, sticky="e")
        # Mostrar elementos de la página 1
        self.framaPresentacionWord.pack(padx=80, pady=40)
        self.butonNEXT.pack()       
        # Cambiar el comando del botón para ir a la página 2
        self.butonNEXT.configure(text="Siguiente", command=self.SIGUIENTE_page_1)
        self.butonPREVIOUS.pack_forget()
        self.frameLOGOSCompany.pack(pady=50)
        
    def SIGUIENTE_page_1(self):
        self.Siguiente = True
        self.Volver = False
        print(self.Siguiente, self.Volver)
        self.page_1_FORGET()
        self.page_2()
        
#////////////////////////////////////////////////   PAGINA 2 ////////////////////////////////////////////////
    def page_2_INIT(self):
        # Elementos de la página 2
        self.frame_pasos = customtkinter.CTkFrame(self.rootCrearSucursal, fg_color="transparent")
        self.label_paso1 = customtkinter.CTkLabel(self.frame_pasos, fg_color='#2FA572', text='Paso 1', corner_radius=10, width=100)
        self.label_paso2 = customtkinter.CTkLabel(self.frame_pasos, fg_color='transparent', text='Paso 2', corner_radius=10, width=100)
        self.label_paso3 = customtkinter.CTkLabel(self.frame_pasos, fg_color='transparent', text='Paso 3', corner_radius=10, width=100)
        self.label_paso4 = customtkinter.CTkLabel(self.frame_pasos, fg_color='transparent', text='Paso 4', corner_radius=10, width=100)
        
        
        self.framePage_2 = customtkinter.CTkFrame(self.rootCrearSucursal, fg_color="transparent")
        self.framePage_2_contenido = customtkinter.CTkFrame(self.framePage_2, fg_color="transparent")
        self.labelExternalID = customtkinter.CTkLabel(self.framePage_2_contenido, text="Ingrese el EXTERNAL ID de la sucursal")
        self.entryExternalID = customtkinter.CTkEntry(self.framePage_2_contenido, placeholder_text="Ej: SUC001")
        self.labelSucName = customtkinter.CTkLabel(self.framePage_2_contenido, text="Ingrese el nombre de la sucursal")
        self.entrySucName = customtkinter.CTkEntry(self.framePage_2_contenido, placeholder_text="Ej: Inforhard Servicios")
        self.butonPREVIOUS = customtkinter.CTkButton(self.frameButtom, text="Volver")
        
    def page_2_FORGET(self):
        self.framePage_2.pack_forget()
        self.butonPREVIOUS.pack_forget()
        self.butonNEXT.pack_forget()
        
        
    def VOLVER_page_2(self):
        self.Volver = True
        self.Siguiente = False
        print(self.Siguiente, self.Volver)
        self.logo_inforhard_img_horizontal_label.grid_forget()
        self.frame_pasos.pack_forget()
        self.page_2_FORGET()
        self.page_1()
    
    def SIGUIENTE_page_2(self):
        if self.entryExternalID.get() == "" or self.entrySucName.get() == "":
            messagebox.showerror('Casillas vacias', 'No puedes dejar ni una casilla vacia')
        else:
            self.Volver = False
            self.Siguiente = True
            self.entryExternalID.configure(state='disable')
            self.entrySucName.configure(state='disable')
            print(self.Siguiente, self.Volver)
            self.page_2_FORGET()
            self.page_3()
    
    def page_2(self):
        self.rootCrearSucursal.geometry("500x340")
        self.frameLOGOSCompany.pack_configure(pady=30)
        self.logo_inforhard_img_horizontal_label.grid(row=1, column=1, padx=10, sticky="e")
        if self.Siguiente:
            self.page_1_FORGET()
        elif self.Volver:
            self.page_3_FORGET()
        
        self.frame_pasos.pack()
        self.label_paso1.grid(row=0, column=0, pady=5, sticky="nsew")
        self.label_paso2.grid(row=0, column=1, pady=5, sticky="nsew")
        self.label_paso3.grid(row=0, column=2, pady=5, sticky="nsew")
        self.label_paso4.grid(row=0, column=3, pady=5, sticky="nsew")

        
        # Mostrar elementos de la página 2
        self.framePage_2.pack()
        self.framePage_2_contenido.pack(padx=20, pady=10)
        self.labelExternalID.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entryExternalID.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.labelSucName.grid(row=1, column=0, padx=20, pady=5, sticky="e")
        self.entrySucName.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        
        # Cambiar el comando del botón para volver a la página 1
        self.butonPREVIOUS.configure(command=self.VOLVER_page_2)
        self.butonPREVIOUS.pack(side="left", padx=20, pady=10)
        # Cambiar el comando del botón para ir a la página 2
        self.butonNEXT.configure(text="Siguiente", command=self.SIGUIENTE_page_2)
        self.butonNEXT.pack(side="right", padx=20, pady=10)
        
#////////////////////////////////////////////////   PAGINA 3 ////////////////////////////////////////////////
        
    def page_3_INIT(self):
        self.check_varLATITUD = customtkinter.StringVar(value="on")
        self.check_varLONGITUD = customtkinter.StringVar(value="on")
        self.framePage_3 = customtkinter.CTkFrame(self.rootCrearSucursal, fg_color="transparent")
        self.framePage_3_contenido = customtkinter.CTkFrame(self.framePage_3, fg_color="transparent")
        self.labelLATITUD = customtkinter.CTkLabel(self.framePage_3_contenido, text="Latitud: ")
        self.entryLATITUD = customtkinter.CTkEntry(self.framePage_3_contenido, placeholder_text="Latitud")
        self.checkboxP3_LATITUD = customtkinter.CTkCheckBox(self.framePage_3_contenido, text="", command=lambda:self.checkbox_event(self.entryLATITUD, self.check_varLATITUD),
                                    variable=self.check_varLATITUD, onvalue="on", offvalue="off")
        self.labelLONGITUD = customtkinter.CTkLabel(self.framePage_3_contenido, text="Longitud: ")
        self.entryLONGITUD = customtkinter.CTkEntry(self.framePage_3_contenido, placeholder_text="Longitud")
        self.checkboxP3_LONGITUD = customtkinter.CTkCheckBox(self.framePage_3_contenido, text="", command=lambda:self.checkbox_event(self.entryLONGITUD, self.check_varLONGITUD),
                                    variable=self.check_varLONGITUD, onvalue="on", offvalue="off")
        
    def page_3_FORGET(self):
        self.framePage_3.pack_forget()
        self.butonPREVIOUS.pack_forget()
        if self.Buscar == True:
            self.butonSEARCH.pack_forget()
            
    def VOLVER_page_3(self):
        self.Volver = True
        self.Siguiente = False
        self.Buscar = True
        print(self.Siguiente, self.Volver)
        self.label_paso1.configure(fg_color='#2FA572')
        self.label_paso2.configure(fg_color='transparent')
        self.entryExternalID.configure(state='normal')
        self.entrySucName.configure(state='normal')
        self.page_3_FORGET()
        self.page_2()
        
            
    def SIGUIENTE_page_3(self):
        self.Siguiente = True
        self.Volver = False
        self.Buscar = True
        print(self.Siguiente, self.Volver)
        self.entryLATITUD.configure(state='disable')
        self.entryLONGITUD.configure(state='disable')
        self.page_3_FORGET()
        self.page_4()
        
    def page_3(self):
        self.label_paso1.configure(fg_color='transparent')
        self.label_paso2.configure(fg_color='#2FA572')
        self.framePage_3.pack(padx=20, pady=10)
        self.framePage_3_contenido.pack()

        self.labelLATITUD.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entryLATITUD.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.labelLONGITUD.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entryLONGITUD.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        self.butonPREVIOUS.configure(text="Volver", command=self.VOLVER_page_3)
        self.butonPREVIOUS.pack(side="left", padx=20, pady=10)
        
        self.butonSEARCH = customtkinter.CTkButton(self.frameButtom, text="Buscar", command=lambda:self.obtenerdireccion((self.entryLATITUD.get()),self.entryLONGITUD.get()))
        self.butonSEARCH.pack(padx=20, pady=10)
        
#////////////////////////////////////////////////   PAGINA 4 ////////////////////////////////////////////////
    
    def page_4_INIT(self):
        self.framePage_4 = customtkinter.CTkFrame(self.rootCrearSucursal, fg_color="transparent")
        self.labelCalle = customtkinter.CTkLabel(self.framePage_4, text= "Calle: ")
        self.labelNROCalle = customtkinter.CTkLabel(self.framePage_4, text= "Altura: ")
        self.labelCiudad = customtkinter.CTkLabel(self.framePage_4, text= "Ciudad: ")
        self.labelProvincia = customtkinter.CTkLabel(self.framePage_4, text= "Provincia: ")
        self.labelLATITUD_4 = customtkinter.CTkLabel(self.framePage_4, text="Latitud: ")
        self.labelLONGITUD_4 = customtkinter.CTkLabel(self.framePage_4, text="Longitud: ")
        
    def page_4_FORGET(self):
        self.framePage_4.pack_forget()
        self.labelCalleINFO.destroy()
        self.labelNROCalleINFO.destroy()
        self.labelCiudadINFO.destroy()
        self.labelProvinciaINFO.destroy()
        self.butonNEXT.pack_forget()
        
    def VOLVER_page_4(self):
        print(self.Siguiente, self.Volver)
        eleccionvolver = messagebox.askquestion("Reiniciar Coordenas", "Si vuelves hacia atras se borrará la dirección registrada.\n¿Seguro que deseas volver?")
        if eleccionvolver == 'yes':
            self.entryLATITUD.delete(0, customtkinter.END)
            self.entryLONGITUD.delete(0, customtkinter.END)
            self.Siguiente = False
            self.Volver = True
            self.label_paso2.configure(fg_color='#2FA572')
            self.label_paso3.configure(fg_color='transparent')
            self.entryLATITUD.configure(state='normal')
            self.entryLONGITUD.configure(state='normal')
            self.page_4_FORGET()
            self.page_3()
        else:
            pass
        
    def SIGUIENTE_page_4(self):
        self.Siguiente = True
        self.Volver = False
        self.page_4_FORGET()
        self.page_5()
        
    def page_4(self):
        self.rootCrearSucursal.geometry("500x415")
        self.label_paso1.configure(fg_color='transparent')
        self.label_paso2.configure(fg_color='transparent')
        self.label_paso3.configure(fg_color='#2FA572')
        self.labelCalleINFO = customtkinter.CTkLabel(self.framePage_4, text=self.listDireccion[1])
        self.labelNROCalleINFO = customtkinter.CTkLabel(self.framePage_4, text=self.listDireccion[0])
        self.labelCiudadINFO = customtkinter.CTkLabel(self.framePage_4, text=self.listDireccion[2])
        self.labelProvinciaINFO = customtkinter.CTkLabel(self.framePage_4, text=self.listDireccion[3])
        self.labelLATITUDINFO = customtkinter.CTkLabel(self.framePage_4, text=self.entryLATITUD.get())
        self.labelLONGITUDINFO = customtkinter.CTkLabel(self.framePage_4, text=self.entryLONGITUD.get())
        self.framePage_4.pack(padx=20, pady=20)
        
        self.labelCalle.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.labelNROCalle.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.labelCiudad.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.labelProvincia.grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.labelLATITUD_4.grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.labelLONGITUD_4.grid(row=6, column=0, padx=5, pady=5, sticky="e")
        self.labelCalleINFO.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.labelNROCalleINFO.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.labelCiudadINFO.grid(row=3, column=1, padx=5, pady=5, sticky="w") 
        self.labelProvinciaINFO.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        self.labelLATITUDINFO.grid(row=5, column=1, padx=5, pady=5, sticky="e")
        self.labelLONGITUDINFO.grid(row=6, column=1, padx=5, pady=5, sticky="e")
        
        
        self.butonPREVIOUS.configure(text="Volver", command=self.VOLVER_page_4)
        self.butonPREVIOUS.pack(side="left", padx=20, pady=10)
        # Cambiar el comando del botón para ir a la página 2
        self.butonNEXT.configure(text="Siguiente", command=self.SIGUIENTE_page_4)
        self.butonNEXT.pack(side="right", padx=20, pady=10)
        
#////////////////////////////////////////////////   PAGINA 5 ////////////////////////////////////////////////  
    def page_5_INIT(self):
        list_Hs = self.generar_horas()
        self.framePage_5 = customtkinter.CTkFrame(self.rootCrearSucursal, fg_color='transparent')
        self.framePage_5_left = customtkinter.CTkFrame(self.framePage_5, fg_color='transparent')
        self.framePage_5_right = customtkinter.CTkFrame(self.framePage_5, fg_color='transparent')
        
        #----------------Lado IZQUIERDO-------------
        self.check_var_monday = customtkinter.StringVar(value="off")
        self.checkboxP6_monday = customtkinter.CTkCheckBox(self.framePage_5_left, text="Lunes", command=lambda:self.evento_check_agregardias(self.check_var_monday, 'monday'),
                                            variable=self.check_var_monday, onvalue="on", offvalue="off")
        self.check_var_tuesday = customtkinter.StringVar(value="off")
        self.checkboxP6_tuesday = customtkinter.CTkCheckBox(self.framePage_5_left, text="Martes", command=lambda:self.evento_check_agregardias(self.check_var_tuesday, 'tuesday'),
                                            variable=self.check_var_tuesday, onvalue="on", offvalue="off")
        self.check_var_wednesday = customtkinter.StringVar(value="off")
        self.checkboxP6_wednesday = customtkinter.CTkCheckBox(self.framePage_5_left, text="Miercoles", command=lambda:self.evento_check_agregardias(self.check_var_wednesday, 'wednesday'),
                                            variable=self.check_var_wednesday, onvalue="on", offvalue="off")
        self.check_var_thursday = customtkinter.StringVar(value="off")
        self.checkboxP6_thursday = customtkinter.CTkCheckBox(self.framePage_5_left, text="Jueves", command=lambda:self.evento_check_agregardias(self.check_var_thursday, 'thursday'),
                                            variable=self.check_var_thursday, onvalue="on", offvalue="off")
        self.check_var_friday = customtkinter.StringVar(value="off")
        self.checkboxP6_friday = customtkinter.CTkCheckBox(self.framePage_5_left, text="Viernes", command=lambda:self.evento_check_agregardias(self.check_var_friday, 'friday'),
                                            variable=self.check_var_friday, onvalue="on", offvalue="off")
        self.check_var_saturday = customtkinter.StringVar(value="off")
        self.checkboxP6_saturday = customtkinter.CTkCheckBox(self.framePage_5_left, text="Sábado", command=lambda:self.evento_check_agregardias(self.check_var_saturday, 'saturday'),
                                            variable=self.check_var_saturday, onvalue="on", offvalue="off")
        self.check_var_sunday = customtkinter.StringVar(value="off")
        self.checkboxP6_sunday = customtkinter.CTkCheckBox(self.framePage_5_left, text="Domingo", command=lambda:self.evento_check_agregardias(self.check_var_sunday, 'sunday'),
                                            variable=self.check_var_sunday, onvalue="on", offvalue="off")
        
        #----------------Lado DERECHO-------------
        self.label_apertura = customtkinter.CTkLabel(self.framePage_5_right, text='Horario de apertura')
        
        self.combobox_var_apertura = customtkinter.StringVar(value=list_Hs[0])
        self.comboboxapertura = customtkinter.CTkComboBox(self.framePage_5_right, variable=self.combobox_var_apertura, state="readonly")
        
        self.hsapertura = CTkScrollableDropdown(self.comboboxapertura, values=list_Hs, command=self.combobox_callback_hsapertura)
                
        self.label_cierre = customtkinter.CTkLabel(self.framePage_5_right, text='Horario de cierre')
        self.combobox_var_cierre = customtkinter.StringVar(value=list_Hs[0])
        self.comboboxcierre = customtkinter.CTkComboBox(self.framePage_5_right, variable=self.combobox_var_cierre, state="readonly")
        
        self.hscierre = CTkScrollableDropdown(self.comboboxcierre, values=list_Hs, command=self.combobox_callback_hscierre)
        
        self.label_referencia_suc = customtkinter.CTkLabel(self.framePage_5_right, text='Referencia')
        self.entry_referencia_suc = customtkinter.CTkEntry(self.framePage_5_right, placeholder_text="Ej: Esquina")
        self.check_var_referencia_suc = customtkinter.StringVar(value="on")        
        self.checkbox_referencia_suc = customtkinter.CTkCheckBox(self.framePage_5_right, text="", command=lambda:self.checkbox_event(self.entry_referencia_suc, self.check_var_referencia_suc),
                                    variable=self.check_var_referencia_suc, onvalue="on", offvalue="off")
        
    def page_5_FORGET(self):
        self.framePage_5.pack_forget()
        self.framePage_5_left.pack_forget()
        self.framePage_5_right.pack_forget()
        
    def VOLVER_page_5(self):
        self.Volver = True
        self.Siguiente = False
        self.rootCrearSucursal.grab_set()
        self.label_paso3.configure(fg_color='#2FA572')
        self.label_paso4.configure(fg_color='transparent')
        self.page_5_FORGET()
        self.page_4()
        
    def SIGUIENTE_page_5(self):
        print(self.listDiasSemana)
        print(self.listHsAperturaCierre)
        self.rootCrearSucursal.grab_set()
        if self.entry_referencia_suc.get() == "":
            messagebox.showerror('Casillas vacias', 'No puedes dejar ni una casilla vacia')
        else:
            self.Volver = False
            self.Siguiente = True
            self.entry_referencia_suc.configure(state='disable')
            self.page_5_FORGET()
            self.rootCrearSucursal.after(0, self.evento_carga_P6)
        
    def page_5(self):
        self.rootCrearSucursal.geometry('730x525')
        self.rootCrearSucursal.grab_release()
        self.label_paso1.configure(fg_color='transparent')
        self.label_paso2.configure(fg_color='transparent')
        self.label_paso3.configure(fg_color='transparent')
        self.label_paso4.configure(fg_color='#2FA572')
        self.framePage_5.pack()
        
        self.framePage_5_left.pack(side='left')        
        self.checkboxP6_monday.pack(pady=5)
        self.checkboxP6_tuesday.pack(pady=5)
        self.checkboxP6_wednesday.pack(pady=5)
        self.checkboxP6_thursday.pack(pady=5)
        self.checkboxP6_friday.pack(pady=5)
        self.checkboxP6_saturday.pack(pady=5)
        self.checkboxP6_sunday.pack(pady=5)
                
        self.framePage_5_right.pack(side='right')
        self.label_apertura.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.comboboxapertura.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.label_cierre.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.comboboxcierre.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.label_referencia_suc.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.entry_referencia_suc.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        
        self.butonPREVIOUS.configure(text="Volver", command=self.VOLVER_page_5)
        self.butonPREVIOUS.pack(side="left", padx=20, pady=10)
        # Cambiar el comando del botón para ir a la página 2
        self.butonNEXT.configure(text="Siguiente", command=self.SIGUIENTE_page_5)
        self.butonNEXT.pack(side="right", padx=20, pady=10)       
        
        
#////////////////////////////////////////////////   PAGINA 6 ////////////////////////////////////////////////        
    def page_6_INIT(self):
        self.framePage_6 = customtkinter.CTkFrame(self.rootCrearSucursal, fg_color='transparent')
        self.labelAvisoP6 = customtkinter.CTkLabel(self.rootCrearSucursal, text='Precarga', font=('Times New Roman', 15))
        
        self.frame_left = customtkinter.CTkFrame(self.framePage_6, fg_color='transparent')
        self.frame_right = customtkinter.CTkFrame(self.framePage_6, fg_color='transparent')
        #----------------Lado IZQUIERDO-------------
        self.frame_exIDP6 = customtkinter.CTkFrame(self.frame_left, fg_color='transparent')
        self.entry_exIDP6 = customtkinter.CTkEntry(self.frame_exIDP6, placeholder_text="External ID", )
        self.entry_exIDP6.insert(0, self.entryExternalID.get())
        self.entry_exIDP6.configure(state='disable')
        self.check_var_EXTID = customtkinter.StringVar(value="on")
        self.checkboxP6_EXTID = customtkinter.CTkCheckBox(self.frame_exIDP6, text="External ID", command=lambda:self.checkbox_event(self.entry_exIDP6, self.check_var_EXTID),
                                            variable=self.check_var_EXTID, onvalue="on", offvalue="off")
        
        self.frame_sucP6 = customtkinter.CTkFrame(self.frame_left, fg_color='transparent')
        self.entry_sucP6 = customtkinter.CTkEntry(self.frame_sucP6, placeholder_text="Nombre", )
        self.entry_sucP6.insert(0, self.entrySucName.get())
        self.entry_sucP6.configure(state='disable')
        self.check_var_SUC = customtkinter.StringVar(value="on")
        self.checkboxP6_SUC = customtkinter.CTkCheckBox(self.frame_sucP6, text="Nombre de la sucursal", command=lambda:self.checkbox_event(self.entry_sucP6, self.check_var_SUC),
                                                    variable=self.check_var_SUC, onvalue="on", offvalue="off")
        
        self.frame_streetnameP6 = customtkinter.CTkFrame(self.frame_left, fg_color='transparent')
        self.entry_streetnameP6 = customtkinter.CTkEntry(self.frame_streetnameP6, placeholder_text="Nombre de la calle", )
        self.entry_streetnameP6.insert(0, self.listDireccion[1])
        self.entry_streetnameP6.configure(state='disable')
        self.check_var_streetname = customtkinter.StringVar(value="on")
        self.checkboxP6_streetname = customtkinter.CTkCheckBox(self.frame_streetnameP6, text="Calle", command=lambda:self.checkbox_event(self.entry_streetnameP6, self.check_var_streetname),
                                                    variable=self.check_var_streetname, onvalue="on", offvalue="off")
        
        self.frame_citynameP6 = customtkinter.CTkFrame(self.frame_left, fg_color='transparent')
        self.entry_citynameP6 = customtkinter.CTkEntry(self.frame_citynameP6, placeholder_text="Nombre de la Ciudad", )
        self.entry_citynameP6.insert(0, self.listDireccion[2])
        self.entry_citynameP6.configure(state='disable')
        self.check_var_citynameP6 = customtkinter.StringVar(value="on")
        self.checkboxP6_citynameP6 = customtkinter.CTkCheckBox(self.frame_citynameP6, text="Ciudad", command=lambda:self.checkbox_event(self.entry_citynameP6, self.check_var_citynameP6),
                                                    variable=self.check_var_citynameP6, onvalue="on", offvalue="off")
        
        #----------------Lado DERECHO-------------
        self.frame_LatitudP6 = customtkinter.CTkFrame(self.frame_right, fg_color='transparent')
        self.entry_LatitudP6 = customtkinter.CTkEntry(self.frame_LatitudP6, placeholder_text="Latitud", )
        self.entry_LatitudP6.insert(0, self.entryLATITUD.get())
        self.entry_LatitudP6.configure(state='disable')
        self.check_var_LatitudP6 = customtkinter.StringVar(value="on")
        self.checkbox_LatitudP6 = customtkinter.CTkCheckBox(self.frame_LatitudP6, text="Latitud", command=lambda:self.checkbox_event(self.entry_LatitudP6, self.check_var_LatitudP6),
                                            variable=self.check_var_LatitudP6, onvalue="on", offvalue="off")
        
        self.frame_LongitudP6 = customtkinter.CTkFrame(self.frame_right, fg_color='transparent')
        self.entry_LongitudP6 = customtkinter.CTkEntry(self.frame_LongitudP6, placeholder_text="Nombre", )
        self.entry_LongitudP6.insert(0, self.entryLONGITUD.get())
        self.entry_LongitudP6.configure(state='disable')
        self.check_var_LongitudP6 = customtkinter.StringVar(value="on")
        self.checkbox_LongitudP6 = customtkinter.CTkCheckBox(self.frame_LongitudP6, text="Longitud", command=lambda:self.checkbox_event(self.entry_LongitudP6, self.check_var_LongitudP6),
                                                    variable=self.check_var_LongitudP6, onvalue="on", offvalue="off")
        
        self.frame_streetnumberP6 = customtkinter.CTkFrame(self.frame_right, fg_color='transparent')
        self.entry_streetnumberP6 = customtkinter.CTkEntry(self.frame_streetnumberP6, placeholder_text="Nombre de la calle", )
        self.entry_streetnumberP6.insert(0, self.listDireccion[0])
        self.entry_streetnumberP6.configure(state='disable')
        self.check_var_streetnumberP6 = customtkinter.StringVar(value="on")
        self.checkbox_streetnumberP6 = customtkinter.CTkCheckBox(self.frame_streetnumberP6, text="Altura", command=lambda:self.checkbox_event(self.entry_streetnumberP6, self.check_var_streetnumberP6),
                                                    variable=self.check_var_streetnumberP6, onvalue="on", offvalue="off")
        
        self.frame_provincenameP6 = customtkinter.CTkFrame(self.frame_right, fg_color='transparent')
        self.entry_provincenameP6 = customtkinter.CTkEntry(self.frame_provincenameP6, placeholder_text="Nombre de la Ciudad", )
        self.entry_provincenameP6.insert(0, self.listDireccion[3])
        self.entry_provincenameP6.configure(state='disable')
        self.check_var_provincenameP6 = customtkinter.StringVar(value="on")
        self.checkbox_provincenameP6 = customtkinter.CTkCheckBox(self.frame_provincenameP6, text="Provincia", command=lambda:self.checkbox_event(self.entry_provincenameP6, self.check_var_provincenameP6),
                                                    variable=self.check_var_provincenameP6, onvalue="on", offvalue="off")
        
        
        
        
    def page_6_FORGET(self):
        self.framePage_6.pack_forget()
        self.frame_left.pack_forget()
        self.frame_right.pack_forget()
        self.butonNEXT.pack_forget()
        
    def VOLVER_page_6(self):
        eleccionvolver = messagebox.askquestion("¿Seguro?", "Si vuelves hacia atras se borrará la dirección registrada.\n¿Seguro que deseas volver?")
        print(eleccionvolver)
        if eleccionvolver == 'yes':
            self.entryLATITUD.delete(0, customtkinter.END)
            self.entryLONGITUD.delete(0, customtkinter.END)
            self.Volver = True
            self.page_5_FORGET()
            self.page_6_FORGET()
            self.page_2()
            
    def SIGUIENTE_page_6(self):
        fecha_completas = self.generar_dict_con_fecha_hs()
        #Juntar datos y enviar
        self.sucursal_info = {
                    'business_hours': fecha_completas,
                    'external_id': f'{self.entry_exIDP6.get()}',
                    'location': {
                        'street_number': self.entry_streetnumberP6.get(),
                        'street_name': self.entry_streetnameP6.get(),
                        'city_name': self.entry_citynameP6.get(),
                        'state_name': self.entry_provincenameP6.get(),
                        'latitude': float(self.entry_LatitudP6.get()),
                        'longitude': float(self.entry_LongitudP6.get()),
                        'reference': self.entry_referencia_suc.get()
                    },
                    'name': self.entry_sucP6.get(),
                }
        self.rootCrearSucursal.after(1000, self.llamada_class_toplevel)
        
    def page_6(self):
        #self.rootCrearSucursal.attributes('-fullscreen', True)
        self.rootCrearSucursal.geometry('1200x515')
        self.framePage_6.pack(side='left', padx=10)
        
        self.frame_left.pack(side='left', padx=10)
        self.frame_right.pack(side='right', padx=10)
        
        self.frame_exIDP6.pack()
        self.entry_exIDP6.pack(side='right',padx=5, pady=20)
        self.checkboxP6_EXTID.pack(side='left',padx=20, pady=20)
        
        self.frame_sucP6.pack()
        self.entry_sucP6.pack(side='right',padx=5, pady=20)        
        self.checkboxP6_SUC.pack(side='left',padx=20, pady=20)
        
        self.frame_streetnameP6.pack()
        self.entry_streetnameP6.pack(side='right',padx=5, pady=20)
        self.checkboxP6_streetname.pack(side='left',padx=20, pady=20)
        
        self.frame_citynameP6.pack()
        self.entry_citynameP6.pack(side='right',padx=5, pady=20)
        self.checkboxP6_citynameP6.pack(side='left',padx=20, pady=20)
        
        self.frame_LatitudP6.pack()
        self.entry_LatitudP6.pack(side='right',padx=5, pady=20)
        self.checkbox_LatitudP6.pack(side='left',padx=20, pady=20)
        
        self.frame_LongitudP6.pack()
        self.entry_LongitudP6.pack(side='right',padx=5, pady=20)
        self.checkbox_LongitudP6.pack(side='left',padx=20, pady=20)
        
        self.frame_streetnumberP6.pack()
        self.entry_streetnumberP6.pack(side='right',padx=5, pady=20)
        self.checkbox_streetnumberP6.pack(side='left',padx=20, pady=20)
        
        self.frame_provincenameP6.pack()
        self.entry_provincenameP6.pack(side='right',padx=5, pady=20)
        self.checkbox_provincenameP6.pack(side='left',padx=20, pady=20)
        
        
        self.framePage_5.pack(side='right', padx=10)
        self.framePage_5_left.pack(side='left', padx=5)
        self.framePage_5_right.pack(side='right', padx=5)
        
        self.checkbox_referencia_suc.grid(row=2, column=2, padx=10, pady=10, sticky="nsew")
        
        self.butonPREVIOUS.configure(text="Volver", command=self.boton_VOLVER_page_6)
        self.butonPREVIOUS.pack(side="left", padx=20, pady=10)
        # Cambiar el comando del botón para ir a la página 2
        self.butonNEXT.configure(text="Enviar", command=self.boton_SIGUIENTE_page_6)
        self.butonNEXT.pack(side="right", padx=20, pady=10)
        
        
        
        """
        #FRAME PASO 2
        self.framePage_2.pack(side='left')
        self.framePage_3.pack(side='right')
        
        
        self.checkboxP2_EXTID.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.checkboxP2_SUC.grid(row=1, column=2, padx=5, pady=5, sticky="w")        
        self.checkboxP3_LATITUD.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.checkboxP3_LONGITUD.grid(row=1, column=2, padx=5, pady=5, sticky="w")
                
        self.butonPREVIOUS.configure(text="Volver", command=self.VOLVER_page_6)
        self.butonPREVIOUS.pack(side="left", padx=20, pady=10)
        # Cambiar el comando del botón para ir a la página 2
        self.butonNEXT.configure(text="Enviar", command=self.SIGUIENTE_page_6)
        self.butonNEXT.pack(side="right", padx=20, pady=10)
        """
        
    def boton_VOLVER_page_6(self):
        self.rootCrearSucursal.after(0, self.VOLVER_page_6)
        
    def boton_SIGUIENTE_page_6(self):
        self.rootCrearSucursal.after(0, self.SIGUIENTE_page_6)
        
        
    def logoMPyInfor(self):
        path_img_inforhard = RutaDeImagenes.LOGO_INFORHARD()
        
        self.frameLOGOSCompany = customtkinter.CTkFrame(self.rootCrearSucursal, fg_color='transparent')
        self.frameLOGOSCompany.pack(pady=20)
        
        self.logo_inforhard_img_horizontal = customtkinter.CTkImage(Image.open(RutaDeImagenes.LOGO_INFORHARD_horizontal()),
                                            size=(200, 50))
        self.logo_inforhard_img_horizontal_label = customtkinter.CTkLabel(self.frameLOGOSCompany, image=self.logo_inforhard_img_horizontal, text="")      
        self.logo_mp_img = customtkinter.CTkImage(Image.open(RutaDeImagenes.LOGO_MP()),
                                            size=(200, 170))
        self.logo_mp_img_label = customtkinter.CTkLabel(self.frameLOGOSCompany, image=self.logo_mp_img, text="")        
        self.labelSignoMas = customtkinter.CTkLabel(self.frameLOGOSCompany, text="+", text_color="#8E8484", font=('Arial', 100))        
        self.logo_inforhard_img = customtkinter.CTkImage(Image.open(path_img_inforhard),
                                            size=(200, 150))
        self.logo_inforhard_img_label = customtkinter.CTkLabel(self.frameLOGOSCompany, image=self.logo_inforhard_img, text="")
        self.logo_mp_img_label.grid(row=1, column=0, padx=20, sticky="e")
        self.labelSignoMas.grid(row=1, column=1, padx=20, sticky="e")
        self.logo_inforhard_img_label.grid(row=1, column=2, padx=20, sticky="e")
        
    def obtenerdireccion(self, Latitud, Longitud):
        if type(Latitud) == str and type(Latitud) == str:
            try:
                if Latitud == "" or Longitud == "":
                    messagebox.showerror("Vacio", "No puedeas dejar campos vacios.")
                else:
                    Latitud = float(Latitud)
                    Longitud = float(Longitud)
                    self.listDireccion = obtener_ubicacion_actual(Latitud, Longitud)
                    print(self.listDireccion)
                    self.SIGUIENTE_page_3()
                    #messagebox.showinfo('Coordenadas', f'Latitud: {Latitud}\nLongitud: {Longitud}')
            except Exception as e:
                if type(e) == KeyError:
                    messagebox.showerror("Error", "Coordenadas invalidas. Intentelo nuevamente")
                    self.entryLATITUD.delete(0, customtkinter.END)
                    self.entryLONGITUD.delete(0, customtkinter.END)
                elif type(e) == ValueError:
                    messagebox.showerror("Error", "Entrada de coordenadas invalidas. Intentelo nuevamente")
                    self.entryLATITUD.delete(0, customtkinter.END)
                    self.entryLONGITUD.delete(0, customtkinter.END)
                else:
                    messagebox.showerror("Error", e)
                    
    def checkbox_event(self, entry, check):
        if check.get() == 'on':
            entry.configure(state='disable')
        else:
            entry.configure(state='normal')
        self.rootCrearSucursal.update_idletasks()
        
    def evento_check_agregardias(self, check_var, dia):
        if check_var.get() == 'on':
            self.listDiasSemana.append(dia)
        else:
            self.listDiasSemana.remove(dia)
        
    def evento_carga_P6(self):
        self.page_6_INIT()
        self.page_6_FORGET()
        self.page_6()
        
    def combobox_callback_hsapertura(self,otro):
        self.listHsAperturaCierre[0] = self.hsapertura.get()
        self.combobox_var_apertura.set(self.hsapertura.get())
    def combobox_callback_hscierre(self, otro):
        self.listHsAperturaCierre[1] = self.hscierre.get()
        self.combobox_var_cierre.set(self.hscierre.get())
    def generar_horas(self):
        horas = []
        for hora in range(24):
            for minuto in range(0, 60, 15):
                horas.append(f"{hora:02d}:{minuto:02d}")
        return horas
    def generar_dict_con_fecha_hs(self):
        dict_fechas = {}
        for day in self.listDiasSemana:
            dict_fechas[day] = [{'open': self.listHsAperturaCierre[0], 'close': self.listHsAperturaCierre[1]}]
        return dict_fechas
    
    def deshabilitar_ventana_principal(self):
        # Deshabilitar la ventana principal
        self.rootCrearSucursal.grab_set()

    def habilitar_ventana_principal(self):
        # Habilitar la ventana principal
        self.rootCrearSucursal.grab_release()

    def llamada_class_toplevel(self):
        if self.toplevel_window is None:
            print(self.sucursal_info)
            self.deshabilitar_ventana_principal()
            self.toplevel_window = TopLevelCargaMenu(self.rootCrearSucursal, self.conexionAPI, **self.sucursal_info)
            self.toplevel_window.iniciar_interfaz()
            self.toplevel_window.top_level.transient(self.rootCrearSucursal)  # Establecer como transient
            self.toplevel_window.top_level.grab_set()  # Bloquear interacción con otras ventanas
        elif not self.toplevel_window.top_level.winfo_exists():
            print(self.sucursal_info)
            self.deshabilitar_ventana_principal()
            self.toplevel_window = TopLevelCargaMenu(self.rootCrearSucursal, self.conexionAPI, **self.sucursal_info)
            self.toplevel_window.iniciar_interfaz()
            self.toplevel_window.top_level.transient(self.rootCrearSucursal)  # Establecer como transient
            self.toplevel_window.top_level.grab_set()  # Bloquear interacción con otras ventanas
        else:
            self.toplevel_window.focus_set()  # Enfocar la ventana existente



-27.448178941448834, -58.986467016224985
-27.63962303974816, -62.413976112669346