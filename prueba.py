import pyautogui
import time
import subprocess

# Abre tu aplicación Tkinter
proc = subprocess.Popen(["python", "main.py"])

# Espera un momento para que la aplicación se abra completamente
time.sleep(5)

"""# Obtén las coordenadas del botón que deseas hacer clic
button_x, button_y = pyautogui.locateCenterOnScreen('ruta_de_la_imagen_del_boton.png')

# Haz clic en el botón
pyautogui.click(button_x, button_y)
"""