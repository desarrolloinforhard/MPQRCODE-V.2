import tkinter as tk
import ttkbootstrap as ttk
import winsound
import threading
import time


def mostrar_error_y_cerrar(__DATOS__, mensaje, teclado_hasar=None, type_msg="error", remarcar=False):
    if isinstance(mensaje, tuple):
        mensaje = "\n".join(mensaje)

    msgbox = CustomMessageBox(
        __DATOS__["root"],
        "Bad Request",
        mensaje if not remarcar else "",
        type_msg,
        teclado_hasar=teclado_hasar
    )

    if remarcar:
        msgbox.set_formatted_message(mensaje)


class CustomMessageBox:
    def __init__(self, parent=None, title="Mensaje", message="Texto del mensaje", msg_type="info",
                 width=700, height=400, font_size=24, teclado_hasar=None):
        self.running = True
        self.result = None
        self.teclado = teclado_hasar
        self.old_func = None  # Guardar función previa

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

        container = ttk.Frame(self.window, padding=20)
        container.pack(fill="both", expand=True)

        content_frame = ttk.Frame(container)
        content_frame.pack(pady=20, expand=True)

        icon_colors = {"info": "primary", "warning": "warning", "error": "danger"}
        icon_text = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}

        ttk.Label(content_frame, text=icon_text.get(msg_type, "ℹ️"), font=("Arial", font_size + 10),
                  bootstyle=icon_colors.get(msg_type, "primary")).pack(pady=(10, 5))

        self.message_label = ttk.Label(content_frame, text=message, font=("Arial", font_size), wraplength=width - 50)
        self.message_label.pack(pady=5, padx=20, fill="both", expand=True)

        self.create_buttons(content_frame, msg_type, font_size)

        self.window.update_idletasks()
        content_width = content_frame.winfo_reqwidth() + 50
        content_height = content_frame.winfo_reqheight() + 150
        new_width = max(width, content_width)
        new_height = max(height, content_height)
        self.window.geometry(f"{new_width}x{new_height}")
        self.center_window(new_width, new_height)

        threading.Thread(target=self.play_alert_sound, args=(msg_type,), daemon=True).start()

        if self.teclado:
            print(f"[MSGBOX] Se recibió teclado: {id(self.teclado)}")
            self._asignar_funcion_teclado()
        else:
            print("[MSGBOX] NO se recibió teclado")

        self.show()

    def _asignar_funcion_teclado(self):
        if not self.teclado:
            return

        # Guardar función original si ya existe
        self.old_func = self.teclado.funciones_personalizadas.get("6a")

        # Registrar si no estaba
        if "6a" not in self.teclado.funciones_personalizadas:
            self.teclado.registrar_combinacion_personalizada("6a")

        print("[MSGBOX] Asignando tecla 6a para cerrar")
        self.teclado.asignar_funcion_personalizada("6a", lambda: self.window.after(0, self.close))

    def close(self):
        print("[MSGBOX] Cerrando con tecla 6a")
        self.running = False
        self.window.destroy()
        if self.teclado:
            # Restaurar función anterior si había
            if self.old_func:
                self.teclado.asignar_funcion_personalizada("6a", self.old_func)
            else:
                self.teclado.funciones_personalizadas.pop("6a", None)

    def play_alert_sound(self, msg_type):
        tonos = {"warning": 1000, "error": 500, "info": 2000}
        duraciones = {"warning": 1000, "error": 1000, "info": 500}
        winsound.Beep(tonos.get(msg_type, 1000), duraciones.get(msg_type, 500))

    def create_buttons(self, content_frame, msg_type, font_size):
        frame = ttk.Frame(content_frame)
        frame.pack(pady=15, fill="x")
        style = ttk.Style()
        style.configure("Custom.TButton", font=("Arial", font_size))

        if msg_type in ["info", "warning", "error"]:
            ttk.Button(frame, text="OK", command=self.close, style="Custom.TButton", bootstyle="success").pack()
        elif msg_type == "yesno":
            ttk.Button(frame, text="Sí", command=lambda: self.set_result(True), style="Custom.TButton",
                       bootstyle="primary").pack(side="left", padx=10)
            ttk.Button(frame, text="No", command=lambda: self.set_result(False), style="Custom.TButton",
                       bootstyle="danger").pack(side="left", padx=10)

    def set_result(self, value):
        self.result = value
        self.window.destroy()

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

    def set_formatted_message(self, mensaje):
        self.message_label.config(text=mensaje)
