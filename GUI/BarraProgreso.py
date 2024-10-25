import ttkbootstrap as ttk
import threading
import time
from log_errors import log_error

class BarraProgreso(ttk.Progressbar):
    def __init__(self, frame):
        try:
            # Inicializar correctamente la clase base ttk.Progressbar
            super().__init__(frame, orient="horizontal", length=350, mode='determinate', style='color.Horizontal.TProgressbar')
            
            
            # Empaquetar el Progressbar en el frame
            self.pack(pady=15)

            # Inicializar el valor de progreso
            self['value'] = 0
            
            self.runnig = True

            # Crear un hilo para actualizar el valor del progreso
            #threading.Thread(target=self.progreso, args=(kwargs, )).start()
        except Exception as e:
            log_error(e, "BarraProgreso__init__")

    def progreso(self, **kwargs):
        try:
            threading.Thread(target=self.func_progreso, args=(kwargs, )).start()
        except Exception as e:
            log_error(e, "progreso")
            
    def func_progreso(self, kwargs):
        try:
            while self.runnig and not int(self['value']) == kwargs["carga"]:
                #print(int(self['value'])) #MUESTRA PORCENTAJE DE CARGA
                self.step(1)
                self.update_idletasks()
                kwargs["widgets"]["label_estado"].config(text=f"{int(self['value'])}%")
                kwargs["widgets"]["my_label_aviso"].config(text=kwargs["text_label_aviso"])
                if not kwargs["text_label_aviso"] == "ERROR":
                    time.sleep(0.05)  # Simulación de proceso
                else:
                    time.sleep(0.005)  # Simulación de proceso
            if int(self['value']) == 99:
                kwargs["widgets"]["label_estado"].config(text="100%")
            print(kwargs["text_label_aviso"])
            if kwargs["command"] and not kwargs["text_label_aviso"] == "ERROR":
                kwargs["command"]()
            else:
                kwargs["widgets"]["root"].destroy()
        except Exception as e:
            log_error(e, "func_rogreso")
            
    def estado(self):
        return self.runnig
            
    def stop_barra(self):
        self.runnig = False