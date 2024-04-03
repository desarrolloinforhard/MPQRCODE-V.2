import threading
import customtkinter as CTk
import os
import time
import json
from PIL import Image
from tkinter import messagebox
path_directorio = os.path.dirname(os.path.abspath(__file__))
path_assets = os.path.join(path_directorio, "..", "assets")
path_Py = os.path.join(path_directorio, "..")
import sys
sys.path.append(path_assets)
import image_path as RutaDeImagenes

class TopLevelCargaMenu():
    def __init__(self, master, conexionAPI, **kwargs):
        self.datos_suc = kwargs
        self.conexionAPI = conexionAPI
        print(f"TopLevel  > {self.conexionAPI.prueba()}")
        self.master = master
        self.aviso = False
        self.aviso_actual = 0
        self.avisos = ["Enviando datos", "Creando Sucursal", "Registrando en el DBA", "Esperando Respuesta"]
        self.numero_deseado = 1
        self.top_level = CTk.CTkToplevel(master, fg_color="white")
        self.frame_ventana_toplevel = CTk.CTkFrame(self.top_level, fg_color="transparent")
        self.centrar_ventana()
        self.cargar_imagen()
        self.progress_bar()

    def iniciar_interfaz(self):
        self.top_level.grid_rowconfigure(0, weight=1)
        self.top_level.grid_columnconfigure(0, weight=1)
        self.top_level.geometry("150x120")
        self.top_level.overrideredirect(True)
        self.frame_ventana_toplevel.grid(row=0, column=0, sticky="nsew")
        threading.Thread(target=self.envio_a_MercadoPago, args=(self.datos_suc,)).start()  # Ejecutar en un hilo secundario

    def centrar_ventana(self):
        self.top_level.update_idletasks()
        ancho = self.top_level.winfo_width()
        alto = self.top_level.winfo_height()
        x = (self.top_level.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.top_level.winfo_screenheight() // 2) - (alto // 2)
        self.top_level.geometry('+{}+{}'.format(x, y)) 

    def cerrar_ventana(self):
        self.top_level.destroy()

    def progress_bar(self):
        self.frame_progress_bar_MP = CTk.CTkFrame(self.frame_ventana_toplevel, fg_color="transparent", width=150, height=100)
        self.progress_bar_envio_MP = CTk.CTkProgressBar(self.frame_progress_bar_MP, orientation='horizontal', mode='indeterminate', progress_color='#00b1ea')
        self.frame_progress_bar_MP.pack()
        self.progress_bar_envio_MP.pack()
        self.progress_bar_envio_MP.start()

    def actualizar_numero_deseado(self, nuevo_numero):
        if 1 <= nuevo_numero <= len(self.avisos):
            self.numero_deseado = nuevo_numero
            self.cambio_de_aviso()

    def label_aviso(self):
        self.label_aviso_carga_menu = CTk.CTkLabel(self.frame_ventana_toplevel, text='', text_color='#000000')
        self.label_aviso_carga_menu.pack(pady=15)
        self.cambio_de_aviso()

    def cambio_de_aviso(self):
        if 1 <= self.numero_deseado <= len(self.avisos):
            numero_actual = self.numero_deseado
            aviso_actual = self.avisos[self.numero_deseado - 1]
            self.actualizar_aviso(aviso_actual)
            self.mostrar_puntos()
            self.top_level.after(10000, self.cambio_de_aviso)
        else:
            print("El número deseado está fuera de rango")

    def mostrar_puntos(self, contador_puntos=0):
        if contador_puntos < 3:
            aviso_actual = self.avisos[self.numero_deseado - 1]
            self.actualizar_aviso(f'{aviso_actual}{"." * (contador_puntos + 1)}')
            self.top_level.after(1000, self.mostrar_puntos, contador_puntos + 1)
        else:
            self.top_level.after(1000, self.cambio_de_aviso)

    def actualizar_aviso(self, aviso):
        self.label_aviso_carga_menu.configure(text=aviso)

    def cargar_imagen(self):
        # Método para cargar la imagen de la ventana
        path_img_mp = RutaDeImagenes.LOGO_MP()
        self.logo_mp_img = CTk.CTkImage(Image.open(path_img_mp), size=(100, 70))
        self.logo_mp_img_label = CTk.CTkLabel(self.frame_ventana_toplevel, image=self.logo_mp_img, text="") 
        self.logo_mp_img_label.pack()    

    def confirmacion(self):
        # Método para mostrar un mensaje de confirmación
        messagebox.showinfo('¡Exitoso!', '🥳🥳🥳La sucursal se ha creado satisfactoriamente en MercadoPago👍😀👍')
        self.cerrar_ventana()
        self.master.destroy()
            
    def envio_a_MercadoPago(self, datos_sucursal):
        self.label_aviso()
        resultado_envio = True
        while resultado_envio:
            if self.numero_deseado == 1:
                print(datos_sucursal)
                self.actualizar_numero_deseado(2)
            elif self.numero_deseado == 2:
                self.actualizar_numero_deseado(3)
            elif self.numero_deseado == 3:
                self.respuesta_mp = self.conexionAPI.creacionSUC(datos_sucursal)
                print(self.respuesta_mp)
                if self.respuesta_mp.status_code < 300:
                    self.actualizar_numero_deseado(4)
                else:
                    messagebox.showerror('Error al Crear Sucursal', self.respuesta_mp.json()['message'])
                    self.top_level.destroy()
                    break
            elif self.numero_deseado == 4:
                self.confirmacion()
                resultado_envio = False
                self.top_level.destroy()
            time.sleep(3)