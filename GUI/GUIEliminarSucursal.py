import customtkinter as CTk
import tkinter as Tk
import os
path_directorio = os.path.dirname(os.path.abspath(__file__))
path_assets = os.path.join(path_directorio, "..", "assets")
import sys
import time
sys.path.append(path_directorio)
sys.path.append(path_assets)
import image_path as RutaDeImagenes
from CTkListbox import *
from PIL import Image
from tkinter import messagebox

class GUIEliminarSucursal():
    def __init__(self, master, conexion_DBAServer, conexion_api):
        self.conexion_api = conexion_api
        self.conexion_DBAServer = conexion_DBAServer
        self.colorwindows()
        self.root_ventena_eliminar_sucursal = CTk.CTkToplevel(master)
        self.root_ventena_eliminar_sucursal.focus
        self.root_ventena_eliminar_sucursal.grab_set()
        self.root_ventena_eliminar_sucursal.iconbitmap(RutaDeImagenes.Icono_MercadoPago_Blue())
        self.root_ventena_eliminar_sucursal.title("Eliminar Sucursal")
        self.dict_datos_suc_cajas = {}
        self.traer_sucursales()
        self.frame_1_page_1()
        self.centrar_ventana()
        self.root_ventena_eliminar_sucursal.mainloop()
        
        
        
        
    def colorwindows(self):
        CTk.set_appearance_mode("dark")
        CTk.set_default_color_theme("green")
        
    def traer_sucursales(self):
        lista_sucursales = self.conexion_DBAServer.specify_search_columna('MPQRCODE_SUCURSAL', 'external_id')
        self.traer_cajas(lista_sucursales)
        
    def traer_cajas(self, lista_sucursales):
        for cajas in lista_sucursales:
            id_sucursal = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_SUCURSAL', 'id', 'external_id', cajas[0], False)
            suc_name = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_SUCURSAL', 'name', 'external_id', cajas[0], False)
            cajas_obtenidas = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_CAJAS', 'name', 'store_id', id_sucursal, True)
            self.dict_datos_suc_cajas[suc_name] = {
                    'external_store_id': cajas[0],
                    'external_id': id_sucursal,
                    'PDV_list_names': cajas_obtenidas
                }
        print(self.dict_datos_suc_cajas)
            
    def frame_1_page_1(self):
        lista_sucursales = []
        for clave, valor in self.dict_datos_suc_cajas.items():
            lista_sucursales.append(clave) 
        self.frame_combobox_page1 = CTk.CTkFrame(self.root_ventena_eliminar_sucursal, fg_color='transparent')
        self.frame_combobox_page1.pack(pady=20)
        
        self.combobox_var_eliminar_sucursal = CTk.StringVar(value=None)
        self.combobox_eliminar_sucursal = CTk.CTkComboBox(self.frame_combobox_page1, values=lista_sucursales,
                                            command=self.combobox_llamada_eliminar_sucursal, variable=self.combobox_var_eliminar_sucursal, width=210)
        self.combobox_var_eliminar_sucursal.set(lista_sucursales[0])
        self.label_seleccionar_sucursal = CTk.CTkLabel(self.frame_combobox_page1, text="Seleccionar sucursal:")
        self.label_seleccionar_sucursal.pack(side='left', pady=5, padx=10)
        self.combobox_eliminar_sucursal.pack(side='right', pady=5, padx=10)
        
        self.frame_2_page_1()
        
    def frame_2_page_1(self):
        self.frame_datos_page1 = CTk.CTkFrame(self.root_ventena_eliminar_sucursal, fg_color='transparent')
        self.frame_datos_page1.pack()
        
        self.frame_datos_page1_left = CTk.CTkFrame(self.frame_datos_page1, fg_color='transparent')
        self.frame_datos_page1_right = CTk.CTkFrame(self.frame_datos_page1, fg_color='transparent')
        
        self.frame_datos_page1_left.pack(side='left', pady=5, padx=100)#FRAME DEL LADO IZQUIERDO
        self.label_external_id = CTk.CTkLabel(self.frame_datos_page1_left, text='External ID:')
        self.label_external_id_variable = CTk.CTkLabel(self.frame_datos_page1_left, text='', text_color='green')
        self.label_external_id.pack(side='left', padx=5)
        self.label_external_id_variable.pack(side='right')
        
        
        self.frame_datos_page1_right.pack(side='right', pady=5, padx=100)#FRAME DEL LADO DERECHO
        self.label_store_id = CTk.CTkLabel(self.frame_datos_page1_right, text='Store ID:')
        self.label_store_id_variable = CTk.CTkLabel(self.frame_datos_page1_right, text='', text_color='green')
        self.label_store_id.pack(side='left', padx=5)
        self.label_store_id_variable.pack(side='right')
        self.frame_3_page_1()
        
        
        
    def frame_3_page_1(self):
        self.frame_3_page_1 = CTk.CTkFrame(self.root_ventena_eliminar_sucursal, fg_color='transparent')
        self.frame_3_page_1.pack(pady=20)

        self.listbox_datos = CTkListbox(self.frame_3_page_1, command=self.show_value)
        self.valor_seleccionado = None
        self.listbox_datos.pack(side='left', padx=10)
        self.button_eliminar = CTk.CTkButton(self.frame_3_page_1, command=self.eliminar_caja, text='Eliminar Caja', state='disable')#image=CTk.CTkImage(Image.open(RutaDeImagenes.TACHO_BASURA()), size=(20, 20))
        self.button_eliminar.pack(side='right', padx=10)
        # Suponiendo que 'datos' es una lista de los datos que traes del DBA
        self.datos_listbox = []  # Reemplaza esto con los datos reales

        for dato in self.datos_listbox:
            self.listbox_datos.insert("end", dato)
        
    def show_value(self, selected_option):
        self.button_eliminar.configure(state='normal')
        self.valor_seleccionado = selected_option
            
    def eliminar_caja(self):
        yesorno = messagebox.askyesno('Eliminar caja', f'¿Desea eliminar la el PDV {self.valor_seleccionado[0]}?')
        print(yesorno)
        if yesorno:
            self.eliminar_caja_proceso()
        else:
            pass
        
    def eliminar_caja_proceso(self):
        external_id = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_CAJAS', 'id', 'name', self.valor_seleccionado[0], False)
        respuesta = self.conexion_api.eliminarCaja(int(external_id))
        if respuesta.status_code >= 200 and respuesta.status_code < 300:
            messagebox.showinfo('Exito', 'Caja eliminado con exito')
            self.actualizar_listbox()
        else:
            messagebox.showerror('Error', respuesta['message'])

    def actualizar_listbox(self):
        # Limpiar el contenido actual del Listbox
        self.listbox_datos.delete(0, 'end')
        # Insertar los nuevos datos en el Listbox
        for dato in self.datos_listbox:
            self.listbox_datos.insert('end', dato)

                
    def combobox_llamada_eliminar_sucursal(self, choice):
        print("combobox dropdown clicked:", choice)
        self.label_external_id_variable.configure(text=self.dict_datos_suc_cajas[choice]['external_id'])
        self.label_store_id_variable.configure(text=self.dict_datos_suc_cajas[choice]['external_store_id'])
        self.datos_listbox = self.dict_datos_suc_cajas[choice]['PDV_list_names']
        self.actualizar_listbox()  # Añadir paréntesis aquí
        self.root_ventena_eliminar_sucursal.update_idletasks()

                
        
    def centrar_ventana(self):
        self.root_ventena_eliminar_sucursal.update_idletasks()
        ancho = self.root_ventena_eliminar_sucursal.winfo_width()
        alto = self.root_ventena_eliminar_sucursal.winfo_height()
        x = (self.root_ventena_eliminar_sucursal.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.root_ventena_eliminar_sucursal.winfo_screenheight() // 2) - (alto // 2)
        self.root_ventena_eliminar_sucursal.geometry('+{}+{}'.format(x, y)) 
