import tkinter as tk
from tecladohasar import TecladoHasar

# Función personalizada: abrir ventana para ingresar DNI
def abrir_ventana_dni():
    ventana = tk.Toplevel()
    ventana.title("Ingresar DNI")
    ventana.geometry("300x100")

    label = tk.Label(ventana, text="DNI:", font=("Arial", 12))
    label.pack(pady=5)

    entry_dni = tk.Entry(ventana, font=("Arial", 14))
    entry_dni.pack(pady=5)
    entry_dni.focus()

    teclado.resetear_estado()  # ✅ limpiar contenido antes de reasignar
    teclado.asignar_entry(entry_dni)
    teclado.activar_escucha_funciones_global(ventana)

    def cerrar():
        teclado.resetear_estado()
        ventana.destroy()

    ventana.protocol("WM_DELETE_WINDOW", cerrar)




# Diccionario opcional de asignaciones personalizadas
asignaciones = {
    160: "A", 161: "B", 162: "C"  # para combinaciones tipo "a0", "a1", etc.
}

# Crear ventana principal
root = tk.Tk()
root.title("Teclado Hasar + Escucha Global")
root.geometry("400x250")

# Crear un Entry para escribir
entry = tk.Entry(root, font=("Arial", 16), width=30)
entry.pack(pady=20)

# Crear el objeto teclado
teclado = TecladoHasar(asignaciones)

# Asignar el Entry para escritura tipo Hasar
teclado.asignar_entry(entry)

# Asignar función personalizada a una combinación (ej. a6)
teclado.teclas_fijas["a6"] = abrir_ventana_dni  # también podrías usar .asignar_funcion_personalizada()

# Escuchar combinaciones desde cualquier parte de la app
teclado.activar_escucha_funciones_global(root)

# Botón opcional para mostrar el modo actual (Hasar o Escáner)
def mostrar_modo():
    modo = "HASAR" if teclado.esta_en_modo_hasar() else "ESCÁNER"
    print(f"📘 Modo actual: {modo}")

tk.Button(root, text="Mostrar modo", command=mostrar_modo).pack(pady=5)

root.mainloop()
