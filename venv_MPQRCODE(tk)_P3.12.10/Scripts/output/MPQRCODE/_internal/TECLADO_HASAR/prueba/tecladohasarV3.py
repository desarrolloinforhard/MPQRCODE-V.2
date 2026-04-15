import tkinter as tk
import time

class TecladoHasar:
    def __init__(self, asignaciones_personalizadas=None):
        self.asignaciones_personalizadas = asignaciones_personalizadas or {}
        self.buffer = []
        self.contenido_actual = ""

        # Estado de entrada
        self.teclado_hasar_activo = True  # Hasar activado por defecto
        self.escaneo_liberado = False  # si está activo, ignora combinaciones
        self.ultimo_tiempo = time.time()
        self.tiempo_inactividad_escaneo = 0.3  # segundos sin input para salir de escáner
        self.escaneo_manual = False  # True si se activó con "44"
        self.escaneo_esta_en_curso = False
        self.ultimo_input_escaneo = time.time()
        self.funciones_personalizadas = {}
        self.entry_asignado = None
        self.estado_por_entry = {}  # cada Entry tendrá su buffer y contenido_actual separados

        # Mapa de teclas
        self.teclas_fijas = {
            "6a": self.enter,              # Enter (si querés usarlo)
            "44": self.toggle_teclado,     # Cambiar modo
            "64": self.borrar_todo,        # Clear total
            "86": self.borrar_1,           # Borrar uno
            "46": lambda: self.insertar("0"),
            "47": lambda: self.insertar("00"),
            "48": lambda: self.insertar("."),
            "56": lambda: self.insertar("1"),
            "57": lambda: self.insertar("2"),
            "58": lambda: self.insertar("3"),
            "66": lambda: self.insertar("4"),
            "67": lambda: self.insertar("5"),
            "68": lambda: self.insertar("6"),
            "76": lambda: self.insertar("7"),
            "77": lambda: self.insertar("8"),
            "78": lambda: self.insertar("9"),
        }


        self.teclas_letras = {
            "a0": 160, "a1": 161, "a2": 162, "a3": 163, "a4": 164, "a5": 165, "a6": 166, "a7": 167, "a8": 168, "a9": 169,
            "90": 144, "91": 145, "92": 146, "93": 147, "94": 148, "95": 149, "96": 150, "97": 151, "98": 152, "99": 153,
            "80": 128, "81": 129, "82": 130, "83": 131,
            "70": 112, "71": 113, "72": 114, "73": 115,
            "60": 96,  "61": 97,  "62": 98,  "63": 99,
            "50": 80,  "51": 81,  "52": 82,  "53": 83,
            "40": 64,  "41": 65,  "42": 66,  "43": 67
        }        
        
    def toggle_teclado(self):
        if self.escaneo_liberado:
            self.activar_modo_hasar()
        else:
            self.activar_modo_escaneo()


    def insertar(self, texto):
        print(f"✍️ Insertando: {texto}")
        if self.entry_asignado in self.estado_por_entry:
            estado = self.estado_por_entry[self.entry_asignado]
            estado["contenido_actual"] += texto

    def borrar_1(self):
        if self.entry_asignado in self.estado_por_entry:
            estado = self.estado_por_entry[self.entry_asignado]
            estado["contenido_actual"] = estado["contenido_actual"][:-1]

    def borrar_todo(self):
        if self.entry_asignado in self.estado_por_entry:
            estado = self.estado_por_entry[self.entry_asignado]
            estado["contenido_actual"] = ""



    def enter(self):
        print("⏎ Se presionó ENTER (no hace nada por ahora)")
        
        
    def activar_modo_escaneo(self):
        self.escaneo_liberado = True
        self.escaneo_manual = True
        print("🔓 Modo ESCÁNER activado (no se procesan combinaciones)")


    def activar_modo_hasar(self):
        self.escaneo_liberado = False
        self.escaneo_manual = False
        print("🔐 Modo HASAR activado (procesa combinaciones)")




    def asignar_entry(self, entry_widget):
        self.entry_asignado = entry_widget  # ✅ NUEVO: guardar el Entry activo
        self.estado_por_entry[entry_widget] = {
            "buffer": [],
            "contenido_actual": "",
            "escaneo_esta_en_curso": False,
            "ultimo_input_escaneo": time.time()
        }


        def on_key(event):
            if not self.teclado_hasar_activo:
                return

            if event.char:
                tecla = event.char.lower()
                estado = self.estado_por_entry[entry_widget]

                resultado = self.procesar_tecla(tecla, estado)
                
                # 🛑 Si se indicó cancelar inserción (como "44"), no insertar nada
                if resultado == "__CANCELAR_INSERCION__":
                    return "break"

                if resultado is not None:
                    estado["contenido_actual"] += resultado

                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, estado["contenido_actual"])
                entry_widget.icursor(tk.END)
                return "break"

        def revisar_inactividad():
            estado = self.estado_por_entry[entry_widget]
            if self.escaneo_liberado and estado["escaneo_esta_en_curso"]:
                delta = time.time() - estado["ultimo_input_escaneo"]
                if delta > self.tiempo_inactividad_escaneo:
                    print("🕒 Fin de escaneo detectado → volvemos a modo Hasar")
                    self.activar_modo_hasar()
                    estado["escaneo_esta_en_curso"] = False
            entry_widget.after(100, revisar_inactividad)


        entry_widget.bind("<Key>", on_key)
        revisar_inactividad()

    def procesar_tecla(self, tecla, estado):
        print(f"🔹 Tecla recibida: {tecla}")
        self.ultimo_tiempo = time.time()

        # 🔁 Si estamos en modo escáner, dejamos pasar las teclas crudas
        if self.escaneo_liberado:
            estado["buffer"].append(tecla)

            # ✅ Registrar actividad si la tecla es letra o número
            if tecla.isalnum():
                estado["escaneo_esta_en_curso"] = True
                estado["ultimo_input_escaneo"] = time.time()

            # Permitimos salir del modo escáner si detectamos la combinación 44
            if len(estado["buffer"]) >= 2:
                combinacion = estado["buffer"][-2] + estado["buffer"][-1]
                if combinacion == "44":
                    print(f"📦 [ESCÁNER] Cambio de modo forzado con combinación: {combinacion}")
                    self.toggle_teclado()
                    estado["buffer"].clear()

                    # ❌ Evitar que se inserten los dos últimos caracteres ("4" + "4")
                    if "contenido_actual" in estado and len(estado["contenido_actual"]) >= 2:
                        estado["contenido_actual"] = estado["contenido_actual"][:-2]

                    return "__CANCELAR_INSERCION__"


            if len(estado["buffer"]) >= 2:
                combinacion = estado["buffer"][-2] + estado["buffer"][-1]
                if combinacion == "44":
                    print(f"📦 [ESCÁNER] Cambio de modo forzado con combinación: {combinacion}")
                    self.toggle_teclado()
                    estado["buffer"].clear()
                    return "__CANCELAR_INSERCION__"

            if len(estado["buffer"]) > 2:
                estado["buffer"] = estado["buffer"][-2:]

            # ✅ Solo devolver si NO es parte de una posible "44"
            # Si acaba de empezar a tipear, no insertamos hasta tener 2 teclas
            if len(estado["buffer"]) == 1:
                return None  # esperar a formar combinación

            return tecla


            return tecla
        # 🔁 Modo HASAR normal
        estado["buffer"].append(tecla)

        if len(estado["buffer"]) >= 2:
            combinacion = estado["buffer"][-2] + estado["buffer"][-1]
            print(f"📦 Detectada combinación: {combinacion}")

            # 1. Ejecutar función personalizada si existe
            if combinacion in self.funciones_personalizadas:
                self.funciones_personalizadas[combinacion]()
                estado["buffer"].clear()
                return None

            # 2. Ejecutar si está en teclas fijas
            if combinacion in self.teclas_fijas:
                accion = self.teclas_fijas[combinacion]
                accion()
                estado["buffer"].clear()
                return None

            # 3. Buscar en teclas_letras y devolver asignación personalizada
            numero = self.teclas_letras.get(combinacion)
            if numero:
                estado["buffer"].clear()
                if numero in self.asignaciones_personalizadas:
                    return self.asignaciones_personalizadas[numero]
                return None

        if len(estado["buffer"]) > 2:
            estado["buffer"] = estado["buffer"][-2:]

        return None


    
    def esta_en_modo_hasar(self):
        return not self.escaneo_liberado
    
    def asignar_funcion_personalizada(self, combinacion, funcion):
        """
        Asigna una función a ejecutar cuando se detecta una combinación (como '4a', 'a0', etc.)
        """
        self.funciones_personalizadas[combinacion] = funcion
        
    def registrar_combinacion_personalizada(self, combinacion):
        """
        Permite registrar combinaciones como 'a6' que no estén en teclas_letras,
        para que sean reconocidas y capturadas como válidas.
        """
        if not hasattr(self, "combinaciones_personalizadas"):
            self.combinaciones_personalizadas = set()
        self.combinaciones_personalizadas.add(combinacion)
        
        
    def eliminar_funcion_de_combinacion(self, combinacion):
        if combinacion in self.teclas_fijas:
            del self.teclas_fijas[combinacion]
            print(f"❌ Combinación '{combinacion}' desactivada de teclas_fijas")
        if combinacion in self.funciones_personalizadas:
            del self.funciones_personalizadas[combinacion]
            print(f"❌ Combinación '{combinacion}' desactivada de funciones_personalizadas")



    def activar_escucha_global(self, widget_raiz):
        def on_key(event):
            if not self.teclado_hasar_activo:
                return

            if event.char:
                tecla = event.char.lower()
                resultado = self.procesar_tecla(tecla)

                # Si devuelve texto, no hacemos nada (en modo global)
                if resultado:
                    print(f"🔤 Resultado ignorado (modo global): {resultado}")

        widget_raiz.bind("<Key>", on_key)
        
        
    def activar_escucha_funciones_global(self, widget_raiz):
        print("✅ Escucha global ACTIVADA en:", widget_raiz)

        def on_key(event):
            print(f"🟡 Tecla presionada: {event.char} ({event.keysym})")

            if not self.teclado_hasar_activo:
                print("⛔ Teclado Hasar no activo")
                return

            tecla = event.char.lower() if event.char else None
            if not tecla:
                return

            if not hasattr(self, "buffer_global"):
                self.buffer_global = []

            self.buffer_global.append(tecla)

            if len(self.buffer_global) > 2:
                self.buffer_global = self.buffer_global[-2:]

            if len(self.buffer_global) == 2:
                combinacion = self.buffer_global[0] + self.buffer_global[1]
                print(f"🔍 Combinación detectada: {combinacion}")
                if combinacion in self.funciones_personalizadas:
                    print(f"🎯 Ejecutando función personalizada para: {combinacion}")
                    self.funciones_personalizadas[combinacion]()
                    self.buffer_global.clear()

        widget_raiz.bind_all("<Key>", on_key)

        
    """def activar_escucha_funciones_global(self, widget_raiz):
        def on_key(event):
            if not self.teclado_hasar_activo:
                return

            tecla = event.char.lower() if event.char else None
            if not tecla:
                return

            if not hasattr(self, "buffer_global"):
                self.buffer_global = []

            self.buffer_global.append(tecla)

            if len(self.buffer_global) > 2:
                self.buffer_global = self.buffer_global[-2:]

            if len(self.buffer_global) == 2:
                combinacion = self.buffer_global[0] + self.buffer_global[1]
                if combinacion in self.funciones_personalizadas:
                    print(f"🎯 Ejecutando función para combinación global: {combinacion}")
                    self.funciones_personalizadas[combinacion]()
                    self.buffer_global.clear()

        widget_raiz.bind_all("<Key>", on_key)"""
        
    def resetear_estado(self):
        self.buffer.clear()
        self.contenido_actual = ""
        self.escaneo_esta_en_curso = False
        self.ultimo_input_escaneo = time.time()



            


