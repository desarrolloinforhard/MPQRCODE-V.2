import customtkinter as CTk
import image_path as RutaDeImagenes
from GUICrearCaja import CrearCajaApp
from CTkListbox import *
from PIL import Image
from tkinter import messagebox
from CTkMessagebox import CTkMessagebox

class GUIEliminarSucursal():
    def __init__(self, master, conexionDBA, conexion_DBAServer, conexion_api):
        self.conexion_api = conexion_api
        self.conexionDBA = conexionDBA
        self.conexion_DBAServer = conexion_DBAServer
        self.datosObtenidosCajasDICT = None
        self.tacho_basura_png = CTk.CTkImage(Image.open(RutaDeImagenes.TACHO_BASURA()), size=(25, 25))
        self.reemplazar_png = CTk.CTkImage(Image.open(RutaDeImagenes.REEMPLAZAR()), size=(25, 25))
        self.agregar_png = CTk.CTkImage(Image.open(RutaDeImagenes.AGREGAR()), size=(25, 25))
        self.colorwindows()
        self.root_ventena_eliminar_sucursal = CTk.CTkToplevel(master)
        self.root_ventena_eliminar_sucursal.focus
        self.root_ventena_eliminar_sucursal.grab_set()
        self.root_ventena_eliminar_sucursal.iconbitmap(RutaDeImagenes.Icono_MercadoPago_Blue())
        self.root_ventena_eliminar_sucursal.title("Configurar Sucursal")
        self.posicion_activo = None
        self.dict_datos_suc_cajas = {}
        self.traer_sucursales()
        
        self.root_ventena_eliminar_sucursal.mainloop()
        
        
        
        
    def colorwindows(self):
        CTk.set_appearance_mode("dark")
        CTk.set_default_color_theme("green")
        
    def traer_sucursales(self):
        lista_sucursales = self.conexion_DBAServer.specify_search_columna('MPQRCODE_SUCURSAL', 'external_id')
        if lista_sucursales:
            self.traer_cajas(lista_sucursales)
            self.frame_1_page_1()
            self.centrar_ventana()
        else:
            CTkMessagebox(title="Error", message="No se encontra ni una SUCURSAL activa.\n Cree una nueva y reeintente de nuevo.", icon="cancel")
            self.root_ventena_eliminar_sucursal.destroy()
        
    def traer_cajas(self, lista_sucursales):
        for cajas in lista_sucursales:
            id_sucursal = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_SUCURSAL', 'id', 'external_id', cajas[0], False)
            suc_name = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_SUCURSAL', 'name', 'external_id', cajas[0], False)
            self.dict_datos_suc_cajas[suc_name] = {
                    'external_store_id': cajas[0],
                    'external_id': id_sucursal,
                    'PDV': []  # Inicializar como una lista vacía en lugar de un diccionario vacío
                }
            cajas_obtenidas = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_CAJAS', 'name', 'store_id', id_sucursal, True)
            for caja in cajas_obtenidas:
                external_id = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_CAJAS', 'id', 'name', caja[0], False)
                self.dict_datos_suc_cajas[suc_name]['PDV'].append({caja[0]: external_id})
        print(self.dict_datos_suc_cajas)

            
    def frame_1_page_1(self):
        lista_sucursales = []
        for clave, valor in self.dict_datos_suc_cajas.items():
            lista_sucursales.append(clave) 
        self.frame_combobox_page1 = CTk.CTkFrame(self.root_ventena_eliminar_sucursal, fg_color='transparent')
        self.frame_combobox_page1.pack(pady=20)
        
        self.combobox_var_eliminar_sucursal = CTk.StringVar(value=None)
        self.combobox_eliminar_sucursal = CTk.CTkComboBox(self.frame_combobox_page1, values=lista_sucursales,
                                            command=self.combobox_llamada_eliminar_sucursal, variable=self.combobox_var_eliminar_sucursal, width=210,  state="readonly")
        self.combobox_var_eliminar_sucursal.set(value="")
        self.label_seleccionar_sucursal = CTk.CTkLabel(self.frame_combobox_page1, text="Seleccionar sucursal:")
        self.label_seleccionar_sucursal.pack(side='left', padx=15)
        self.combobox_eliminar_sucursal.pack(side='right', padx=15)
        
        self.frame_2_page_1()
        
    def frame_2_page_1(self):
        self.frame_datos_page1 = CTk.CTkFrame(self.root_ventena_eliminar_sucursal)
        self.frame_datos_page1.pack(padx=10, pady=10)
        
        self.frame_contenido_datos_frame2 = CTk.CTkFrame(self.frame_datos_page1, fg_color='transparent')
        self.frame_contenido_datos_frame2.pack()
        
        self.frame_datos_page1_columna1 = CTk.CTkFrame(self.frame_contenido_datos_frame2, fg_color='transparent')
        self.frame_datos_page1_columna2 = CTk.CTkFrame(self.frame_contenido_datos_frame2, fg_color='transparent')
        self.frame_datos_page1_columna3 = CTk.CTkFrame(self.frame_contenido_datos_frame2, fg_color='transparent')
        
        self.frame_datos_page1_columna1.grid(row=0, column=0, padx=10)
        self.label_external_id = CTk.CTkLabel(self.frame_datos_page1_columna1, text='External ID:')
        self.label_external_id_variable = CTk.CTkLabel(self.frame_datos_page1_columna1, text='', text_color='green')
        self.label_external_id.pack(side='left', padx=5)
        self.label_external_id_variable.pack(side='right', padx=5)
        
        
        self.frame_datos_page1_columna2.grid(row=0, column=1, padx=10)
        self.label_store_id = CTk.CTkLabel(self.frame_datos_page1_columna2, text='Store ID:')
        self.label_store_id_variable = CTk.CTkLabel(self.frame_datos_page1_columna2, text='', text_color='green')
        self.label_store_id.pack(side='left', padx=5)
        self.label_store_id_variable.pack(side='right', padx=5)
        
        self.frame_datos_page1_columna3.grid(row=0, column=2, padx=10)
        self.label_pdv_active = CTk.CTkLabel(self.frame_datos_page1_columna3, text='Caja activa:')
        self.label_pdv_active_variable = CTk.CTkLabel(self.frame_datos_page1_columna3, text='', text_color='red')
        self.label_pdv_active.pack(side='left', padx=5)
        self.label_pdv_active_variable.pack(side='right', padx=5)
        
        self.frame_3_page_1()
        
        
        
    def frame_3_page_1(self):
        self.frame_3_page1 = CTk.CTkFrame(self.root_ventena_eliminar_sucursal)
        self.frame_3_page1.pack(padx=10, pady=20)

        self.frame_listbox_datos = CTk.CTkFrame(self.frame_3_page1, fg_color='transparent')
        self.frame_listbox_datos.pack(side='left', padx=20, pady=10)
        self.listbox_datos = CTkListbox(self.frame_listbox_datos, command=self.show_value)
        self.valor_seleccionado = None
        self.listbox_datos.pack()
        
        self.frame_buttons_frame_3 = CTk.CTkFrame(self.frame_3_page1, fg_color='transparent')
        self.frame_buttons_frame_3.pack(side='right', padx=20, pady=10)
        self.button_cambiar_caja = CTk.CTkButton(self.frame_buttons_frame_3, command=self.cambiar_caja, image=self.reemplazar_png, text='', state='disable', width=20)#image=CTk.CTkImage(Image.open(RutaDeImagenes.TACHO_BASURA()), size=(20, 20))
        self.button_cambiar_caja.grid(row=0, column=0, pady=10, padx=5)
        self.button_eliminar = CTk.CTkButton(self.frame_buttons_frame_3, command=self.eliminar_caja, image=self.tacho_basura_png, text='', state='disable', width=20)
        self.button_eliminar.grid(row=1, column=0, pady=10, padx=5)
        self.button_agregar_caja = CTk.CTkButton(self.frame_buttons_frame_3, command=self.agregar_caja, image=self.agregar_png, text='', state='disable', width=20)
        self.button_agregar_caja.grid(row=0, column=1, pady=10, padx=5)
        # Suponiendo que 'datos' es una lista de los datos que traes del DBA
        self.datos_listbox = []  # Reemplaza esto con los datos reales

        for dato in self.datos_listbox:
            self.listbox_datos.insert("end", dato)
        
    def show_value(self, selected_option):
        self.button_cambiar_caja.configure(state='normal')
        self.button_eliminar.configure(state='normal')
        self.button_agregar_caja.configure(state='normal')
        self.valor_seleccionado = selected_option
                    
    def eliminar_caja(self):
        if not self.label_pdv_active_variable.cget('text') == self.listbox_datos.get():
            msg = CTkMessagebox(title='Eliminar caja', message=f'¿Desea eliminar la el PDV {self.valor_seleccionado}?',
                    icon="warning", option_1="Si", option_2="No")
            print(msg)
            if msg.get() ==  "Si":
                self.eliminar_caja_proceso()
            else:
                pass
        else:
            CTkMessagebox(title="Error", message="No puedes eliminar una caja activa.", icon="cancel")
        
    def eliminar_caja_proceso(self):
        external_id = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_CAJAS', 'id', 'name', self.valor_seleccionado, False)
        respuesta = self.conexion_api.eliminarCaja(external_id)
        if respuesta.status_code >= 200 and respuesta.status_code < 300:
            messagebox.showinfo('Exito', 'Caja eliminado con exito')
            print(self.dict_datos_suc_cajas)
            for lista in self.dict_datos_suc_cajas[self.combobox_var_eliminar_sucursal.get()]['PDV']:
                print(lista)
                for name, external_id in lista.items():
                    print(name, self.valor_seleccionado)
                    if name == self.valor_seleccionado:
                        self.dict_datos_suc_cajas[self.combobox_var_eliminar_sucursal.get()]['PDV'].remove(lista)
                        break  # Para salir del bucle interior una vez que se elimina el elemento
            self.datos_listbox.remove(self.valor_seleccionado)
            self.actualizar_listbox()
        else:
            messagebox.showerror('Error', respuesta['message'])

    def actualizar_listbox(self):
        # Limpiar el contenido actual del Listbox
        self.listbox_datos.delete(0, 'end')
        # Insertar los nuevos datos en el Listbox
        for dato in self.datos_listbox:
            self.listbox_datos.insert('end', dato)
        external_id_pos_05 = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_CAJA', 'external_id_pos', 'idINCREMENT', 1, False)[0:6]
        print(f'EXTRENN: {external_id_pos_05}')
        print(f"LABEL:  {self.label_store_id_variable.cget('text')}")
        if not self.posicion_activo == None and external_id_pos_05 == self.label_store_id_variable.cget('text'):
            self.listbox_datos.activate(self.posicion_activo)
        else:
            if self.posicion_activo == None:
                pass
            else:
                self.listbox_datos.deactivate(self.posicion_activo)

                
    def combobox_llamada_eliminar_sucursal(self, choice):
        print("combobox dropdown clicked:", choice)
        self.label_external_id_variable.configure(text=self.dict_datos_suc_cajas[choice]['external_id'])
        self.label_store_id_variable.configure(text=self.dict_datos_suc_cajas[choice]['external_store_id'])
        
        # Reiniciar self.datos_listbox a una lista vacía antes de agregar nuevos datos
        self.datos_listbox = []
        
        for lista in self.dict_datos_suc_cajas[choice]['PDV']:
            if not lista:
                print('VACIA')
            else:
                for name, external_id in lista.items():
                    self.datos_listbox.append(name)
        caja_activa = self.conexionDBA.specify_search_condicion('MPQRCODE_CAJA', 'posNAME', 'idINCREMENT', 1, False)
        print(caja_activa)
        if caja_activa in self.datos_listbox:
            self.label_pdv_active_variable.configure(text=caja_activa)
            self.posicion_activo = self.datos_listbox.index(caja_activa)
            
        
        # Después de actualizar self.datos_listbox, llama a la función actualizar_listbox para reflejar los cambios en la interfaz
        self.actualizar_listbox()

    def cambiar_caja(self):
        try:
            msg = CTkMessagebox(title='Cambiar caja', message=f'¿Deseas cambiar el PDV al {self.listbox_datos.get()}?',
                icon="warning", option_1="Si", option_2="No")
            print(msg.get())
            if msg.get() == 'Si':
                datosObtnerCajas = ['external_store_id', "external_id", "IPN_url"]
                datosObtenidosCajas = []
                print(self.listbox_datos.get())
                for columna in datosObtnerCajas:
                    datosObtenidosCajas.append(self.conexion_DBAServer.specify_search_condicion("MPQRCODE_CAJAS", columna, "name", self.listbox_datos.get(), False))
                print(datosObtenidosCajas)
                print(self.conexion_DBAServer.specify_search_condicion("MPQRCODE_SUCURSAL", 'name', 'external_id', datosObtenidosCajas[0], False))
                self.datosObtenidosCajasDICT = {
                    "sucNAME": self.conexion_DBAServer.specify_search_condicion("MPQRCODE_SUCURSAL", 'name', 'external_id', datosObtenidosCajas[0], False),
                    "posNAME": self.listbox_datos.get(),
                    "external_id_pos": datosObtenidosCajas[1],
                    "IPN_url": datosObtenidosCajas[2]
                }
                print(self.datosObtenidosCajasDICT)
                print(self.conexionDBA.tabla_vacia('MPQRCODE_CAJA'))
                if self.conexionDBA.tabla_vacia('MPQRCODE_CAJA'):
                    self.conexionDBA.insertar_datos_sin_obtener_id("MPQRCODE_CAJA", self.datosObtenidosCajasDICT)
                else:
                    self.conexionDBA.actualizar_datos('MPQRCODE_CAJA', self.datosObtenidosCajasDICT, 1)
                    
                
                self.label_pdv_active_variable.configure(text=self.listbox_datos.get())
                CTkMessagebox(title='Exito', message=f"PDV actualizado al {self.listbox_datos.get()}.",
                icon="check", option_1="Aceptar")
            else:
                pass
        except Exception as e:
            print(e)
            messagebox.showerror("Error", f"Error al configurar la Caja: {e}")
            
    def agregar_caja(self):
        CrearCajaApp(self.conexion_api, self.conexion_DBAServer)
        
    def centrar_ventana(self):
        self.width = self.root_ventena_eliminar_sucursal.winfo_reqwidth()
        self.height = self.root_ventena_eliminar_sucursal.winfo_reqheight()

        if self.root_ventena_eliminar_sucursal is not None:
            screen_width = self.root_ventena_eliminar_sucursal.winfo_screenwidth()
            screen_height = self.root_ventena_eliminar_sucursal.winfo_screenheight()

            spawn_x = int((screen_width - self.width) / 2)
            spawn_y = int((screen_height - self.height) / 2)

            self.root_ventena_eliminar_sucursal.geometry("+{}+{}".format(spawn_x, spawn_y))
        else:
            print("La ventana es None, no se puede centrar.")

        """
        self.root_ventena_eliminar_sucursal.update_idletasks()
        ancho = self.root_ventena_eliminar_sucursal.winfo_width()
        alto = self.root_ventena_eliminar_sucursal.winfo_height()
        x = (self.root_ventena_eliminar_sucursal.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.root_ventena_eliminar_sucursal.winfo_screenheight() // 2) - (alto // 2)
        self.root_ventena_eliminar_sucursal.geometry('+{}+{}'.format(x, y)) 
        """