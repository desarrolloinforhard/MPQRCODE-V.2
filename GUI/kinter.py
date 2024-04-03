import tkinter as tk
from tkinter import messagebox

class CrearSucursalApp:
    def __init__(self, master):
        self.master = master
        self.top_level = tk.Toplevel(master)
        self.top_level.protocol("WM_DELETE_WINDOW", self.on_close)
        self.top_level.geometry("300x200")
        self.top_level.title("Crear Sucursal")
        self.create_widgets()

    def create_widgets(self):
        self.label = tk.Label(self.top_level, text="Ventana para crear la sucursal")
        self.label.pack(pady=20)
        self.button_close = tk.Button(self.top_level, text="Cerrar", command=self.on_close)
        self.button_close.pack(pady=10)

    def on_close(self):
        self.master.deiconify()  # Restaurar la ventana principal
        self.top_level.destroy()


class App:
    def __init__(self, master):
        self.master = master
        self.master.geometry("300x200")
        self.master.title("Ventana Principal")
        self.create_widgets()

    def create_widgets(self):
        self.button_open = tk.Button(self.master, text="Abrir Ventana de Crear Sucursal", command=self.crear_sucursal_app)
        self.button_open.pack(pady=20)

    def crear_sucursal_app(self):
        try:
            self.master.withdraw()  # Ocultar la ventana principal
            CrearSucursalApp(self.master)
        except Exception as e:
            print(e)
            messagebox.showerror("Error", f"Error al crear la instancia de CrearSucursalApp: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
