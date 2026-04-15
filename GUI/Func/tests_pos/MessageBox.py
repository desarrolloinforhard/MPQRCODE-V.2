import tkinter as tk
import ttkbootstrap as ttk
import winsound
import threading
import re


def mostrar_error_y_cerrar(__DATOS__, mensaje, teclado_hasar=None, type_msg="error", remarcar=False):
    if isinstance(mensaje, tuple):
        mensaje = "\n".join(mensaje)

    msgbox = CustomMessageBox(
        __DATOS__["root"],
        "Bad Request",
        mensaje,
        type_msg,
        teclado_hasar=teclado_hasar,
        remarcar=remarcar
    )

    # ✅ Guardás el objeto ANTES de mostrar
    __DATOS__["variable_contendora_MensajeERROR"] = msgbox

    # 🟡 Ahora sí lo mostrás (espera hasta que se cierre)
    msgbox.show()
    print("Retorna")

    return msgbox


def mostrar_cancelar_continuar(__DATOS__, mensaje, teclado_hasar=None, remarcar=False, title="Confirmación"):
    if isinstance(mensaje, tuple):
        mensaje = "\n".join(mensaje)

    msgbox = CustomMessageBox(
        __DATOS__["root"],
        title,
        mensaje,
        msg_type="continuar_cancelar",   # 👈 nuevo tipo
        teclado_hasar=teclado_hasar,
        remarcar=remarcar
    )
    __DATOS__["variable_contendora_MensajeERROR"] = msgbox
    return msgbox.show()   # True=Continuar / False=Cancelar


def mostrar_reintentar_cancelar(__DATOS__, mensaje, teclado_hasar=None, remarcar=False, title="Reintentar/CANCELAR"):
    if isinstance(mensaje, tuple):
        mensaje = "\n".join(mensaje)

    msgbox = CustomMessageBox(
        __DATOS__["root"],
        title,
        mensaje,
        msg_type="reintentar_cancelar",
        teclado_hasar=teclado_hasar,
        remarcar=remarcar
    )
    __DATOS__["variable_contendora_MensajeERROR"] = msgbox
    return msgbox.show()  # True = Reintentar, False = Cancelar





