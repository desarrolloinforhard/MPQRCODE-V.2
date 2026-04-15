import threading
import time
import keyboard
# VERSION 1.1.0

"""
1.1.0 > Se agrega la declarion para el abecedario
"""
class TecladoHasar:
    instancia_unica = None  # Variable estática para almacenar la instancia única
    def __new__(cls, *args, **kwargs):
        """Patrón Singleton: Solo permite una instancia activa a la vez"""
        if cls.instancia_unica is None:
            cls.instancia_unica = super(TecladoHasar, cls).__new__(cls)
        return cls.instancia_unica

    def __init__(self):
        """Inicializa el teclado HASAR sin necesidad de Entry al inicio."""
        if hasattr(self, "inicializado"):  # Evita reinicializar múltiples veces
            return
        self.inicializado = True

        # Mapeo de teclas numéricas
        self.key_mapping = {
            "46": "0",  "47": "00", "48": ".",  
            "56": "1",  "57": "2",  "58": "3",
            "66": "4",  "67": "5",  "68": "6",
            "76": "7",  "77": "8",  "78": "9",
            # Nuevas combinaciones para letras
            "a0": "A", "a1": "B", "a2": "C", "a3": "D",
            "90": "E", "91": "F", "92": "G", "93": "H",
            "80": "I", "81": "J", "82": "K", "83": "L",
            "70": "M", "71": "N", "72": "Ñ", "73": "O",
            "60": "P", "61": "Q", "62": "R", "63": "S",
            "50": "T", "51": "U", "52": "V", "53": "W",
            "40": "X", "41": "Y", "42": "Z", "43": " "
        }
        
        self.funciones = {}  # Diccionario para funciones personalizadas
        self.current_keys = []  # Almacena las teclas presionadas
        self.entry_widget = None  # Inicialmente no hay un Entry asignado
            
        self.escuchando = True  # Controla si se debe escuchar o no
        self.modo_normal = False  # Cuando es True, no interceptamos nada
        self.hook_registrado = False
        self.escaneo_activo = False

        
        if not hasattr(self, "hook_registrado") or not self.hook_registrado:
            keyboard.hook(self.on_key_event)
            print("[TECLADO] Hook conectado: on_key_event activado")
            self.hook_registrado = True


    def set_entry(self, entry_widget):
        """Asigna el Entry donde se insertarán los números."""
        self.entry_widget = entry_widget

    def asignar_funcion(self, tecla, funcion):
        print(f"[TECLADO] Registrando función para {tecla}")
        self.funciones[tecla] = funcion

    def on_key_event(self, event):
        if self.modo_normal:
            return  # ✅ NO interceptar si está en modo normal

        if event.event_type == "down":
            # Ejemplo: detectar combinación "4a"
            if keyboard.is_pressed("4") and keyboard.is_pressed("a"):
                if "4a" in self.funciones:
                    self.funciones["4a"]()
                return

            # Probar combinaciones configuradas
            for comb in self.funciones:
                if len(comb) == 2 and all(keyboard.is_pressed(k) for k in comb):
                    self.funciones[comb]()
                    return


    def insertar_en_entry(self, caracter):
        """Agrega el caracter detectado al Entry de Tkinter sin eliminar otros valores."""
        if self.entry_widget:
            self.entry_widget.insert("end", caracter)  # Inserta al final del Entry
            
    def borrar_ultimo_caracter(self):
        """Elimina el último carácter del Entry."""
        if self.entry_widget:
            texto_actual = self.entry_widget.get()  # Obtiene el contenido actual
            if texto_actual:  # Verifica si hay algo para borrar
                self.entry_widget.delete(len(texto_actual) - 1, "end")  # Borra el último carácter

    def iniciar_escucha(self):
        while True:
            if not self.escuchando or self.escaneo_activo:
                time.sleep(0.1)
                continue

            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                tecla = event.name.lower()
                self.current_keys.append(tecla)

                if len(self.current_keys) == 2:
                    combinacion = "".join(self.current_keys)
                    if combinacion in self.key_mapping:
                        self.insertar_en_entry(self.key_mapping[combinacion])
                    elif combinacion in self.funciones:
                        self.funciones[combinacion]()
                    else:
                        print(f"Teclas desconocidas: {combinacion}")
                    self.current_keys.clear()
                elif tecla == "enter":
                    self.current_keys.clear()
    
    def activar_escaneo_continuo(self):
        print("[TECLADO] Activando escaneo completo (modo scanner)")
        self.escaneo_activo = True
        self.modo_normal = False  # Previene conflictos

        def esperar_codigo():
            keyboard.start_recording()
            while self.escaneo_activo:
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN and event.name == 'enter':
                    eventos = keyboard.stop_recording()
                    texto = ''.join(e.name for e in eventos if e.event_type == 'down' and len(e.name) == 1)
                    if self.entry_widget:
                        self.entry_widget.delete(0, 'end')
                        self.entry_widget.insert(0, texto)
                        print(f"[DEBUG] Escaneo detectado: {texto}")
                    break
                time.sleep(0.01)

        threading.Thread(target=esperar_codigo, daemon=True).start()

    def desactivar_escaneo_continuo(self):
        print("[TECLADO] Desactivando escaneo")
        self.escaneo_activo = False
        try:
            keyboard.stop_recording()
        except:
            pass  # Puede lanzar si ya se detuvo
        
    def activar_modo_normal(self):
        print("[TECLADO] Modo normal activado: sin interceptar")
        self.modo_normal = True

        # 🔓 Permitir que el usuario escriba libremente
        if self.entry_widget and hasattr(self, "_bind_id"):
            self.entry_widget.unbind("<Key>", self._bind_id)

    def desactivar_modo_normal(self):
        print("[TECLADO] Modo Hasar reactivado")
        self.modo_normal = False

        # 🔒 Bloquear escritura manual y dejar solo Hasar
        if self.entry_widget:
            self._bind_id = self.entry_widget.bind("<Key>", lambda e: "break")




    """# Ejemplo de uso
if __name__ == "__main__":
    teclado = TecladoHasar()

    # Ejemplo de funciones que se pueden asignar
    def buscar_pago():
        print("Buscando pago...")

    def cerrar_orden():
        print("Cerrando orden...")

    teclado.asignar_funcion("a6", buscar_pago)
    teclado.asignar_funcion("a7", cerrar_orden)

    print("Escuchando teclado... (Presiona ESC para salir)")
    keyboard.wait("esc")  # Espera hasta que se presione ESC"""
