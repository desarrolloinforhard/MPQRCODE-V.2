import tkinter as tk

def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def on_resize(event):
    center_window(event.widget)

# Crear la ventana
root = tk.Tk()
root.title("Ventana Centrada")
root.geometry("400x300")

# Centrar la ventana inicialmente
center_window(root)

# Asociar evento de cambio de tamaño
root.bind("<Configure>", on_resize)

# Ejecutar el bucle principal de la aplicación
root.mainloop()




"""import os
import threading
import time
import customtkinter as CTk
path_directorio = os.path.dirname(os.path.abspath(__file__))
path_assets = os.path.join(path_directorio, "..", "assets")
import sys
sys.path.append(path_assets)
import image_path as RutaDeImagenes
from PIL import ImageTk, Image
from tkinter import messagebox

class VentanaCargaMKOD():
    def __init__(self, conexionAPI, conexionDBA, conexionDBASERVER):
        self.conexionAPI = conexionAPI
        self.conexionDBA = conexionDBA
        self.conexionDBASERVER = conexionDBASERVER
        self.aviso = False
        self.aviso_actual = 0
        self.avisos = ['Conectando']
        self.numero_deseado = 1
        self.aviso_creado = threading.Event()  # Evento de sincronización
        self.hilo_activo = True  # Bandera para controlar la ejecución del hilo
        path_img_mp = RutaDeImagenes.LOGO_MP()
        self.ventana = CTk.CTk(fg_color="white") 
        self.logo_mp_img_CTK = CTk.CTkImage(Image.open(path_img_mp), size=(100, 70))
        # Crear un widget CTkLabel para mostrar la imagen
        self.logo_mp_img_label = CTk.CTkLabel(self.ventana, image=self.logo_mp_img_CTK, text="")
        # Empaquetar el widget en el frame
        self.logo_mp_img_label.pack()
        self.ventana.title('Ventana Principal')
        self.frame_ventana_toplevel = CTk.CTkFrame(self.ventana, fg_color="transparent")
        self.progress_bar()
        threading.Thread(target=self.iniciar_interfaz).start()  # Ejecutar en un hilo secundario
        self.centrar_ventana()
        self.ventana.mainloop()
        
    def iniciar_interfaz(self):
        self.frame_ventana_toplevel.pack()
        self.crear_label_aviso()
        self.label_aviso()
    
    def cerrar_ventana(self):
        self.ventana.destroy()

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
        # Esta función actualiza el texto del widget CTkLabel para mostrar el aviso actual
        # Se programa para ejecutarse en el hilo principal usando self.ventana.after
        self.ventana.after(0, self.actualizar_aviso)  # Luego actualizar_aviso

    def crear_label_aviso(self):
        # Esta función crea el widget CTkLabel
        self.label_aviso_carga_menu = CTk.CTkLabel(self.frame_ventana_toplevel, text='', text_color='#000000')
        self.label_aviso_carga_menu.pack(pady=15, side='bottom')
        self.aviso_creado.set()  # Indica que el aviso ha sido creado y está listo

    def cambio_de_aviso(self):
        if 1 <= self.numero_deseado <= len(self.avisos):
            numero_actual = self.numero_deseado
            aviso_actual = self.avisos[self.numero_deseado - 1]
            self.actualizar_aviso(aviso_actual)
            self.mostrar_puntos()  # Llamar a mostrar_puntos después de mostrar el aviso
            self.ventana.after(10000, self.cambio_de_aviso)  # Programar el próximo cambio de aviso
        else:
            print("El número deseado está fuera de rango")

    def mostrar_puntos(self, contador_puntos=0):
        if contador_puntos < 3:
            aviso_actual = self.avisos[self.numero_deseado - 1]
            self.actualizar_aviso(f'{aviso_actual}{"." * (contador_puntos + 1)}')
            self.ventana.after(1000, self.mostrar_puntos, contador_puntos + 1)
        else:
            self.actualizar_aviso(self.avisos[self.numero_deseado - 1])  # Restaurar el aviso completo después de los puntos

    def actualizar_aviso(self, aviso=''):
        # Esta función actualiza el texto del widget CTkLabel con el aviso actual
        self.label_aviso_carga_menu.configure(text=aviso)
        
    def confirmacion(self):
        # Método para mostrar un mensaje de confirmación
        messagebox.showinfo('¡Exitoso!', '🥳🥳🥳La sucursal se ha creado satisfactoriamente en MercadoPago👍😀👍')
        self.cerrar_ventana()
        self.master.destroy()
            
    def centrar_ventana(self):
        self.ventana.update_idletasks()
        ancho = self.ventana.winfo_width()
        alto = self.ventana.winfo_height()
        x = (self.ventana.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.ventana.winfo_screenheight() // 2) - (alto // 2)
        self.ventana.geometry('+{}+{}'.format(x, y)) 

#VentanaPrincipal(None,None,None)
"""