class CustomMessageBox:
    def __init__(self, parent=None, title="Mensaje", message="Texto del mensaje", msg_type="info",
                 width=600, height=400, font_size=24, teclado_hasar=None, remarcar=False):
        self.running = True
        self.result = None
        self.teclado = teclado_hasar
        self.old_func = None
        self.msg_type = msg_type

        if parent is None:
            self.parent = tk.Tk()
            self.parent.withdraw()
            self.window = tk.Toplevel(self.parent)
        else:
            self.parent = parent
            self.window = ttk.Toplevel(parent)

        self.window.title(title)
        self.window.protocol("WM_DELETE_WINDOW", lambda: None)
        self.window.transient(self.parent)
        self.window.grab_set()
        self._detach_keyboard = None
        if self.teclado:
            self._detach_keyboard = self.teclado.attach_widget(self.window)


        container = ttk.Frame(self.window, padding=20)
        container.pack(fill="both", expand=True)

        content_frame = ttk.Frame(container)
        content_frame.pack(pady=20, expand=True, fill="both")

        icon_colors = {"info": "primary", "warning": "warning", "error": "danger",
               "yesno": "primary", "continuar_cancelar": "warning", "reintentar_cancelar": "warning"}
        icon_text   = {"info": "ℹ️", "warning": "⚠️", "error": "❌",
                    "yesno": "❓", "continuar_cancelar": "❓", "reintentar_cancelar": "↻"}  # ↻ reintentar



        ttk.Label(content_frame, text=icon_text.get(msg_type, "ℹ️"), font=("Arial", font_size + 10),
                  bootstyle=icon_colors.get(msg_type, "primary")).pack(pady=(10, 5))

        self.text_box = tk.Text(content_frame, font=("Arial", font_size), wrap="word", height=8, bg="white", relief="flat", width=60)
        self.text_box.pack(padx=10, pady=10, fill="both", expand=True)
        self.text_box.config(state="disabled")

        if remarcar:
            self.insert_remarcado(message)
        else:
            self.insert_texto_plano(message)

        self.create_buttons(content_frame, msg_type, font_size)

        self.window.update_idletasks()
        width = max(width, self.window.winfo_reqwidth())
        height = max(height, self.window.winfo_reqheight())
        self.window.after_idle(lambda: self.center_window(width, height))  # centrado correcto

        threading.Thread(target=self.play_alert_sound, args=(msg_type,), daemon=True).start()

        self._ctx_token = None
        if self.teclado:
            print(f"[MSGBOX] Se recibió teclado: {id(self.teclado)}")
            self._instalar_contexto_teclado()
        else:
            print("[MSGBOX] NO se recibió teclado")
            
    def _key_confirm(self):
        if self.msg_type in ("yesno", "continuar_cancelar", "reintentar_cancelar"):
            self.set_result(True)

    def _key_cancel(self):
        if self.msg_type in ("yesno", "continuar_cancelar", "reintentar_cancelar"):
            self.set_result(False)

    def _on_confirm_key(self):
        if self.msg_type in ("yesno", "continuar_cancelar", "reintentar_cancelar"):
            self.set_result(True)
        else:
            self.close()

    def _on_cancel_key(self):
        if self.msg_type in ("yesno", "continuar_cancelar", "reintentar_cancelar"):
            self.set_result(False)
        else:
            self.close()


    """def _restaurar_teclas(self):
        if not getattr(self, "teclado", None):
            return
        old = getattr(self, "_old_funcs", {})
        for combo in ("6a", "86"):
            fn = old.get(combo)
            if fn:
                self.teclado.asignar_funcion_personalizada(combo, fn)
            else:
                # si no tenía asignación previa, la quitamos
                self.teclado.funciones_personalizadas.pop(combo, None)"""



    def insert_texto_plano(self, mensaje):
        if isinstance(mensaje, tuple):
            mensaje = "\n".join(mensaje)
        self.text_box.config(state="normal")
        self.text_box.delete("1.0", tk.END)
        self.text_box.insert(tk.END, mensaje)
        self.text_box.config(state="disabled")

    def insert_remarcado(self, mensaje):
        if isinstance(mensaje, tuple):
            mensaje = "\n".join(mensaje)

        self.text_box.config(state="normal")
        self.text_box.delete("1.0", tk.END)

        pattern = r"\*\((.+?)\{(.+?)\}\)\*"
        last_index = 0

        for match in re.finditer(pattern, mensaje):
            start, end = match.span()
            normal_text = mensaje[last_index:start]
            word, color = match.group(1), match.group(2)

            self.text_box.insert(tk.END, normal_text)
            tag_name = f"color_{color}"
            self.text_box.tag_config(tag_name, foreground=color, font=("Arial", 24, "bold"))
            self.text_box.insert(tk.END, word, tag_name)
            last_index = end

        self.text_box.insert(tk.END, mensaje[last_index:])
        self.text_box.config(state="disabled")

    """def _asignar_funcion_teclado(self):
        if not self.teclado:
            return

        # backup de funciones previas (para restaurar al cerrar)
        self._old_funcs = getattr(self, "_old_funcs", {})
        for combo in ("6a", "86"):
            if combo not in self.teclado.funciones_personalizadas:
                self.teclado.registrar_combinacion_personalizada(combo)
            self._old_funcs[combo] = self.teclado.funciones_personalizadas.get(combo)

        # Mapeo según el tipo de mensaje
        if getattr(self, "msg_type", None) == "continuar_cancelar":
            print("[MSGBOX] Asignando teclas (continuar_cancelar): 6a=Continuar, 86=Cancelar")
            mapping = {"6a": self._on_confirm_key, "86": self._on_cancel_key}
        elif getattr(self, "msg_type", None) == "reintentar_cancelar":
            print("[MSGBOX] Asignando teclas (reintentar_cancelar): 6a=Reintentar, 86=Cancelar")
            mapping = {"6a": self._on_confirm_key, "86": self._on_cancel_key}  # 👈 6a confirma, 86 cancela
        else:
            print("[MSGBOX] Asignando teclas (default): 6a=Cancelar, 86=Continuar")
            mapping = {"6a": self._on_cancel_key, "86": self._on_confirm_key}


        # asignación con after y cierre correcto
        for combo, fn in mapping.items():
            self.teclado.asignar_funcion_personalizada(combo,
                (lambda fn=fn: self.window.after(0, fn))
            )"""




    def close(self):
        print("[MSGBOX] Cerrando con tecla o botón")

        if self.msg_type in ("yesno", "continuar_cancelar") and self.result is None:
            self.result = False

        # ✅ sacar contexto primero
        try:
            if self.teclado and self._ctx_token:
                self.teclado.pop_context(self._ctx_token)
                self._ctx_token = None
        except Exception:
            pass

        self.running = False
        try:
            if self._detach_keyboard:
                self._detach_keyboard()
                self._detach_keyboard = None
        except Exception:
            pass

        try:
            self.window.destroy()
        except Exception:
            pass




    def play_alert_sound(self, msg_type):
        tonos = {"warning": 1000, "error": 500, "info": 2000}
        duraciones = {"warning": 1000, "error": 1000, "info": 500}
        winsound.Beep(tonos.get(msg_type, 1000), duraciones.get(msg_type, 500))

    def create_buttons(self, content_frame, msg_type, font_size):
        self._botones = []
        self._idx_focus = 0

        frame = ttk.Frame(content_frame)
        frame.pack(pady=15, fill="x")

        style = ttk.Style()
        style.configure("Custom.TButton", font=("Arial", font_size))

        def add_btn(**kwargs):
            """Crea botón, lo packea y lo registra para navegación."""
            pack_info = kwargs.pop("pack_info", {})
            btn = ttk.Button(frame, **kwargs)
            btn.pack(**pack_info)
            self._botones.append(btn)
            return btn

        if msg_type in ["info", "warning", "error"]:
            add_btn(
                text="OK",
                command=self.close,
                style="Custom.TButton",
                bootstyle="success",
                pack_info={"side": "top", "padx": 10}
            )
            self._idx_focus = 0

        elif msg_type == "yesno":
            # Orden: Sí (izq) / No (der)
            add_btn(
                text="Sí",
                command=lambda: self.set_result(True),
                style="Custom.TButton",
                bootstyle="primary",
                pack_info={"side": "left", "padx": 10}
            )
            add_btn(
                text="No",
                command=lambda: self.set_result(False),
                style="Custom.TButton",
                bootstyle="danger",
                pack_info={"side": "left", "padx": 10}
            )
            self._idx_focus = 0  # default: Sí

        elif msg_type == "continuar_cancelar":
            # Orden: Cancelar (izq) / Continuar (der) => default: Continuar
            if self.teclado is None:
                add_btn(
                    text="Cancelar",
                    command=lambda: self.set_result(False),
                    style="Custom.TButton",
                    bootstyle="secondary",
                    pack_info={"side": "left", "padx": 10}
                )
                add_btn(
                    text="Continuar",
                    command=lambda: self.set_result(True),
                    style="Custom.TButton",
                    bootstyle="success",
                    pack_info={"side": "right", "padx": 10}
                )
            else:
                add_btn(
                    text="Cancelar (Clear)",
                    command=lambda: self.set_result(False),
                    style="Custom.TButton",
                    bootstyle="secondary",
                    pack_info={"side": "left", "padx": 10}
                )
                add_btn(
                    text="Continuar (Sub Total)",
                    command=lambda: self.set_result(True),
                    style="Custom.TButton",
                    bootstyle="success",
                    pack_info={"side": "right", "padx": 10}
                )

            # En este tipo, el default UX es "Continuar" => índice 1
            self._idx_focus = 1 if len(self._botones) > 1 else 0

        elif msg_type == "reintentar_cancelar":
            # Orden: Cancelar (izq) / Reintentar (der) => default: Reintentar
            if self.teclado is None:
                add_btn(
                    text="Cancelar",
                    command=lambda: self.set_result(False),
                    style="Custom.TButton",
                    bootstyle="secondary",
                    pack_info={"side": "left", "padx": 10}
                )
                add_btn(
                    text="Reintentar",
                    command=lambda: self.set_result(True),
                    style="Custom.TButton",
                    bootstyle="success",
                    pack_info={"side": "right", "padx": 10}
                )
            else:
                add_btn(
                    text="Cancelar (Clear)",
                    command=lambda: self.set_result(False),
                    style="Custom.TButton",
                    bootstyle="secondary",
                    pack_info={"side": "left", "padx": 10}
                )
                add_btn(
                    text="Reintentar (Sub Total)",
                    command=lambda: self.set_result(True),
                    style="Custom.TButton",
                    bootstyle="success",
                    pack_info={"side": "right", "padx": 10}
                )

            self._idx_focus = 1 if len(self._botones) > 1 else 0

        else:
            # fallback
            add_btn(
                text="OK",
                command=self.close,
                style="Custom.TButton",
                bootstyle="success",
                pack_info={"side": "top", "padx": 10}
            )
            self._idx_focus = 0

        # ✅ foco inicial al botón default
        self.window.after(50, lambda: self._focus_button(self._idx_focus))



    def _focus_button(self, idx: int):
        if not getattr(self, "_botones", None):
            return
        idx = max(0, min(idx, len(self._botones) - 1))
        self._idx_focus = idx
        try:
            self._botones[idx].focus_set()
        except Exception:
            pass

    def _move_focus(self, delta: int):
        if not getattr(self, "_botones", None):
            return
        self._focus_button(self._idx_focus + delta)

    def _invoke_focused(self):
        if not getattr(self, "_botones", None):
            return
        try:
            self._botones[self._idx_focus].invoke()
        except Exception:
            pass



    def set_result(self, value):
        self.result = value
        self.close()


    def center_window(self, width, height):
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def show(self):
        try:
            if self.window.winfo_exists():
                self.window.lift()
                self.window.focus_force()
                self.window.wait_window()
        except Exception as e:
            import traceback
            print(traceback.format_exc())
        return self.result
    def _instalar_contexto_teclado(self):
        if not self.teclado:
            return

        # Mapeo Hasar -> acciones estándar:
        # ✅ Tu requerimiento: 86 = Enter / 6a = Escape
        hasar_map = {
            "86": lambda: self.window.after(0, self._on_confirm_key),
            "6a": lambda: self.window.after(0, self._on_cancel_key),
        }

        # En teclado normal también: Return/Escape
        normal_map = {
            "Return": lambda: self.window.after(0, self._on_confirm_key),
            "KP_Enter": lambda: self.window.after(0, self._on_confirm_key),
            "Escape": lambda: self.window.after(0, self._on_cancel_key),
        }

        self._ctx_token = self.teclado.push_context(
            name=f"MSGBOX:{self.msg_type}",
            hasar_map=hasar_map,
            normal_map=normal_map
        )
