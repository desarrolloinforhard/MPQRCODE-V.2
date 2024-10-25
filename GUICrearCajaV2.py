import customtkinter as CTk
import os
from win32com.client import Dispatch
import winshell
from image_path import *
from GUICrearCaja import CrearCajaApp
from CTkListbox import *
from PIL import Image
from tkinter import messagebox
from CTkMessagebox import CTkMessagebox

class GUIEliminarSucursal():
    def __init__(self, master, conexionDBA, conexion_DBAServer, conexion_api, conexion_DBACentral=False):
        self.conexion_api = conexion_api
        self.conexionDBA = conexionDBA
        self.conexion_DBAServer = conexion_DBAServer
        self.conexion_DBACentral = conexion_DBACentral
        self.datosObtenidosCajasDICT = None
        self.tacho_basura_png = CTk.CTkImage(Image.open(TACHO_BASURA()), size=(25, 25))
        self.reemplazar_png = CTk.CTkImage(Image.open(REEMPLAZAR()), size=(25, 25))
        self.agregar_png = CTk.CTkImage(Image.open(AGREGAR()), size=(25, 25))
        self.check_png = CTk.CTkImage(Image.open(CHECK()), size=(25, 25))
        self.logo_inforhard_horizontal = CTk.CTkImage(Image.open(LOGO_INFORHARD_horizontal()), size=(300, 80))
        self.home_frame_large_image_label = CTk.CTkLabel(master, text="", image=self.logo_inforhard_horizontal)
        self.home_frame_large_image_label.pack(pady=40)
        self.root_ventena_eliminar_sucursal = CTk.CTkFrame(master)
        self.root_ventena_eliminar_sucursal.pack()
        self.root_ventena_eliminar_sucursal.place(relx=0.5, rely=0.5, anchor=CTk.CENTER)
        self.posicion_activo = None
        self.dict_datos_suc_cajas = {}
        self.traer_sucursales()
        
        
    def traer_sucursales(self):
        if not self.conexion_DBACentral:
            lista_sucursales = self.conexion_DBAServer.specify_search_columna('MPQRCODE_SUCURSAL', 'external_id')
        else:
            lista_sucursales = self.conexion_DBACentral.specify_search_columna('MPQRCODE_SUCURSAL', 'external_id')
        if lista_sucursales:
            print(lista_sucursales)
            self.traer_cajas(lista_sucursales)
            self.frame_1_page_1()
        else:
            texto1 = 'No se ha encontrado ninguna sucursal en la Base de Datos'
            texto2 = 'Vuelve a la pestaña SUCURSAL para cargar una Sucursal y vuelva a intentarlo.'
            self.root_ventena_eliminar_sucursal.configure(fg_color='transparent')
            self.label_sucursal_vacia1 = CTk.CTkLabel(self.root_ventena_eliminar_sucursal, text=texto1)
            self.label_sucursal_vacia2 = CTk.CTkLabel(self.root_ventena_eliminar_sucursal, text=texto2)
            self.label_sucursal_vacia1.pack()
            self.label_sucursal_vacia2.pack()
        
    def traer_cajas(self, lista_sucursales):
        for cajas in lista_sucursales:
            if not self.conexion_DBACentral:
                id_sucursal = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_SUCURSAL', 'id', 'external_id', cajas, False)
                suc_name = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_SUCURSAL', 'name', 'external_id', cajas, False)
            else:
                id_sucursal = self.conexion_DBACentral.specify_search_condicion('MPQRCODE_SUCURSAL', 'id', 'external_id', cajas, False)
                suc_name = self.conexion_DBACentral.specify_search_condicion('MPQRCODE_SUCURSAL', 'name', 'external_id', cajas, False)
            self.dict_datos_suc_cajas[suc_name] = {
                    'external_store_id': cajas,
                    'external_id': id_sucursal,
                    'PDV': []  # Inicializar como una lista vacía en lugar de un diccionario vacío
                }
            if not self.conexion_DBACentral:
                cajas_obtenidas = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_CAJAS', 'name', 'store_id', id_sucursal, True)
                for caja in cajas_obtenidas:
                    external_id = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_CAJAS', 'id', 'name', caja[0], False)
                    self.dict_datos_suc_cajas[suc_name]['PDV'].append({caja[0]: external_id})
            else:
                cajas_obtenidas = self.conexion_DBACentral.specify_search_condicion('MPQRCODE_CAJAS', 'name', 'store_id', id_sucursal, True)
                for caja in cajas_obtenidas:
                    external_id = self.conexion_DBACentral.specify_search_condicion('MPQRCODE_CAJAS', 'id', 'name', caja[0], False)
                    self.dict_datos_suc_cajas[suc_name]['PDV'].append({caja[0]: external_id})
        print(self.dict_datos_suc_cajas)

            
    def frame_1_page_1(self):
        if not self.conexion_DBACentral:
            if not self.conexion_DBAServer.tabla_vacia('MPQRCODE_SUCURSAL'):
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
        else:
            if not self.conexion_DBACentral.tabla_vacia('MPQRCODE_SUCURSAL'):
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
        self.button_cambiar_caja = CTk.CTkButton(self.frame_buttons_frame_3, command=lambda:self.cambiar_caja('cambiar'), image=self.reemplazar_png, text='', width=20, fg_color='#666A6C')#image=CTk.CTkImage(Image.open(RutaDeImagenes.TACHO_BASURA()), size=(20, 20))
        self.button_cambiar_caja.grid(row=1, column=0, pady=10, padx=5)
        self.button_eliminar = CTk.CTkButton(self.frame_buttons_frame_3, command=self.eliminar_caja, image=self.tacho_basura_png, text='', width=20, fg_color='#666A6C')
        self.button_eliminar.grid(row=0, column=1, pady=10, padx=5)
        self.button_agregar_caja = CTk.CTkButton(self.frame_buttons_frame_3, command=self.agregar_caja, image=self.agregar_png, text='', width=20, fg_color='#666A6C')
        self.button_agregar_caja.grid(row=0, column=0, pady=10, padx=5)
        self.activar_caja = CTk.CTkButton(self.frame_buttons_frame_3, command=self.crear_acceso_directo, image=self.check_png, text='', width=20, fg_color='#666A6C')
        self.activar_caja.grid(row=1, column=1, pady=10, padx=5)
        self.toggle_disable(self.button_cambiar_caja, self.cambiar_caja)
        self.toggle_disable(self.button_eliminar, self.eliminar_caja)
        self.toggle_disable(self.button_agregar_caja, self.agregar_caja)
        self.toggle_disable(self.activar_caja, self.crear_acceso_directo)
        # Suponiendo que 'datos' es una lista de los datos que traes del DBA
        self.datos_listbox = []  # Reemplaza esto con los datos reales

        for dato in self.datos_listbox:
            self.listbox_datos.insert("end", dato)
        
    def show_value(self, selected_option):
        print(selected_option)
        self.button_agregar_caja.configure(state='normal', fg_color='#02B960', hover_color='#008A47')
        if self.label_pdv_active_variable.cget('text') == "":
            self.activar_caja.configure(state='normal',  fg_color='#009ee3', hover_color='#137AA9')
        else:
            if not self.label_pdv_active_variable.cget('text') == selected_option:
                print("entro")
                self.button_eliminar.configure(state='normal', fg_color='#02B960', hover_color='#008A47')
                self.button_cambiar_caja.configure(state='normal', fg_color='#02B960', hover_color='#008A47')
            else:
                self.button_eliminar.configure(fg_color='#666A6C')
                self.toggle_disable(self.button_eliminar, self.eliminar_caja)
                self.button_cambiar_caja.configure(fg_color='#666A6C')
                self.toggle_disable(self.button_cambiar_caja, self.cambiar_caja)
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
        if not self.conexion_DBACentral:
            external_id = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_CAJAS', 'id', 'name', self.valor_seleccionado, False)
        else:
            external_id = self.conexion_DBACentral.specify_search_condicion('MPQRCODE_CAJAS', 'id', 'name', self.valor_seleccionado, False)
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
        try:
            # Limpiar el contenido actual del Listbox
            self.listbox_datos.delete(0, 'end')
            # Insertar los nuevos datos en el Listbox
            for dato in self.datos_listbox:
                self.listbox_datos.insert('end', dato)
            external_id_pos_05 = self.conexion_DBAServer.specify_search_condicion('MPQRCODE_CAJA', 'external_id_pos', 'idINCREMENT', 1, False)
            if not external_id_pos_05 == None:
                external_id_pos_05 = external_id_pos_05[0:6]
            else:
                self.button_agregar_caja.configure(state='normal', fg_color='#02B960', hover_color='#008A47')
            print(f'EXTRENN: {external_id_pos_05}')
            print(f"LABEL:  {self.label_store_id_variable.cget('text')}")
            if not self.posicion_activo == None and external_id_pos_05 == self.label_store_id_variable.cget('text'):
                self.listbox_datos.activate(self.posicion_activo)
            else:
                try:
                    if self.posicion_activo == None:
                        pass
                    else:
                        self.listbox_datos.deactivate(self.posicion_activo)
                except IndexError:
                    print('No se encontraron PDV')
        except Exception as e:
            CTkMessagebox(title="Error", message=f"{e}", icon="cancel")
            

                
    def combobox_llamada_eliminar_sucursal(self, choice):
        print("combobox dropdown clicked:", choice)
        self.label_external_id_variable.configure(text=self.dict_datos_suc_cajas[choice]['external_id'])
        self.label_store_id_variable.configure(text=self.dict_datos_suc_cajas[choice]['external_store_id'])
        
        # Reiniciar self.datos_listbox a una lista vacía antes de agregar nuevos datos
        self.datos_listbox = []
        self.button_agregar_caja.configure(state='normal', fg_color='#02B960', hover_color='#008A47')
        
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
            self.valor_seleccionado = caja_activa
            self.posicion_activo = self.datos_listbox.index(caja_activa)
            
        
        # Después de actualizar self.datos_listbox, llama a la función actualizar_listbox para reflejar los cambios en la interfaz
        self.actualizar_listbox()

    def cambiar_caja(self, elecc):
        try:
            if elecc == 'cambiar':
                msg = CTkMessagebox(title='Cambiar caja', message=f'¿Deseas cambiar el PDV al {self.listbox_datos.get()}?',
                    icon="warning", option_1="Si", option_2="No")
            elif elecc == 'activar':
                msg = CTkMessagebox(title='Activar caja', message=f'¿Deseas activar el PDV al {self.listbox_datos.get()}?',
                    icon="info", option_1="Si", option_2="No")
            print(msg.get())
            if msg.get() == 'Si':
                datosObtnerCajas = ['external_store_id', "external_id", "IPN_url"]
                datosObtenidosCajas = []
                print(self.listbox_datos.get())
                for columna in datosObtnerCajas:
                    datosObtenidosCajas.append(self.conexion_DBAServer.specify_search_condicion("MPQRCODE_CAJAS", columna, "name", self.listbox_datos.get(), False))
                print(datosObtenidosCajas)
                if not self.conexion_DBACentral:
                    sucName = self.conexion_DBAServer.specify_search_condicion("MPQRCODE_SUCURSAL", 'name', 'external_id', datosObtenidosCajas[0], False)
                else:
                    sucName = self.conexion_DBACentral.specify_search_condicion("MPQRCODE_SUCURSAL", 'name', 'external_id', datosObtenidosCajas[0], False),
                self.datosObtenidosCajasDICT = {
                    "sucNAME": sucName,
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
                if elecc == 'cambiar':
                    CTkMessagebox(title='Exito', message=f"PDV actualizado al {self.listbox_datos.get()}.",
                icon="check", option_1="Aceptar")
                elif elecc == 'activar':
                    CTkMessagebox(title='Exito', message=f"PDV {self.listbox_datos.get()} activado.",
                icon="check", option_1="Aceptar")
                    self.activar_caja.configure(fg_color='#666A6C')
                self.toggle_disable(self.activar_caja, self.crear_acceso_directo)
            else:
                pass
        except Exception as e:
            print(e)
            messagebox.showerror("Error", f"Error al configurar la Caja: {e}")
            
    def agregar_caja(self):
        CrearCajaApp(self.conexion_api, self.conexion_DBAServer)
        
        

    def crear_acceso_directo(self):
        self.cambiar_caja('activar')
        path_archivos = os.path.dirname(os.path.abspath(__file__))
        ruta_directorio_trabajo = os.path.join(path_archivos, "MPQRCODE")  # Sin comillas dobles aquí
        ruta_archivo_exe = os.path.join(ruta_directorio_trabajo, "MPQRCODE.exe")
        self.conexionDBA.modificar_columna_y_dato_variable(ruta_archivo_exe, len(ruta_archivo_exe))

        # Obtener la ruta al directorio de destino
        ruta_destino = os.path.join(path_archivos, "..")

        # Crear la ruta completa del acceso directo
        ruta_completa_acceso_directo = os.path.join(ruta_destino, "MPQRCODE.lnk")

        # Crear el acceso directo
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortcut(ruta_completa_acceso_directo)
        shortcut.TargetPath = ruta_archivo_exe
        shortcut.WorkingDirectory = ruta_directorio_trabajo  # Establecer el directorio de trabajo
        shortcut.Save()
        print(ruta_archivo_exe)
        
            
    def toggle_disable(self, boton, evento):
        if boton.cget('state') == "disabled":
            if not self.valor_seleccionado == self.label_pdv_active_variable.cget('text'):
                boton.configure(state= "normal")
                boton.bind("<Button-1>", evento)
        else:
            boton.configure(state= "disabled")
            boton.unbind("<Button-1>")
