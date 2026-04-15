import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os


RUTA_JSON = os.path.join(os.path.dirname(__file__), "TABLAS_DBA.json")


class TablaEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("Editor de TABLAS_DBA.json")
        self.data = {}
        self.tabla_actual = None

        self.combo_tablas = ttk.Combobox(master, state="readonly")
        self.combo_tablas.pack(padx=10, pady=10)
        self.combo_tablas.bind("<<ComboboxSelected>>", self.mostrar_columnas)

        self.tree = ttk.Treeview(master, columns=("Nombre", "Tipo"), show="headings")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.frame_abajo = tk.Frame(master)
        self.frame_abajo.pack(pady=10)

        tk.Button(self.frame_abajo, text="Agregar columna", command=self.agregar_columna).grid(row=0, column=0, padx=5)
        tk.Button(self.frame_abajo, text="Eliminar columna", command=self.eliminar_columna).grid(row=0, column=1, padx=5)
        tk.Button(self.frame_abajo, text="Guardar cambios", command=self.guardar).grid(row=0, column=2, padx=5)

        self.cargar_datos()

    def cargar_datos(self):
        try:
            with open(RUTA_JSON, "r", encoding="utf-8") as f:
                self.data = json.load(f)
                self.combo_tablas["values"] = list(self.data.keys())
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el JSON: {e}")

    def mostrar_columnas(self, event=None):
        self.tabla_actual = self.combo_tablas.get()
        self.tree.delete(*self.tree.get_children())
        if self.tabla_actual in self.data:
            for nombre, tipo in self.data[self.tabla_actual]:
                self.tree.insert("", tk.END, values=(nombre, tipo))

    def agregar_columna(self):
        def guardar():
            nombre = entry_nombre.get().strip()
            tipo = entry_tipo.get().strip()
            if nombre and tipo:
                self.data[self.tabla_actual].append((nombre, tipo))
                self.tree.insert("", tk.END, values=(nombre, tipo))
                ventana.destroy()
            else:
                messagebox.showwarning("Campos vacíos", "Debes ingresar nombre y tipo.")

        ventana = tk.Toplevel(self.master)
        ventana.title("Agregar columna")

        tk.Label(ventana, text="Nombre de columna:").pack(pady=5)
        entry_nombre = tk.Entry(ventana)
        entry_nombre.pack(pady=5)

        tk.Label(ventana, text="Tipo de dato:").pack(pady=5)
        entry_tipo = tk.Entry(ventana)
        entry_tipo.pack(pady=5)

        tk.Button(ventana, text="Agregar", command=guardar).pack(pady=10)

    def eliminar_columna(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Selecciona una fila", "Debes seleccionar una columna para eliminar.")
            return

        for item in seleccion:
            nombre_columna = self.tree.item(item)["values"][0]
            self.data[self.tabla_actual] = [col for col in self.data[self.tabla_actual] if col[0] != nombre_columna]
            self.tree.delete(item)

    def guardar(self):
        try:
            with open(RUTA_JSON, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            messagebox.showinfo("Guardado", "Cambios guardados correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")


if __name__ == "__main__":
    from tkinter import Tk
    root = Tk()
    app = TablaEditor(root)
    root.mainloop()
